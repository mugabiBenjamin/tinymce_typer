import time

from selenium.common.exceptions import WebDriverException

from tinymce_typer.exceptions import InsertionError
from tinymce_typer.insertion.base import InsertionContext, InsertionResult


class CharacterTypingStrategy:
    name = "character-typing"

    def __init__(
        self,
        delay_seconds: float = 0.01,
        progress_interval: int = 25,
        use_real_keystrokes: bool = True,
    ):
        self.delay_seconds = max(0.0, delay_seconds)
        self.progress_interval = max(1, progress_interval)
        self.use_real_keystrokes = use_real_keystrokes

    def can_run(self, context: InsertionContext) -> bool:
        return bool(context.remaining_text)

    def insert(self, context: InsertionContext) -> InsertionResult:
        if self.use_real_keystrokes:
            return self._insert_with_send_keys(context)

        return self._insert_incremental_dom(context)

    def _insert_with_send_keys(self, context: InsertionContext) -> InsertionResult:
        text = context.remaining_text

        if not text:
            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=0,
                final_offset=context.start_offset,
                message="No remaining text to type.",
            )

        try:
            context.adapter.focus(context.driver, context.candidate)
            active = context.driver.switch_to.active_element
            inserted = 0

            for index, character in enumerate(text, start=1):
                active.send_keys(character)
                inserted = index
                final_offset = context.start_offset + inserted

                if self.delay_seconds:
                    time.sleep(self.delay_seconds)

                if inserted % self.progress_interval == 0 or inserted == len(text):
                    context.emit_progress(
                        strategy_name=self.name,
                        offset=final_offset,
                        inserted=inserted,
                        metadata={"method": "selenium_send_keys"},
                    )

            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=inserted,
                final_offset=context.start_offset + inserted,
                message="Inserted content using real Selenium send_keys character typing.",
                metadata={"honest_label": "real keystroke simulation"},
            )
        except WebDriverException as exc:
            raise InsertionError(f"Character typing failed in browser: {exc}") from exc
        except Exception as exc:
            raise InsertionError(f"Character typing failed: {exc}") from exc

    def _insert_incremental_dom(self, context: InsertionContext) -> InsertionResult:
        text = context.remaining_text

        if not text:
            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=0,
                final_offset=context.start_offset,
                message="No remaining text to insert.",
            )

        try:
            inserted = 0

            for index, character in enumerate(text, start=1):
                html = self._character_to_html(character)
                context.adapter.insert_html(context.driver, context.candidate, html)
                inserted = index
                final_offset = context.start_offset + inserted

                if self.delay_seconds:
                    time.sleep(self.delay_seconds)

                if inserted % self.progress_interval == 0 or inserted == len(text):
                    context.emit_progress(
                        strategy_name=self.name,
                        offset=final_offset,
                        inserted=inserted,
                        metadata={"method": "incremental_dom_insertion"},
                    )

            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=inserted,
                final_offset=context.start_offset + inserted,
                message="Inserted content using incremental DOM insertion.",
                metadata={"honest_label": "incremental DOM insertion, not real typing"},
            )
        except Exception as exc:
            raise InsertionError(f"Incremental DOM insertion failed: {exc}") from exc

    def _character_to_html(self, character: str) -> str:
        if character == "\n":
            return "<br>"

        if character == "\t":
            return "&nbsp;&nbsp;&nbsp;&nbsp;"

        if character == " ":
            return " "

        return (
            character.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )