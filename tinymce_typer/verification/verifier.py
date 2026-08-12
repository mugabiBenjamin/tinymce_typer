from typing import Any

from tinymce_typer.config.settings import VerificationConfig
from tinymce_typer.content.models import ContentDocument, FormattedContent
from tinymce_typer.editors.base import EditorAdapter
from tinymce_typer.editors.models import EditorCandidate
from tinymce_typer.exceptions import VerificationError
from tinymce_typer.verification.html_compare import HtmlComparator
from tinymce_typer.verification.models import ComparisonResult, VerificationMode, VerificationResult
from tinymce_typer.verification.text_compare import TextComparator


class VerificationService:
    def __init__(
        self,
        text_comparator: TextComparator | None = None,
        html_comparator: HtmlComparator | None = None,
    ):
        self.text_comparator = text_comparator or TextComparator()
        self.html_comparator = html_comparator or HtmlComparator()

    def verify(
        self,
        driver: Any,
        adapter: EditorAdapter,
        candidate: EditorCandidate,
        document: ContentDocument,
        formatted: FormattedContent,
        config: VerificationConfig,
    ) -> VerificationResult:
        if config.no_verification:
            return VerificationResult(
                passed=True,
                mode=VerificationMode(config.verification_mode),
                similarity=1.0,
                threshold=config.verification_threshold,
                expected_length=0,
                actual_length=0,
                editor_kind=candidate.kind.value,
                editor_identifier=self._editor_identifier(candidate),
                current_url=self._current_url(driver),
                message="Verification is disabled.",
                metadata={"disabled": "true"},
            )

        mode = self._mode(config.verification_mode)

        try:
            comparison = self._compare(
                mode=mode,
                driver=driver,
                adapter=adapter,
                candidate=candidate,
                document=document,
                formatted=formatted,
                threshold=config.verification_threshold,
            )
        except VerificationError:
            raise
        except Exception as exc:
            raise VerificationError(f"Verification failed unexpectedly: {exc}") from exc

        return VerificationResult(
            passed=comparison.passed,
            mode=mode,
            similarity=comparison.similarity,
            threshold=config.verification_threshold,
            expected_length=comparison.expected_length,
            actual_length=comparison.actual_length,
            editor_kind=candidate.kind.value,
            editor_identifier=self._editor_identifier(candidate),
            current_url=self._current_url(driver),
            message=comparison.message,
            mismatch=comparison.mismatch,
            metadata={
                "selector": candidate.selector,
                "support_level": candidate.support_level.value,
            },
        )

    def _compare(
        self,
        mode: VerificationMode,
        driver: Any,
        adapter: EditorAdapter,
        candidate: EditorCandidate,
        document: ContentDocument,
        formatted: FormattedContent,
        threshold: float,
    ) -> ComparisonResult:
        if mode == VerificationMode.EXACT_TEXT:
            actual_text = adapter.read_text(driver, candidate)
            return self.text_comparator.compare_exact(
                expected=document.text,
                actual=actual_text,
                threshold=threshold,
            )

        if mode == VerificationMode.NORMALIZED_TEXT:
            actual_text = adapter.read_text(driver, candidate)
            return self.text_comparator.compare_normalized(
                expected=document.text,
                actual=actual_text,
                threshold=threshold,
            )

        if mode == VerificationMode.HTML:
            actual_html = adapter.read_html(driver, candidate)
            return self.html_comparator.compare_html(
                expected_html=formatted.html,
                actual_html=actual_html,
                threshold=threshold,
            )

        raise VerificationError(f"Unsupported verification mode: {mode}")

    def _mode(self, value: str) -> VerificationMode:
        try:
            return VerificationMode(value)
        except ValueError as exc:
            raise VerificationError(f"Invalid verification mode: {value}") from exc

    def _current_url(self, driver: Any) -> str:
        try:
            return str(driver.current_url or "")
        except Exception:
            return ""

    def _editor_identifier(self, candidate: EditorCandidate) -> str:
        iframe_id = candidate.metadata.get("iframe_id", "")
        editor_id = candidate.metadata.get("editor_id", "")

        if iframe_id:
            return f"iframe:{iframe_id}"

        if editor_id:
            return f"element:{editor_id}"

        return f"{candidate.kind.value}:{candidate.selector}:{candidate.index}"