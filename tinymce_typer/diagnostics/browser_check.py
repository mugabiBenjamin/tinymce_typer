import platform
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path

from tinymce_typer.config.settings import AppConfig


@dataclass(frozen=True)
class BrowserDiagnosticResult:
    name: str
    passed: bool
    message: str
    details: dict[str, str]


class BrowserDiagnostic:
    def run(self, config: AppConfig) -> list[BrowserDiagnosticResult]:
        results = [
            self._check_browser_choice(config),
            self._check_browser_binary(config),
            self._check_profile(config),
        ]

        if config.browser.use_existing:
            results.append(self._check_port(config.browser.debugging_port))

        return results

    def _check_browser_choice(self, config: AppConfig) -> BrowserDiagnosticResult:
        browser = config.browser.browser

        if browser in {"chrome", "firefox"}:
            return BrowserDiagnosticResult(
                name="browser_choice",
                passed=True,
                message=f"Browser choice is valid: {browser}",
                details={"browser": browser},
            )

        return BrowserDiagnosticResult(
            name="browser_choice",
            passed=False,
            message=f"Unsupported browser: {browser}",
            details={"browser": browser},
        )

    def _check_browser_binary(self, config: AppConfig) -> BrowserDiagnosticResult:
        browser = config.browser.browser
        candidates = self._browser_candidates(browser)
        found = [candidate for candidate in candidates if shutil.which(candidate)]

        if found:
            return BrowserDiagnosticResult(
                name="browser_binary",
                passed=True,
                message=f"Detected browser executable: {found[0]}",
                details={
                    "browser": browser,
                    "executable": found[0],
                    "platform": platform.system(),
                },
            )

        return BrowserDiagnosticResult(
            name="browser_binary",
            passed=False,
            message=f"Could not detect a {browser} executable in PATH",
            details={
                "browser": browser,
                "checked": ", ".join(candidates),
                "platform": platform.system(),
            },
        )

    def _check_profile(self, config: AppConfig) -> BrowserDiagnosticResult:
        profile = config.browser.profile.strip()

        if not profile:
            return BrowserDiagnosticResult(
                name="browser_profile",
                passed=True,
                message="No browser profile path configured",
                details={},
            )

        path = Path(profile).expanduser()

        if path.exists() and path.is_dir():
            return BrowserDiagnosticResult(
                name="browser_profile",
                passed=True,
                message=f"Browser profile path exists: {path}",
                details={"profile": str(path)},
            )

        return BrowserDiagnosticResult(
            name="browser_profile",
            passed=False,
            message=f"Browser profile path does not exist or is not a directory: {path}",
            details={"profile": str(path)},
        )

    def _check_port(self, port: int) -> BrowserDiagnosticResult:
        if port <= 0 or port > 65535:
            return BrowserDiagnosticResult(
                name="debugging_port",
                passed=False,
                message=f"Invalid debugging port: {port}",
                details={"port": str(port)},
            )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            status = sock.connect_ex(("127.0.0.1", port))

        if status == 0:
            return BrowserDiagnosticResult(
                name="debugging_port",
                passed=True,
                message=f"Remote debugging port is reachable: {port}",
                details={"port": str(port)},
            )

        return BrowserDiagnosticResult(
            name="debugging_port",
            passed=False,
            message=f"Remote debugging port is not reachable: {port}",
            details={"port": str(port)},
        )

    def _browser_candidates(self, browser: str) -> list[str]:
        system = platform.system().lower()

        if browser == "chrome":
            if system == "windows":
                return ["chrome", "chrome.exe", "google-chrome"]
            if system == "darwin":
                return ["google-chrome", "chrome"]
            return ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]

        if browser == "firefox":
            if system == "windows":
                return ["firefox", "firefox.exe"]
            return ["firefox"]

        return []