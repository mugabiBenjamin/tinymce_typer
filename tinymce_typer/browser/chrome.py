from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from tinymce_typer.browser.base import BrowserSession
from tinymce_typer.browser.validation import BrowserValidator
from tinymce_typer.config.settings import BrowserConfig
from tinymce_typer.exceptions import BrowserConnectionError, BrowserSetupError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class ChromeBrowserProvider:
    browser_name = "chrome"

    def __init__(self, validator: BrowserValidator | None = None):
        self.validator = validator or BrowserValidator()

    def start(self, config: BrowserConfig) -> BrowserSession:
        self.validator.validate_or_raise(config)

        if config.use_existing:
            return self._connect_existing(config)

        return self._start_new(config)

    def _start_new(self, config: BrowserConfig) -> BrowserSession:
        options = webdriver.ChromeOptions()

        if config.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
        else:
            options.add_argument("--start-maximized")

        if config.profile:
            options.add_argument(f"--user-data-dir={config.profile}")
            logger.warning("Using Chrome profile: %s", config.profile)

        try:
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options,
            )
            driver.implicitly_wait(config.implicit_wait_seconds)
        except WebDriverException as exc:
            raise BrowserSetupError(f"Could not start Chrome browser: {exc}") from exc

        return BrowserSession(
            driver=driver,
            browser_name=self.browser_name,
            is_existing_session=False,
            should_quit_driver=True,
        )
    def _connect_existing(self, config: BrowserConfig) -> BrowserSession:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"localhost:{config.debugging_port}")

        try:
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options,
            )
            driver.execute_script("return document.readyState")
        except WebDriverException as exc:
            raise BrowserConnectionError(
                "Could not connect to existing Chrome session. "
                f"Start Chrome with --remote-debugging-port={config.debugging_port}. "
                f"Original error: {exc}"
            ) from exc

        logger.info("Connected to existing Chrome session on port %s", config.debugging_port)

        return BrowserSession(
            driver=driver,
            browser_name=self.browser_name,
            is_existing_session=True,
            should_quit_driver=False,
        )