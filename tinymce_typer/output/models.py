from dataclasses import asdict, dataclass, field
from typing import Any

from tinymce_typer.insertion.base import InsertionResult
from tinymce_typer.verification.models import VerificationResult


@dataclass(frozen=True)
class RunOutput:
    success: bool
    duration_seconds: float
    editor_type: str = ""
    editor_identifier: str = ""
    strategy_used: str = ""
    content_length: int = 0
    inserted_characters: int = 0
    final_offset: int = 0
    message: str = ""
    verification: VerificationResult | None = None
    session_file: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_insertion_result(
        cls,
        result: InsertionResult,
        duration_seconds: float,
        editor_type: str,
        editor_identifier: str,
        content_length: int,
        verification: VerificationResult | None = None,
        session_file: str = "",
        artifacts: dict[str, str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> "RunOutput":
        success = result.success

        if verification is not None:
            success = success and verification.passed

        return cls(
            success=success,
            duration_seconds=duration_seconds,
            editor_type=editor_type,
            editor_identifier=editor_identifier,
            strategy_used=result.strategy_name,
            content_length=content_length,
            inserted_characters=result.inserted_characters,
            final_offset=result.final_offset,
            message=result.message,
            verification=verification,
            session_file=session_file,
            artifacts=artifacts or {},
            errors=(),
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        message: str,
        duration_seconds: float = 0.0,
        errors: tuple[str, ...] = (),
        metadata: dict[str, str] | None = None,
    ) -> "RunOutput":
        return cls(
            success=False,
            duration_seconds=duration_seconds,
            message=message,
            errors=errors or (message,),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        if self.verification is not None:
            data["verification"] = asdict(self.verification)
        else:
            data["verification"] = None

        data["duration_seconds"] = round(self.duration_seconds, 4)

        return data