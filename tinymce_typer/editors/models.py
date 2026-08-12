from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EditorKind(StrEnum):
    TINYMCE = "tinymce"
    CKEDITOR = "ckeditor"
    QUILL = "quill"
    CONTENTEDITABLE = "contenteditable"
    UNKNOWN = "unknown"


class EditorSupportLevel(StrEnum):
    PRIMARY = "primary"
    BEST_EFFORT = "best-effort"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class EditorCandidate:
    kind: EditorKind
    support_level: EditorSupportLevel
    element: Any
    frame_element: Any | None
    selector: str
    label: str
    index: int
    confidence: float
    metadata: dict[str, str]

    @property
    def requires_frame_switch(self) -> bool:
        return self.frame_element is not None


@dataclass(frozen=True)
class EditorDetectionResult:
    candidates: tuple[EditorCandidate, ...]

    @property
    def found(self) -> bool:
        return bool(self.candidates)

    @property
    def count(self) -> int:
        return len(self.candidates)

    def first(self) -> EditorCandidate | None:
        if not self.candidates:
            return None
        return self.candidates[0]


@dataclass(frozen=True)
class EditorOperationResult:
    success: bool
    message: str
    metadata: dict[str, str]