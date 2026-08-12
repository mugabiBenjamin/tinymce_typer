import re
from html.parser import HTMLParser


class _HtmlTextExtractor(HTMLParser):
    block_tags = {
        "p",
        "div",
        "br",
        "li",
        "tr",
        "table",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "pre",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


class TextNormalizer:
    def normalize_exact(self, value: str) -> str:
        return value.replace("\r\n", "\n").replace("\r", "\n")

    def normalize_relaxed(self, value: str) -> str:
        normalized = self.normalize_exact(value)
        normalized = normalized.replace("\xa0", " ")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n\s*\n+", "\n\n", normalized)
        normalized = "\n".join(line.strip() for line in normalized.splitlines())
        return normalized.strip()


class HtmlNormalizer:
    def __init__(self, text_normalizer: TextNormalizer | None = None):
        self.text_normalizer = text_normalizer or TextNormalizer()

    def html_to_text(self, html: str) -> str:
        parser = _HtmlTextExtractor()
        parser.feed(html)
        parser.close()
        return self.text_normalizer.normalize_relaxed(parser.text())

    def normalize_html(self, html: str) -> str:
        value = html.replace("\r\n", "\n").replace("\r", "\n")
        value = re.sub(r">\s+<", "><", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()