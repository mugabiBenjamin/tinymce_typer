from typing import Any

from selenium.common.exceptions import JavascriptException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

from tinymce_typer.editors.models import EditorCandidate, EditorKind, EditorSupportLevel
from tinymce_typer.exceptions import EditorNotFoundError, InsertionError, VerificationError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class TinyMCEAdapter:
    kind = EditorKind.TINYMCE
    support_level = EditorSupportLevel.PRIMARY

    iframe_selectors = (
        "iframe[id$='_ifr']",
        "iframe#tinymce_ifr",
        "div.mce-edit-area iframe",
        "iframe.tox-edit-area__iframe",
        ".tox-edit-area iframe",
    )

    body_selectors = (
        "body#tinymce",
        "body.mce-content-body",
        "body[data-id]",
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
                logger.debug("TinyMCE selector failed: %s | %s", selector, exc)
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
                    body = self._find_body(driver)
                    driver.switch_to.default_content()
                except WebDriverException as exc:
                    driver.switch_to.default_content()
                    logger.debug("TinyMCE frame rejected: %s", exc)
                    continue

                candidates.append(
                    EditorCandidate(
                        kind=self.kind,
                        support_level=self.support_level,
                        element=body,
                        frame_element=frame,
                        selector=selector,
                        label=self._label(frame, len(candidates)),
                        index=len(candidates),
                        confidence=0.95,
                        metadata={
                            "iframe_id": frame_id,
                            "iframe_name": frame_name,
                            "adapter": self.kind.value,
                        },
                    )
                )

        return candidates

    def focus(self, driver: Any, candidate: EditorCandidate) -> None:
        self._switch_to_candidate(driver, candidate)

        try:
            body = self._find_body(driver)
            body.click()
            driver.execute_script("arguments[0].focus();", body)
        except WebDriverException as exc:
            raise EditorNotFoundError(f"Could not focus TinyMCE editor: {exc}") from exc

    def clear(self, driver: Any, candidate: EditorCandidate) -> None:
        self.set_html(driver, candidate, "")

    def read_html(self, driver: Any, candidate: EditorCandidate) -> str:
        self._switch_to_candidate(driver, candidate)

        try:
            body = self._find_body(driver)
            return str(driver.execute_script("return arguments[0].innerHTML || '';", body))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read TinyMCE HTML: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def read_text(self, driver: Any, candidate: EditorCandidate) -> str:
        self._switch_to_candidate(driver, candidate)

        try:
            body = self._find_body(driver)
            return str(driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", body))
        except WebDriverException as exc:
            raise VerificationError(f"Could not read TinyMCE text: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def set_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        self._switch_to_candidate(driver, candidate)

        try:
            if self._try_native_set(driver, html):
                return

            body = self._find_body(driver)
            driver.execute_script(
                """
                arguments[0].innerHTML = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                body,
                html,
            )
        except WebDriverException as exc:
            raise InsertionError(f"Could not set TinyMCE HTML: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def insert_html(self, driver: Any, candidate: EditorCandidate, html: str) -> None:
        self._switch_to_candidate(driver, candidate)

        try:
            if self._try_native_insert(driver, html):
                return

            body = self._find_body(driver)
            driver.execute_script(
                """
                arguments[0].insertAdjacentHTML('beforeend', arguments[1]);
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                body,
                html,
            )
        except WebDriverException as exc:
            raise InsertionError(f"Could not insert TinyMCE HTML: {exc}") from exc
        finally:
            driver.switch_to.default_content()

    def _switch_to_candidate(self, driver: Any, candidate: EditorCandidate) -> None:
        driver.switch_to.default_content()

        if candidate.frame_element is None:
            raise EditorNotFoundError("TinyMCE candidate does not include an iframe.")

        try:
            driver.switch_to.frame(candidate.frame_element)
        except WebDriverException as exc:
            raise EditorNotFoundError(f"Could not switch into TinyMCE iframe: {exc}") from exc

    def _find_body(self, driver: Any) -> Any:
        for selector in self.body_selectors:
            try:
                return driver.find_element(By.CSS_SELECTOR, selector)
            except NoSuchElementException:
                continue

        raise EditorNotFoundError("TinyMCE editor body was not found inside iframe.")

    def _try_native_set(self, driver: Any, html: str) -> bool:
        try:
            return bool(
                driver.execute_script(
                    """
                    if (window.tinymce && window.tinymce.activeEditor) {
                        window.tinymce.activeEditor.setContent(arguments[0]);
                        window.tinymce.activeEditor.fire('change');
                        window.tinymce.activeEditor.fire('input');
                        return true;
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
                    if (window.tinymce && window.tinymce.activeEditor) {
                        window.tinymce.activeEditor.insertContent(arguments[0]);
                        window.tinymce.activeEditor.fire('change');
                        window.tinymce.activeEditor.fire('input');
                        return true;
                    }
                    return false;
                    """,
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

    def _label(self, frame: Any, index: int) -> str:
        frame_id = self._safe_attr(frame, "id")
        frame_name = self._safe_attr(frame, "name")

        if frame_id:
            return f"TinyMCE iframe #{frame_id}"

        if frame_name:
            return f"TinyMCE iframe {frame_name}"

        return f"TinyMCE editor {index + 1}"