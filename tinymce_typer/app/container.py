from dataclasses import dataclass
from getpass import getpass

from tinymce_typer.browser.factory import BrowserProviderFactory
from tinymce_typer.browser.lifecycle import BrowserLifecycleManager
from tinymce_typer.browser.navigation import BrowserNavigator
from tinymce_typer.cli.prompts import PromptManager
from tinymce_typer.config.settings import AppConfig
from tinymce_typer.content.formatter import ContentFormatter
from tinymce_typer.content.loader import ContentLoader
from tinymce_typer.editors.detector import EditorDetector
from tinymce_typer.exceptions import SessionError
from tinymce_typer.insertion.factory import InsertionStrategyFactory
from tinymce_typer.output.json_output import JsonOutputWriter
from tinymce_typer.output.terminal_output import TerminalOutputWriter
from tinymce_typer.progress.silent import SilentProgressReporter
from tinymce_typer.progress.terminal import TerminalProgressReporter
from tinymce_typer.sessions.store import SessionStore
from tinymce_typer.sessions.validator import SessionValidator
from tinymce_typer.verification.report import VerificationReporter
from tinymce_typer.verification.verifier import VerificationService


@dataclass(frozen=True)
class AppContainer:
    browser_provider: object
    browser_lifecycle: object
    browser_navigator: object
    content_loader: object
    content_formatter: object
    editor_detector: object
    insertion_chain: object
    session_store: object | None
    session_validator: object
    verification_service: object
    verification_reporter: object
    progress_reporter: object
    prompt_manager: object
    output_writer: object


class AppContainerFactory:
    def build(self, config: AppConfig) -> AppContainer:
        session_password = self._resolve_session_password(config)

        return AppContainer(
            browser_provider=BrowserProviderFactory().create(config.browser),
            browser_lifecycle=BrowserLifecycleManager(),
            browser_navigator=BrowserNavigator(),
            content_loader=ContentLoader(),
            content_formatter=ContentFormatter(),
            editor_detector=EditorDetector(),
            insertion_chain=InsertionStrategyFactory().create_chain(config.insertion),
            session_store=self._build_session_store(config, session_password),
            session_validator=SessionValidator(),
            verification_service=VerificationService(),
            verification_reporter=VerificationReporter(config.verification.verification_report_dir),
            progress_reporter=self._build_progress_reporter(config),
            prompt_manager=PromptManager(
                non_interactive=config.cli.non_interactive,
                assume_yes=config.cli.yes,
            ),
            output_writer=self._build_output_writer(config),
        )

    def _build_session_store(self, config: AppConfig, password: str) -> object | None:
        if config.session.no_session:
            return None

        return SessionStore(
            path=config.session.session_file,
            encrypted=config.session.encrypt,
            password=password,
        )

    def _resolve_session_password(self, config: AppConfig) -> str:
        if not config.session.encrypt:
            return ""

        if config.cli.non_interactive:
            raise SessionError("Encrypted sessions require an interactive password prompt.")

        password = getpass("Session password: ")

        if not password:
            raise SessionError("Encrypted sessions require a non-empty password.")

        return password

    def _build_progress_reporter(self, config: AppConfig) -> object:
        if config.output.mode == "json" or config.output.quiet_progress:
            return SilentProgressReporter()

        return TerminalProgressReporter()

    def _build_output_writer(self, config: AppConfig) -> object:
        if config.output.mode == "json":
            return JsonOutputWriter()

        return TerminalOutputWriter()