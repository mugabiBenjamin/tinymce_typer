import platform
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path

from tinymce_typer.config.settings import BrowserConfig
from tinymce_typer.exceptions import BrowserSetupError


@dataclass(frozen=True)
class BrowserValidationResult:
    passed: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


class BrowserValidator:
    supported_browsers = {"chrome", "firefox", "edge", "remote"}
    supported_remote_browsers = {"chrome", "firefox", "edge"}

    def validate(self, config: BrowserConfig, strict_binary_check: bool = False) -> BrowserValidationResult:
        warnings: list[str] = []
        errors: list[str] = []

        if config.browser not in self.supported_browsers:
            errors.append(f"Unsupported browser: {config.browser}")

        if config.debugging_port <= 0 or config.debugging_port > 65535:
            errors.append("Debugging port must be between 1 and 65535.")

        if config.marionette_port is not None:
            if config.marionette_port <= 0 or config.marionette_port > 65535:
                errors.append("Marionette port must be between 1 and 65535.")

        if config.browser == "remote":
            self._validate_remote_config(config, warnings, errors)
        else:
            self._validate_local_config(config, strict_binary_check, warnings, errors)

        return BrowserValidationResult(
            passed=not errors,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    def _validate_local_config(
        self,
        config: BrowserConfig,
        strict_binary_check: bool,
        warnings: list[str],
        errors: list[str],
    ) -> None:
        if config.remote_webdriver_url.strip():
            errors.append("remote_webdriver_url can only be used when browser is remote.")

        if config.profile:
            profile_path = Path(config.profile).expanduser()

            if not profile_path.exists():
                errors.append(f"Browser profile path does not exist: {profile_path}")
            elif not profile_path.is_dir():
                errors.append(f"Browser profile path is not a directory: {profile_path}")
            else:
                warnings.append(
                    "Using a browser profile can expose authenticated sessions. "
                    "Prefer a dedicated automation profile."
                )

        if config.use_existing:
            if config.browser in {"chrome", "edge"}:
                if not self.is_port_open(config.debugging_port):
                    warnings.append(
                        f"{config.browser.title()} remote debugging port "
                        f"{config.debugging_port} is not reachable yet."
                    )

            if config.browser == "firefox":
                port = config.marionette_port or config.debugging_port

                if not self.is_port_open(port):
                    warnings.append(
                        f"Firefox remote control port {port} is not reachable yet."
                    )

        if strict_binary_check:
            binary = self.find_browser_binary(config.browser)

            if binary is None:
                errors.append(f"Could not detect a {config.browser} executable in PATH.")

    def _validate_remote_config(
        self,
        config: BrowserConfig,
        warnings: list[str],
        errors: list[str],
    ) -> None:
        if not config.remote_webdriver_url.strip():
            errors.append("Remote WebDriver URL is required when browser is remote.")

        if config.remote_browser_name not in self.supported_remote_browsers:
            errors.append("Remote browser name must be one of: chrome, firefox, edge.")

        if config.use_existing:
            errors.append("use_existing cannot be used when browser is remote.")

        if config.profile:
            errors.append("Browser profiles are not supported when browser is remote.")

        if config.debugging_port != 9222:
            warnings.append("debugging_port is ignored when browser is remote.")

        if config.marionette_port is not None:
            warnings.append("marionette_port is ignored when browser is remote.")

        if config.force_navigation:
            warnings.append("force_navigation has no special effect for new remote browser sessions.")

    def validate_or_raise(self, config: BrowserConfig, strict_binary_check: bool = False) -> None:
        result = self.validate(config, strict_binary_check=strict_binary_check)

        if result.errors:
            raise BrowserSetupError("; ".join(result.errors))

    def find_browser_binary(self, browser: str) -> str | None:
        if browser == "remote":
            return None

        for candidate in self.browser_candidates(browser):
            resolved = shutil.which(candidate)

            if resolved:
                return resolved

        return None

    def browser_candidates(self, browser: str) -> tuple[str, ...]:
        system = platform.system().lower()

        if browser == "chrome":
            if system == "windows":
                return ("chrome.exe", "chrome", "google-chrome")
            if system == "darwin":
                return ("google-chrome", "chrome")
            return ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")

        if browser == "firefox":
            if system == "windows":
                return ("firefox.exe", "firefox")
            return ("firefox",)

        if browser == "edge":
            if system == "windows":
                return ("msedge.exe", "msedge", "microsoft-edge")
            if system == "darwin":
                return ("microsoft-edge", "msedge")
            return ("microsoft-edge", "microsoft-edge-stable", "msedge")

        if browser == "remote":
            return ()

        return ()

    def is_port_open(self, port: int, host: str = "127.0.0.1", timeout_seconds: float = 1.0) -> bool:
        if port <= 0 or port > 65535:
            return False

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout_seconds)
                return sock.connect_ex((host, port)) == 0
        except OSError:
            return False