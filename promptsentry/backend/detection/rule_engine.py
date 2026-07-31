"""
layer 1: high-precision regex on attack *intent*, not topic words.

saying "jailbreak" or "prompt injection" in an essay must not block.
paraphrases without these shapes go to layer 2.
"""

import re

# (compiled pattern, threat_type, human-readable id for logs)
LAYER1_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(
            r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
            re.IGNORECASE,
        ),
        "prompt_injection",
        "ignore_previous_instructions",
    ),
    (
        re.compile(
            r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
            re.IGNORECASE,
        ),
        "prompt_injection",
        "disregard_previous_instructions",
    ),
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
    (
        re.compile(
            r"reveal\s+(your\s+)?(hidden\s+|system\s+)?(prompt|instructions)",
            re.IGNORECASE,
        ),
        "system_prompt_extraction",
        "reveal_system_prompt",
    ),
    (
        re.compile(
            r"(print|show|paste)\s+(me\s+)?(the\s+)?(exact\s+)?(system|developer|hidden)\s+(prompt|message|instructions)",
            re.IGNORECASE,
        ),
        "system_prompt_extraction",
        "show_system_prompt",
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
