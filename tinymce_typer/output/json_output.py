import json
import sys
from typing import TextIO

from tinymce_typer.output.models import RunOutput


class JsonOutputWriter:
    def __init__(self, stream: TextIO | None = None, indent: int | None = 2):
        self.stream = stream or sys.stdout
        self.indent = indent

    def write(self, output: RunOutput) -> None:
        try:
            print(
                json.dumps(
                    output.to_dict(),
                    indent=self.indent,
                    sort_keys=True,
                    default=str,
                ),
                file=self.stream,
            )
        except TypeError as exc:
            fallback = RunOutput.failure(
                message=f"Could not serialize run output: {exc}",
                errors=(str(exc),),
            )
            print(json.dumps(fallback.to_dict(), indent=self.indent, sort_keys=True), file=self.stream)