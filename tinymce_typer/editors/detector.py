from collections.abc import Sequence
from typing import Any

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from tinymce_typer.config.settings import EditorConfig
from tinymce_typer.editors.base import EditorAdapter
from tinymce_typer.editors.ckeditor import CKEditorAdapter
from tinymce_typer.editors.contenteditable import ContentEditableAdapter
from tinymce_typer.editors.models import EditorCandidate, EditorDetectionResult, EditorKind, EditorSupportLevel
from tinymce_typer.editors.quill import QuillAdapter
from tinymce_typer.editors.tinymce import TinyMCEAdapter
from tinymce_typer.exceptions import EditorNotFoundError, MultipleEditorsError
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class EditorDetector:
    def __init__(self, adapters: Sequence[EditorAdapter] | None = None):
        self.adapters = tuple(
            adapters
            if adapters is not None
            else (
                TinyMCEAdapter(),
                CKEditorAdapter(),
                QuillAdapter(),
                ContentEditableAdapter(),
            )
        )

    def detect(self, driver: Any, config: EditorConfig) -> EditorDetectionResult:
        candidates: list[EditorCandidate] = []

        explicit = self._detect_explicit(driver, config)
        if explicit is not None:
            return EditorDetectionResult(candidates=(explicit,))

        for adapter in self.adapters:
            try:
                adapter_candidates = adapter.detect(driver)
                candidates.extend(adapter_candidates)
            except WebDriverException as exc:
                logger.debug("Editor adapter failed during detection: %s | %s", adapter.kind, exc)
            except Exception as exc:
                logger.debug("Editor adapter raised unexpected detection error: %s | %s", adapter.kind, exc)

        ranked = self._rank(candidates)

        return EditorDetectionResult(candidates=tuple(ranked))

    def select(self, result: EditorDetectionResult, config: EditorConfig) -> EditorCandidate:
        if not result.found:
            raise EditorNotFoundError("No supported rich text editor was detected.")

        if config.editor_index is not None:
            index = config.editor_index - 1

            if not 0 <= index < result.count:
                raise MultipleEditorsError(
                    f"Configured editor index {config.editor_index} is outside valid range 1-{result.count}."
                )

            return result.candidates[index]

        if result.count == 1:
            return result.candidates[0]

        if config.detect_multiple:
            raise MultipleEditorsError(
                "Multiple editors were detected. Provide --editor-index to select one in non-interactive mode."
            )

        return result.candidates[0]

    def find_and_focus(self, driver: Any, config: EditorConfig) -> EditorCandidate:
        result = self.detect(driver, config)
        candidate = self.select(result, config)
        adapter = self.adapter_for(candidate)
        adapter.focus(driver, candidate)
        return candidate

    def adapter_for(self, candidate: EditorCandidate) -> EditorAdapter:
        for adapter in self.adapters:
            if adapter.kind == candidate.kind:
                return adapter

        raise EditorNotFoundError(f"No adapter registered for editor type: {candidate.kind}")

    def _detect_explicit(self, driver: Any, config: EditorConfig) -> EditorCandidate | None:
        driver.switch_to.default_content()

        if config.iframe_id:
            return self._candidate_from_iframe_id(driver, config.iframe_id)

        if config.editor_id:
            return self._candidate_from_editor_id(driver, config.editor_id)

        return None

    def _candidate_from_iframe_id(self, driver: Any, iframe_id: str) -> EditorCandidate:
        try:
            frame = driver.find_element(By.ID, iframe_id)
            driver.switch_to.frame(frame)
            element = driver.find_element(By.CSS_SELECTOR, "body")
            driver.switch_to.default_content()
        except WebDriverException as exc:
            driver.switch_to.default_content()
            raise EditorNotFoundError(f"Could not locate editor iframe with ID '{iframe_id}': {exc}") from exc

        kind = self._infer_frame_kind(iframe_id)

        return EditorCandidate(
            kind=kind,
            support_level=self._support_level_for(kind),
            element=element,
            frame_element=frame,
            selector=f"#{iframe_id}",
            label=f"{kind.value} iframe #{iframe_id}",
            index=0,
            confidence=0.98,
            metadata={
                "explicit": "true",
                "iframe_id": iframe_id,
            },
        )

    def _candidate_from_editor_id(self, driver: Any, editor_id: str) -> EditorCandidate:
        try:
            element = driver.find_element(By.ID, editor_id)
        except WebDriverException as exc:
            raise EditorNotFoundError(f"Could not locate editor element with ID '{editor_id}': {exc}") from exc

        kind = self._infer_element_kind(element)

        return EditorCandidate(
            kind=kind,
            support_level=self._support_level_for(kind),
            element=element,
            frame_element=None,
            selector=f"#{editor_id}",
            label=f"{kind.value} element #{editor_id}",
            index=0,
            confidence=0.90,
            metadata={
                "explicit": "true",
                "editor_id": editor_id,
                "class": self._safe_attr(element, "class"),
            },
        )

    def _rank(self, candidates: list[EditorCandidate]) -> list[EditorCandidate]:
        priority = {
            EditorKind.TINYMCE: 0,
            EditorKind.CKEDITOR: 1,
            EditorKind.QUILL: 2,
            EditorKind.CONTENTEDITABLE: 3,
            EditorKind.UNKNOWN: 4,
        }

        ranked = sorted(
            candidates,
            key=lambda item: (
                priority.get(item.kind, 99),
                -item.confidence,
                item.index,
            ),
        )

        return [
            EditorCandidate(
                kind=candidate.kind,
                support_level=candidate.support_level,
                element=candidate.element,
                frame_element=candidate.frame_element,
                selector=candidate.selector,
                label=candidate.label,
                index=index,
                confidence=candidate.confidence,
                metadata=candidate.metadata,
            )
            for index, candidate in enumerate(ranked)
        ]

    def _infer_frame_kind(self, iframe_id: str) -> EditorKind:
        normalized = iframe_id.lower()

        if "tinymce" in normalized or normalized.endswith("_ifr"):
            return EditorKind.TINYMCE

        if "cke" in normalized or "ckeditor" in normalized:
            return EditorKind.CKEDITOR

        return EditorKind.CONTENTEDITABLE

    def _infer_element_kind(self, element: Any) -> EditorKind:
        class_name = self._safe_attr(element, "class").lower()

        if "ql-editor" in class_name:
            return EditorKind.QUILL

        if "mce-content-body" in class_name or "tox" in class_name:
            return EditorKind.TINYMCE

        if "cke_editable" in class_name:
            return EditorKind.CKEDITOR

        if self._safe_attr(element, "contenteditable").lower() == "true":
            return EditorKind.CONTENTEDITABLE

        return EditorKind.CONTENTEDITABLE

    def _support_level_for(self, kind: EditorKind) -> EditorSupportLevel:
        if kind == EditorKind.TINYMCE:
            return EditorSupportLevel.PRIMARY

        if kind in {EditorKind.CKEDITOR, EditorKind.QUILL}:
            return EditorSupportLevel.BEST_EFFORT

        return EditorSupportLevel.FALLBACK

    def _safe_attr(self, element: Any, name: str) -> str:
        try:
            return str(element.get_attribute(name) or "")
        except WebDriverException:
            return ""