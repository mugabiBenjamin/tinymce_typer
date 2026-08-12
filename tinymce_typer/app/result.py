from dataclasses import dataclass, field

from tinymce_typer.insertion.base import InsertionResult
from tinymce_typer.output.models import RunOutput
from tinymce_typer.verification.models import VerificationResult


@dataclass(frozen=True)
class AppResult:
    success: bool
    exit_code: int
    message: str
    duration_seconds: float
    insertion: InsertionResult | None = None
    verification: VerificationResult | None = None
    output: RunOutput | None = None
    errors: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        message: str,
        duration_seconds: float,
        insertion: InsertionResult,
        verification: VerificationResult | None,
        output: RunOutput,
        metadata: dict[str, str] | None = None,
    ) -> "AppResult":
        success = insertion.success

        if verification is not None:
            success = success and verification.passed

        return cls(
            success=success,
            exit_code=0 if success else 1,
            message=message,
            duration_seconds=duration_seconds,
            insertion=insertion,
            verification=verification,
            output=output,
            metadata=metadata or {},
        )

    @classmethod
    def fail(
        cls,
        message: str,
        exit_code: int = 1,
        duration_seconds: float = 0.0,
        errors: tuple[str, ...] = (),
        output: RunOutput | None = None,
        metadata: dict[str, str] | None = None,
    ) -> "AppResult":
        return cls(
            success=False,
            exit_code=exit_code,
            message=message,
            duration_seconds=duration_seconds,
            output=output,
            errors=errors or (message,),
            metadata=metadata or {},
        )