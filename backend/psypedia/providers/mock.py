"""Deterministic provider for development without a connected model."""


class MockChatProvider:
    def answer(self, message: str, *, system_prompt: str | None = None,
               history: list[dict[str, str]] | None = None) -> str:
        return (
            "Respuesta de demostración (mock): no se ha consultado ningún modelo de IA "
            "ni se ha generado una respuesta clínica."
        )
