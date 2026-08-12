from dataclasses import dataclass, field
from enum import StrEnum


class VerificationMode(StrEnum):
    NORMALIZED_TEXT = "normalized-text"
    EXACT_TEXT = "exact-text"
    HTML = "html"


@dataclass(frozen=True)
class MismatchDetail:
    index: int
    expected_context: str
    actual_context: str
    expected_character: str
    actual_character: str


@dataclass(frozen=True)
class ComparisonResult:
    passed: bool
    similarity: float
    expected_length: int
    actual_length: int
    mismatch: MismatchDetail | None = None
    message: str = ""


@dataclass(frozen=True)
class VerificationArtifact:
    report_path: str = ""
    screenshot_path: str = ""
    actual_content_path: str = ""


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    mode: VerificationMode
    similarity: float
    threshold: float
    expected_length: int
    actual_length: int
    editor_kind: str
    editor_identifier: str
    current_url: str
    message: str
    mismatch: MismatchDetail | None = None
    artifacts: VerificationArtifact = field(default_factory=VerificationArtifact)
    metadata: dict[str, str] = field(default_factory=dict)