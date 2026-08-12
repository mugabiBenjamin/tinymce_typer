from tinymce_typer.config.settings import InsertionConfig
from tinymce_typer.insertion.batch import BatchInsertionStrategy
from tinymce_typer.insertion.character_typing import CharacterTypingStrategy
from tinymce_typer.insertion.clipboard import ClipboardInsertionStrategy
from tinymce_typer.insertion.direct_html import DirectHtmlInsertionStrategy
from tinymce_typer.insertion.strategy_chain import InsertionStrategyChain


class InsertionStrategyFactory:
    def create_chain(self, config: InsertionConfig) -> InsertionStrategyChain:
        strategies = []

        if config.strategy == "clipboard":
            if not config.no_clipboard:
                strategies.append(ClipboardInsertionStrategy())
            return InsertionStrategyChain(strategies)

        if config.strategy == "direct-html":
            strategies.append(DirectHtmlInsertionStrategy())
            return InsertionStrategyChain(strategies)

        if config.strategy == "character":
            strategies.append(
                CharacterTypingStrategy(
                    delay_seconds=config.type_delay,
                    use_real_keystrokes=config.real_keystrokes,
                )
            )
            return InsertionStrategyChain(strategies)

        if config.strategy == "batch":
            strategies.append(
                BatchInsertionStrategy(
                    batch_size=config.batch_size,
                    delay_seconds=config.batch_delay,
                )
            )
            return InsertionStrategyChain(strategies)

        if not config.no_clipboard:
            strategies.append(ClipboardInsertionStrategy())

        if config.batch:
            strategies.append(
                BatchInsertionStrategy(
                    batch_size=config.batch_size,
                    delay_seconds=config.batch_delay,
                )
            )

        if config.formatted:
            strategies.append(DirectHtmlInsertionStrategy())

        strategies.append(
            CharacterTypingStrategy(
                delay_seconds=config.type_delay,
                use_real_keystrokes=config.real_keystrokes,
            )
        )

        strategies.append(DirectHtmlInsertionStrategy())

        return InsertionStrategyChain(strategies)