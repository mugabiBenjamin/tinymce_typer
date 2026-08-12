from typing import Protocol

from tinymce_typer.insertion.base import InsertionProgress


class ProgressReporterProtocol(Protocol):
    def update(self, progress: InsertionProgress) -> None:
        ...

    def complete(self) -> None:
        ...

    def fail(self, message: str) -> None:
        ...