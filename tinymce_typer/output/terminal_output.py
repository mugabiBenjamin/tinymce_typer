import sys
from typing import TextIO

from tinymce_typer.output.models import RunOutput


class TerminalOutputWriter:
    def __init__(self, stream: TextIO | None = None):
        self.stream = stream or sys.stdout

    def write(self, output: RunOutput) -> None:
        status = "SUCCESS" if output.success else "FAILED"
        print(f"{status}: {output.message}", file=self.stream)

        if output.editor_type:
            print(f"Editor: {output.editor_type}", file=self.stream)

        if output.editor_identifier:
            print(f"Editor identifier: {output.editor_identifier}", file=self.stream)

        if output.strategy_used:
            print(f"Strategy: {output.strategy_used}", file=self.stream)

        if output.content_length:
            print(f"Content length: {output.content_length}", file=self.stream)

        if output.inserted_characters:
            print(f"Inserted characters: {output.inserted_characters}", file=self.stream)

        print(f"Duration: {output.duration_seconds:.2f}s", file=self.stream)

        if output.session_file:
            print(f"Session file: {output.session_file}", file=self.stream)

        if output.verification is not None:
            self._write_verification(output)

        if output.artifacts:
            print("Artifacts:", file=self.stream)
            for name, path in output.artifacts.items():
                if path:
                    print(f"  - {name}: {path}", file=self.stream)

        if output.errors:
            print("Errors:", file=self.stream)
            for error in output.errors:
                print(f"  - {error}", file=self.stream)

    def _write_verification(self, output: RunOutput) -> None:
        verification = output.verification

        if verification is None:
            return

        verification_status = "passed" if verification.passed else "failed"
        print(f"Verification: {verification_status}", file=self.stream)
        print(f"Verification mode: {verification.mode.value}", file=self.stream)
        print(f"Similarity: {verification.similarity:.4f}", file=self.stream)
        print(f"Threshold: {verification.threshold:.4f}", file=self.stream)

        if verification.mismatch is not None:
            mismatch = verification.mismatch
            print(f"First mismatch index: {mismatch.index}", file=self.stream)
            print(f"Expected context: {mismatch.expected_context}", file=self.stream)
            print(f"Actual context: {mismatch.actual_context}", file=self.stream)