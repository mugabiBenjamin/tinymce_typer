import time

from tinymce_typer.app.container import AppContainer, AppContainerFactory
from tinymce_typer.app.result import AppResult
from tinymce_typer.config.settings import AppConfig
from tinymce_typer.content.formatter import FormatMode
from tinymce_typer.content.models import ContentDocument, FormattedContent
from tinymce_typer.editors.models import EditorCandidate
from tinymce_typer.exceptions import TinyMCETyperError
from tinymce_typer.insertion.base import InsertionContext, InsertionProgress, InsertionResult
from tinymce_typer.output.models import RunOutput
from tinymce_typer.sessions.models import SessionMetadata, SessionProgress, SessionState
from tinymce_typer.verification.models import VerificationResult


class TyperApp:
    def __init__(
        self,
        config: AppConfig,
        container: AppContainer | None = None,
    ):
        self.config = config
        self.container = container or AppContainerFactory().build(config)

    def run(self) -> AppResult:
        started_at = time.monotonic()
        browser_session = None

        try:
            document = self.container.content_loader.load_from_config(self.config.content)
            formatted = self._format_content(document)

            browser_session = self.container.browser_provider.start(self.config.browser)
            driver = browser_session.driver

            self.container.browser_navigator.navigate(
                driver=driver,
                browser_config=self.config.browser,
                content_config=self.config.content,
                editor_config=self.config.editor,
            )

            editor_candidate = self.container.editor_detector.find_and_focus(driver, self.config.editor)
            editor_adapter = self.container.editor_detector.adapter_for(editor_candidate)

            resume_offset = self._resolve_resume_offset(document, editor_candidate)

            insertion_result = self.container.insertion_chain.insert(
                InsertionContext(
                    driver=driver,
                    adapter=editor_adapter,
                    candidate=editor_candidate,
                    document=document,
                    formatted=formatted,
                    start_offset=resume_offset,
                    append=resume_offset > 0,
                    progress_callback=self.container.progress_reporter.update,
                    session_callback=lambda progress: self._save_progress(
                        progress=progress,
                        document=document,
                        editor_candidate=editor_candidate,
                    ),
                )
            )

            self.container.progress_reporter.complete()

            verification_result = self._verify(
                driver=driver,
                document=document,
                formatted=formatted,
                editor_candidate=editor_candidate,
            )

            output = self._build_output(
                insertion_result=insertion_result,
                verification_result=verification_result,
                editor_candidate=editor_candidate,
                duration_seconds=time.monotonic() - started_at,
                content_length=document.total_character_count,
            )

            self._write_output(output)

            self._mark_session_completed(
                document=document,
                editor_candidate=editor_candidate,
                insertion_result=insertion_result,
            )

            self.container.browser_lifecycle.handle_completion(browser_session, self.config.browser)

            return AppResult.ok(
                message=output.message,
                duration_seconds=time.monotonic() - started_at,
                insertion=insertion_result,
                verification=verification_result,
                output=output,
                metadata={
                    "editor": editor_candidate.kind.value,
                    "strategy": insertion_result.strategy_name,
                },
            )

        except KeyboardInterrupt:
            duration = time.monotonic() - started_at
            self.container.progress_reporter.fail("Interrupted by user")
            self.container.browser_lifecycle.handle_failure(browser_session, self.config.browser)

            return AppResult.fail(
                message="Interrupted by user.",
                exit_code=130,
                duration_seconds=duration,
            )

        except TinyMCETyperError as exc:
            duration = time.monotonic() - started_at
            self.container.progress_reporter.fail(str(exc))
            self.container.browser_lifecycle.handle_failure(browser_session, self.config.browser)

            output = RunOutput.failure(
                message=str(exc),
                duration_seconds=duration,
                errors=(str(exc),),
                metadata={"error_type": exc.__class__.__name__},
            )
            self._write_output(output)

            return AppResult.fail(
                message=str(exc),
                exit_code=getattr(exc, "exit_code", 1),
                duration_seconds=duration,
                errors=(str(exc),),
                output=output,
                metadata={"error_type": exc.__class__.__name__},
            )

        except Exception as exc:
            duration = time.monotonic() - started_at
            self.container.progress_reporter.fail(str(exc))
            self.container.browser_lifecycle.handle_failure(browser_session, self.config.browser)

            output = RunOutput.failure(
                message=f"Unexpected application failure: {exc}",
                duration_seconds=duration,
                errors=(str(exc),),
                metadata={"error_type": exc.__class__.__name__},
            )
            self._write_output(output)

            return AppResult.fail(
                message=f"Unexpected application failure: {exc}",
                exit_code=1,
                duration_seconds=duration,
                errors=(str(exc),),
                output=output,
                metadata={"error_type": exc.__class__.__name__},
            )

    def _format_content(self, document: ContentDocument) -> FormattedContent:
        mode = FormatMode.PARAGRAPHS

        if self.config.insertion.formatted:
            mode = FormatMode.HTML

        return self.container.content_formatter.format_document(document, mode=mode)

    def _resolve_resume_offset(
        self,
        document: ContentDocument,
        editor_candidate: EditorCandidate,
    ) -> int:
        store = self.container.session_store

        if store is None:
            return 0

        if self.config.session.reset:
            store.delete()
            return 0

        if self.config.session.no_resume:
            return 0

        saved_session = store.load()

        if saved_session is None:
            return 0

        validation = self.container.session_validator.validate_resume(
            session=saved_session,
            config=self.config,
            document=document,
            editor_candidate=editor_candidate,
            force_url=self.config.session.force_resume_url,
        )

        if not validation.allowed:
            reasons = "; ".join(validation.reasons)

            if self.config.session.resume:
                raise TinyMCETyperError(f"Cannot resume saved session: {reasons}")

            return 0

        if validation.warnings:
            if self.config.session.resume or self.config.cli.yes:
                return saved_session.progress.offset

            confirmed = self.container.prompt_manager.confirm_resume_warnings(validation.warnings)

            if confirmed:
                return saved_session.progress.offset

            return 0

        if self.config.session.resume:
            return saved_session.progress.offset

        if self.config.cli.non_interactive:
            return 0

        if self.container.prompt_manager.ask_resume():
            return saved_session.progress.offset

        return 0

    def _save_progress(
        self,
        progress: InsertionProgress,
        document: ContentDocument,
        editor_candidate: EditorCandidate,
    ) -> None:
        store = self.container.session_store

        if store is None:
            return

        state = SessionState(
            metadata=self._session_metadata(document, editor_candidate, progress.strategy_name),
            progress=SessionProgress(
                offset=progress.offset,
                total=progress.total,
                inserted=progress.inserted,
                current_file=progress.current_file,
                current_file_offset=0,
                completed=False,
                last_strategy=progress.strategy_name,
            ),
        )

        store.save(state)

    def _mark_session_completed(
        self,
        document: ContentDocument,
        editor_candidate: EditorCandidate,
        insertion_result: InsertionResult,
    ) -> None:
        store = self.container.session_store

        if store is None:
            return

        state = SessionState(
            metadata=self._session_metadata(document, editor_candidate, insertion_result.strategy_name),
            progress=SessionProgress(
                offset=insertion_result.final_offset,
                total=document.total_character_count,
                inserted=insertion_result.inserted_characters,
                current_file="",
                current_file_offset=0,
                completed=insertion_result.success,
                last_strategy=insertion_result.strategy_name,
            ),
        )

        store.save(state)

    def _session_metadata(
        self,
        document: ContentDocument,
        editor_candidate: EditorCandidate,
        strategy_name: str,
    ) -> SessionMetadata:
        return SessionMetadata(
            url=self.config.content.url,
            source_file=self.config.content.file,
            content_hash=document.content_hash,
            insertion_strategy=strategy_name,
            editor_kind=editor_candidate.kind.value,
            editor_identifier=self.container.session_validator.editor_identifier(editor_candidate),
        )

    def _verify(
        self,
        driver,
        document: ContentDocument,
        formatted: FormattedContent,
        editor_candidate: EditorCandidate,
    ) -> VerificationResult | None:
        if self.config.verification.no_verification:
            return None

        editor_adapter = self.container.editor_detector.adapter_for(editor_candidate)

        verification_result = self.container.verification_service.verify(
            driver=driver,
            adapter=editor_adapter,
            candidate=editor_candidate,
            document=document,
            formatted=formatted,
            config=self.config.verification,
        )

        if not verification_result.passed and self.config.verification.verification_report:
            verification_result = self.container.verification_reporter.write_failure_artifacts(
                result=verification_result,
                driver=driver,
                adapter=editor_adapter,
                candidate=editor_candidate,
                include_screenshot=self.config.verification.screenshot_on_verification_failure,
            )

        return verification_result

    def _build_output(
        self,
        insertion_result: InsertionResult,
        verification_result: VerificationResult | None,
        editor_candidate: EditorCandidate,
        duration_seconds: float,
        content_length: int,
    ) -> RunOutput:
        artifacts = {}

        if verification_result is not None:
            artifacts = {
                "verification_report": verification_result.artifacts.report_path,
                "verification_screenshot": verification_result.artifacts.screenshot_path,
                "actual_content": verification_result.artifacts.actual_content_path,
            }

        return RunOutput.from_insertion_result(
            result=insertion_result,
            duration_seconds=duration_seconds,
            editor_type=editor_candidate.kind.value,
            editor_identifier=self.container.session_validator.editor_identifier(editor_candidate),
            content_length=content_length,
            verification=verification_result,
            session_file="" if self.config.session.no_session else self.config.session.session_file,
            artifacts=artifacts,
            metadata={
                "url": self.config.content.url,
                "selector": editor_candidate.selector,
            },
        )

    def _write_output(self, output: RunOutput) -> None:
        writer = self.container.output_writer
        write = getattr(writer, "write", None)

        if callable(write):
            write(output)

    def _editor_identifier(self, candidate: EditorCandidate) -> str:
        return self.editor_identifier(candidate)