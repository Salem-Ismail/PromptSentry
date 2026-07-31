"""
pii redaction with microsoft presidio. runs locally so we dont send raw pii to a cloud model just to detect it.
"""

import json
from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# pin the small spacy model from the dockerfile
_nlp_configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
_nlp_engine = NlpEngineProvider(nlp_configuration=_nlp_configuration).create_engine()

# load default recognizers then drop SpacyRecognizer (NER).
# that was the slow part on long text even when we found nothing.
_registry = RecognizerRegistry()
_registry.load_predefined_recognizers(nlp_engine=_nlp_engine)
_registry.remove_recognizer("SpacyRecognizer")

_analyzer = AnalyzerEngine(
    registry=_registry,
    nlp_engine=_nlp_engine,
    supported_languages=["en"],
)
_anonymizer = AnonymizerEngine()

# pattern-style entities only
_ENTITIES = [
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "US_SSN",
    "IBAN_CODE",
    "IP_ADDRESS",
]

_OPERATORS = {
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
    "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
    "IBAN_CODE": OperatorConfig("replace", {"new_value": "[IBAN]"}),
    "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP]"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
}


def _might_have_pii(text: str) -> bool:
    # phones/cards/ssn/ip need digits; email needs @. skip spaCy work otherwise.
    if "@" in text:
        return True
    return any(ch.isdigit() for ch in text)


def redact_text(text: str) -> tuple[str, list[str]]:
    """
    scrub pii out of text. always continues, never blocks the request.
    returns (redacted_text, list of entity types we found)
    """
    if not text or not text.strip():
        return text, []

    if not _might_have_pii(text):
        return text, []

    results = _analyzer.analyze(
        text=text,
        language="en",
        entities=_ENTITIES,
    )
    if not results:
        return text, []

    entity_types = sorted({r.entity_type for r in results})

    anonymized = _anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=_OPERATORS,
    )
    return anonymized.text, entity_types


def rebuild_body_with_redacted_prompt(body: bytes, redacted_prompt: str) -> bytes:
    """
    stick the redacted user message back into the openai-style json.
    if we forwarded the original body bytes we'd still leak the phone number.
    """
    data: dict[str, Any] = json.loads(body)
    messages = data.get("messages")
    if not isinstance(messages, list):
        return body

    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            message["content"] = redacted_prompt
            break

    data["messages"] = messages
    return json.dumps(data).encode("utf-8")
