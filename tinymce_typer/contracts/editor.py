from typing import Any, Protocol

from tinymce_typer.config.settings import EditorConfig
from tinymce_typer.editors.models import EditorCandidate, EditorDetectionResult, EditorKind, EditorSupportLevel


class EditorAdapterProtocol(Protocol):
    kind: EditorKind
    support_level: EditorSupportLevel

    def detect(self, driver: Any) -> list[EditorCandidate]:
        ...

    def focus(self, driver: Any, candidate: EditorCandidate) -> None:
        ...

    def clear(self, driver: Any, candidate: EditorCandidate) -> None:
        ...

    def read_html(self, driver: Any, candidate: EditorCandidate) -> str:
        ...

    def read_text(self, driver: Any, candidate: EditorCandidate) -> str:
        ...

    def set_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        ...

    def insert_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        ...


class EditorDetectorProtocol(Protocol):
    def detect(self, driver: Any, config: EditorConfig) -> EditorDetectionResult:
        ...

    def select(self, result: EditorDetectionResult, config: EditorConfig) -> EditorCandidate:
        ...

    def find_and_focus(self, driver: Any, config: EditorConfig) -> EditorCandidate:
        ...

    def adapter_for(self, candidate: EditorCandidate) -> EditorAdapterProtocol:
        ...