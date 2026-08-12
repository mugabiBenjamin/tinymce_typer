from typing import Any, Protocol

from tinymce_typer.config.settings import BrowserConfig


class BrowserSessionProtocol(Protocol):
    driver: Any
    browser_name: str
    is_existing_session: bool
    should_quit_driver: bool


class BrowserProviderProtocol(Protocol):
    browser_name: str

    def start(self, config: BrowserConfig) -> BrowserSessionProtocol:
        ...


class BrowserLifecycleProtocol(Protocol):
    def handle_completion(self, session: BrowserSessionProtocol, config: BrowserConfig) -> None:
        ...

    def handle_failure(self, session: BrowserSessionProtocol | None, config: BrowserConfig) -> None:
        ...

    def close(self, session: BrowserSessionProtocol) -> None:
        ...