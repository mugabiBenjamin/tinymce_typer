import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinymce_typer.editors.base import EditorAdapter
from tinymce_typer.editors.models import EditorCandidate
from tinymce_typer.exceptions import VerificationError
from tinymce_typer.verification.models import VerificationArtifact, VerificationResult


class VerificationReporter:
    def __init__(self, output_dir: str | Path = "diagnostics/verification"):
        self.output_dir = Path(output_dir).expanduser()

    def write_failure_artifacts(
        self,
        result: VerificationResult,
        driver: Any,
        adapter: EditorAdapter,
        candidate: EditorCandidate,
        include_screenshot: bool = False,
    ) -> VerificationResult:
        if result.passed:
            return result

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise VerificationError(f"Could not create verification artifact directory: {exc}") from exc

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base_name = f"verification_failure_{timestamp}"

        actual_content_path = self._write_actual_content(base_name, driver, adapter, candidate)
        report_path = self._write_report(base_name, result, actual_content_path)
        screenshot_path = ""

        if include_screenshot:
            screenshot_path = self._write_screenshot(base_name, driver)

        return VerificationResult(
            passed=result.passed,
            mode=result.mode,
            similarity=result.similarity,
            threshold=result.threshold,
            expected_length=result.expected_length,
            actual_length=result.actual_length,
            editor_kind=result.editor_kind,
            editor_identifier=result.editor_identifier,
            current_url=result.current_url,
            message=result.message,
            mismatch=result.mismatch,
            artifacts=VerificationArtifact(
                report_path=str(report_path),
                screenshot_path=str(screenshot_path),
                actual_content_path=str(actual_content_path),
            ),
            metadata=result.metadata,
        )

    def _write_actual_content(
        self,
        base_name: str,
        driver: Any,
        adapter: EditorAdapter,
        candidate: EditorCandidate,
    ) -> Path:
        path = self.output_dir / f"{base_name}_actual.html"

        try:
            actual_html = adapter.read_html(driver, candidate)
            path.write_text(actual_html, encoding="utf-8")
            return path
        except Exception as exc:
            raise VerificationError(f"Could not write actual editor content artifact: {exc}") from exc

    def _write_report(
        self,
        base_name: str,
        result: VerificationResult,
        actual_content_path: Path,
    ) -> Path:
        path = self.output_dir / f"{base_name}_report.json"

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": asdict(result),
            "actual_content_path": str(actual_content_path),
        }

        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            return path
        except OSError as exc:
            raise VerificationError(f"Could not write verification report: {exc}") from exc

    def _write_screenshot(self, base_name: str, driver: Any) -> Path:
        path = self.output_dir / f"{base_name}_screenshot.png"

        try:
            ok = driver.save_screenshot(str(path))
        except Exception as exc:
            raise VerificationError(f"Could not capture verification screenshot: {exc}") from exc

        if not ok:
            raise VerificationError("Browser did not save verification screenshot.")

        return path