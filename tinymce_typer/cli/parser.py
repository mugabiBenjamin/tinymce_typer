import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tinymce_typer.config.loader import ConfigLoadError, load_config
from tinymce_typer.config.settings import AppConfig, ConfigError


class CliError(Exception):
    pass


def _str_default(defaults: dict, key: str, fallback: str = "") -> str:
    value = defaults.get(key, fallback)
    if value is None:
        return fallback
    return str(value)


def _int_default(defaults: dict, key: str, fallback: int) -> int:
    value = defaults.get(key, fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _float_default(defaults: dict, key: str, fallback: float) -> float:
    value = defaults.get(key, fallback)
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _bool_default(defaults: dict, key: str, fallback: bool = False) -> bool:
    value = defaults.get(key, fallback)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _list_default(defaults: dict, key: str) -> list[str]:
    value = defaults.get(key, [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return [str(item) for item in value]
    return []


def build_parser(defaults: dict | None = None) -> argparse.ArgumentParser:
    defaults = defaults or {}

    parser = argparse.ArgumentParser(
        prog="tinymce-typer",
        description="Insert local text-based content into browser rich text editors.",
    )

    parser.add_argument("url", help="URL of the page with the editor")
    parser.add_argument("file", help="Path to the main text file containing content to insert")

    parser.add_argument(
        "--config",
        default=_str_default(defaults, "config_path"),
        help="Path to a JSON, TOML, or YAML configuration file",
    )

    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default=_str_default(defaults, "browser", "chrome"),
        help="Browser to use",
    )
    parser.add_argument(
        "--profile",
        default=_str_default(defaults, "profile"),
        help="Path to browser profile directory",
    )

    parser.add_argument(
        "--iframe-id",
        default=_str_default(defaults, "iframe_id"),
        help="ID of the iframe containing the editor",
    )
    parser.add_argument(
        "--editor-id",
        default=_str_default(defaults, "editor_id"),
        help="ID of the editor element",
    )
    parser.add_argument(
        "--detect-multiple",
        action="store_true",
        default=_bool_default(defaults, "detect_multiple"),
        help="Detect and select from multiple editors",
    )
    parser.add_argument(
        "--editor-index",
        type=int,
        default=defaults.get("editor_index"),
        help="Editor index to use when multiple editors are detected",
    )
    parser.add_argument(
        "--wait-selector",
        default=_str_default(defaults, "wait_selector"),
        help="CSS selector to wait for before editor detection",
    )

    parser.add_argument(
        "--type-delay",
        type=float,
        default=_float_default(defaults, "type_delay", 0.01),
        help="Delay between character insertions",
    )
    parser.add_argument(
        "--formatted",
        action="store_true",
        default=_bool_default(defaults, "formatted"),
        help="Preserve HTML formatting in the content",
    )
    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        default=_bool_default(defaults, "no_clipboard"),
        help="Disable clipboard paste attempt",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        default=_bool_default(defaults, "batch"),
        help="Use batch insertion",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=_int_default(defaults, "batch_size", 50),
        help="Number of characters to insert per batch",
    )
    parser.add_argument(
        "--batch-delay",
        type=float,
        default=_float_default(defaults, "batch_delay", 0.1),
        help="Delay between batch insertions",
    )

    parser.add_argument(
        "--no-session",
        action="store_true",
        default=_bool_default(defaults, "no_session"),
        help="Disable session saving/loading",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=_bool_default(defaults, "reset"),
        help="Reset previous session progress",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=_bool_default(defaults, "resume"),
        help="Resume saved progress without asking",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        default=_bool_default(defaults, "no_resume"),
        help="Do not resume saved progress",
    )
    parser.add_argument(
        "--encrypt",
        action="store_true",
        default=_bool_default(defaults, "encrypt"),
        help="Encrypt session data with a password",
    )
    parser.add_argument(
        "--session-file",
        default=_str_default(defaults, "session_file", "tinymce_session.json"),
        help="Path to the session file",
    )

    parser.add_argument(
        "--no-verification",
        action="store_true",
        default=_bool_default(defaults, "no_verification"),
        help="Disable content verification after insertion",
    )
    parser.add_argument(
        "--verification-mode",
        choices=["normalized-text", "exact-text", "html"],
        default=_str_default(defaults, "verification_mode", "normalized-text"),
        help="Verification mode to use after insertion",
    )
    parser.add_argument(
        "--verification-threshold",
        type=float,
        default=_float_default(defaults, "verification_threshold", 0.90),
        help="Minimum similarity threshold for verification",
    )

    parser.add_argument(
        "--use-existing",
        action="store_true",
        default=_bool_default(defaults, "use_existing"),
        help="Connect to an existing browser session",
    )
    parser.add_argument(
        "--debugging-port",
        type=int,
        default=_int_default(defaults, "debugging_port", 9222),
        help="Chrome remote debugging port",
    )
    parser.add_argument(
        "--marionette-port",
        type=int,
        default=defaults.get("marionette_port"),
        help="Firefox Marionette port",
    )
    parser.add_argument(
        "--force-navigation",
        action="store_true",
        default=_bool_default(defaults, "force_navigation"),
        help="Navigate to the given URL even when using an existing browser",
    )

    parser.add_argument(
        "--files",
        nargs="+",
        default=_list_default(defaults, "files"),
        help="Multiple content files to insert sequentially",
    )
    parser.add_argument(
        "--file-separator",
        default=_str_default(defaults, "file_separator", "\n\n"),
        help="Separator to place between multiple input files",
    )
    parser.add_argument(
        "--include-file-headings",
        action="store_true",
        default=_bool_default(defaults, "include_file_headings"),
        help="Add a heading before each file when merging multiple files",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        default=_bool_default(defaults, "yes"),
        help="Automatically answer yes to safe confirmation prompts",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=_bool_default(defaults, "non_interactive"),
        help="Run without interactive prompts",
    )
    parser.add_argument(
        "--close-on-complete",
        action="store_true",
        default=_bool_default(defaults, "close_on_complete"),
        help="Close the browser after successful completion",
    )
    parser.add_argument(
        "--keep-open",
        "--keep-browser-open",
        dest="keep_browser_open",
        action="store_true",
        default=_bool_default(defaults, "keep_browser_open", True),
        help="Keep the browser open after completion",
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        default=_bool_default(defaults, "detach"),
        help="Detach from the browser session without closing it",
    )
    parser.add_argument(
        "--browser-wait-timeout",
        dest="browser_wait_timeout_seconds",
        type=int,
        default=_int_default(defaults, "browser_wait_timeout_seconds", 0),
        help="Seconds to keep the browser open before closing. Use 0 to wait until interrupted.",
    )
    parser.add_argument(
        "--implicit-wait",
        dest="implicit_wait_seconds",
        type=int,
        default=_int_default(defaults, "implicit_wait_seconds", 10),
        help="Selenium implicit wait in seconds",
    )

    parser.add_argument(
        "--log-level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        default=_str_default(defaults, "log_level", "INFO").upper(),
        help="Logging level",
    )
    parser.add_argument(
        "--log-file",
        default=_str_default(defaults, "log_file"),
        help="Optional path to write detailed logs",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=_bool_default(defaults, "verbose"),
        help="Enable debug-level console logs",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=_bool_default(defaults, "quiet"),
        help="Only show errors",
    )

    parser.add_argument(
        "--diagnostics",
        choices=["all", "browser", "clipboard", "editor", "file", "session"],
        default=_str_default(defaults, "diagnostics"),
        help="Run diagnostics instead of full content insertion",
    )

    return parser


def _parse_config_path(argv: Sequence[str] | None) -> str | None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default="")
    parsed, _ = pre_parser.parse_known_args(argv)
    value = parsed.config.strip()
    return value or None


def parse_cli_args(argv: Sequence[str] | None = None) -> AppConfig:
    argv = list(argv if argv is not None else sys.argv[1:])

    try:
        config_path = _parse_config_path(argv)
        defaults = load_config(Path(config_path)) if config_path else load_config(None)
        parser = build_parser(defaults)
        namespace = parser.parse_args(argv)
        return AppConfig.from_namespace(namespace)
    except ConfigLoadError as exc:
        raise CliError(str(exc)) from exc
    except ConfigError as exc:
        raise CliError(str(exc)) from exc