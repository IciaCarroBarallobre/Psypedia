"""Deterministic provider for development without a connected model."""


class MockChatProvider:
    def answer(self, message: str) -> str:
        return (
            "Mock response: the assistant is not connected yet. "
            "No clinical answer has been generated."
        )
