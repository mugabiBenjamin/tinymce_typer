from typing import Any

from selenium.common.exceptions import JavascriptException, WebDriverException
from selenium.webdriver.common.by import By

from tinymce_typer.editors.models import EditorCandidate, EditorKind, EditorSupportLevel
from tinymce_typer.exceptions import EditorNotFoundError, InsertionError, VerificationError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class QuillAdapter:
    kind = EditorKind.QUILL
    support_level = EditorSupportLevel.BEST_EFFORT

    editor_selectors = (
        ".ql-editor",
    )

    def detect(self, driver: Any) -> list[EditorCandidate]:
        candidates: list[EditorCandidate] = []

        driver.switch_to.default_content()

        for selector in self.editor_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            except WebDriverException as exc:
                logger.debug("Quill selector failed: %s | %s", selector, exc)
                continue

            for element in elements:
                candidates.append(
                    EditorCandidate(
                        kind=self.kind,
                        support_level=self.support_level,
                        element=element,
                        frame_element=None,
                        selector=selector,
                        label=self._label(element, len(candidates)),
                        index=len(candidates),
                        confidence=0.85,
                        metadata={
                            "adapter": self.kind.value,
                            "support": self.support_level.value,
                            "class": self._safe_attr(element, "class"),
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
            raise EditorNotFoundError(f"Could not focus Quill editor: {exc}") from exc

    def clear(self, driver: Any, candidate: EditorCandidate) -> None:
        self.set_html(driver, candidate, "")

    def read_html(self, driver: Any, candidate: EditorCandidate) -> str:
        driver.switch_to.default_content()

        try:
            return str(driver.execute_script("return arguments[0].innerHTML || '';", candidate.element))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read Quill HTML: {exc}") from exc

    def read_text(self, driver: Any, candidate: EditorCandidate) -> str:
        driver.switch_to.default_content()

        try:
            return str(driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", candidate.element))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read Quill text: {exc}") from exc

    def set_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        driver.switch_to.default_content()

        try:
            if self._try_native_set(driver, candidate, html):
                return

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
            raise InsertionError(f"Could not set Quill HTML: {exc}") from exc

    def insert_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        driver.switch_to.default_content()

        try:
            if self._try_native_insert(driver, candidate, html):
                return

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
            raise InsertionError(f"Could not insert Quill HTML: {exc}") from exc

    def _try_native_set(self, driver: Any, candidate: EditorCandidate, html: str) -> bool:
        try:
            return bool(
                driver.execute_script(
                    """
                    const editor = arguments[0];
                    const html = arguments[1];
                    const container = editor.closest('.ql-container');
                    if (!container) return false;

                    const candidates = Array.from(document.querySelectorAll('.ql-container'));
                    const index = candidates.indexOf(container);

                    if (!window.Quill || index < 0) return false;

                    const quill = Quill.find(container) || Quill.find(editor);
                    if (!quill) return false;

                    quill.clipboard.dangerouslyPasteHTML(0, html, 'api');
                    quill.setSelection(quill.getLength(), 0, 'silent');
                    quill.root.dispatchEvent(new Event('input', { bubbles: true }));
                    quill.root.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                    """,
                    candidate.element,
                    html,
                )
            )
        except JavascriptException:
            return False

    def _try_native_insert(self, driver: Any, candidate: EditorCandidate, html: str) -> bool:
        try:
            return bool(
                driver.execute_script(
                    """
                    const editor = arguments[0];
                    const html = arguments[1];
                    const container = editor.closest('.ql-container');
                    if (!container) return false;

                    if (!window.Quill) return false;

                    const quill = Quill.find(container) || Quill.find(editor);
                    if (!quill) return false;

                    const index = quill.getLength();
                    quill.clipboard.dangerouslyPasteHTML(index, html, 'api');
                    quill.setSelection(quill.getLength(), 0, 'silent');
                    quill.root.dispatchEvent(new Event('input', { bubbles: true }));
                    quill.root.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                    """,
                    candidate.element,
                    html,
                )
            )
        except JavascriptException:
            return False

    def _safe_attr(self, element: Any, name: str) -> str:
        try:
            return str(element.get_attribute(name) or "")
        except WebDriverException:
            return ""

    def _label(self, element: Any, index: int) -> str:
        editor_id = self._safe_attr(element, "id")

        if editor_id:
            return f"Quill editor #{editor_id}"

        return f"Quill editor {index + 1}"