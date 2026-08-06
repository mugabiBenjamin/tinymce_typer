from html.parser import HTMLParser


class _SafeHtmlParser(HTMLParser):
    allowed_tags = {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "blockquote",
        "pre",
        "code",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "span",
        "div",
        "a",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
    }

    allowed_attrs = {
        "href",
        "title",
        "target",
        "rel",
        "class",
    }

    void_tags = {"br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()

        if tag not in self.allowed_tags:
            return

        safe_attrs = []

        for name, value in attrs:
            name = name.lower()

            if name.startswith("on"):
                continue

            if name not in self.allowed_attrs:
                continue

            if value is None:
                continue

            escaped_value = self._escape_attr(value)

            if name == "href" and not self._is_safe_href(value):
                continue

            safe_attrs.append(f'{name}="{escaped_value}"')

        attr_text = f" {' '.join(safe_attrs)}" if safe_attrs else ""
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag not in self.allowed_tags:
            return

        if tag in self.void_tags:
            return

        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(self._escape_text(data))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self.parts)

    def _is_safe_href(self, value: str) -> bool:
        normalized = value.strip().lower()
        return not normalized.startswith(("javascript:", "data:", "vbscript:"))

    def _escape_text(self, value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _escape_attr(self, value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


class HtmlSanitizer:
    def sanitize(self, html: str) -> str:
        parser = _SafeHtmlParser()

        try:
            parser.feed(html)
            parser.close()
        except Exception as exc:
            from tinymce_typer.exceptions import ContentFormatError

            raise ContentFormatError(f"Could not sanitize HTML content: {exc}") from exc

        return parser.get_html()