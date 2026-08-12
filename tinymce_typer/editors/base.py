from typing import Any, Protocol

from tinymce_typer.editors.models import EditorCandidate, EditorKind, EditorSupportLevel


class EditorAdapter(Protocol):
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