from typing import Any

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from tinymce_typer.editors.models import EditorCandidate, EditorKind, EditorSupportLevel
from tinymce_typer.exceptions import EditorNotFoundError, InsertionError, VerificationError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class ContentEditableAdapter:
    kind = EditorKind.CONTENTEDITABLE
    support_level = EditorSupportLevel.FALLBACK

    editor_selectors = (
        "[contenteditable='true']",
        "[contenteditable=true]",
    )

    ignored_tags = {"html", "body"}

    def detect(self, driver: Any) -> list[EditorCandidate]:
        candidates: list[EditorCandidate] = []
        seen: set[str] = set()

        driver.switch_to.default_content()

        for selector in self.editor_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            except WebDriverException as exc:
                logger.debug("contenteditable selector failed: %s | %s", selector, exc)
                continue

            for element in elements:
                tag_name = self._safe_attr(element, "tagName").lower()

                if tag_name in self.ignored_tags:
                    continue

                key = self._element_key(element)

                if key in seen:
                    continue

                seen.add(key)

                candidates.append(
                    EditorCandidate(
                        kind=self.kind,
                        support_level=self.support_level,
                        element=element,
                        frame_element=None,
                        selector=selector,
                        label=self._label(element, len(candidates)),
                        index=len(candidates),
                        confidence=0.55,
                        metadata={
                            "adapter": self.kind.value,
                            "support": self.support_level.value,
                            "id": self._safe_attr(element, "id"),
                            "class": self._safe_attr(element, "class"),
                            "tag": tag_name,
                        },
                    )
                )

        return candidates

    def focus(self, driver: Any, candidate: EditorCandidate) -> None:
        driver.switch_to.default_content()

        try:
            candidate.element.click()
            driver.execute_script("arguments[0].focus();", candidate.element)
        except WebDriverException as exc:
            raise EditorNotFoundError(f"Could not focus contenteditable editor: {exc}") from exc

    def clear(self, driver: Any, candidate: EditorCandidate) -> None:
        self.set_html(driver, candidate, "")

    def read_html(self, driver: Any, candidate: EditorCandidate) -> str:
        driver.switch_to.default_content()

        try:
            return str(driver.execute_script("return arguments[0].innerHTML || '';", candidate.element))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read contenteditable HTML: {exc}") from exc

    def read_text(self, driver: Any, candidate: EditorCandidate) -> str:
        driver.switch_to.default_content()

        try:
            return str(driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", candidate.element))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read contenteditable text: {exc}") from exc

    def set_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        driver.switch_to.default_content()

        try:
            driver.execute_script(
                """
                arguments[0].innerHTML = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                candidate.element,
                html,
            )
        except WebDriverException as exc:
            raise InsertionError(f"Could not set contenteditable HTML: {exc}") from exc

    def insert_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        driver.switch_to.default_content()

        try:
            driver.execute_script(
                """
                arguments[0].insertAdjacentHTML('beforeend', arguments[1]);
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                candidate.element,
                html,
            )
        except WebDriverException as exc:
            raise InsertionError(f"Could not insert contenteditable HTML: {exc}") from exc

    def _safe_attr(self, element: Any, name: str) -> str:
        try:
            return str(element.get_attribute(name) or "")
        except WebDriverException:
            return ""

    def _element_key(self, element: Any) -> str:
        element_id = self._safe_attr(element, "id")
        element_class = self._safe_attr(element, "class")
        tag_name = self._safe_attr(element, "tagName")

        return f"{tag_name}:{element_id}:{element_class}:{id(element)}"

    def _label(self, element: Any, index: int) -> str:
        element_id = self._safe_attr(element, "id")
        element_class = self._safe_attr(element, "class")
        tag_name = self._safe_attr(element, "tagName").lower() or "element"

        if element_id:
            return f"contenteditable {tag_name} #{element_id}"

        if element_class:
            return f"contenteditable {tag_name}.{element_class.split()[0]}"

        return f"contenteditable editor {index + 1}"