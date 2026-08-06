from enum import StrEnum
from html import escape

from tinymce_typer.content.hashing import ContentHasher
from tinymce_typer.content.html_sanitizer import HtmlSanitizer
from tinymce_typer.content.models import ContentDocument, FormattedContent
from tinymce_typer.exceptions import ContentFormatError


class FormatMode(StrEnum):
    PLAIN_TEXT = "plain-text"
    HTML = "html"
    PRE_FORMATTED = "pre-formatted"
    PARAGRAPHS = "paragraphs"


class ContentFormatter:
    def __init__(
        self,
        sanitizer: HtmlSanitizer | None = None,
        hasher: ContentHasher | None = None,
    ):
        self.sanitizer = sanitizer or HtmlSanitizer()
        self.hasher = hasher or ContentHasher()

    def format_document(
        self,
        document: ContentDocument,
        mode: FormatMode = FormatMode.PARAGRAPHS,
        sanitize_html: bool = True,
    ) -> FormattedContent:
        return self.format_text(
            text=document.text,
            mode=mode,
            sanitize_html=sanitize_html,
        )

    def format_text(
        self,
        text: str,
        mode: FormatMode = FormatMode.PARAGRAPHS,
        sanitize_html: bool = True,
    ) -> FormattedContent:
        try:
            if mode == FormatMode.PLAIN_TEXT:
                html = self._plain_text_to_html(text)
            elif mode == FormatMode.HTML:
                html = self.sanitizer.sanitize(text) if sanitize_html else text
            elif mode == FormatMode.PRE_FORMATTED:
                html = self._preformatted_to_html(text)
            elif mode == FormatMode.PARAGRAPHS:
                html = self._paragraphs_to_html(text)
            else:
                raise ContentFormatError(f"Unsupported format mode: {mode}")
        except ContentFormatError:
            raise
        except Exception as exc:
            raise ContentFormatError(f"Could not format content: {exc}") from exc

        return FormattedContent(
            raw_text=text,
            html=html,
            plain_text=text,
            mode=str(mode),
            content_hash=self.hasher.hash_text(text),
        )

    def _plain_text_to_html(self, text: str) -> str:
        escaped = escape(text)
        escaped = escaped.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        escaped = self._preserve_consecutive_spaces(escaped)
        return escaped.replace("\n", "<br>")

    def _preformatted_to_html(self, text: str) -> str:
        return f"<pre><code>{escape(text)}</code></pre>"

    def _paragraphs_to_html(self, text: str) -> str:
        if not text:
            return ""

        blocks = self._split_paragraph_blocks(text)
        html_blocks = []

        for block in blocks:
            if self._looks_like_code_block(block):
                html_blocks.append(self._preformatted_to_html(block))
                continue

            escaped = escape(block)
            escaped = escaped.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
            escaped = self._preserve_consecutive_spaces(escaped)
            escaped = escaped.replace("\n", "<br>")
            html_blocks.append(f"<p>{escaped}</p>")

        return "".join(html_blocks)

    def _split_paragraph_blocks(self, text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        raw_blocks = normalized.split("\n\n")
        return [block for block in (item.strip("\n") for item in raw_blocks) if block != ""]

    def _looks_like_code_block(self, block: str) -> bool:
        lines = block.splitlines()

        if not lines:
            return False

        indented = sum(1 for line in lines if line.startswith(("    ", "\t")))
        code_markers = sum(
            1
            for line in lines
            if line.strip().startswith(
                (
                    "def ",
                    "class ",
                    "import ",
                    "from ",
                    "const ",
                    "let ",
                    "var ",
                    "function ",
                    "{",
                    "}",
                    "<",
                    "</",
                    "#!",
                )
            )
        )

        return indented >= max(1, len(lines) // 2) or code_markers >= 2

    def _preserve_consecutive_spaces(self, text: str) -> str:
        result = []
        previous_was_space = False

        for char in text:
            if char == " ":
                if previous_was_space:
                    result.append("&nbsp;")
                else:
                    result.append(" ")
                previous_was_space = True
            else:
                result.append(char)
                previous_was_space = False

        return "".join(result)