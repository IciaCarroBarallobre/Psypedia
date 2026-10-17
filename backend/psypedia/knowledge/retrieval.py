"""Small local demonstration corpus; no embeddings or manual ingestion."""

import json
from pathlib import Path
import re
import unicodedata
from typing import Protocol


# Category queries combine a subject with ordinary question/request vocabulary;
# an unexplained qualifier is not permission to answer an undocumented topic.
_APPROACH_DESCRIPTOR = r"(?:psicologic[oa]s?|(?:psico)?terapeutic[oa]s?)"
_DESCRIPTOR_WORD = re.compile(_APPROACH_DESCRIPTOR)
_CATEGORIES = {
    "psychotherapy": re.compile(
        r"\b(?:(?:psico)?terapias?(?: " + _APPROACH_DESCRIPTOR + r")?|"
        r"psychotherap(?:y|ies)|therap(?:y|ies)|"
        r"(?:enfoques?|corrientes?|modelos?|orientacion(?:es)?) " + _APPROACH_DESCRIPTOR + r")\b"
    ),
}
_QUERY_WORDS = set(
    "a al de del el la los las un una unos unas que cual cuales son es hay en "
    "sobre acerca con como me nos por favor hola quiero quisiera gustaria interesa "
    "puedes podrias podemos informacion especialmente tales para y entre "
    "tipo tipos clase clases diferente diferentes distinto distintos opcion opciones "
    "disponible disponibles general generales the a an of "
    "what which are is about me please i want would like some types available "
    "o u or and it in especially".split()
)
_COMMUNICATION_VERB = (
    r"(?:habl|cont|explic|ensen|mostr|muestr)(?:ar|a|as|an|amos|ais|o|ame|adme|arme|andome|emos)|"
    r"cuent(?:a|as|an|ame)"
)
_QUERY_VERBS = re.compile(
    _COMMUNICATION_VERB + "|" +
    r"(?:conoc|aprend|ten|tien|exist)(?:er|e|es|en|emos|eis|o|go|a|as|an)|"
    r"tell|explain|learn|know|show|compare|compara"
)
# Strip only a rhetorical request prefix, not a refusal such as "no quiero".
_RHETORICAL_REQUEST = re.compile(
    r"^(?:(?:por que|porque) )?no (?:(?:me|nos) )?"
    r"(?:(?:puedes|podrias|podemos) )?(?:" + _COMMUNICATION_VERB + r")\b"
)
_THERAPY_TERM = re.compile(r"\b(?:(?:psico)?terapias?|psychotherap(?:y|ies)|therap(?:y|ies))\b")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(re.findall(r"\w+", "".join(
        character for character in text if not unicodedata.combining(character)
    )))


def _request_word(word: str) -> bool:
    return word in _QUERY_WORDS or bool(_QUERY_VERBS.fullmatch(word))


def has_unsupported_name(message: str, topics: list[dict]) -> bool:
    """Identify named therapy gaps without discarding the documented topics."""
    text = normalize(message)
    aliases = {normalize(alias) for topic in topics for alias in topic.get("aliases", [])}
    for alias in sorted(aliases, key=len, reverse=True):
        text = re.sub(r"\b" + re.escape(alias) + r"\b", " known_topic ", text)
    for term in _THERAPY_TERM.finditer(text):
        after = text[term.end():].split()
        while after and _DESCRIPTOR_WORD.fullmatch(after[0]):
            after = after[1:]
        if after and after[0] in {"de", "del", "of"}:
            if len(after) > 1 and after[1] != "known_topic":
                return True
        elif after and after[0] != "known_topic" and not _request_word(after[0]):
            return True
        # English commonly places a therapy name before the category noun.
        if "therapy" in term.group() or "therapies" in term.group():
            before = text[:term.start()].split()
            if before and before[-1] != "known_topic" and not _request_word(before[-1]):
                return True
    return False


class KnowledgeBase(Protocol):
    def retrieve(self, message: str) -> list[dict]:
        """Return relevant cards, including pending named entries without content."""
        ...

    def introductory_topic(self) -> dict | None:
        """Return an available card when the user asks us to choose a starting point."""
        ...


class DemoKnowledgeBase:
    def __init__(self):
        self.topics = json.loads(Path(__file__).with_name("topics.json").read_text(encoding="utf-8"))

    def retrieve(self, message: str) -> list[dict]:
        text = normalize(message)
        matching = [topic for topic in self.topics if any(
            f" {normalize(alias)} " in f" {text} " for alias in topic["aliases"]
        )]
        if matching:
            return matching
        if has_unsupported_name(message, []):
            return []
        category_query = _RHETORICAL_REQUEST.sub("", text, count=1)
        for category, pattern in _CATEGORIES.items():
            remainder, count = pattern.subn(" ", category_query)
            # Coordinated descriptors can omit the noun once a category is known.
            if count:
                remainder = re.sub(r"\b" + _APPROACH_DESCRIPTOR + r"\b", " ", remainder)
            if count and all(_request_word(word) for word in remainder.split()):
                return [topic for topic in self.topics
                        if topic.get("category") == category and topic["summary"]]
        return []

    def introductory_topic(self) -> dict | None:
        return next((topic for topic in self.topics if topic["summary"]), None)
