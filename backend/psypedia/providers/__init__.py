"""Model-provider contract, independent of Flask and HTTP."""

from typing import Protocol


class ChatProvider(Protocol):
    def answer(self, message: str) -> str:
        """Return an answer for a validated question."""
        ...
