"""
layer 1 keyword checks. maps phrase -> threat_type
"""

SAFETY_BYPASS_KEYWORD_RULES = {
    "ignore previous instructions": "prompt_injection",
    "jailbreak": "jailbreak",
    "dan mode": "jailbreak",
    "reveal your system prompt": "system_prompt_extraction",
}


def check_prompt(text: str) -> dict:
    cleaned_text = text.lower()

    for keyword, threat_type in SAFETY_BYPASS_KEYWORD_RULES.items():
        if keyword in cleaned_text:
            return {
                "blocked": True,
                "threat_type": threat_type,
                "matched_pattern": keyword,
            }

    return {
        "blocked": False,
        "threat_type": None,
        "matched_pattern": None,
    }
