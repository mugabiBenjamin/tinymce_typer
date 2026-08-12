from difflib import SequenceMatcher

from tinymce_typer.verification.models import ComparisonResult, MismatchDetail
from tinymce_typer.verification.normalizers import TextNormalizer


class TextComparator:
    def __init__(self, normalizer: TextNormalizer | None = None):
        self.normalizer = normalizer or TextNormalizer()

    def compare_exact(self, expected: str, actual: str, threshold: float = 1.0) -> ComparisonResult:
        expected_value = self.normalizer.normalize_exact(expected)
        actual_value = self.normalizer.normalize_exact(actual)
        return self._compare(expected_value, actual_value, threshold)

    def compare_normalized(self, expected: str, actual: str, threshold: float) -> ComparisonResult:
        expected_value = self.normalizer.normalize_relaxed(expected)
        actual_value = self.normalizer.normalize_relaxed(actual)
        return self._compare(expected_value, actual_value, threshold)

    def _compare(self, expected: str, actual: str, threshold: float) -> ComparisonResult:
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
            message="Verification passed." if passed else "Verification failed.",
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

    def _context(self, value: str, index: int, radius: int = 40) -> str:
        start = max(0, index - radius)
        end = min(len(value), index + radius)
        return value[start:end]