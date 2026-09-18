/** Static mirror of backend detection scope - for UI explainers only. */

export const PII_ENTITIES = [
  { token: "[PHONE]", entity: "PHONE_NUMBER", note: "US/intl phone patterns" },
  { token: "[EMAIL]", entity: "EMAIL_ADDRESS", note: "Email addresses" },
  { token: "[CREDIT_CARD]", entity: "CREDIT_CARD", note: "Card numbers (Luhn)" },
  { token: "[SSN]", entity: "US_SSN", note: "US Social Security numbers" },
  { token: "[IBAN]", entity: "IBAN_CODE", note: "International bank accounts" },
  { token: "[IP]", entity: "IP_ADDRESS", note: "IPv4 / IPv6" },
] as const;

export const PII_OUT_OF_SCOPE = [
  "Street addresses / LOCATION",
  "Person / organization names",
  "Dates of birth",
] as const;

export const LAYER1_RULES = [
  {
    id: "override_instructions",
    threat: "prompt_injection",
    summary: "Ignore / disregard / forget + instructions|rules|prompt|input|text|above|below",
  },
  {
    id: "ignore_except_or_above_below",
    threat: "prompt_injection",
    summary: "Ignore/disregard input|text except|above|below",
  },
  {
    id: "enable_jailbreak",
    threat: "jailbreak",
    summary: "Enable / activate / enter jailbreak (mode)",
  },
  {
    id: "jailbreak_mode",
    threat: "jailbreak",
    summary: "Jailbreak mode",
  },
  {
    id: "dan_mode",
    threat: "jailbreak",
    summary: "DAN mode (flexible separators)",
  },
  {
    id: "extract_instructions_or_prompt",
    threat: "system_prompt_extraction",
    summary: "Repeat / print / show / reveal / tell your|the instructions|prompt|rules",
  },
] as const;

export const LAYER2_SCOPE = [
  "Prompt injection",
  "Jailbreak / safety bypass",
  "System-prompt / hidden-instruction extraction",
] as const;

export const LAYER2_NOT = [
  "General harmful-content refusal (e.g. JBB misuse essays)",
  "Street-address PII (pattern-only Presidio)",
] as const;

const TOKEN_RE = /\[([A-Z_]+)\]/g;

export function tokensInPrompt(prompt: string | null): string[] {
  if (!prompt) return [];
  const found = new Set<string>();
  for (const m of prompt.matchAll(TOKEN_RE)) {
    found.add(`[${m[1]}]`);
  }
  return [...found].sort();
}

export function hasPiiTokens(prompt: string | null): boolean {
  return tokensInPrompt(prompt).length > 0;
}
