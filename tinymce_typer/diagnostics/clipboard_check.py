import os
import platform
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class ClipboardDiagnosticResult:
    name: str
    passed: bool
    message: str
    details: dict[str, str]


class ClipboardDiagnostic:
    def run(self) -> list[ClipboardDiagnosticResult]:
        return [
            self._check_pyperclip(),
            self._check_platform_backend(),
        ]

    def _check_pyperclip(self) -> ClipboardDiagnosticResult:
        try:
            import pyperclip
        except ImportError:
            return ClipboardDiagnosticResult(
                name="pyperclip",
                passed=False,
                message="pyperclip is not installed",
                details={},
            )

        try:
            mechanism = pyperclip.determine_clipboard()
        except Exception as exc:
            return ClipboardDiagnosticResult(
                name="pyperclip",
                passed=False,
                message=f"pyperclip is installed but clipboard detection failed: {exc}",
                details={},
            )

        return ClipboardDiagnosticResult(
            name="pyperclip",
            passed=True,
            message="pyperclip is installed",
            details={"mechanism": str(mechanism)},
        )

    def _check_platform_backend(self) -> ClipboardDiagnosticResult:
        system = platform.system().lower()

        if system == "linux":
            return self._check_linux_backend()

        return ClipboardDiagnosticResult(
            name="platform_clipboard_backend",
            passed=True,
            message=f"No extra clipboard utility check required for {platform.system()}",
            details={"platform": platform.system()},
        )

    def _check_linux_backend(self) -> ClipboardDiagnosticResult:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        candidates = ["xclip", "xsel"]

        if session_type == "wayland":
            candidates.insert(0, "wl-copy")

        found = [candidate for candidate in candidates if shutil.which(candidate)]

        if found:
            return ClipboardDiagnosticResult(
                name="linux_clipboard_backend",
                passed=True,
                message=f"Detected Linux clipboard utility: {found[0]}",
                details={
                    "session_type": session_type or "unknown",
                    "utility": found[0],
                },
            )

        return ClipboardDiagnosticResult(
            name="linux_clipboard_backend",
            passed=False,
            message="No Linux clipboard utility detected. Install xclip, xsel, or wl-clipboard.",
            details={
                "session_type": session_type or "unknown",
                "checked": ", ".join(candidates),
            },
        )