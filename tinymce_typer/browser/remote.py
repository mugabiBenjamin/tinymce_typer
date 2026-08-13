from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from tinymce_typer.browser.base import BrowserSession
from tinymce_typer.browser.validation import BrowserValidator
from tinymce_typer.config.settings import BrowserConfig
from tinymce_typer.exceptions import BrowserConnectionError, BrowserSetupError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class RemoteBrowserProvider:
    browser_name = "remote"

    supported_remote_browsers = {"chrome", "firefox", "edge"}

    def __init__(self, validator: BrowserValidator | None = None):
        self.validator = validator or BrowserValidator()

    def start(self, config: BrowserConfig) -> BrowserSession:
        self.validator.validate_or_raise(config)

        self._validate_remote_config(config)

        return self._connect_remote(config)

    def _connect_remote(self, config: BrowserConfig) -> BrowserSession:
        options = self._build_options(config)

        try:
            driver = webdriver.Remote(
                command_executor=config.remote_webdriver_url,
                options=options,
            )
            driver.implicitly_wait(config.implicit_wait_seconds)
            driver.execute_script("return document.readyState")
        except WebDriverException as exc:
            raise BrowserConnectionError(
                "Could not connect to remote WebDriver. "
                f"URL: {config.remote_webdriver_url}. "
                f"Remote browser: {config.remote_browser_name}. "
                f"Original error: {exc}"
            ) from exc

        logger.info(
            "Connected to remote WebDriver at %s using browser %s",
            config.remote_webdriver_url,
            config.remote_browser_name,
        )

        return BrowserSession(
            driver=driver,
            browser_name=f"remote:{config.remote_browser_name}",
            is_existing_session=False,
            should_quit_driver=True,
        )

    def _build_options(self, config: BrowserConfig):
        browser_name = config.remote_browser_name.strip().lower()

        if browser_name == "chrome":
            options = webdriver.ChromeOptions()
            self._apply_chromium_options(options, config)
            return options

        if browser_name == "edge":
            options = webdriver.EdgeOptions()
            self._apply_chromium_options(options, config)
            return options

        if browser_name == "firefox":
            options = webdriver.FirefoxOptions()

            if config.headless:
                options.add_argument("-headless")

            return options

        raise BrowserSetupError(
            f"Unsupported remote browser name: {config.remote_browser_name}. "
            "Supported values are: chrome, firefox, edge."
        )

    def _apply_chromium_options(self, options, config: BrowserConfig) -> None:
        if config.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")

        # These are useful in Docker/Selenium Grid environments.
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    def _validate_remote_config(self, config: BrowserConfig) -> None:
        url = config.remote_webdriver_url.strip()

        if not url:
            raise BrowserSetupError("Remote WebDriver URL is required when --browser remote is used.")

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise BrowserSetupError(
                "Remote WebDriver URL must be a valid http(s) URL, "
                "for example: http://localhost:4444/wd/hub"
            )

        browser_name = config.remote_browser_name.strip().lower()

        if browser_name not in self.supported_remote_browsers:
            raise BrowserSetupError(
                f"Remote browser name must be one of: {', '.join(sorted(self.supported_remote_browsers))}."
            )

        if config.use_existing:
            raise BrowserSetupError(
                "--use-existing is not supported with --browser remote. "
                "Remote WebDriver creates or connects to a managed remote session."
            )

        if config.profile:
            raise BrowserSetupError(
                "Browser profiles are not supported with --browser remote. "
                "Use remote browser/container capabilities instead."
            )