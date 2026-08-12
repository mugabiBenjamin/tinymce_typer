from dataclasses import dataclass
from typing import Protocol

from tinymce_typer.insertion.base import InsertionProgress


@dataclass(frozen=True)
class ProgressSnapshot:
    strategy_name: str
    offset: int
    total: int
    inserted: int
    percent: float
    current_file: str = ""
    message: str = ""

    @classmethod
    def from_insertion_progress(cls, progress: InsertionProgress) -> "ProgressSnapshot":
        return cls(
            strategy_name=progress.strategy_name,
            offset=progress.offset,
            total=progress.total,
            inserted=progress.inserted,
            percent=progress.percent,
            current_file=progress.current_file,
            message=progress.metadata.get("message", ""),
        )

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "strategy_name": self.strategy_name,
            "offset": self.offset,
            "total": self.total,
            "inserted": self.inserted,
            "percent": round(self.percent, 2),
            "current_file": self.current_file,
            "message": self.message,
        }


class ProgressReporter(Protocol):
    def update(self, progress: InsertionProgress) -> None:
        ...

    def complete(self) -> None:
        ...

    def fail(self, message: str) -> None:
        ...