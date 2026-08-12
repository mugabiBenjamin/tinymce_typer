import sys
import time

from tinymce_typer.insertion.base import InsertionProgress
from tinymce_typer.progress.reporter import ProgressSnapshot


class TerminalProgressReporter:
    def __init__(
        self,
        stream=None,
        min_interval_seconds: float = 0.1,
        show_file: bool = True,
    ):
        self.stream = stream or sys.stderr
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self.show_file = show_file
        self._last_render_time = 0.0
        self._last_snapshot: ProgressSnapshot | None = None

    def update(self, progress: InsertionProgress) -> None:
        snapshot = ProgressSnapshot.from_insertion_progress(progress)
        now = time.monotonic()

        if not self._should_render(snapshot, now):
            self._last_snapshot = snapshot
            return

        self._last_render_time = now
        self._last_snapshot = snapshot
        self._render(snapshot)

    def complete(self) -> None:
        if self._last_snapshot is not None:
            self._render(self._last_snapshot)

        print(file=self.stream)
        print("Completed.", file=self.stream)

    def fail(self, message: str) -> None:
        print(file=self.stream)
        print(f"Failed: {message}", file=self.stream)

    def _should_render(self, snapshot: ProgressSnapshot, now: float) -> bool:
        if self._last_snapshot is None:
            return True

        if snapshot.offset >= snapshot.total:
            return True

        if snapshot.offset == self._last_snapshot.offset:
            return False

        return now - self._last_render_time >= self.min_interval_seconds

    def _render(self, snapshot: ProgressSnapshot) -> None:
        total = max(snapshot.total, 1)
        width = 30
        filled = int(width * min(snapshot.offset, total) / total)
        bar = "#" * filled + "-" * (width - filled)

        file_text = ""

        if self.show_file and snapshot.current_file:
            file_text = f" | file: {snapshot.current_file}"

        message = (
            f"\r[{bar}] {snapshot.percent:6.2f}% "
            f"({snapshot.offset}/{snapshot.total}) "
            f"| strategy: {snapshot.strategy_name}"
            f"{file_text}"
        )

        print(message, end="", file=self.stream, flush=True)