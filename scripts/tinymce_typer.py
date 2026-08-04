import sys

from tinymce_typer.cli.parser import CliError, parse_cli_args


def main() -> int:
    try:
        config = parse_cli_args()
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        from tinymce_typer.app.typer_app import TyperApp
    except ImportError as exc:
        print(
            "Error: TyperApp is not available yet. Move the existing automation workflow "
            "into tinymce_typer.app.typer_app before using this thin entry point.",
            file=sys.stderr,
        )
        return 2

    try:
        app = TyperApp(config)
        result = app.run()
    except KeyboardInterrupt:
        print("\nScript terminated by user", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    if result is None:
        return 0

    if isinstance(result, bool):
        return 0 if result else 1

    success = getattr(result, "success", None)
    if success is None:
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())