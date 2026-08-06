from pathlib import Path

from tinymce_typer.config.settings import ContentConfig
from tinymce_typer.content.hashing import ContentHasher
from tinymce_typer.content.models import ContentBoundary, ContentDocument, ContentFile
from tinymce_typer.exceptions import ContentLoadError


class ContentLoader:
    def __init__(self, hasher: ContentHasher | None = None):
        self.hasher = hasher or ContentHasher()

    def load_from_config(self, config: ContentConfig) -> ContentDocument:
        paths = self._resolve_paths(config)
        return self.load_many(
            paths=paths,
            separator=config.file_separator,
            include_file_headings=config.include_file_headings,
        )

    def load_one(self, path: str | Path) -> ContentDocument:
        resolved = self._resolve_path(path)
        content_file = self._load_file(resolved)

        boundary = ContentBoundary(
            file_path=content_file.path,
            display_name=content_file.display_name,
            start_offset=0,
            end_offset=content_file.character_count,
            size_bytes=content_file.size_bytes,
            character_count=content_file.character_count,
            content_hash=content_file.content_hash,
        )

        return ContentDocument(
            text=content_file.text,
            files=(content_file,),
            boundaries=(boundary,),
            content_hash=content_file.content_hash,
            total_size_bytes=content_file.size_bytes,
            total_character_count=content_file.character_count,
            separator="",
        )

    def load_many(
        self,
        paths: list[str | Path],
        separator: str = "\n\n",
        include_file_headings: bool = False,
    ) -> ContentDocument:
        if not paths:
            raise ContentLoadError("At least one content file is required.")

        loaded_files = [self._load_file(self._resolve_path(path)) for path in paths]
        parts: list[str] = []
        boundaries: list[ContentBoundary] = []
        current_offset = 0

        for index, content_file in enumerate(loaded_files):
            if index > 0:
                parts.append(separator)
                current_offset += len(separator)

            section_text = self._build_section_text(content_file, include_file_headings)
            start_offset = current_offset
            end_offset = start_offset + len(section_text)

            parts.append(section_text)

            boundaries.append(
                ContentBoundary(
                    file_path=content_file.path,
                    display_name=content_file.display_name,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    size_bytes=content_file.size_bytes,
                    character_count=len(section_text),
                    content_hash=content_file.content_hash,
                )
            )

            current_offset = end_offset

        merged_text = "".join(parts)
        merged_hash = self.hasher.hash_parts(
            [
                separator,
                "include_file_headings=true" if include_file_headings else "include_file_headings=false",
                *[content_file.content_hash for content_file in loaded_files],
                merged_text,
            ]
        )

        return ContentDocument(
            text=merged_text,
            files=tuple(loaded_files),
            boundaries=tuple(boundaries),
            content_hash=merged_hash,
            total_size_bytes=sum(content_file.size_bytes for content_file in loaded_files),
            total_character_count=len(merged_text),
            separator=separator,
        )

    def _resolve_paths(self, config: ContentConfig) -> list[Path]:
        if config.files:
            return [self._resolve_path(path) for path in config.files]

        return [self._resolve_path(config.file)]

    def _resolve_path(self, path: str | Path) -> Path:
        if path is None:
            raise ContentLoadError("Content file path cannot be empty.")

        resolved = Path(path).expanduser()

        if not str(resolved).strip():
            raise ContentLoadError("Content file path cannot be empty.")

        if not resolved.exists():
            raise ContentLoadError(f"Content file does not exist: {resolved}")

        if not resolved.is_file():
            raise ContentLoadError(f"Content path is not a file: {resolved}")

        return resolved

    def _load_file(self, path: Path) -> ContentFile:
        try:
            text = path.read_text(encoding="utf-8")
            size_bytes = path.stat().st_size
        except UnicodeDecodeError as exc:
            raise ContentLoadError(f"Content file is not valid UTF-8: {path}") from exc
        except OSError as exc:
            raise ContentLoadError(f"Could not read content file '{path}': {exc}") from exc

        content_hash = self.hasher.hash_text(text)

        return ContentFile(
            path=path,
            display_name=path.name,
            text=text,
            size_bytes=size_bytes,
            character_count=len(text),
            content_hash=content_hash,
        )

    def _build_section_text(self, content_file: ContentFile, include_file_headings: bool) -> str:
        if not include_file_headings:
            return content_file.text

        heading = f"# {content_file.display_name}"
        return f"{heading}\n\n{content_file.text}"