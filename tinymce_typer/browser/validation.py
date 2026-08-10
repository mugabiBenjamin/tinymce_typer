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
    supported_browsers = {"chrome", "firefox"}

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

        if config.profile:
            profile_path = Path(config.profile).expanduser()

            if not profile_path.exists():
                errors.append(f"Browser profile path does not exist: {profile_path}")
            elif not profile_path.is_dir():
                errors.append(f"Browser profile path is not a directory: {profile_path}")
            else:
                warnings.append(
                    "Using a browser profile can expose authenticated sessions. Prefer a dedicated automation profile."
                )

        if config.use_existing:
            if config.browser == "chrome":
                if not self.is_port_open(config.debugging_port):
                    warnings.append(
                        f"Chrome remote debugging port {config.debugging_port} is not reachable yet."
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

        return BrowserValidationResult(
            passed=not errors,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    def validate_or_raise(self, config: BrowserConfig, strict_binary_check: bool = False) -> None:
        result = self.validate(config, strict_binary_check=strict_binary_check)

        if result.errors:
            raise BrowserSetupError("; ".join(result.errors))

    def find_browser_binary(self, browser: str) -> str | None:
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