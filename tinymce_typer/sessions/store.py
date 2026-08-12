import json
from pathlib import Path
from typing import Any

from tinymce_typer.exceptions import SessionError
from tinymce_typer.sessions.crypto import SessionCrypto, SessionCryptoError
from tinymce_typer.sessions.models import SessionState


class SessionStore:
    def __init__(
        self,
        path: str | Path,
        crypto: SessionCrypto | None = None,
        encrypted: bool = False,
        password: str = "",
    ):
        self.path = Path(path).expanduser()
        self.crypto = crypto or SessionCrypto()
        self.encrypted = encrypted
        self.password = password

    def exists(self) -> bool:
        return self.path.exists() and self.path.is_file()

    def delete(self) -> None:
        if not self.path.exists():
            return

        try:
            self.path.unlink()
        except OSError as exc:
            raise SessionError(f"Could not delete session file '{self.path}': {exc}") from exc

    def load(self) -> SessionState | None:
        if not self.exists():
            return None

        try:
            raw_text = self.path.read_text(encoding="utf-8")
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise SessionError(f"Session file is not valid JSON: {self.path}") from exc
        except OSError as exc:
            raise SessionError(f"Could not read session file '{self.path}': {exc}") from exc

        if not isinstance(payload, dict):
            raise SessionError("Session file must contain a JSON object.")

        if payload.get("encrypted") is True:
            return self._load_encrypted(payload)

        return SessionState.from_dict(payload)

    def save(self, state: SessionState) -> None:
        payload = state.to_dict()

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SessionError(f"Could not create session directory '{self.path.parent}': {exc}") from exc

        if self.encrypted:
            payload = self._encrypt_payload(payload)

        try:
            temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            temp_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            temp_path.replace(self.path)
        except OSError as exc:
            raise SessionError(f"Could not write session file '{self.path}': {exc}") from exc

    def _load_encrypted(self, payload: dict[str, Any]) -> SessionState:
        try:
            decrypted = self.crypto.decrypt_json_bytes(payload, self.password)
            data = json.loads(decrypted.decode("utf-8"))
        except SessionCryptoError as exc:
            raise SessionError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise SessionError("Decrypted session data is not valid JSON.") from exc
        except UnicodeDecodeError as exc:
            raise SessionError("Decrypted session data is not valid UTF-8.") from exc

        return SessionState.from_dict(data)

    def _encrypt_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            raw = json.dumps(payload, sort_keys=True).encode("utf-8")
            return self.crypto.encrypt_json_bytes(raw, self.password)
        except SessionCryptoError as exc:
            raise SessionError(str(exc)) from exc