from dataclasses import dataclass
from typing import Any, Protocol

from tinymce_typer.config.settings import BrowserConfig


@dataclass(frozen=True)
class BrowserSession:
    driver: Any
    browser_name: str
    is_existing_session: bool
    should_quit_driver: bool


class BrowserProvider(Protocol):
    browser_name: str

    def start(self, config: BrowserConfig) -> BrowserSession:
        ...