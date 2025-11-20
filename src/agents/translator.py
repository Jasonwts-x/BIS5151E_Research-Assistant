from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranslatorAgent:
    """
    Handles translation (e.g. via DeepL API).

    Phase-0: stub, no actual translation.
    """

    def translate(self, text: str, target_lang: str = "de") -> str:
        # TODO: call DeepL or other translation API in a later phase.
        return text
