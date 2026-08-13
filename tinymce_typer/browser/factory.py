from tinymce_typer.browser.base import BrowserProvider
from tinymce_typer.browser.chrome import ChromeBrowserProvider
from tinymce_typer.browser.edge import EdgeBrowserProvider
from tinymce_typer.browser.firefox import FirefoxBrowserProvider
from tinymce_typer.browser.validation import BrowserValidator
from tinymce_typer.config.settings import BrowserConfig
from tinymce_typer.exceptions import BrowserSetupError


class BrowserProviderFactory:
    def __init__(self, validator: BrowserValidator | None = None):
        self.validator = validator or BrowserValidator()

    def create(self, config: BrowserConfig) -> BrowserProvider:
        if config.browser == "chrome":
            return ChromeBrowserProvider(self.validator)

        if config.browser == "firefox":
            return FirefoxBrowserProvider(self.validator)

        if config.browser == "edge":
            return EdgeBrowserProvider(self.validator)

        raise BrowserSetupError(f"Unsupported browser provider: {config.browser}")