SUPPORTED_CONFIG_EXTENSIONS = {".json", ".toml", ".yaml", ".yml"}

ENV_PREFIX = "TINYMCE_TYPER_"

CONFIG_KEYS = {
    "browser",
    "profile",
    "use_existing",
    "debugging_port",
    "marionette_port",
    "force_navigation",
    "close_on_complete",
    "keep_browser_open",
    "iframe_id",
    "editor_id",
    "detect_multiple",
    "editor_index",
    "wait_selector",
    "type_delay",
    "formatted",
    "no_clipboard",
    "batch",
    "batch_size",
    "batch_delay",
    "no_session",
    "reset",
    "resume",
    "no_resume",
    "encrypt",
    "session_file",
    "no_verification",
    "verification_mode",
    "verification_threshold",
    "files",
    "file_separator",
    "yes",
    "non_interactive",
    "log_level",
    "log_file",
    "verbose",
    "quiet",
    "diagnostics",
}


ENV_KEY_MAP = {
    "TINYMCE_TYPER_BROWSER": "browser",
    "TINYMCE_TYPER_BROWSER_PROFILE": "profile",
    "TINYMCE_TYPER_USE_EXISTING": "use_existing",
    "TINYMCE_TYPER_DEBUGGING_PORT": "debugging_port",
    "TINYMCE_TYPER_MARIONETTE_PORT": "marionette_port",
    "TINYMCE_TYPER_FORCE_NAVIGATION": "force_navigation",
    "TINYMCE_TYPER_CLOSE_ON_COMPLETE": "close_on_complete",
    "TINYMCE_TYPER_KEEP_BROWSER_OPEN": "keep_browser_open",
    "TINYMCE_TYPER_IFRAME_ID": "iframe_id",
    "TINYMCE_TYPER_EDITOR_ID": "editor_id",
    "TINYMCE_TYPER_DETECT_MULTIPLE": "detect_multiple",
    "TINYMCE_TYPER_EDITOR_INDEX": "editor_index",
    "TINYMCE_TYPER_WAIT_SELECTOR": "wait_selector",
    "TINYMCE_TYPER_TYPE_DELAY": "type_delay",
    "TINYMCE_TYPER_FORMATTED": "formatted",
    "TINYMCE_TYPER_NO_CLIPBOARD": "no_clipboard",
    "TINYMCE_TYPER_BATCH": "batch",
    "TINYMCE_TYPER_BATCH_SIZE": "batch_size",
    "TINYMCE_TYPER_BATCH_DELAY": "batch_delay",
    "TINYMCE_TYPER_NO_SESSION": "no_session",
    "TINYMCE_TYPER_RESET": "reset",
    "TINYMCE_TYPER_RESUME": "resume",
    "TINYMCE_TYPER_NO_RESUME": "no_resume",
    "TINYMCE_TYPER_ENCRYPT_SESSION": "encrypt",
    "TINYMCE_TYPER_SESSION_FILE": "session_file",
    "TINYMCE_TYPER_NO_VERIFICATION": "no_verification",
    "TINYMCE_TYPER_VERIFICATION_MODE": "verification_mode",
    "TINYMCE_TYPER_VERIFICATION_THRESHOLD": "verification_threshold",
    "TINYMCE_TYPER_FILE_SEPARATOR": "file_separator",
    "TINYMCE_TYPER_YES": "yes",
    "TINYMCE_TYPER_NON_INTERACTIVE": "non_interactive",
    "TINYMCE_TYPER_LOG_LEVEL": "log_level",
    "TINYMCE_TYPER_LOG_FILE": "log_file",
    "TINYMCE_TYPER_VERBOSE": "verbose",
    "TINYMCE_TYPER_QUIET": "quiet",
    "TINYMCE_TYPER_DIAGNOSTICS": "diagnostics",
}


BOOL_KEYS = {
    "use_existing",
    "force_navigation",
    "close_on_complete",
    "keep_browser_open",
    "detect_multiple",
    "formatted",
    "no_clipboard",
    "batch",
    "no_session",
    "reset",
    "resume",
    "no_resume",
    "encrypt",
    "no_verification",
    "yes",
    "non_interactive",
    "verbose",
    "quiet",
}


INT_KEYS = {
    "debugging_port",
    "marionette_port",
    "editor_index",
    "batch_size",
}


FLOAT_KEYS = {
    "type_delay",
    "batch_delay",
    "verification_threshold",
}


LIST_KEYS = {
    "files",
}


def normalize_key(key: str) -> str:
    return key.strip().replace("-", "_").lower()


def is_supported_key(key: str) -> bool:
    return normalize_key(key) in CONFIG_KEYS