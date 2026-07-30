"""
pii redaction with microsoft presidio. runs locally so we dont send raw pii to a cloud model just to detect it.
"""

import json
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# pin the small spacy model from the dockerfile (default tried to pull lg which is huge)
_nlp_configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
_nlp_engine = NlpEngineProvider(nlp_configuration=_nlp_configuration).create_engine()

_analyzer = AnalyzerEngine(nlp_engine=_nlp_engine, supported_languages=["en"])
_anonymizer = AnonymizerEngine()

# placeholders we swap in
_OPERATORS = {
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
    "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
    "IBAN_CODE": OperatorConfig("replace", {"new_value": "[IBAN]"}),
    "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP]"}),
    "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
    "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
}


def redact_text(text: str) -> tuple[str, list[str]]:
    """
    scrub pii out of text. always continues, never blocks the request.
    returns (redacted_text, list of entity types we found)
    """
    if not text or not text.strip():
        return text, []

    results = _analyzer.analyze(text=text, language="en")
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

    # last user message (same one we extract for logging)
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            message["content"] = redacted_prompt
            break

    data["messages"] = messages
    return json.dumps(data).encode("utf-8")
