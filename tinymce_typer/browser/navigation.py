from typing import Any

from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait

from tinymce_typer.config.settings import BrowserConfig, ContentConfig, EditorConfig
from tinymce_typer.exceptions import BrowserNavigationError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class BrowserNavigator:
    def navigate(
        self,
        driver: Any,
        browser_config: BrowserConfig,
        content_config: ContentConfig,
        editor_config: EditorConfig,
    ) -> None:
        if browser_config.use_existing and not browser_config.force_navigation:
            logger.info("Using existing browser session without forced navigation")
            return

        self._open_url(driver, content_config.url)

        if editor_config.wait_selector:
            self._wait_for_selector(
                driver=driver,
                selector=editor_config.wait_selector,
                timeout_seconds=max(1, browser_config.implicit_wait_seconds),
            )

    def _open_url(self, driver: Any, url: str) -> None:
        if not url.strip():
            raise BrowserNavigationError("Cannot navigate because URL is empty.")

        try:
            logger.info("Navigating to %s", url)
            driver.get(url)
        except WebDriverException as exc:
            raise BrowserNavigationError(f"Could not navigate to page '{url}': {exc}") from exc

    def _wait_for_selector(self, driver: Any, selector: str, timeout_seconds: int) -> None:
        if not selector.strip():
            return

        try:
            wait = WebDriverWait(driver, timeout_seconds)
            wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, selector)))
            logger.info("Detected wait selector: %s", selector)
        except TimeoutException as exc:
            raise BrowserNavigationError(
                f"Timed out waiting for selector '{selector}' after {timeout_seconds} second(s)."
            ) from exc
        except WebDriverException as exc:
            raise BrowserNavigationError(f"Could not wait for selector '{selector}': {exc}") from exc