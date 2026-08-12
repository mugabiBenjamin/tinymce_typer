from selenium.common.exceptions import WebDriverException

from tinymce_typer.exceptions import InsertionError
from tinymce_typer.insertion.base import InsertionContext, InsertionResult


class DirectHtmlInsertionStrategy:
    name = "direct-html"

    def can_run(self, context: InsertionContext) -> bool:
        return bool(context.formatted.html or context.document.text)

    def insert(self, context: InsertionContext) -> InsertionResult:
        html = context.remaining_html

        if not html:
            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=0,
                final_offset=context.start_offset,
                message="No formatted HTML content to insert.",
            )

        try:
            context.adapter.focus(context.driver, context.candidate)

            if context.append:
                context.adapter.insert_html(context.driver, context.candidate, html)
            else:
                context.adapter.set_html(context.driver, context.candidate, html)

            final_offset = context.total_characters

            context.emit_progress(
                strategy_name=self.name,
                offset=final_offset,
                inserted=max(0, final_offset - context.start_offset),
                metadata={"method": "dom_html_insertion"},
            )

            return InsertionResult(
                success=True,
                strategy_name=self.name,
                inserted_characters=max(0, final_offset - context.start_offset),
                final_offset=final_offset,
                message="Inserted content using direct DOM HTML insertion.",
                metadata={
                    "honest_label": "DOM insertion, not typing",
                    "append": str(context.append),
                },
            )
        except WebDriverException as exc:
            raise InsertionError(f"Direct HTML insertion failed in browser: {exc}") from exc
        except Exception as exc:
            raise InsertionError(f"Direct HTML insertion failed: {exc}") from exc