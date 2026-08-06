import hashlib
from pathlib import Path


class ContentHasher:
    def hash_text(self, text: str) -> str:
        digest = hashlib.sha256()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest()

    def hash_bytes(self, data: bytes) -> str:
        digest = hashlib.sha256()
        digest.update(data)
        return digest.hexdigest()

    def hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()

        try:
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            from tinymce_typer.exceptions import ContentLoadError

            raise ContentLoadError(f"Could not hash file '{path}': {exc}") from exc

        return digest.hexdigest()

    def hash_parts(self, parts: list[str]) -> str:
        digest = hashlib.sha256()

        for part in parts:
            digest.update(part.encode("utf-8"))
            digest.update(b"\0")

        return digest.hexdigest()