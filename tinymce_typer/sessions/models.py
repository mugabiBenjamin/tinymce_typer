from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class ResumeDecision(StrEnum):
    ALLOW = "allow"
    REFUSE = "refuse"
    WARN = "warn"


@dataclass(frozen=True)
class SessionMetadata:
    url: str
    source_file: str
    content_hash: str
    insertion_strategy: str
    editor_kind: str
    editor_identifier: str
    app_version: str = "0.1.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "source_file": self.source_file,
            "content_hash": self.content_hash,
            "insertion_strategy": self.insertion_strategy,
            "editor_kind": self.editor_kind,
            "editor_identifier": self.editor_identifier,
            "app_version": self.app_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetadata":
        return cls(
            url=str(data.get("url", "")),
            source_file=str(data.get("source_file", "")),
            content_hash=str(data.get("content_hash", "")),
            insertion_strategy=str(data.get("insertion_strategy", "")),
            editor_kind=str(data.get("editor_kind", "")),
            editor_identifier=str(data.get("editor_identifier", "")),
            app_version=str(data.get("app_version", "0.1.0")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass(frozen=True)
class SessionProgress:
    offset: int = 0
    total: int = 0
    inserted: int = 0
    current_file: str = ""
    current_file_offset: int = 0
    completed: bool = False
    last_strategy: str = ""

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 100.0
        return min(100.0, max(0.0, (self.offset / self.total) * 100))

    def to_dict(self) -> dict[str, Any]:
        return {
            "offset": self.offset,
            "total": self.total,
            "inserted": self.inserted,
            "current_file": self.current_file,
            "current_file_offset": self.current_file_offset,
            "completed": self.completed,
            "last_strategy": self.last_strategy,
            "percent": self.percent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionProgress":
        return cls(
            offset=int(data.get("offset", 0)),
            total=int(data.get("total", 0)),
            inserted=int(data.get("inserted", 0)),
            current_file=str(data.get("current_file", "")),
            current_file_offset=int(data.get("current_file_offset", 0)),
            completed=bool(data.get("completed", False)),
            last_strategy=str(data.get("last_strategy", "")),
        )


@dataclass(frozen=True)
class SessionState:
    metadata: SessionMetadata
    progress: SessionProgress
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "metadata": self.metadata.to_dict(),
            "progress": self.progress.to_dict(),
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        if not isinstance(data, dict):
            from tinymce_typer.exceptions import SessionError

            raise SessionError("Session payload must be a JSON object.")

        metadata = data.get("metadata", {})
        progress = data.get("progress", {})
        extra = data.get("extra", {})

        if not isinstance(metadata, dict):
            from tinymce_typer.exceptions import SessionError

            raise SessionError("Session metadata must be a JSON object.")

        if not isinstance(progress, dict):
            from tinymce_typer.exceptions import SessionError

            raise SessionError("Session progress must be a JSON object.")

        if not isinstance(extra, dict):
            extra = {}

        return cls(
            metadata=SessionMetadata.from_dict(metadata),
            progress=SessionProgress.from_dict(progress),
            extra=extra,
        )


@dataclass(frozen=True)
class ResumeValidationResult:
    decision: ResumeDecision
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.decision in {ResumeDecision.ALLOW, ResumeDecision.WARN}