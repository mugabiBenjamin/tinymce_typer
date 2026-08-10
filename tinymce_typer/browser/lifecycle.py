import time

from tinymce_typer.browser.base import BrowserSession
from tinymce_typer.config.settings import BrowserConfig
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class BrowserLifecycleManager:
    def handle_completion(self, session: BrowserSession, config: BrowserConfig) -> None:
        if config.detach:
            logger.info("Detaching from browser session")
            return

        if session.is_existing_session:
            logger.info("Leaving existing browser session open")
            return

        if config.close_on_complete:
            self.close(session)
            return

        if config.keep_browser_open:
            self.wait_before_close(session, config)
            return

        self.close(session)

    def handle_failure(self, session: BrowserSession | None, config: BrowserConfig) -> None:
        if session is None:
            return

        if config.detach:
            logger.info("Failure occurred; detaching from browser session")
            return

        if session.is_existing_session:
            logger.info("Failure occurred; existing browser session will remain open")
            return

        if config.keep_browser_open and not config.close_on_complete:
            self.wait_before_close(session, config)
            return

        self.close(session)

    def close(self, session: BrowserSession) -> None:
        if not session.should_quit_driver:
            logger.info("Browser session is not owned by this process; skipping quit")
            return

        try:
            session.driver.quit()
            logger.info("Browser closed")
        except Exception:
            logger.exception("Failed to close browser cleanly")

    def wait_before_close(self, session: BrowserSession, config: BrowserConfig) -> None:
        if not session.should_quit_driver:
            logger.info("Browser session is not owned by this process; leaving it open")
            return

        timeout = config.browser_wait_timeout_seconds

        if timeout <= 0:
            logger.info("Browser will remain open until the process is interrupted")
            self._wait_forever()
            self.close(session)
            return

        logger.info("Keeping browser open for %s second(s)", timeout)

        try:
            time.sleep(timeout)
        except KeyboardInterrupt:
            logger.info("Browser wait interrupted by user")

        self.close(session)

    def _wait_forever(self) -> None:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Browser wait interrupted by user")