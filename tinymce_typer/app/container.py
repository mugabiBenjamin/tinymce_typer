from dataclasses import dataclass
from getpass import getpass

from tinymce_typer.browser.factory import BrowserProviderFactory
from tinymce_typer.browser.lifecycle import BrowserLifecycleManager
from tinymce_typer.browser.navigation import BrowserNavigator
from tinymce_typer.cli.prompts import PromptManager
from tinymce_typer.config.settings import AppConfig
from tinymce_typer.content.formatter import ContentFormatter
from tinymce_typer.content.loader import ContentLoader
from tinymce_typer.contracts.browser import BrowserLifecycleProtocol, BrowserNavigatorProtocol, BrowserProviderProtocol
from tinymce_typer.contracts.editor import EditorDetectorProtocol
from tinymce_typer.contracts.insertion import InsertionStrategyChainProtocol
from tinymce_typer.contracts.progress import ProgressReporterProtocol
from tinymce_typer.contracts.session import SessionStoreProtocol, SessionValidatorProtocol
from tinymce_typer.contracts.verifier import VerificationReporterProtocol, VerificationServiceProtocol
from tinymce_typer.editors.detector import EditorDetector
from tinymce_typer.insertion.factory import InsertionStrategyFactory
from tinymce_typer.output.json_output import JsonOutputWriter
from tinymce_typer.output.terminal_output import TerminalOutputWriter
from tinymce_typer.progress.silent import SilentProgressReporter
from tinymce_typer.progress.terminal import TerminalProgressReporter
from tinymce_typer.sessions.store import SessionStore
from tinymce_typer.sessions.validator import SessionValidator
from tinymce_typer.verification.report import VerificationReporter
from tinymce_typer.verification.verifier import VerificationService


@dataclass(frozen=True)
class AppContainer:
    browser_provider: BrowserProviderProtocol
    browser_lifecycle: BrowserLifecycleProtocol
    browser_navigator: BrowserNavigatorProtocol
    content_loader: ContentLoader
    content_formatter: ContentFormatter
    editor_detector: EditorDetectorProtocol
    insertion_chain: InsertionStrategyChainProtocol
    session_store: SessionStoreProtocol | None
    session_validator: SessionValidatorProtocol
    verification_service: VerificationServiceProtocol
    verification_reporter: VerificationReporterProtocol
    progress_reporter: ProgressReporterProtocol
    prompt_manager: PromptManager
    output_writer: object


class AppContainerFactory:
    def build(self, config: AppConfig) -> AppContainer:
        session_password = self._resolve_session_password(config)

        return AppContainer(
            browser_provider=BrowserProviderFactory().create(config.browser),
            browser_lifecycle=BrowserLifecycleManager(),
            browser_navigator=BrowserNavigator(),
            content_loader=ContentLoader(),
            content_formatter=ContentFormatter(),
            editor_detector=EditorDetector(),
            insertion_chain=InsertionStrategyFactory().create_chain(config.insertion),
            session_store=self._build_session_store(config, session_password),
            session_validator=SessionValidator(),
            verification_service=VerificationService(),
            verification_reporter=VerificationReporter(config.verification.verification_report_dir),
            progress_reporter=self._build_progress_reporter(config),
            prompt_manager=PromptManager(
                assume_yes=config.cli.yes,
                non_interactive=config.cli.non_interactive,
            ),
            output_writer=self._build_output_writer(config),
        )

    def _build_session_store(self, config: AppConfig, password: str) -> SessionStoreProtocol | None:
        if config.session.no_session:
            return None

        return SessionStore(
            path=config.session.session_file,
            encrypted=config.session.encrypt,
            password=password,
        )

    def _resolve_session_password(self, config: AppConfig) -> str:
        if not config.session.encrypt:
            return ""

        if config.cli.non_interactive:
            raise ValueError("Encrypted sessions require an interactive password prompt.")

        return getpass("Session password: ")

    def _build_progress_reporter(self, config: AppConfig) -> ProgressReporterProtocol:
        output_mode = getattr(config.output, "mode", "terminal")
        quiet_progress = getattr(config.output, "quiet_progress", False)

        if output_mode == "json" or quiet_progress:
            return SilentProgressReporter()

        return TerminalProgressReporter()

    def _build_output_writer(self, config: AppConfig) -> object:
        output_mode = getattr(config.output, "mode", "terminal")

        if output_mode == "json":
            return JsonOutputWriter()

        return TerminalOutputWriter()