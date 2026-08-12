from dataclasses import dataclass
from typing import Any

from tinymce_typer.config.settings import AppConfig
from tinymce_typer.editors.detector import EditorDetector


@dataclass(frozen=True)
class EditorDiagnosticResult:
    name: str
    passed: bool
    message: str
    details: dict[str, str]


class EditorDiagnostic:
    def __init__(self, detector: EditorDetector | None = None):
        self.detector = detector or EditorDetector()

    def run_static(self, config: AppConfig) -> list[EditorDiagnosticResult]:
        return [
            self._check_editor_selectors(config),
            self._check_non_interactive_editor_selection(config),
        ]

    def run_with_driver(self, driver: Any, config: AppConfig) -> list[EditorDiagnosticResult]:
        results = self.run_static(config)

        try:
            detection = self.detector.detect(driver, config.editor)
        except Exception as exc:
            results.append(
                EditorDiagnosticResult(
                    name="editor_detection",
                    passed=False,
                    message=f"Editor detection failed: {exc}",
                    details={},
                )
            )
            return results

        details = {
            f"candidate_{index + 1}": f"{candidate.kind.value} | {candidate.support_level.value} | {candidate.label}"
            for index, candidate in enumerate(detection.candidates)
        }

        if detection.found:
            results.append(
                EditorDiagnosticResult(
                    name="editor_detection",
                    passed=True,
                    message=f"Detected {detection.count} possible editor target(s)",
                    details=details,
                )
            )
        else:
            results.append(
                EditorDiagnosticResult(
                    name="editor_detection",
                    passed=False,
                    message="No editor candidates were detected on the current page",
                    details={},
                )
            )

        return results

    def _check_editor_selectors(self, config: AppConfig) -> EditorDiagnosticResult:
        selectors = {
            "iframe_id": config.editor.iframe_id,
            "editor_id": config.editor.editor_id,
            "wait_selector": config.editor.wait_selector,
        }

        configured = {key: value for key, value in selectors.items() if value}

        if configured:
            return EditorDiagnosticResult(
                name="editor_selectors",
                passed=True,
                message="Editor targeting hints are configured",
                details=configured,
            )

        return EditorDiagnosticResult(
            name="editor_selectors",
            passed=True,
            message="No explicit editor targeting hints configured; automatic detection will be used",
            details={},
        )

    def _check_non_interactive_editor_selection(self, config: AppConfig) -> EditorDiagnosticResult:
        if not config.cli.non_interactive:
            return EditorDiagnosticResult(
                name="non_interactive_editor_selection",
                passed=True,
                message="Interactive editor selection is allowed",
                details={},
            )

        if config.editor.editor_index is not None:
            return EditorDiagnosticResult(
                name="non_interactive_editor_selection",
                passed=True,
                message="Non-interactive mode has an editor index configured",
                details={"editor_index": str(config.editor.editor_index)},
            )

        if config.editor.iframe_id or config.editor.editor_id:
            return EditorDiagnosticResult(
                name="non_interactive_editor_selection",
                passed=True,
                message="Non-interactive mode has explicit editor targeting hints",
                details={
                    "iframe_id": config.editor.iframe_id,
                    "editor_id": config.editor.editor_id,
                },
            )

        return EditorDiagnosticResult(
            name="non_interactive_editor_selection",
            passed=False,
            message="Non-interactive mode may fail if multiple editors are detected; provide --editor-index, --iframe-id, or --editor-id",
            details={},
        )