"""Compose language signals for help routing, without assessing clinical risk."""

from dataclasses import dataclass
import re
from typing import Literal

from psypedia.knowledge import normalize

# Shared with the privacy guard. Vocabulary describes concepts, not user sentences.
PATIENT_TERM_ES = r"(?:paciente|cliente|clienta|consultante)"
PATIENT_TERM_EN = r"(?:patient|client)"


def _words(expression: str) -> re.Pattern:
    return re.compile(r"\b(?:" + expression + r")\b")


_PATIENT = _words(PATIENT_TERM_ES + "|" + PATIENT_TERM_EN)
_SELF = _words(r"yo|me|estoy|tengo|quiero|voy|pienso|necesito|i|im|myself|\w+(?:arme|irme)")
_SELF_SUBJECT = _words(r"yo|estoy|tengo|quiero|voy|pienso|necesito|i|im")
_OTHER_PERSON = _words(r"persona|alguien|person|someone")
_INTENT = _words(r"quier\w*|pretend\w*|plane\w*|piens\w*|pensando|amenaz\w*|decid\w*|inten[tc]\w*|voy a|va(?:mos|n)? a|wants?|intend\w*|planning|going to")
_REPORTED_SITUATION = r"hay|existe\w*|veo|detect\w*|observ\w*|refier\w*|report\w*|comunica\w*"
_REPORT_ASSERTION = _words(_REPORTED_SITUATION)
_OBSERVATION = _words(r"teng\w*|tien\w*|present\w*|est(?:a|oy|an)|es|necesit\w*|ha|has|is|am|" + _REPORTED_SITUATION)
_REPORT = _words(r"dice|dijo|afirma|explica|cuenta|comunica|says?|said|reports?")
_ONGOING = _words(r"me|se|estoy|esta|ha|acabo|is|has|am")
_HARM_TOPIC = _words(r"suicid\w*|autoles\w*|self harm\w*|self injur\w*")
_RISK = _words(r"riesg\w*|peligro|ideacion|ideas|thoughts|risk|suicidal")
_HARM_ACTION = _words(
    r"suicidar(?:me|se|te)|matar(?:me|se|te)|quitar(?:me|se|te)? la vida|"
    r"(?:acabar|terminar) con (?:mi|su) vida|"
    r"(?:hacer(?:me|se|te)?|haciendo) dano|"
    r"(?:auto)?(?:lesion|lexion)(?:ar\w*|ando|a|an|o)|"
    r"kill (?:myself|themselves)|hurt (?:myself|themselves)|self harming"
)
_MEDICAL_FAILURE = _words(
    r"muero|muere|muriendo|dying|"
    r"no (?:puedo |puede |pueden )?respirar|no respira|"
    r"(?:cannot|cant|can t) breathe|dificultad para respirar"
)
_URGENT_HELP = _words(r"peligro|danger|emergencia|emergency|ambulancia|ambulance|ayuda urgente")
_NEGATION = _words(r"no|nunca|jamas|tampoco|ni|niega|sin|not|never|denies")
_EDUCATION = re.compile(
    r"^(?:que es|como (?:se define|aborda)|what (?:does|is meant)|en teoria|"
    r"(?:en|segun) (?:un|una|el|la) (?:articulo|libro|pelicula|novela|ejemplo|trabajo academico)|"
    r"(?:la|una) (?:novela|pelicula)|(?:a|an|the) (?:article|book|novel|movie|example))\b|"
    r"\b(?:que significa|que quiere decir|(?:la|una) frase|es una cita|caso ficticio|caso hipotetico|ejemplo ficticio|ejemplo hipotetico)\b"
)
_KNOWLEDGE_REQUEST = _words(r"saber|conocer|entender|estudi\w*|aprend\w*|pregunt\w*|informacion|know|learn|questions?")
_ACTION_QUESTION = re.compile(r"\b(?:como(?: (?:puedo|puede|podria))?|a|how (?:to|can i|can they)) $")
_FIGURATIVE = _words(r"de (?:risa|hambre|aburrimiento)")
_CONTINUATION = re.compile(r"^(?:(?:el|ella|they) )?(?:se\b|dice\b|dijo\b|afirma\b|explica\b|quiere\b|va a\b|tiene\b|presenta\b|no respira\b)")
_CLAUSES = re.compile(r"(,|\b(?:y|pero|aunque|and|but)\b)", re.IGNORECASE)
_QUOTES = re.compile(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|(?<!\w)\x27[^\x27\n]*\x27(?!\w)')
_TOPIC_LABEL = re.compile(r"(?:(?:ideas|ideacion|riesgo)(?: de)? )?suicid\w*")
_INJURY_LABEL = re.compile(r"(?:auto)?(?:lesion|lexion)|dano")
# A short affirmation must contain only conversational/reference words. A new
# substantive question is analysed independently, never inherited as a crisis.
_CONFIRMATION_WORDS = set("si claro cierto efectivamente confirmo hay inmediato inmediata ahora mismo yes indeed".split())
_CONFIRMATION_VOCABULARY = _CONFIRMATION_WORDS | set("creo pienso parece que lo es el la un una riesgo peligro existe it is there right now".split())


@dataclass(frozen=True)
class _ClauseSignals:
    subject: Literal["patient", "self", "unspecified"]
    concept: Literal["danger", "harm"]
    asserted: bool
    urgent: bool


def _asserted(prefix: str) -> bool:
    """Negation applies to a local predicate, not an earlier unrelated sentence."""
    references = list(_PATIENT.finditer(prefix))
    if references:
        prefix = prefix[references[-1].end():]
    return not _NEGATION.search(" ".join(prefix.split()[-8:]))


def _clause_signals(text: str, *, patient: bool) -> list[_ClauseSignals]:
    subject = "patient" if patient else "self" if _SELF.search(text) else "unspecified"
    signals = []
    for failure in _MEDICAL_FAILURE.finditer(text):
        if not _FIGURATIVE.match(text, failure.end() + 1):
            signals.append(_ClauseSignals(subject, "danger", _asserted(text[:failure.start()]), True))
    for urgent in _URGENT_HELP.finditer(text):
        if patient or _SELF.search(text) or _OBSERVATION.search(text) or urgent.group() == text:
            signals.append(_ClauseSignals(subject, "danger", _asserted(text[:urgent.start()]), True))
    for action in _HARM_ACTION.finditer(text):
        if _FIGURATIVE.match(text, action.end() + 1):
            continue
        prefix = text[:action.start()]
        intentions = list(_INTENT.finditer(prefix))
        predicate = intentions[-1] if intentions else None
        # Intent must concern the harmful action, not learning about the subject.
        bridge = prefix[predicate.end():] if predicate else prefix
        action_question = bool(_ACTION_QUESTION.search(prefix))
        if _KNOWLEDGE_REQUEST.search(bridge) and not action_question:
            continue
        stated = predicate is not None or bool(_ONGOING.search(prefix)) or action_question
        asserted = stated and _asserted(prefix)
        signals.append(_ClauseSignals(subject, "harm", asserted, subject == "self"))
    if _HARM_TOPIC.search(text) and _RISK.search(text) and not _KNOWLEDGE_REQUEST.search(text):
        observations = list(_OBSERVATION.finditer(text))
        if subject == "unspecified" and not _OTHER_PERSON.search(text):
            observations = [predicate for predicate in observations if _REPORT_ASSERTION.fullmatch(predicate.group())]
        if observations:
            predicate = observations[-1]
            signals.append(_ClauseSignals(subject, "harm", _asserted(text[:predicate.start()]), False))
    return signals


def _clauses(sentence: str):
    """An educational frame persists until a contrasting clause changes it."""
    educational = False
    for part in _CLAUSES.split(sentence):
        text = normalize(part)
        if text in {"pero", "aunque", "but"}:
            educational = False
        elif text and text not in {"y", "and"}:
            educational = educational or bool(_EDUCATION.search(text))
            yield text, educational


def _signals(message: str) -> list[_ClauseSignals]:
    """Use the same signal extraction for current input and recent user turns."""
    signals = []
    patient_context = False
    for sentence in re.split(r"[.!?;\n]+", message):
        plain = _QUOTES.sub(" ", sentence)
        text = normalize(plain)
        if not text:
            continue
        patient_context = patient_context and bool(_CONTINUATION.match(text))
        inherited_patient = patient_context
        educational = False
        for clause, educational in _clauses(plain):
            if _PATIENT.search(clause):
                patient_context = True
            elif _SELF_SUBJECT.search(clause) and not _REPORT.search(clause):
                patient_context = False
            if not educational:
                signals.extend(_clause_signals(clause, patient=patient_context))
        # A quotation is data unless attributed to a person reporting intent.
        for quote in _QUOTES.finditer(sentence):
            prefix_clauses = list(_clauses(_QUOTES.sub(" ", sentence[:quote.start()])))
            if not prefix_clauses or prefix_clauses[-1][1]:
                continue
            quoted_patient = inherited_patient
            for prefix, _ in prefix_clauses:
                if _PATIENT.search(prefix):
                    quoted_patient = True
                elif _SELF_SUBJECT.search(prefix) and not _REPORT.search(prefix):
                    quoted_patient = False
            report = list(_REPORT.finditer(prefix))
            if quoted_patient and report and _asserted(prefix[:report[-1].start()]):
                signals.extend(signal for signal in _clause_signals(normalize(quote.group()[1:-1]), patient=True)
                               if signal.concept == "harm")
        if educational:
            patient_context = False
    return [signal for signal in signals if signal.asserted]


def _confirmation(text: str) -> bool:
    words = set(text.split())
    return bool(words & _CONFIRMATION_WORDS) and words <= _CONFIRMATION_VOCABULARY


# Replies share the Spanish interface language, including for recognised English input.
_REPORTED_RISK_REPLY_ES = (
    "Entiendo tu preocupación. Activa ahora el protocolo de tu centro y "
    "contacta con el equipo asistencial o el servicio correspondiente para "
    "una valoración clínica.\n\n"
    "Si crees que hay peligro inmediato, contacta ahora con emergencias: "
    "llama al 112 en España o la Unión Europea; en otros países, al número "
    "local. No esperes al chat para activar la ayuda.\n\n"
    "No puedo valorar el riesgo ni contactar con los servicios por ti. "
    "No compartas datos identificativos."
)

_PATIENT_EMERGENCY_REPLY_ES = (
    "Entiendo tu preocupación por el paciente. Activa ahora los protocolos "
    "de emergencia de tu centro y contacta inmediatamente con emergencias: "
    "llama al 112 si estás en España o en la Unión Europea; en otros países, "
    "utiliza el número local. No esperes al chat para activar la ayuda.\n\n"
    "No puedo evaluar al paciente ni contactar con emergencias por ti. "
    "No compartas datos identificativos del paciente."
)

_PATIENT_RISK_REPLY_ES = (
    "Entiendo tu preocupación por el paciente. Ante una comunicación de riesgo "
    "de suicidio o autolesión, sigue el protocolo de tu centro y contacta con "
    "el equipo asistencial o el servicio correspondiente para una valoración clínica. "
    "No utilices este chat para determinar el nivel de riesgo ni elegir un tratamiento.\n\n"
    "Si hay peligro inmediato o una urgencia médica, contacta con emergencias: "
    "112 en España y la Unión Europea; en otros países, el número local. "
    "No esperes una respuesta del chat para activar la ayuda.\n\n"
    "No puedo evaluar al paciente ni contactar con los servicios por ti. "
    "No compartas datos identificativos del paciente."
)

_INJURY_REPLY_ES = (
    "Si te refieres a una lesión o una situación actual de riesgo, busca apoyo "
    "profesional. Ante peligro inmediato, contacta con emergencias: 112 en España "
    "y la UE; en otros países, el número local. No esperes al chat. "
    "No puedo evaluar una lesión ni determinar el nivel de riesgo."
)

_IMMEDIATE_DANGER_REPLY_ES = (
    "Siento que estés pasando por esto. Busca ayuda inmediata: llama al 112 "
    "si estás en España o en otro país de la Unión Europea. Si estás en otro "
    "lugar, llama al número de emergencias local.\n\n"
    "Si puedes, pide a alguien cercano que te acompañe y te ayude a llamar. "
    "No esperes a que el chat responda para buscar ayuda.\n\n"
    "No puedo evaluar lo que te está pasando ni contactar con emergencias por ti."
)


_UNSPECIFIED_SUICIDE_REPLY_ES = (
    "Si te refieres a un riesgo actual de suicidio, sigue el protocolo de tu centro "
    "y contacta con el equipo asistencial para una valoración clínica. "
    "Si hay peligro inmediato, llama al 112 en España o la Unión Europea; "
    "en otros países, contacta con emergencias locales. No esperes al chat.\n\n"
    "Si buscas información educativa, formula una pregunta general sin datos de pacientes. "
    "No puedo valorar el riesgo ni contactar con los servicios por ti."
)


def emergency_response(message: str, *, history: list[dict[str, str]] | None = None) -> str | None:
    """Map asserted signals to guidance before privacy, retrieval, or inference."""
    text = normalize(message)
    if _confirmation(text) or _TOPIC_LABEL.fullmatch(text):
        for turn in reversed(history or []):
            if turn["role"] != "user":
                continue
            previous = normalize(turn["content"])
            if _confirmation(previous):
                continue
            if _signals(turn["content"]) or _TOPIC_LABEL.fullmatch(previous):
                return _REPORTED_RISK_REPLY_ES
            break

    signals = _signals(message)
    # Urgent medical/danger signals take precedence over other reported concerns.
    for signal in sorted(signals, key=lambda item: (item.concept == "danger", item.urgent), reverse=True):
        if signal.concept == "danger":
            return _PATIENT_EMERGENCY_REPLY_ES if signal.subject == "patient" else _IMMEDIATE_DANGER_REPLY_ES
        if signal.subject == "patient":
            return _PATIENT_RISK_REPLY_ES
        return _IMMEDIATE_DANGER_REPLY_ES if signal.urgent else _REPORTED_RISK_REPLY_ES
    if _TOPIC_LABEL.fullmatch(text):
        return _UNSPECIFIED_SUICIDE_REPLY_ES
    if _INJURY_LABEL.fullmatch(text):
        return _INJURY_REPLY_ES
    return None
