from dataclasses import dataclass
from pathlib import Path

from tinymce_typer.config.settings import AppConfig
from tinymce_typer.diagnostics.browser_check import BrowserDiagnostic, BrowserDiagnosticResult
from tinymce_typer.diagnostics.clipboard_check import ClipboardDiagnostic, ClipboardDiagnosticResult
from tinymce_typer.diagnostics.editor_check import EditorDiagnostic, EditorDiagnosticResult


DiagnosticResult = BrowserDiagnosticResult | ClipboardDiagnosticResult | EditorDiagnosticResult


@dataclass(frozen=True)
class DiagnosticsSummary:
    passed: bool
    results: list[DiagnosticResult]


class DiagnosticsRunner:
    def __init__(
        self,
        browser_diagnostic: BrowserDiagnostic | None = None,
        clipboard_diagnostic: ClipboardDiagnostic | None = None,
        editor_diagnostic: EditorDiagnostic | None = None,
    ):
        self.browser_diagnostic = browser_diagnostic or BrowserDiagnostic()
        self.clipboard_diagnostic = clipboard_diagnostic or ClipboardDiagnostic()
        self.editor_diagnostic = editor_diagnostic or EditorDiagnostic()

    def run(self, config: AppConfig) -> DiagnosticsSummary:
        mode = config.diagnostics.mode
        results: list[DiagnosticResult] = []

        if mode in {"all", "browser"}:
            results.extend(self.browser_diagnostic.run(config))

        if mode in {"all", "clipboard"}:
            results.extend(self.clipboard_diagnostic.run())

        if mode in {"all", "editor"}:
            results.extend(self.editor_diagnostic.run_static(config))

        if mode in {"all", "file"}:
            results.append(self._check_content_file(config))

        if mode in {"all", "session"}:
            results.append(self._check_session_file(config))

        return DiagnosticsSummary(
            passed=all(result.passed for result in results),
            results=results,
        )

    def _check_content_file(self, config: AppConfig) -> DiagnosticResult:
        path = Path(config.content.file).expanduser()

        if not path.exists():
            return BrowserDiagnosticResult(
                name="content_file",
                passed=False,
                message=f"Main content file does not exist: {path}",
                details={"file": str(path)},
            )

        if not path.is_file():
            return BrowserDiagnosticResult(
                name="content_file",
                passed=False,
                message=f"Main content path is not a file: {path}",
                details={"file": str(path)},
            )

        try:
            size = path.stat().st_size
        except OSError as exc:
            return BrowserDiagnosticResult(
                name="content_file",
                passed=False,
                message=f"Could not inspect main content file: {exc}",
                details={"file": str(path)},
            )

        missing_files = []

        for file_path in config.content.files:
            candidate = Path(file_path).expanduser()
            if not candidate.exists() or not candidate.is_file():
                missing_files.append(str(candidate))

        if missing_files:
            return BrowserDiagnosticResult(
                name="content_file",
                passed=False,
                message="One or more configured extra files are missing",
                details={
                    "main_file": str(path),
                    "missing_files": ", ".join(missing_files),
                },
            )

        return BrowserDiagnosticResult(
            name="content_file",
            passed=True,
            message=f"Main content file is readable: {path}",
            details={
                "file": str(path),
                "size_bytes": str(size),
                "extra_files": str(len(config.content.files)),
            },
        )

    def _check_session_file(self, config: AppConfig) -> DiagnosticResult:
        path = Path(config.session.session_file).expanduser()

        if config.session.no_session:
            return BrowserDiagnosticResult(
                name="session_file",
                passed=True,
                message="Session handling is disabled",
                details={"session_file": str(path)},
            )

        if not path.exists():
            return BrowserDiagnosticResult(
                name="session_file",
                passed=True,
                message="Session file does not exist yet; a new one can be created",
                details={"session_file": str(path)},
            )

        if not path.is_file():
            return BrowserDiagnosticResult(
                name="session_file",
                passed=False,
                message=f"Session path exists but is not a file: {path}",
                details={"session_file": str(path)},
            )

        try:
            size = path.stat().st_size
        except OSError as exc:
            return BrowserDiagnosticResult(
                name="session_file",
                passed=False,
                message=f"Could not inspect session file: {exc}",
                details={"session_file": str(path)},
            )

        return BrowserDiagnosticResult(
            name="session_file",
            passed=True,
            message=f"Session file exists: {path}",
            details={
                "session_file": str(path),
                "size_bytes": str(size),
            },
        )