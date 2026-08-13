from typing import Protocol

from tinymce_typer.config.settings import AppConfig
from tinymce_typer.content.models import ContentDocument
from tinymce_typer.editors.models import EditorCandidate
from tinymce_typer.sessions.models import ResumeValidationResult, SessionState


class SessionStoreProtocol(Protocol):
    def exists(self) -> bool:
        ...

    def delete(self) -> None:
        ...

    def load(self) -> SessionState | None:
        ...

    def save(self, state: SessionState) -> None:
        ...


class SessionValidatorProtocol(Protocol):
    def validate_resume(
        self,
        session: SessionState,
        config: AppConfig,
        document: ContentDocument,
        editor_candidate: EditorCandidate | None = None,
        force_url: bool = False,
    ) -> ResumeValidationResult:
        ...

    def editor_identifier(self, candidate: EditorCandidate) -> str:
        ...