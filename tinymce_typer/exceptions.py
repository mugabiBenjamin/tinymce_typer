class TinyMCETyperError(Exception):
    exit_code = 1


class ConfigurationError(TinyMCETyperError):
    exit_code = 2


class CliInputError(TinyMCETyperError):
    exit_code = 2


class BrowserSetupError(TinyMCETyperError):
    exit_code = 10


class BrowserConnectionError(TinyMCETyperError):
    exit_code = 11


class BrowserNavigationError(TinyMCETyperError):
    exit_code = 12


class EditorNotFoundError(TinyMCETyperError):
    exit_code = 20


class MultipleEditorsError(TinyMCETyperError):
    exit_code = 21


class ContentLoadError(TinyMCETyperError):
    exit_code = 30


class ContentFormatError(TinyMCETyperError):
    exit_code = 31


class ClipboardError(TinyMCETyperError):
    exit_code = 40


class InsertionError(TinyMCETyperError):
    exit_code = 50


class VerificationError(TinyMCETyperError):
    exit_code = 60


class SessionError(TinyMCETyperError):
    exit_code = 70


class DiagnosticsError(TinyMCETyperError):
    exit_code = 80