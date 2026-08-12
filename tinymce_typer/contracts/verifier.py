from typing import Any, Protocol

from tinymce_typer.config.settings import VerificationConfig
from tinymce_typer.content.models import ContentDocument, FormattedContent
from tinymce_typer.contracts.editor import EditorAdapterProtocol
from tinymce_typer.editors.models import EditorCandidate
from tinymce_typer.verification.models import VerificationResult


class VerificationServiceProtocol(Protocol):
    def verify(
        self,
        driver: Any,
        adapter: EditorAdapterProtocol,
        candidate: EditorCandidate,
        document: ContentDocument,
        formatted: FormattedContent,
        config: VerificationConfig,
    ) -> VerificationResult:
        ...


class VerificationReporterProtocol(Protocol):
    def write_failure_artifacts(
        self,
        result: VerificationResult,
        driver: Any,
        adapter: EditorAdapterProtocol,
        candidate: EditorCandidate,
        include_screenshot: bool = False,
    ) -> VerificationResult:
        ...