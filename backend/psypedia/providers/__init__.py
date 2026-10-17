"""Model-provider contract, independent of Flask and HTTP."""

from typing import Protocol


class ChatProvider(Protocol):
    def answer(self, message: str, *, system_prompt: str | None = None,
               history: list[dict[str, str]] | None = None) -> str:
        """Return an answer for a validated question."""
        ...


class ProviderUnavailable(Exception):
    """Service or configured model is unavailable."""


class ProviderTimeout(Exception):
    """Generation exceeded the provider time limit."""


class ProviderInvalidResponse(Exception):
    """Provider returned an unusable answer."""
