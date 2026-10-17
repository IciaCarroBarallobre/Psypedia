"""Coordinate chat responses using an explicitly supplied provider."""

import re
from time import monotonic

from psypedia.providers import ChatProvider, ProviderInvalidResponse
from psypedia.knowledge import KnowledgeBase, has_unsupported_name, normalize
from psypedia.prompting import build_context, build_system_prompt


MISSING_INFORMATION = (
    "No tengo información suficiente sobre ese tema en la base disponible. "
    "Puedo ayudarte con los temas documentados, sin inventar información."
)
# Include the earlier one-sentence form of this application-only notice.
_INFORMATION_NOTICES = {normalize(reply) for reply in (
    MISSING_INFORMATION, MISSING_INFORMATION.split(".", 1)[0],
)}
PARTIAL_INFORMATION = (
    "No tengo información suficiente sobre todos los términos que mencionas. "
    "Puedo explicarte la parte documentada, sin dar por hecho que sean equivalentes."
)
_AGREEMENTS = {"si", "vale", "ok", "de acuerdo", "yes", "sure"}
_ACKNOWLEDGEMENTS = _AGREEMENTS | {
    "ni idea", "no se", "no se por donde empezar", "lo que quieras",
    "i dont know", "i don t know",
}
_FOLLOW_UPS = _AGREEMENTS | {
    "cuentame mas", "explicamelo", "continua", "un ejemplo", "por ejemplo", "tell me more",
}


class ChatService:
    def __init__(self, provider: ChatProvider, knowledge_base: KnowledgeBase | None = None):
        self.provider = provider
        self.knowledge_base = knowledge_base

    def answer(self, message: str, *, history: list[dict[str, str]] | None = None) -> str:
        text = normalize(message)
        provider_options = {"history": history} if history else {}
        if self.knowledge_base is None:
            return self.provider.answer(message, **provider_options)
        topics = self.knowledge_base.retrieve(message)
        # Short follow-ups can refer to an approach introduced in earlier turns.
        if not topics and text in _FOLLOW_UPS:
            for turn in reversed(history or []):
                topics = self.knowledge_base.retrieve(turn["content"])
                if topics:
                    # An assistant may mention other approaches in passing; do not
                    # expand the retrieved set from every incidental mention.
                    if turn["role"] == "assistant":
                        topics = topics[:1]
                    break
        if not topics and text in _AGREEMENTS:
            return (
                "Claro. Para ayudarte necesito una pregunta o un tema concreto de psicología. "
                "Puedes escribirlo con tus palabras; no hace falta que conozcas el nombre de una terapia."
            )
        acknowledgement = text in _ACKNOWLEDGEMENTS
        if not topics and acknowledgement:
            introduction = self.knowledge_base.introductory_topic()
            topics = [introduction] if introduction else []
        if not topics:
            if re.fullmatch(r"(?:hola|holi|hello|hi|buenas|buenos dias|buenas tardes)(?: que tal| como estas)?", text):
                return "¡Hola! Estoy aquí para ayudarte con preguntas sobre psicología. ¿Qué te gustaría saber?"
            if re.fullmatch(r"(?:muchas )?(?:gracias|thanks)(?: por tu ayuda)?", text):
                return "De nada. Puedes preguntarme sobre los temas disponibles en la base."
            if text in {"que puedes hacer", "como puedes ayudarme", "what can you do"}:
                return "Puedo explicar la información de las fichas disponibles. Si no tengo información sobre un tema, te lo diré."
            return MISSING_INFORMATION
        pending = any(not topic["summary"] for topic in topics)
        topics = [topic for topic in topics if topic["summary"]]
        if not topics:
            return MISSING_INFORMATION
        # Keep routing/topic context, but do not feed obsolete application
        # abstentions back as model memory when reference content is available.
        model_history = [turn for turn in (history or []) if not (
            turn["role"] == "assistant" and normalize(turn["content"]) in _INFORMATION_NOTICES
        )]
        provider_options = {"history": model_history} if model_history else {}
        context = build_context(topics)
        partial = pending or has_unsupported_name(message, topics)
        system_prompt = build_system_prompt(context, continuation=acknowledgement, partial=partial)
        started = monotonic()
        answer = self.provider.answer(message, system_prompt=system_prompt, **provider_options)
        previous_answers = {
            normalize(turn["content"].removeprefix(PARTIAL_INFORMATION + "\n\n")
                      .split("\n\nReferencias de las fichas / Card references:")[0])
            for turn in (history or []) if turn["role"] == "assistant"
        }
        if normalize(answer) in previous_answers:
            if monotonic() - started >= 10:
                raise ProviderInvalidResponse()
            retry_prompt = build_system_prompt(context, continuation=acknowledgement, retry=True, partial=partial)
            answer = self.provider.answer(message, system_prompt=retry_prompt, **provider_options)
            if normalize(answer) in previous_answers:
                raise ProviderInvalidResponse()
        references = "\n\nReferencias de las fichas / Card references:\n" + "\n".join(
            f"- {topic['source_title']}: {topic['source_url']}" for topic in topics
        )
        notice = PARTIAL_INFORMATION + "\n\n" if partial else ""
        return notice + answer + references
