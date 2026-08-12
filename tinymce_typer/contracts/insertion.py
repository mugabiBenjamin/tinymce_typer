from typing import Protocol

from tinymce_typer.insertion.base import InsertionContext, InsertionResult


class InsertionStrategyChainProtocol(Protocol):
    def insert(self, context: InsertionContext) -> InsertionResult:
        ...