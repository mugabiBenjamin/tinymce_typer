from tinymce_typer.insertion.base import InsertionProgress
from tinymce_typer.progress.reporter import ProgressSnapshot


class SilentProgressReporter:
    def __init__(self):
        self.last_snapshot: ProgressSnapshot | None = None
        self.failed_message = ""
        self.completed = False

    def update(self, progress: InsertionProgress) -> None:
        self.last_snapshot = ProgressSnapshot.from_insertion_progress(progress)

    def complete(self) -> None:
        self.completed = True

    def fail(self, message: str) -> None:
        self.failed_message = message