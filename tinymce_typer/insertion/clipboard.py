import platform
import time

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from tinymce_typer.exceptions import ClipboardError, InsertionError
from tinymce_typer.insertion.base import InsertionContext, InsertionResult
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class ClipboardInsertionStrategy:
    name = "clipboard"

    def __init__(self, paste_delay_seconds: float = 0.2):
        self.paste_delay_seconds = paste_delay_seconds

    def can_run(self, context: InsertionContext) -> bool:
        try:
            import pyperclip
        except ImportError:
            return False

        try:
            pyperclip.determine_clipboard()
            return True
        except Exception:
            return False

    def insert(self, context: InsertionContext) -> InsertionResult:
        if not self.can_run(context):
            raise ClipboardError("Clipboard insertion is unavailable. Install pyperclip and a working clipboard backend.")

        import pyperclip

        original_clipboard = self._read_clipboard_safe(pyperclip)
        text_to_paste = context.remaining_text

        if not text_to_paste:
            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=0,
                final_offset=context.start_offset,
                message="No remaining content to paste.",
            )

        try:
            context.adapter.focus(context.driver, context.candidate)
            pyperclip.copy(text_to_paste)
            self._paste(context)
            final_offset = context.start_offset + len(text_to_paste)
            context.emit_progress(
                strategy_name=self.name,
                offset=final_offset,
                inserted=len(text_to_paste),
                metadata={"method": "system_clipboard_plain_text"},
            )

            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=len(text_to_paste),
                final_offset=final_offset,
                message="Inserted content using system clipboard paste.",
                metadata={"clipboard_mode": "plain_text"},
            )
        except WebDriverException as exc:
            raise InsertionError(f"Clipboard paste failed in browser: {exc}") from exc
        except Exception as exc:
            raise ClipboardError(f"Clipboard insertion failed: {exc}") from exc
        finally:
            self._restore_clipboard_safe(pyperclip, original_clipboard)

    def _paste(self, context: InsertionContext) -> None:
        active = context.driver.switch_to.active_element
        modifier = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        active.send_keys(modifier, "v")
        time.sleep(self.paste_delay_seconds)

    def _read_clipboard_safe(self, pyperclip_module) -> str:
        try:
            value = pyperclip_module.paste()
            return str(value or "")
        except Exception as exc:
            logger.warning("Could not read existing clipboard before insertion: %s", exc)
            return ""

    def _restore_clipboard_safe(self, pyperclip_module, value: str) -> None:
        try:
            pyperclip_module.copy(value)
        except Exception as exc:
            logger.warning("Could not restore clipboard after insertion: %s", exc)