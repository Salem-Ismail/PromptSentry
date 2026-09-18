"""
layer 1: high-precision regex on attack *intent*, not topic words.

saying "jailbreak" or "prompt injection" in an essay must not block.
paraphrases without these shapes go to layer 2.
"""

import re

# Object of an override verb: instructions, rules, prompt, input, text, or
# positional "above"/"below" (e.g. "ignore any input above").
_OVERRIDE_OBJECT = (
    r"(?:(?:all|any|the|your|my)\s+)?"
    r"(?:(?:previous|prior|above|below|new)\s+)?"
    r"(?:instructions?|rules?|prompts?|input|text|"
    r"(?:all\s+)?(?:text|input)\s+(?:above|below)|"
    r"(?:above|below))"
)

# (compiled pattern, threat_type, human-readable id for logs)
LAYER1_RULES: list[tuple[re.Pattern[str], str, str]] = [
    # --- instruction override (ignore / disregard / forget) ---
    (
        re.compile(
            rf"(?:ignore|disregard|forget)\s+{_OVERRIDE_OBJECT}",
            re.IGNORECASE,
        ),
        "prompt_injection",
        "override_instructions",
    ),
    (
        re.compile(
            r"(?:ignore|disregard)\s+(?:all\s+|any\s+)?(?:input|text|instructions?|rules?)\s+"
            r"(?:except|above|below|and\s+below)",
            re.IGNORECASE,
        ),
        "prompt_injection",
        "ignore_except_or_above_below",
    ),
    # --- jailbreak mode (topic word alone still does NOT match) ---
    (
        re.compile(
            r"(enable|activate|enter)\s+jailbreak(\s+mode)?",
            re.IGNORECASE,
        ),
        "jailbreak",
        "enable_jailbreak",
    ),
    (
        re.compile(r"jailbreak\s+mode", re.IGNORECASE),
        "jailbreak",
        "jailbreak_mode",
    ),
    (
        re.compile(r"\bdan[\s_-]*mode\b", re.IGNORECASE),
        "jailbreak",
        "dan_mode",
    ),
    # --- system / instruction extraction ---
    (
        re.compile(
            r"(?:repeat|print|show|reveal|tell|paste)\s+"
            r"(?:me\s+|all\s+)?"
            r"(?:(?:your|the|my)\s+)?"
            r"(?:(?:full|exact|entire|initial|additional|hidden|system|developer)\s+)*"
            r"(?:instructions?|prompts?|rules?|message)",
            re.IGNORECASE,
        ),
        "system_prompt_extraction",
        "extract_instructions_or_prompt",
    ),
]


def check_prompt(text: str) -> dict:
    for pattern, threat_type, rule_id in LAYER1_RULES:
        if pattern.search(text):
            return {
                "blocked": True,
                "threat_type": threat_type,
                "matched_pattern": rule_id,
            }

    return {
        "blocked": False,
        "threat_type": None,
        "matched_pattern": None,
    }
