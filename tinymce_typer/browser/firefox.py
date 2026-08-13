from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

from tinymce_typer.browser.base import BrowserSession
from tinymce_typer.browser.validation import BrowserValidator
from tinymce_typer.config.settings import BrowserConfig
from tinymce_typer.exceptions import BrowserConnectionError, BrowserSetupError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class FirefoxBrowserProvider:
    browser_name = "firefox"

    def __init__(self, validator: BrowserValidator | None = None):
        self.validator = validator or BrowserValidator()

    def start(self, config: BrowserConfig) -> BrowserSession:
        self.validator.validate_or_raise(config)

        if config.use_existing:
            return self._connect_existing(config)

        return self._start_new(config)

    def _start_new(self, config: BrowserConfig) -> BrowserSession:
        options = webdriver.FirefoxOptions()

        if config.headless:
            options.add_argument("-headless")

        if config.profile:
            options.add_argument("-profile")
            options.add_argument(config.profile)
            logger.warning("Using Firefox profile: %s", config.profile)

        try:
            driver = webdriver.Firefox(
                service=FirefoxService(GeckoDriverManager().install()),
                options=options,
            )
            driver.implicitly_wait(config.implicit_wait_seconds)
        except WebDriverException as exc:
            raise BrowserSetupError(f"Could not start Firefox browser: {exc}") from exc

        return BrowserSession(
            driver=driver,
            browser_name=self.browser_name,
            is_existing_session=False,
            should_quit_driver=True,
        )
    def _connect_existing(self, config: BrowserConfig) -> BrowserSession:
        port = config.marionette_port or config.debugging_port

        raise BrowserConnectionError(
            "Connecting to an already-running Firefox session is not reliably supported by this provider yet. "
            f"Requested port: {port}. Start a new Firefox session instead or implement a dedicated Marionette provider."
        )