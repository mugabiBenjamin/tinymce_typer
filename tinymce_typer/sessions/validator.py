from tinymce_typer.config.settings import AppConfig
from tinymce_typer.content.models import ContentDocument
from tinymce_typer.editors.models import EditorCandidate
from tinymce_typer.sessions.models import (
    ResumeDecision,
    ResumeValidationResult,
    SessionState,
)


class SessionValidator:
    def validate_resume(
        self,
        session: SessionState,
        config: AppConfig,
        document: ContentDocument,
        editor_candidate: EditorCandidate | None = None,
        force_url: bool = False,
    ) -> ResumeValidationResult:
        reasons: list[str] = []
        warnings: list[str] = []

        if session.progress.completed:
            reasons.append("Saved session is already marked as completed.")

        if not session.metadata.content_hash:
            reasons.append("Saved session does not contain a content hash.")

        if session.metadata.content_hash and session.metadata.content_hash != document.content_hash:
            reasons.append("Source content has changed since the session was saved.")

        if session.metadata.url and session.metadata.url != config.content.url:
            if force_url or config.browser.force_navigation:
                warnings.append("Saved session URL differs from current URL, but URL mismatch was allowed.")
            else:
                reasons.append("Saved session URL differs from current URL.")

        if session.metadata.source_file and session.metadata.source_file != config.content.file:
            warnings.append("Saved session source file path differs from current file path.")

        if session.metadata.insertion_strategy and session.metadata.insertion_strategy != config.insertion.strategy:
            warnings.append("Saved session insertion strategy differs from current insertion strategy.")

        if editor_candidate is not None:
            current_editor_kind = editor_candidate.kind.value
            current_editor_identifier = self._editor_identifier(editor_candidate)

            if session.metadata.editor_kind and session.metadata.editor_kind != current_editor_kind:
                warnings.append("Saved session editor type differs from current detected editor type.")

            if session.metadata.editor_identifier and session.metadata.editor_identifier != current_editor_identifier:
                warnings.append("Saved session editor identity differs from current detected editor.")

        if session.progress.offset < 0:
            reasons.append("Saved session offset is invalid.")

        if session.progress.total and session.progress.offset > session.progress.total:
            reasons.append("Saved session offset is greater than saved total.")

        if document.total_character_count and session.progress.offset > document.total_character_count:
            reasons.append("Saved session offset is greater than current content length.")

        if reasons:
            return ResumeValidationResult(
                decision=ResumeDecision.REFUSE,
                reasons=tuple(reasons),
                warnings=tuple(warnings),
            )

        if warnings:
            return ResumeValidationResult(
                decision=ResumeDecision.WARN,
                reasons=(),
                warnings=tuple(warnings),
            )

        return ResumeValidationResult(
            decision=ResumeDecision.ALLOW,
            reasons=(),
            warnings=(),
        )

    def _editor_identifier(self, candidate: EditorCandidate) -> str:
        iframe_id = candidate.metadata.get("iframe_id", "")
        editor_id = candidate.metadata.get("editor_id", "")
        selector = candidate.selector

        if iframe_id:
            return f"iframe:{iframe_id}"

        if editor_id:
            return f"element:{editor_id}"

        return f"{candidate.kind.value}:{selector}:{candidate.index}"