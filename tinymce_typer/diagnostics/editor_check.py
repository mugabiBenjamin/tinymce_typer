from dataclasses import dataclass
from typing import Any

from tinymce_typer.config.settings import AppConfig


@dataclass(frozen=True)
class EditorDiagnosticResult:
    name: str
    passed: bool
    message: str
    details: dict[str, str]


class EditorDiagnostic:
    def run_static(self, config: AppConfig) -> list[EditorDiagnosticResult]:
        results = [
            self._check_editor_selectors(config),
            self._check_non_interactive_editor_selection(config),
        ]

        return results

    def run_with_driver(self, driver: Any, config: AppConfig) -> list[EditorDiagnosticResult]:
        results = self.run_static(config)

        try:
            detected = self._detect_editor_candidates(driver)
            results.append(detected)
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

    def _detect_editor_candidates(self, driver: Any) -> EditorDiagnosticResult:
        selectors = {
            "tinymce_iframes": "iframe[id$='_ifr'], iframe#tinymce_ifr, div.mce-edit-area iframe, div.tox-edit-area__iframe",
            "ckeditor_frames": "iframe.cke_wysiwyg_frame",
            "quill_editors": ".ql-editor",
            "contenteditable": "[contenteditable='true']",
        }

        counts: dict[str, str] = {}

        for name, selector in selectors.items():
            elements = driver.find_elements("css selector", selector)
            counts[name] = str(len(elements))

        total = sum(int(value) for value in counts.values())

        if total > 0:
            return EditorDiagnosticResult(
                name="editor_detection",
                passed=True,
                message=f"Detected {total} possible editor target(s)",
                details=counts,
            )

        return EditorDiagnosticResult(
            name="editor_detection",
            passed=False,
            message="No editor candidates were detected on the current page",
            details=counts,
        )