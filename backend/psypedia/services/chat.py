"""Coordinate chat responses using an explicitly supplied provider."""

from psypedia.providers import ChatProvider


class ChatService:
    def __init__(self, provider: ChatProvider):
        self.provider = provider

    def answer(self, message: str) -> str:
        return self.provider.answer(message)
