from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContentFile:
    path: Path
    display_name: str
    text: str
    size_bytes: int
    character_count: int
    content_hash: str


@dataclass(frozen=True)
class ContentBoundary:
    file_path: Path
    display_name: str
    start_offset: int
    end_offset: int
    size_bytes: int
    character_count: int
    content_hash: str

    @property
    def length(self) -> int:
        return self.end_offset - self.start_offset

    def contains_offset(self, offset: int) -> bool:
        return self.start_offset <= offset < self.end_offset


@dataclass(frozen=True)
class ContentDocument:
    text: str
    files: tuple[ContentFile, ...]
    boundaries: tuple[ContentBoundary, ...]
    content_hash: str
    total_size_bytes: int
    total_character_count: int
    separator: str

    @property
    def is_multi_file(self) -> bool:
        return len(self.files) > 1

    def file_at_offset(self, offset: int) -> ContentBoundary | None:
        for boundary in self.boundaries:
            if boundary.contains_offset(offset):
                return boundary
        return None

    def progress_context(self, offset: int) -> dict[str, str | int] | None:
        boundary = self.file_at_offset(offset)

        if boundary is None:
            return None

        return {
            "file": boundary.display_name,
            "file_path": str(boundary.file_path),
            "file_start_offset": boundary.start_offset,
            "file_end_offset": boundary.end_offset,
            "offset_in_file": offset - boundary.start_offset,
            "file_character_count": boundary.character_count,
        }


@dataclass(frozen=True)
class FormattedContent:
    raw_text: str
    html: str
    plain_text: str
    mode: str
    content_hash: str