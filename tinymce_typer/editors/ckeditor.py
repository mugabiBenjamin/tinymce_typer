from typing import Any

from selenium.common.exceptions import JavascriptException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

from tinymce_typer.editors.models import EditorCandidate, EditorKind, EditorSupportLevel
from tinymce_typer.exceptions import EditorNotFoundError, InsertionError, VerificationError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class CKEditorAdapter:
    kind = EditorKind.CKEDITOR
    support_level = EditorSupportLevel.BEST_EFFORT

    iframe_selectors = (
        "iframe.cke_wysiwyg_frame",
        ".cke_contents iframe",
    )

    editable_selectors = (
        "body.cke_editable",
        "[contenteditable='true']",
        "body",
    )

    def detect(self, driver: Any) -> list[EditorCandidate]:
        candidates: list[EditorCandidate] = []
        seen: set[str] = set()

        driver.switch_to.default_content()

        for selector in self.iframe_selectors:
            try:
                frames = driver.find_elements(By.CSS_SELECTOR, selector)
            except WebDriverException as exc:
                logger.debug("CKEditor selector failed: %s | %s", selector, exc)
                continue

            for frame in frames:
                frame_id = self._safe_attr(frame, "id")
                frame_name = self._safe_attr(frame, "name")
                key = frame_id or frame_name or str(id(frame))

                if key in seen:
                    continue

                seen.add(key)

                try:
                    driver.switch_to.frame(frame)
                    editable = self._find_editable(driver)
                    driver.switch_to.default_content()
                except WebDriverException as exc:
                    driver.switch_to.default_content()
                    logger.debug("CKEditor frame rejected: %s", exc)
                    continue

                candidates.append(
                    EditorCandidate(
                        kind=self.kind,
                        support_level=self.support_level,
                        element=editable,
                        frame_element=frame,
                        selector=selector,
                        label=self._label(frame, len(candidates)),
                        index=len(candidates),
                        confidence=0.80,
                        metadata={
                            "iframe_id": frame_id,
                            "iframe_name": frame_name,
                            "adapter": self.kind.value,
                            "support": self.support_level.value,
                        },
                    )
                )

        return candidates

    def focus(self, driver: Any, candidate: EditorCandidate) -> None:
        self._switch_to_candidate(driver, candidate)

        try:
            editable = self._find_editable(driver)
            editable.click()
            driver.execute_script("arguments[0].focus();", editable)
        except WebDriverException as exc:
            raise EditorNotFoundError(f"Could not focus CKEditor editor: {exc}") from exc

    def clear(self, driver: Any, candidate: EditorCandidate) -> None:
        self.set_html(driver, candidate, "")

    def read_html(self, driver: Any, candidate: EditorCandidate) -> str:
        self._switch_to_candidate(driver, candidate)

        try:
            if native_value := self._try_native_read_html(driver):
                return native_value

            editable = self._find_editable(driver)
            return str(driver.execute_script("return arguments[0].innerHTML || '';", editable))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read CKEditor HTML: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def read_text(self, driver: Any, candidate: EditorCandidate) -> str:
        self._switch_to_candidate(driver, candidate)

        try:
            editable = self._find_editable(driver)
            return str(driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", editable))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read CKEditor text: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def set_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        self._switch_to_candidate(driver, candidate)

        try:
            if self._try_native_set(driver, html):
                return

            editable = self._find_editable(driver)
            driver.execute_script(
                """
                arguments[0].innerHTML = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                editable,
                html,
            )
        except WebDriverException as exc:
            raise InsertionError(f"Could not set CKEditor HTML: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def insert_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        self._switch_to_candidate(driver, candidate)

        try:
            if self._try_native_insert(driver, html):
                return

            editable = self._find_editable(driver)
            driver.execute_script(
                """
                arguments[0].insertAdjacentHTML('beforeend', arguments[1]);
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                editable,
                html,
            )
        except WebDriverException as exc:
            raise InsertionError(f"Could not insert CKEditor HTML: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def _switch_to_candidate(self, driver: Any, candidate: EditorCandidate) -> None:
        driver.switch_to.default_content()

        if candidate.frame_element is None:
            raise EditorNotFoundError("CKEditor candidate does not include an iframe.")

        try:
            driver.switch_to.frame(candidate.frame_element)
        except WebDriverException as exc:
            raise EditorNotFoundError(f"Could not switch into CKEditor iframe: {exc}") from exc

    def _find_editable(self, driver: Any) -> Any:
        for selector in self.editable_selectors:
            try:
                return driver.find_element(By.CSS_SELECTOR, selector)
            except NoSuchElementException:
                continue

        raise EditorNotFoundError("CKEditor editable body was not found inside iframe.")

    def _try_native_set(self, driver: Any, html: str) -> bool:
        try:
            return bool(
                driver.execute_script(
                    """
                    if (window.CKEDITOR && window.CKEDITOR.instances) {
                        const names = Object.keys(window.CKEDITOR.instances);
                        if (names.length > 0) {
                            window.CKEDITOR.instances[names[0]].setData(arguments[0]);
                            window.CKEDITOR.instances[names[0]].fire('change');
                            return true;
                        }
                    }
                    return false;
                    """,
                    html,
                )
            )
        except JavascriptException:
            return False

    def _try_native_insert(self, driver: Any, html: str) -> bool:
        try:
            return bool(
                driver.execute_script(
                    """
                    if (window.CKEDITOR && window.CKEDITOR.instances) {
                        const names = Object.keys(window.CKEDITOR.instances);
                        if (names.length > 0) {
                            window.CKEDITOR.instances[names[0]].insertHtml(arguments[0]);
                            window.CKEDITOR.instances[names[0]].fire('change');
                            return true;
                        }
                    }
                    return false;
                    """,
                    html,
                )
            )
        except JavascriptException:
            return False

    def _try_native_read_html(self, driver: Any) -> str:
        try:
            value = driver.execute_script(
                """
                if (window.CKEDITOR && window.CKEDITOR.instances) {
                    const names = Object.keys(window.CKEDITOR.instances);
                    if (names.length > 0) {
                        return window.CKEDITOR.instances[names[0]].getData() || '';
                    }
                }
                return '';
                """
            )
            return str(value or "")
        except JavascriptException:
            return ""

    def _safe_attr(self, element: Any, name: str) -> str:
        try:
            return str(element.get_attribute(name) or "")
        except WebDriverException:
            return ""

    def _label(self, frame: Any, index: int) -> str:
        frame_id = self._safe_attr(frame, "id")
        frame_name = self._safe_attr(frame, "name")

        if frame_id:
            return f"CKEditor iframe #{frame_id}"

        if frame_name:
            return f"CKEditor iframe {frame_name}"

        return f"CKEditor editor {index + 1}"