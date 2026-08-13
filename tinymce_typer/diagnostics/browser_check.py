from dataclasses import dataclass

from tinymce_typer.browser.validation import BrowserValidator
from tinymce_typer.config.settings import AppConfig


@dataclass(frozen=True)
class BrowserDiagnosticResult:
    name: str
    passed: bool
    message: str
    details: dict[str, str]


class BrowserDiagnostic:
    def __init__(self, validator: BrowserValidator | None = None):
        self.validator = validator or BrowserValidator()

    def run(self, config: AppConfig) -> list[BrowserDiagnosticResult]:
        validation = self.validator.validate(config.browser, strict_binary_check=True)
        results: list[BrowserDiagnosticResult] = []

        results.append(
            BrowserDiagnosticResult(
                name="browser_validation",
                passed=validation.passed,
                message="Browser configuration is valid" if validation.passed else "Browser configuration has errors",
                details={
                    "errors": "; ".join(validation.errors),
                    "warnings": "; ".join(validation.warnings),
                    "headless": str(config.browser.headless),
                },
            )
        )

        binary = self.validator.find_browser_binary(config.browser.browser)

        results.append(
            BrowserDiagnosticResult(
                name="browser_binary",
                passed=binary is not None,
                message=f"Detected browser executable: {binary}" if binary else f"Could not detect {config.browser.browser} in PATH",
                details={
                    "browser": config.browser.browser,
                    "binary": binary or "",
                },
            )
        )

        if config.browser.use_existing:
            if config.browser.browser == "chrome":
                port = config.browser.debugging_port
            else:
                port = config.browser.marionette_port or config.browser.debugging_port

            reachable = self.validator.is_port_open(port)

            results.append(
                BrowserDiagnosticResult(
                    name="browser_remote_port",
                    passed=reachable,
                    message=f"Remote browser port is reachable: {port}" if reachable else f"Remote browser port is not reachable: {port}",
                    details={"port": str(port)},
                )
            )

        return results