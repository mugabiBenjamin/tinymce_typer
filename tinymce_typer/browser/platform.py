import os
import platform
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class BrowserAvailability:
    name: str
    available: bool
    executable: str
    candidates_checked: tuple[str, ...]


@dataclass(frozen=True)
class ClipboardBackend:
    available: bool
    backend: str
    session_type: str
    message: str
    candidates_checked: tuple[str, ...]


@dataclass(frozen=True)
class PortCheck:
    host: str
    port: int
    reachable: bool
    message: str


@dataclass(frozen=True)
class ContainerInfo:
    detected: bool
    runtime: str
    message: str


@dataclass(frozen=True)
class HeadlessHint:
    recommended: bool
    message: str
    details: dict[str, str]


@dataclass(frozen=True)
class PlatformReport:
    os_name: str
    os_release: str
    os_version: str
    system: str
    architecture: str
    machine: str
    processor: str
    python_version: str
    display_server: str
    is_linux: bool
    is_windows: bool
    is_macos: bool
    container: ContainerInfo
    clipboard: ClipboardBackend
    browsers: tuple[BrowserAvailability, ...]
    headless_hint: HeadlessHint

    def browser(self, name: str) -> BrowserAvailability | None:
        normalized = name.strip().lower()

        for browser in self.browsers:
            if browser.name == normalized:
                return browser

        return None


class PlatformInspector:
    def inspect(self) -> PlatformReport:
        system_name = platform.system()
        normalized_system = system_name.lower()

        is_linux = normalized_system == "linux"
        is_windows = normalized_system == "windows"
        is_macos = normalized_system == "darwin"

        display_server = self.display_server()
        container = self.container_info()

        return PlatformReport(
            os_name=system_name,
            os_release=platform.release(),
            os_version=platform.version(),
            system=normalized_system,
            architecture=platform.architecture()[0],
            machine=platform.machine(),
            processor=platform.processor(),
            python_version=platform.python_version(),
            display_server=display_server,
            is_linux=is_linux,
            is_windows=is_windows,
            is_macos=is_macos,
            container=container,
            clipboard=self.clipboard_backend(),
            browsers=(
                self.browser_availability("chrome"),
                self.browser_availability("firefox"),
                self.browser_availability("edge"),
            ),
            headless_hint=self.headless_hint(
                is_linux=is_linux,
                is_windows=is_windows,
                is_macos=is_macos,
                display_server=display_server,
                container_detected=container.detected,
            ),
        )

    def browser_availability(self, browser: str) -> BrowserAvailability:
        candidates = self.browser_candidates(browser)
        executable = ""

        for candidate in candidates:
            resolved = shutil.which(candidate)

            if resolved:
                executable = resolved
                break

        return BrowserAvailability(
            name=browser,
            available=bool(executable),
            executable=executable,
            candidates_checked=candidates,
        )

    def browser_candidates(self, browser: str) -> tuple[str, ...]:
        system_name = platform.system().lower()
        normalized = browser.strip().lower()

        if normalized == "chrome":
            if system_name == "windows":
                return (
                    "chrome.exe",
                    "chrome",
                    "google-chrome",
                    "google-chrome-stable",
                )

            if system_name == "darwin":
                return (
                    "google-chrome",
                    "chrome",
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                )

            return (
                "google-chrome",
                "google-chrome-stable",
                "chromium",
                "chromium-browser",
            )

        if normalized == "firefox":
            if system_name == "windows":
                return (
                    "firefox.exe",
                    "firefox",
                )

            if system_name == "darwin":
                return (
                    "firefox",
                    "/Applications/Firefox.app/Contents/MacOS/firefox",
                )

            return (
                "firefox",
                "firefox-esr",
            )

        if normalized == "edge":
            if system_name == "windows":
                return (
                    "msedge.exe",
                    "msedge",
                    "microsoft-edge",
                )

            if system_name == "darwin":
                return (
                    "microsoft-edge",
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                )

            return (
                "microsoft-edge",
                "microsoft-edge-stable",
                "msedge",
            )

        return ()

    def clipboard_backend(self) -> ClipboardBackend:
        system_name = platform.system().lower()
        session_type = self.display_server()

        if system_name == "linux":
            return self._linux_clipboard_backend(session_type)

        if system_name == "darwin":
            return ClipboardBackend(
                available=shutil.which("pbcopy") is not None and shutil.which("pbpaste") is not None,
                backend="pbcopy/pbpaste",
                session_type=session_type,
                message="macOS clipboard uses pbcopy/pbpaste.",
                candidates_checked=("pbcopy", "pbpaste"),
            )

        if system_name == "windows":
            return ClipboardBackend(
                available=True,
                backend="windows-clipboard",
                session_type=session_type,
                message="Windows clipboard is available through the OS clipboard APIs.",
                candidates_checked=(),
            )

        return ClipboardBackend(
            available=False,
            backend="unknown",
            session_type=session_type,
            message=f"No clipboard backend detection is implemented for {platform.system()}.",
            candidates_checked=(),
        )

    def _linux_clipboard_backend(self, session_type: str) -> ClipboardBackend:
        candidates = ["xclip", "xsel"]

        if session_type == "wayland":
            candidates = ["wl-copy", "wl-paste", *candidates]

        found = [candidate for candidate in candidates if shutil.which(candidate)]

        if found:
            return ClipboardBackend(
                available=True,
                backend=found[0],
                session_type=session_type or "unknown",
                message=f"Detected Linux clipboard utility: {found[0]}",
                candidates_checked=tuple(candidates),
            )

        return ClipboardBackend(
            available=False,
            backend="",
            session_type=session_type or "unknown",
            message="No Linux clipboard utility detected. Install xclip, xsel, or wl-clipboard.",
            candidates_checked=tuple(candidates),
        )

    def display_server(self) -> str:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()

        if session_type:
            return session_type

        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"

        if os.environ.get("DISPLAY"):
            return "x11"

        return "none"

    def container_info(self) -> ContainerInfo:
        if Path("/.dockerenv").exists():
            return ContainerInfo(
                detected=True,
                runtime="docker",
                message="Docker container detected through /.dockerenv.",
            )

        try:
            cgroup_text = Path("/proc/1/cgroup").read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            cgroup_text = ""

        indicators = {
            "docker": "docker",
            "containerd": "containerd",
            "kubepods": "kubernetes",
            "podman": "podman",
        }

        for marker, runtime in indicators.items():
            if marker in cgroup_text:
                return ContainerInfo(
                    detected=True,
                    runtime=runtime,
                    message=f"Container runtime hint detected: {runtime}.",
                )

        return ContainerInfo(
            detected=False,
            runtime="",
            message="No container runtime detected.",
        )

    def headless_hint(
        self,
        is_linux: bool,
        is_windows: bool,
        is_macos: bool,
        display_server: str,
        container_detected: bool,
    ) -> HeadlessHint:
        details = {
            "display_server": display_server,
            "container_detected": str(container_detected),
        }

        if container_detected:
            return HeadlessHint(
                recommended=True,
                message="Headless mode is recommended in containers and server environments.",
                details=details,
            )

        if is_linux and display_server == "none":
            return HeadlessHint(
                recommended=True,
                message="No Linux display server was detected. Use --headless or provide X11/Wayland display access.",
                details=details,
            )

        if is_linux:
            return HeadlessHint(
                recommended=False,
                message="Linux display server detected. Headed or headless mode can both work.",
                details=details,
            )

        if is_windows or is_macos:
            return HeadlessHint(
                recommended=False,
                message="Visible browser mode is usually best for first-time setup and manual review.",
                details=details,
            )

        return HeadlessHint(
            recommended=False,
            message="No specific headless recommendation is available for this platform.",
            details=details,
        )

    def check_port(self, port: int, host: str = "127.0.0.1", timeout_seconds: float = 1.0) -> PortCheck:
        if port <= 0 or port > 65535:
            return PortCheck(
                host=host,
                port=port,
                reachable=False,
                message="Port is outside the valid range 1-65535.",
            )

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout_seconds)
                reachable = sock.connect_ex((host, port)) == 0
        except OSError as exc:
            return PortCheck(
                host=host,
                port=port,
                reachable=False,
                message=f"Could not check port: {exc}",
            )

        return PortCheck(
            host=host,
            port=port,
            reachable=reachable,
            message=f"Port {host}:{port} is reachable." if reachable else f"Port {host}:{port} is not reachable.",
        )

    def check_remote_webdriver_url(self, url: str, timeout_seconds: float = 1.0) -> PortCheck:
        stripped = url.strip()

        if not stripped:
            return PortCheck(
                host="",
                port=0,
                reachable=False,
                message="Remote WebDriver URL is empty.",
            )

        parsed = urlparse(stripped)

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return PortCheck(
                host="",
                port=0,
                reachable=False,
                message="Remote WebDriver URL is not a valid http(s) URL.",
            )

        port = parsed.port

        if port is None:
            port = 443 if parsed.scheme == "https" else 80

        return self.check_port(
            host=parsed.hostname,
            port=port,
            timeout_seconds=timeout_seconds,
        )