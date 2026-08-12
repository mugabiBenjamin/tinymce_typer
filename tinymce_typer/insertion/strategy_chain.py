from collections.abc import Sequence

from tinymce_typer.exceptions import InsertionError
from tinymce_typer.insertion.base import (
    InsertionContext,
    InsertionResult,
    InsertionStrategy,
    StrategyFailure,
)
from tinymce_typer.logging.setup import get_logger


logger = get_logger(__name__)


class InsertionStrategyChain:
    def __init__(self, strategies: Sequence[InsertionStrategy]):
        self.strategies = tuple(strategies)

    def insert(self, context: InsertionContext) -> InsertionResult:
        failures: list[StrategyFailure] = []

        if not self.strategies:
            raise InsertionError("No insertion strategies are configured.")

        for strategy in self.strategies:
            try:
                if not strategy.can_run(context):
                    failures.append(
                        StrategyFailure(
                            strategy_name=strategy.name,
                            message="Strategy cannot run for current context.",
                            recoverable=True,
                        )
                    )
                    continue

                logger.info("Trying insertion strategy: %s", strategy.name)
                result = strategy.insert(context)

                if result.success:
                    return InsertionResult(
                        success=True,
                        strategy_name=result.strategy_name,
                        inserted_characters=result.inserted_characters,
                        final_offset=result.final_offset,
                        message=result.message,
                        failures=tuple(failures),
                        metadata=result.metadata,
                    )

                failures.append(
                    StrategyFailure(
                        strategy_name=strategy.name,
                        message=result.message,
                        recoverable=True,
                        metadata=result.metadata,
                    )
                )
            except Exception as exc:
                logger.warning("Insertion strategy failed: %s | %s", strategy.name, exc)
                failures.append(
                    StrategyFailure(
                        strategy_name=strategy.name,
                        message=str(exc),
                        recoverable=True,
                    )
                )

        raise InsertionError(self._failure_message(failures))

    def _failure_message(self, failures: list[StrategyFailure]) -> str:
        if not failures:
            return "All insertion strategies failed."

        details = "; ".join(
            f"{failure.strategy_name}: {failure.message}" for failure in failures
        )

        return f"All insertion strategies failed. {details}"