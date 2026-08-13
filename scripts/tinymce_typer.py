import sys

from tinymce_typer.cli.parser import CliError, parse_cli_args
from tinymce_typer.diagnostics.runner import DiagnosticsRunner
from tinymce_typer.exceptions import TinyMCETyperError
from tinymce_typer.logging.setup import configure_logging, get_logger


logger = get_logger(__name__)


def _print_diagnostics(summary) -> None:
    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.message}")

        if result.details:
            for key, value in result.details.items():
                print(f"  - {key}: {value}")


def main() -> int:
    try:
        config = parse_cli_args()
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    configure_logging(config.logging)

    logger.debug("Configuration loaded successfully")

    if config.diagnostics.mode:
        logger.info("Running diagnostics mode: %s", config.diagnostics.mode)
        summary = DiagnosticsRunner().run(config)
        _print_diagnostics(summary)
        return 0 if summary.passed else 80

    try:
        from tinymce_typer.app.typer_app import TyperApp
    except ImportError as exc:
        logger.error(
            "TyperApp is not available. Ensure tinymce_typer.app.typer_app exists and imports correctly. "
            "Original error: %s",
            exc,
        )
        return 2

    try:
        app = TyperApp(config)
        result = app.run()
    except KeyboardInterrupt:
        logger.warning("Script terminated by user")
        return 130
    except TinyMCETyperError as exc:
        logger.error("%s", exc)
        return getattr(exc, "exit_code", 1)
    except Exception:
        logger.exception("Unexpected fatal error")
        return 1

    exit_code = getattr(result, "exit_code", None)

    if isinstance(exit_code, int):
        return exit_code

    success = getattr(result, "success", None)

    if isinstance(success, bool):
        return 0 if success else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())