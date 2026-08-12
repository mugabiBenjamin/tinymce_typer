from difflib import SequenceMatcher

from tinymce_typer.verification.models import ComparisonResult, MismatchDetail
from tinymce_typer.verification.normalizers import HtmlNormalizer


class HtmlComparator:
    def __init__(self, normalizer: HtmlNormalizer | None = None):
        self.normalizer = normalizer or HtmlNormalizer()

    def compare_html(self, expected_html: str, actual_html: str, threshold: float) -> ComparisonResult:
        expected = self.normalizer.normalize_html(expected_html)
        actual = self.normalizer.normalize_html(actual_html)

        similarity = SequenceMatcher(None, expected, actual).ratio()
        passed = similarity >= threshold
        mismatch = None

        if not passed:
            mismatch = self._first_mismatch(expected, actual)

        return ComparisonResult(
            passed=passed,
            similarity=similarity,
            expected_length=len(expected),
            actual_length=len(actual),
            mismatch=mismatch,
            message="HTML verification passed." if passed else "HTML verification failed.",
        )

    def compare_html_as_text(self, expected_html: str, actual_html: str, threshold: float) -> ComparisonResult:
        expected = self.normalizer.html_to_text(expected_html)
        actual = self.normalizer.html_to_text(actual_html)

        similarity = SequenceMatcher(None, expected, actual).ratio()
        passed = similarity >= threshold
        mismatch = None

        if not passed:
            mismatch = self._first_mismatch(expected, actual)

        return ComparisonResult(
            passed=passed,
            similarity=similarity,
            expected_length=len(expected),
            actual_length=len(actual),
            mismatch=mismatch,
            message="HTML text verification passed." if passed else "HTML text verification failed.",
        )

    def _first_mismatch(self, expected: str, actual: str) -> MismatchDetail | None:
        max_length = max(len(expected), len(actual))

        for index in range(max_length):
            expected_character = expected[index] if index < len(expected) else ""
            actual_character = actual[index] if index < len(actual) else ""

            if expected_character != actual_character:
                return MismatchDetail(
                    index=index,
                    expected_context=self._context(expected, index),
                    actual_context=self._context(actual, index),
                    expected_character=expected_character,
                    actual_character=actual_character,
                )

        return None

    def _context(self, value: str, index: int, radius: int = 80) -> str:
        start = max(0, index - radius)
        end = min(len(value), index + radius)
        return value[start:end]