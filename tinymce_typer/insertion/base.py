from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from tinymce_typer.content.models import ContentDocument, FormattedContent
from tinymce_typer.editors.base import EditorAdapter
from tinymce_typer.editors.models import EditorCandidate


ProgressCallback = Callable[["InsertionProgress"], None]
SessionCallback = Callable[["InsertionProgress"], None]


class InsertionStrategyError(Exception):
    pass


@dataclass(frozen=True)
class InsertionProgress:
    strategy_name: str
    offset: int
    total: int
    inserted: int
    current_file: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 100.0
        return min(100.0, max(0.0, (self.offset / self.total) * 100))


@dataclass(frozen=True)
class StrategyFailure:
    strategy_name: str
    message: str
    recoverable: bool = True
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InsertionResult:
    success: bool
    strategy_name: str
    inserted_characters: int
    final_offset: int
    message: str
    failures: tuple[StrategyFailure, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InsertionContext:
    driver: Any
    adapter: EditorAdapter
    candidate: EditorCandidate
    document: ContentDocument
    formatted: FormattedContent
    start_offset: int = 0
    append: bool = False
    progress_callback: ProgressCallback | None = None
    session_callback: SessionCallback | None = None

    @property
    def remaining_text(self) -> str:
        return self.document.text[self.start_offset:]

    @property
    def remaining_html(self) -> str:
        if self.start_offset <= 0:
            return self.formatted.html
        return self.formatted.html

    @property
    def total_characters(self) -> int:
        return self.document.total_character_count

    def emit_progress(self, strategy_name: str, offset: int, inserted: int, metadata: dict[str, str] | None = None) -> None:
        boundary = self.document.file_at_offset(offset)
        progress = InsertionProgress(
            strategy_name=strategy_name,
            offset=offset,
            total=self.total_characters,
            inserted=inserted,
            current_file=boundary.display_name if boundary else "",
            metadata=metadata or {},
        )

        if self.progress_callback:
            self.progress_callback(progress)

        if self.session_callback:
            self.session_callback(progress)


class InsertionStrategy(Protocol):
    name: str

    def can_run(self, context: InsertionContext) -> bool:
        ...

    def insert(self, context: InsertionContext) -> InsertionResult:
        ...