import logging
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LoggingConfig:
    level: str = "INFO"
    verbose: bool = False
    quiet: bool = False
    log_file: str = ""


_VALID_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _resolve_level(config: LoggingConfig) -> int:
    if config.quiet:
        return logging.ERROR

    if config.verbose:
        return logging.DEBUG

    normalized = config.level.strip().upper()

    if normalized not in _VALID_LEVELS:
        return logging.INFO

    return _VALID_LEVELS[normalized]


def _build_formatter(verbose: bool) -> logging.Formatter:
    if verbose:
        return logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        )

    return logging.Formatter("%(levelname)s | %(message)s")


def configure_logging(config: LoggingConfig) -> None:
    level = _resolve_level(config)
    formatter = _build_formatter(config.verbose)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if config.log_file.strip():
        log_path = Path(config.log_file).expanduser()

        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
                )
            )
            root_logger.addHandler(file_handler)
        except OSError as exc:
            root_logger.warning("Could not create log file '%s': %s", log_path, exc)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)