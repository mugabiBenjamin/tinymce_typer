import time
from html import escape

from tinymce_typer.exceptions import InsertionError
from tinymce_typer.insertion.base import InsertionContext, InsertionResult


class BatchInsertionStrategy:
    name = "batch"

    def __init__(
        self,
        batch_size: int = 50,
        delay_seconds: float = 0.1,
        use_html_batches: bool = True,
    ):
        self.batch_size = max(1, batch_size)
        self.delay_seconds = max(0.0, delay_seconds)
        self.use_html_batches = use_html_batches

    def can_run(self, context: InsertionContext) -> bool:
        return bool(context.remaining_text)

    def insert(self, context: InsertionContext) -> InsertionResult:
        text = context.remaining_text

        if not text:
            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=0,
                final_offset=context.start_offset,
                message="No remaining content to insert.",
            )

        try:
            context.adapter.focus(context.driver, context.candidate)
            inserted = 0

            for start in range(0, len(text), self.batch_size):
                raw_batch = text[start : start + self.batch_size]
                html_batch = self._format_batch(raw_batch)
                context.adapter.insert_html(context.driver, context.candidate, html_batch)

                inserted += len(raw_batch)
                final_offset = context.start_offset + inserted

                context.emit_progress(
                    strategy_name=self.name,
                    offset=final_offset,
                    inserted=inserted,
                    metadata={
                        "batch_start": str(start),
                        "batch_size": str(len(raw_batch)),
                        "method": "batch_dom_insertion",
                    },
                )

                if self.delay_seconds:
                    time.sleep(self.delay_seconds)

            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=inserted,
                final_offset=context.start_offset + inserted,
                message="Inserted content using batch DOM insertion.",
                metadata={
                    "batch_size": str(self.batch_size),
                    "honest_label": "batch DOM insertion, not typing",
                },
            )
        except Exception as exc:
            raise InsertionError(
                f"Batch insertion failed after {locals().get('inserted', 0)} character(s): {exc}"
            ) from exc

    def _format_batch(self, text: str) -> str:
        if not self.use_html_batches:
            return escape(text)

        escaped = escape(text)
        escaped = escaped.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        escaped = self._preserve_consecutive_spaces(escaped)
        return escaped.replace("\n", "<br>")

    def _preserve_consecutive_spaces(self, text: str) -> str:
        result = []
        previous_was_space = False

        for character in text:
            if character == " ":
                if previous_was_space:
                    result.append("&nbsp;")
                else:
                    result.append(" ")
                previous_was_space = True
            else:
                result.append(character)
                previous_was_space = False

        return "".join(result)