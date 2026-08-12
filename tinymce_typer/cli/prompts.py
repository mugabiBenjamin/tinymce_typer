from collections.abc import Sequence


class PromptError(Exception):
    pass


class PromptManager:
    def __init__(self, non_interactive: bool = False, assume_yes: bool = False):
        self.non_interactive = non_interactive
        self.assume_yes = assume_yes

    def confirm(self, message: str, default: bool = False) -> bool:
        if self.assume_yes:
            return True

        if self.non_interactive:
            return default

        suffix = " [Y/n]: " if default else " [y/N]: "

        try:
            answer = input(message + suffix).strip().lower()
        except EOFError as exc:
            if default is not None:
                return default
            raise PromptError("Input is unavailable for confirmation prompt.") from exc

        if not answer:
            return default

        if answer in {"y", "yes"}:
            return True

        if answer in {"n", "no"}:
            return False

        raise PromptError(f"Invalid confirmation response: {answer}")

    def wait_for_ready(self, message: str) -> None:
        if self.non_interactive:
            return

        try:
            input(message)
        except EOFError as exc:
            raise PromptError("Input is unavailable while waiting for page readiness.") from exc

    def choose_index(
        self,
        message: str,
        options: Sequence[str],
        configured_index: int | None = None,
        zero_based: bool = False,
    ) -> int:
        if not options:
            raise PromptError("No options are available for selection.")

        if configured_index is not None:
            index = configured_index if zero_based else configured_index - 1
            if 0 <= index < len(options):
                return index
            raise PromptError(
                f"Configured index {configured_index} is outside the valid range 1-{len(options)}."
            )

        if self.non_interactive:
            if len(options) == 1:
                return 0
            raise PromptError(
                "Multiple options require --editor-index when running in non-interactive mode."
            )

        print(message)
        for index, option in enumerate(options, start=1):
            print(f"{index}. {option}")

        try:
            raw_value = input("Enter option number: ").strip()
            selected = int(raw_value) - 1
        except EOFError as exc:
            raise PromptError("Input is unavailable for selection prompt.") from exc
        except ValueError as exc:
            raise PromptError("Selection must be a number.") from exc

        if not 0 <= selected < len(options):
            raise PromptError(f"Selection is outside the valid range 1-{len(options)}.")

        return selected

    def ask_resume(self, has_saved_session: bool, resume: bool, no_resume: bool) -> bool:
        if not has_saved_session:
            return False

        if resume and no_resume:
            raise PromptError("Use either --resume or --no-resume, not both.")

        if resume:
            return True

        if no_resume:
            return False

        return self.confirm("Resume from saved progress?", default=False)

    def confirm_navigation(self, current_url: str, target_url: str, force_navigation: bool) -> bool:
        if force_navigation:
            return True

        if current_url == target_url:
            return False

        return self.confirm(
            f"Current page differs from target URL.\nCurrent: {current_url}\nTarget: {target_url}\nNavigate to target URL?",
            default=False,
        )

    def confirm_resume_warnings(self, warnings: Sequence[str]) -> bool:
        if not warnings:
            return True

        if self.assume_yes:
            return True

        if self.non_interactive:
            return False

        print("Resume has warnings:")
        for warning in warnings:
            print(f"- {warning}")

        return self.confirm("Resume anyway?", default=False)