from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from tinymce_typer.logging.setup import LoggingConfig as RuntimeLoggingConfig


BrowserName = Literal["chrome", "firefox"]
VerificationMode = Literal["normalized-text", "exact-text", "html"]
DiagnosticsMode = Literal["", "all", "browser", "clipboard", "editor", "file", "session"]


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class BrowserConfig:
    browser: BrowserName = "chrome"
    profile: str = ""
    use_existing: bool = False
    debugging_port: int = 9222
    marionette_port: int | None = None
    force_navigation: bool = False
    close_on_complete: bool = False
    keep_browser_open: bool = True


@dataclass(frozen=True)
class EditorConfig:
    iframe_id: str = ""
    editor_id: str = ""
    detect_multiple: bool = False
    editor_index: int | None = None
    wait_selector: str = ""


@dataclass(frozen=True)
class InsertionConfig:
    type_delay: float = 0.01
    formatted: bool = False
    no_clipboard: bool = False
    batch: bool = False
    batch_size: int = 50
    batch_delay: float = 0.1


@dataclass(frozen=True)
class SessionConfig:
    no_session: bool = False
    reset: bool = False
    resume: bool = False
    no_resume: bool = False
    encrypt: bool = False
    session_file: str = "tinymce_session.json"


@dataclass(frozen=True)
class VerificationConfig:
    no_verification: bool = False
    verification_mode: VerificationMode = "normalized-text"
    verification_threshold: float = 0.90


@dataclass(frozen=True)
class CliBehaviorConfig:
    yes: bool = False
    non_interactive: bool = False


@dataclass(frozen=True)
class ContentConfig:
    url: str
    file: str
    files: list[str] = field(default_factory=list)
    file_separator: str = "\n\n"


@dataclass(frozen=True)
class DiagnosticsConfig:
    mode: DiagnosticsMode = ""


@dataclass(frozen=True)
class AppConfig:
    content: ContentConfig
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)
    insertion: InsertionConfig = field(default_factory=InsertionConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    verification: VerificationConfig = field(default_factory=VerificationConfig)
    cli: CliBehaviorConfig = field(default_factory=CliBehaviorConfig)
    logging: RuntimeLoggingConfig = field(default_factory=RuntimeLoggingConfig)
    diagnostics: DiagnosticsConfig = field(default_factory=DiagnosticsConfig)
    config_path: str = ""

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "AppConfig":
        data = vars(namespace)

        config = cls(
            content=ContentConfig(
                url=str(data["url"]),
                file=str(data["file"]),
                files=[str(item) for item in data.get("files", [])],
                file_separator=str(data.get("file_separator", "\n\n")),
            ),
            browser=BrowserConfig(
                browser=data.get("browser", "chrome"),
                profile=str(data.get("profile", "")),
                use_existing=bool(data.get("use_existing", False)),
                debugging_port=int(data.get("debugging_port", 9222)),
                marionette_port=data.get("marionette_port"),
                force_navigation=bool(data.get("force_navigation", False)),
                close_on_complete=bool(data.get("close_on_complete", False)),
                keep_browser_open=bool(data.get("keep_browser_open", True)),
            ),
            editor=EditorConfig(
                iframe_id=str(data.get("iframe_id", "")),
                editor_id=str(data.get("editor_id", "")),
                detect_multiple=bool(data.get("detect_multiple", False)),
                editor_index=data.get("editor_index"),
                wait_selector=str(data.get("wait_selector", "")),
            ),
            insertion=InsertionConfig(
                type_delay=float(data.get("type_delay", 0.01)),
                formatted=bool(data.get("formatted", False)),
                no_clipboard=bool(data.get("no_clipboard", False)),
                batch=bool(data.get("batch", False)),
                batch_size=int(data.get("batch_size", 50)),
                batch_delay=float(data.get("batch_delay", 0.1)),
            ),
            session=SessionConfig(
                no_session=bool(data.get("no_session", False)),
                reset=bool(data.get("reset", False)),
                resume=bool(data.get("resume", False)),
                no_resume=bool(data.get("no_resume", False)),
                encrypt=bool(data.get("encrypt", False)),
                session_file=str(data.get("session_file", "tinymce_session.json")),
            ),
            verification=VerificationConfig(
                no_verification=bool(data.get("no_verification", False)),
                verification_mode=data.get("verification_mode", "normalized-text"),
                verification_threshold=float(data.get("verification_threshold", 0.90)),
            ),
            cli=CliBehaviorConfig(
                yes=bool(data.get("yes", False)),
                non_interactive=bool(data.get("non_interactive", False)),
            ),
            logging=RuntimeLoggingConfig(
                level=str(data.get("log_level", "INFO")),
                verbose=bool(data.get("verbose", False)),
                quiet=bool(data.get("quiet", False)),
                log_file=str(data.get("log_file", "")),
            ),
            diagnostics=DiagnosticsConfig(
                mode=str(data.get("diagnostics", "")),
            ),
            config_path=str(data.get("config", "")),
        )

        config.validate()
        return config

    def validate(self) -> None:
        if not self.content.url.strip():
            raise ConfigError("URL is required.")

        if not self.content.file.strip():
            raise ConfigError("Main content file path is required.")

        if self.browser.browser not in {"chrome", "firefox"}:
            raise ConfigError("Browser must be either 'chrome' or 'firefox'.")

        if self.browser.debugging_port <= 0 or self.browser.debugging_port > 65535:
            raise ConfigError("Debugging port must be between 1 and 65535.")

        if self.browser.marionette_port is not None:
            if self.browser.marionette_port <= 0 or self.browser.marionette_port > 65535:
                raise ConfigError("Marionette port must be between 1 and 65535.")

        if self.editor.editor_index is not None and self.editor.editor_index < 1:
            raise ConfigError("Editor index must be 1 or greater.")

        if self.insertion.type_delay < 0:
            raise ConfigError("Type delay cannot be negative.")

        if self.insertion.batch_size < 1:
            raise ConfigError("Batch size must be 1 or greater.")

        if self.insertion.batch_delay < 0:
            raise ConfigError("Batch delay cannot be negative.")

        if self.session.resume and self.session.no_resume:
            raise ConfigError("Use either resume or no-resume, not both.")

        if not self.session.session_file.strip():
            raise ConfigError("Session file path cannot be empty.")

        if self.verification.verification_mode not in {"normalized-text", "exact-text", "html"}:
            raise ConfigError("Invalid verification mode.")

        if not 0 <= self.verification.verification_threshold <= 1:
            raise ConfigError("Verification threshold must be between 0 and 1.")

        if self.browser.profile:
            profile_path = Path(self.browser.profile).expanduser()
            if not profile_path.exists():
                raise ConfigError(f"Browser profile path does not exist: {profile_path}")

        if self.logging.level.strip().upper() not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ConfigError("Log level must be CRITICAL, ERROR, WARNING, INFO, or DEBUG.")

        if self.logging.verbose and self.logging.quiet:
            raise ConfigError("Use either verbose or quiet logging, not both.")

        if self.diagnostics.mode not in {"", "all", "browser", "clipboard", "editor", "file", "session"}:
            raise ConfigError("Diagnostics mode must be one of: all, browser, clipboard, editor, file, session.")

    def to_legacy_namespace(self) -> SimpleNamespace:
        return SimpleNamespace(
            url=self.content.url,
            file=self.content.file,
            files=self.content.files,
            file_separator=self.content.file_separator,
            browser=self.browser.browser,
            profile=self.browser.profile,
            use_existing=self.browser.use_existing,
            debugging_port=self.browser.debugging_port,
            marionette_port=self.browser.marionette_port,
            force_navigation=self.browser.force_navigation,
            iframe_id=self.editor.iframe_id,
            editor_id=self.editor.editor_id,
            detect_multiple=self.editor.detect_multiple,
            editor_index=self.editor.editor_index,
            wait_selector=self.editor.wait_selector,
            type_delay=self.insertion.type_delay,
            formatted=self.insertion.formatted,
            no_clipboard=self.insertion.no_clipboard,
            batch=self.insertion.batch,
            batch_size=self.insertion.batch_size,
            batch_delay=self.insertion.batch_delay,
            no_session=self.session.no_session,
            reset=self.session.reset,
            resume=self.session.resume,
            no_resume=self.session.no_resume,
            encrypt=self.session.encrypt,
            session_file=self.session.session_file,
            no_verification=self.verification.no_verification,
            verification_mode=self.verification.verification_mode,
            verification_threshold=self.verification.verification_threshold,
            yes=self.cli.yes,
            non_interactive=self.cli.non_interactive,
            close_on_complete=self.browser.close_on_complete,
            keep_browser_open=self.browser.keep_browser_open,
            log_level=self.logging.level,
            log_file=self.logging.log_file,
            verbose=self.logging.verbose,
            quiet=self.logging.quiet,
            diagnostics=self.diagnostics.mode,
        )