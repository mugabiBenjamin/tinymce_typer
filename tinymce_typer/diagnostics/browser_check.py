from dataclasses import dataclass
from logging import config

from tinymce_typer.browser.platform import PlatformInspector
from tinymce_typer.browser.validation import BrowserValidator
from tinymce_typer.config.settings import AppConfig


@dataclass(frozen=True)
class BrowserDiagnosticResult:
    name: str
    passed: bool
    message: str
    details: dict[str, str]


class BrowserDiagnostic:
    def __init__(
        self,
        validator: BrowserValidator | None = None,
        platform_inspector: PlatformInspector | None = None,
    ):
        self.validator = validator or BrowserValidator()
        self.platform_inspector = platform_inspector or PlatformInspector()

    def run(self, config: AppConfig) -> list[BrowserDiagnosticResult]:
        platform_report = self.platform_inspector.inspect()
        validation = self.validator.validate(config.browser, strict_binary_check=True)

        results = [
            self._platform_result(platform_report),
            self._display_result(platform_report),
            self._container_result(platform_report),
            self._headless_result(config, platform_report),
            self._clipboard_result(platform_report),
            self._browser_matrix_result(platform_report),
            self._browser_validation_result(validation),
            self._configured_browser_result(config, platform_report),
        ]

        if config.browser.use_existing or config.browser.browser == "remote":
            results.append(self._remote_port_result(config))

        return results

    def _platform_result(self, platform_report) -> BrowserDiagnosticResult:
        return BrowserDiagnosticResult(
            name="platform",
            passed=True,
            message=f"{platform_report.os_name} {platform_report.os_release} on {platform_report.machine}",
            details={
                "os": platform_report.os_name,
                "release": platform_report.os_release,
                "version": platform_report.os_version,
                "system": platform_report.system,
                "architecture": platform_report.architecture,
                "machine": platform_report.machine,
                "processor": platform_report.processor,
                "python": platform_report.python_version,
            },
        )

    def _display_result(self, platform_report) -> BrowserDiagnosticResult:
        passed = not platform_report.is_linux or platform_report.display_server != "none" or platform_report.headless_hint.recommended

        return BrowserDiagnosticResult(
            name="display_server",
            passed=passed,
            message=f"Display server: {platform_report.display_server}",
            details={
                "display_server": platform_report.display_server,
                "is_linux": str(platform_report.is_linux),
            },
        )

    def _container_result(self, platform_report) -> BrowserDiagnosticResult:
        return BrowserDiagnosticResult(
            name="container",
            passed=True,
            message=platform_report.container.message,
            details={
                "detected": str(platform_report.container.detected),
                "runtime": platform_report.container.runtime,
            },
        )

    def _headless_result(self, config: AppConfig, platform_report) -> BrowserDiagnosticResult:
        if config.browser.use_existing and getattr(config.browser, "headless", False):
            return BrowserDiagnosticResult(
                name="headless_mode",
                passed=False,
                message="Headless mode cannot be applied when connecting to an existing browser session.",
                details={
                    "headless": str(config.browser.headless),
                    "use_existing": str(config.browser.use_existing),
                    "hint": platform_report.headless_hint.message,
                },
            )

        return BrowserDiagnosticResult(
            name="headless_mode",
            passed=True,
            message=platform_report.headless_hint.message,
            details={
                "configured_headless": str(getattr(config.browser, "headless", False)),
                "recommended": str(platform_report.headless_hint.recommended),
                **platform_report.headless_hint.details,
            },
        )

    def _clipboard_result(self, platform_report) -> BrowserDiagnosticResult:
        return BrowserDiagnosticResult(
            name="clipboard_backend",
            passed=platform_report.clipboard.available,
            message=platform_report.clipboard.message,
            details={
                "backend": platform_report.clipboard.backend,
                "session_type": platform_report.clipboard.session_type,
                "checked": ", ".join(platform_report.clipboard.candidates_checked),
            },
        )

    def _browser_matrix_result(self, platform_report) -> BrowserDiagnosticResult:
        details = {}

        for browser in platform_report.browsers:
            details[f"{browser.name}_available"] = str(browser.available)
            details[f"{browser.name}_executable"] = browser.executable
            details[f"{browser.name}_checked"] = ", ".join(browser.candidates_checked)

        available = [browser.name for browser in platform_report.browsers if browser.available]

        return BrowserDiagnosticResult(
            name="browser_matrix",
            passed=bool(available),
            message=f"Available browsers: {', '.join(available)}" if available else "No supported browser executable was detected.",
            details=details,
        )

    def _browser_validation_result(self, validation) -> BrowserDiagnosticResult:
        return BrowserDiagnosticResult(
            name="browser_validation",
            passed=validation.passed,
            message="Browser configuration is valid" if validation.passed else "Browser configuration has errors",
            details={
                "errors": "; ".join(validation.errors),
                "warnings": "; ".join(validation.warnings),
            },
        )

    def _configured_browser_result(self, config: AppConfig, platform_report) -> BrowserDiagnosticResult:
        if config.browser.browser == "remote":
            port_check = self.platform_inspector.check_remote_webdriver_url(
                config.browser.remote_webdriver_url
            )

            return BrowserDiagnosticResult(
                name="configured_browser",
                passed=port_check.reachable,
                message=(
                    f"Remote WebDriver endpoint is reachable: {config.browser.remote_webdriver_url}"
                    if port_check.reachable
                    else f"Remote WebDriver endpoint is not reachable: {config.browser.remote_webdriver_url}"
                ),
                details={
                    "browser": "remote",
                    "remote_browser_name": config.browser.remote_browser_name,
                    "remote_webdriver_url": config.browser.remote_webdriver_url,
                    "host": port_check.host,
                    "port": str(port_check.port),
                    "reachable": str(port_check.reachable),
                },
            )

        configured = platform_report.browser(config.browser.browser)

        if configured is None:
            return BrowserDiagnosticResult(
                name="configured_browser",
                passed=False,
                message=f"Configured browser is unknown: {config.browser.browser}",
                details={"browser": config.browser.browser},
            )

        return BrowserDiagnosticResult(
            name="configured_browser",
            passed=configured.available,
            message=(
                f"Configured browser executable detected: {configured.executable}"
                if configured.available
                else f"Configured browser executable was not found: {config.browser.browser}"
            ),
            details={
                "browser": configured.name,
                "available": str(configured.available),
                "executable": configured.executable,
                "checked": ", ".join(configured.candidates_checked),
            },
        )

    def _remote_port_result(self, config: AppConfig) -> BrowserDiagnosticResult:
        if config.browser.browser == "remote":
            port_check = self.platform_inspector.check_remote_webdriver_url(
                config.browser.remote_webdriver_url
            )

            return BrowserDiagnosticResult(
                name="remote_webdriver_port",
                passed=port_check.reachable,
                message=port_check.message,
                details={
                    "url": config.browser.remote_webdriver_url,
                    "host": port_check.host,
                    "port": str(port_check.port),
                    "reachable": str(port_check.reachable),
                },
            )

        if config.browser.browser in {"chrome", "edge"}:
            port = config.browser.debugging_port
        else:
            port = config.browser.marionette_port or config.browser.debugging_port

        port_check = self.platform_inspector.check_port(port)

        return BrowserDiagnosticResult(
            name="browser_remote_port",
            passed=port_check.reachable,
            message=port_check.message,
            details={
                "host": port_check.host,
                "port": str(port_check.port),
                "reachable": str(port_check.reachable),
            },
        )