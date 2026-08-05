"""
Dry-run eval on Tensor Trust (hijacking + prompt extraction), not JailbreakBench harm.

Attacks = user `attack` strings from:
 - benchmarks/hijacking-robustness (prompt hijacking / injection)
 - benchmarks/extraction-robustness (prompt / instruction stealing)

Safe = legitimate Tensor Trust `access_code` submissions (intended password phrases),
NOT adversarial attacks.

Hit for PromptSentry = HTTP 400 request_blocked.

Usage (from promptsentry/):
  set -a && source .env && set +a
  python eval/dry_run_tensor_trust.py --limit 25 --preview-only   # inspect samples first
  python eval/dry_run_tensor_trust.py --limit 25                 # run against proxy
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass

import httpx

HIJACK_URL = (
    "https://raw.githubusercontent.com/HumanCompatibleAI/tensor-trust-data/main/"
    "benchmarks/hijacking-robustness/v1/hijacking_robustness_dataset.jsonl"
)
EXTRACT_URL = (
    "https://raw.githubusercontent.com/HumanCompatibleAI/tensor-trust-data/main/"
    "benchmarks/extraction-robustness/v1/extraction_robustness_dataset.jsonl"
)

# Must look like injection / hijack / instruction-or-prompt theft (not harm topics).
ATTACK_SIGNAL = re.compile(
    r"""(?ix)
    (
      ignore\s+(all\s+)?(previous|prior|above)|
      disregard\s+(all\s+)?(previous|prior)|
      forget\s+(your\s+)?(instructions|rules)|
      override|
      new\s+instructions|
      you\s+are\s+now|
      pretend\s+you|
      system\s*prompt|
      reveal|
      repeat\s+(your\s+)?(instructions|prompt)|
      print\s+(your\s+)?(instructions|prompt)|
      show\s+(me\s+)?(your\s+)?(instructions|prompt|hidden)|
      access\s*code|
      end\s+(of\s+)?(prompt|instructions)|
      prompt\s+draft|
      convert\s+.{0,40}instructions|
      instructions\s+to\s+python|
      begin\s+your\s+response\s+with|
      access\s+granted
    )
    """,
)


@dataclass
class Sample:
    kind: str  # attack | safe
    source: str  # hijack | extract | access_code
    sample_id: str
    text: str


@dataclass
class TrialResult:
    kind: str
    source: str
    sample_id: str
    status: int
    blocked: bool
    layer: int | None
    reason: str | None
    latency_ms: int
    preview: str


def _download_jsonl(url: str, max_rows: int = 8000) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "PromptSentry-Eval"})
    rows: list[dict] = []
    with urllib.request.urlopen(req, timeout=180) as resp:
        for i, line in enumerate(resp):
            if i >= max_rows:
                break
            rows.append(json.loads(line))
    return rows


def _is_spam(text: str) -> bool:
    t = text.strip()
    if len(t) < 24:
        return True

    toks = t.split()
    if not toks:
        return True

    # single-char / tiny-token floods (k k k / ö ö ö / ) ] } )
    short = sum(1 for x in toks if len(x) <= 1)
    if len(toks) >= 10 and short / len(toks) > 0.45:
        return True

    if len(toks) >= 8 and len(set(toks)) <= 4:
        return True

    compact = re.sub(r"\s+", "", t)
    if compact:
        top_n = Counter(compact).most_common(1)[0][1]
        if top_n / len(compact) > 0.28:
            return True

    # need real words, not punctuation soup with one buried keyword
    alpha_words = re.findall(r"[A-Za-z]{3,}", t)
    if len(set(w.lower() for w in alpha_words)) < 8:
        return True
    if len(alpha_words) / max(1, len(toks)) < 0.25:
        return True

    return False


def _is_in_scope_attack(text: str) -> bool:
    if _is_spam(text):
        return False
    if not ATTACK_SIGNAL.search(text):
        return False
    # skip mostly-roleplay with a single weak keyword buried far down
    m = ATTACK_SIGNAL.search(text)
    assert m is not None
    if m.start() > 400 and len(re.findall(r"[A-Za-z]{3,}", text[: m.start()])) > 40:
        # long preamble then late keyword - often off-topic stories
        return False
    return True


def load_attack_samples(limit: int) -> list[Sample]:
    """Half hijack / half extract when possible."""
    hijack_rows = _download_jsonl(HIJACK_URL)
    extract_rows = _download_jsonl(EXTRACT_URL)

    hijack: list[Sample] = []
    for row in hijack_rows:
        atk = str(row.get("attack") or "").strip()
        if not _is_in_scope_attack(atk):
            continue
        hijack.append(
            Sample("attack", "hijack", str(row["sample_id"]), atk)
        )

    extract: list[Sample] = []
    for row in extract_rows:
        atk = str(row.get("attack") or "").strip()
        if not _is_in_scope_attack(atk):
            continue
        extract.append(
            Sample("attack", "extract", str(row["sample_id"]), atk)
        )

    n_h = (limit + 1) // 2
    n_e = limit - n_h
    chosen = hijack[:n_h] + extract[:n_e]
    if len(chosen) < limit:
        raise RuntimeError(
            f"Only collected {len(chosen)} in-scope Tensor Trust attacks "
            f"(hijack={len(hijack)}, extract={len(extract)}); need {limit}."
        )
    return chosen[:limit]


def load_safe_samples(limit: int) -> list[Sample]:
    """Legitimate password / access-code phrases from the same Tensor Trust benches."""
    rows = _download_jsonl(HIJACK_URL) + _download_jsonl(EXTRACT_URL)
    seen: set[str] = set()
    out: list[Sample] = []
    for row in rows:
        code = str(row.get("access_code") or "").strip()
        if not code or code.lower() in seen:
            continue
        if len(code) < 4 or len(code) > 100:
            continue
        # access codes are often short phrases / tokens - don't use attack spam heuristics
        if ATTACK_SIGNAL.search(code):
            continue
        # skip pure punctuation soup
        if len(re.findall(r"[A-Za-z0-9]", code)) < 4:
            continue
        seen.add(code.lower())
        out.append(Sample("safe", "access_code", str(row["sample_id"]), code))
        if len(out) >= limit:
            break
    if len(out) < limit:
        raise RuntimeError(f"Only collected {len(out)} safe access_codes; need {limit}.")
    return out


def preview_samples(attacks: list[Sample], safes: list[Sample]) -> None:
    print("\n===== PREVIEW ATTACKS (must be hijack/injection/extract) =====")
    for i, s in enumerate(attacks, 1):
        print(f"\n[{i}] source={s.source} id={s.sample_id}")
        print(s.text.replace("\n", " ")[:240])

    print("\n===== PREVIEW SAFE (Tensor Trust access_code phrases) =====")
    for i, s in enumerate(safes, 1):
        print(f"[{i}] id={s.sample_id} :: {s.text.replace(chr(10), ' ')[:160]}")


def post_chat(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    prompt: str,
    max_tokens: int,
) -> tuple[int, dict | None, int]:
    t0 = time.perf_counter()
    resp = client.post(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    try:
        body = resp.json()
    except Exception:
        body = None
    return resp.status_code, body, latency_ms


def run_batch(
    client: httpx.Client,
    samples: list[Sample],
    *,
    base_url: str,
    api_key: str,
    max_tokens: int,
    pace_seconds: float,
    out_f,
) -> list[TrialResult]:
    results: list[TrialResult] = []
    for i, sample in enumerate(samples, start=1):
        status, body, latency_ms = post_chat(
            client,
            base_url=base_url,
            api_key=api_key,
            prompt=sample.text,
            max_tokens=max_tokens,
        )
        blocked = status == 400
        layer = body.get("layer") if isinstance(body, dict) else None
        reason = body.get("reason") if isinstance(body, dict) else None
        trial = TrialResult(
            kind=sample.kind,
            source=sample.source,
            sample_id=sample.sample_id,
            status=status,
            blocked=blocked,
            layer=layer if isinstance(layer, int) else None,
            reason=str(reason) if reason is not None else None,
            latency_ms=latency_ms,
            preview=sample.text.replace("\n", " ")[:160],
        )
        results.append(trial)
        out_f.write(json.dumps(asdict(trial)) + "\n")
        out_f.flush()
        flag = "BLOCK" if blocked else "allow"
        print(
            f"[{sample.kind} {i}/{len(samples)}] {sample.source} "
            f"{flag} status={status} layer={trial.layer} {latency_ms}ms"
        )
        if i < len(samples) and pace_seconds > 0:
            time.sleep(pace_seconds)
    return results


def summarize(results: list[TrialResult]) -> None:
    attacks = [r for r in results if r.kind == "attack"]
    safes = [r for r in results if r.kind == "safe"]
    ab = sum(1 for r in attacks if r.blocked)
    sb = sum(1 for r in safes if r.blocked)
    print("\n========== TENSOR TRUST DRY RUN ==========")
    print(f"attacks: {ab}/{len(attacks)} blocked  detection_rate={ab/len(attacks):.1%}")
    print(f"safe:    {sb}/{len(safes)} blocked  false_positive_rate={sb/len(safes):.1%}")
    lat = [r.latency_ms for r in results]
    print(
        f"client latency: median={statistics.median(lat):.0f}ms "
        f"p95={sorted(lat)[int(0.95*(len(lat)-1))]:.0f}ms"
    )
    by: dict[str, int] = {}
    for r in attacks:
        key = "miss" if not r.blocked else f"layer_{r.layer}"
        by[key] = by.get(key, 0) + 1
    print("attack outcomes:", by)

    misses = [r for r in attacks if not r.blocked]
    if misses:
        print("\nMissed attacks:")
        for r in misses[:8]:
            print(f"  [{r.source}/{r.sample_id}] {r.preview[:140]!r}")
    fps = [r for r in safes if r.blocked]
    if fps:
        print("\nFalse positives:")
        for r in fps[:8]:
            print(f"  [{r.sample_id}] layer={r.layer} {r.preview[:140]!r}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--preview-only", action="store_true")
    p.add_argument("--base-url", default=os.getenv("PROMPTSENTRY_BASE_URL", "http://localhost:8000"))
    p.add_argument(
        "--api-key",
        default=os.getenv("PROMPTSENTRY_API_KEYS", "").split(",")[0].strip(),
    )
    p.add_argument("--pace-seconds", type=float, default=3.5)
    p.add_argument("--max-tokens", type=int, default=16)
    p.add_argument("--samples-out", default="eval/tensor_trust_samples.json")
    p.add_argument("--out", default="eval/tensor_trust_results.jsonl")
    args = p.parse_args()

    print("Loading Tensor Trust hijack + extract benches…")
    attacks = load_attack_samples(args.limit)
    safes = load_safe_samples(args.limit)
    print(
        f"Selected attacks={len(attacks)} "
        f"(hijack={sum(1 for s in attacks if s.source=='hijack')}, "
        f"extract={sum(1 for s in attacks if s.source=='extract')}) "
        f"safe={len(safes)}"
    )

    payload = {
        "attacks": [asdict(s) for s in attacks],
        "safe": [asdict(s) for s in safes],
        "sources": {
            "hijack": HIJACK_URL,
            "extract": EXTRACT_URL,
            "safe": "access_code fields from the same two JSONL files",
        },
    }
    os.makedirs(os.path.dirname(args.samples_out) or ".", exist_ok=True)
    with open(args.samples_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote sample pack to {args.samples_out}")

    preview_samples(attacks, safes)

    if args.preview_only:
        print("\n(--preview-only) Not sending to the proxy.")
        return

    if not args.api_key:
        raise SystemExit("Missing PROMPTSENTRY_API_KEYS")

    print(f"\nSending to {args.base_url} …")
    results: list[TrialResult] = []
    with httpx.Client(timeout=120.0) as client, open(args.out, "w", encoding="utf-8") as out_f:
        results.extend(
            run_batch(
                client,
                attacks,
                base_url=args.base_url,
                api_key=args.api_key,
                max_tokens=args.max_tokens,
                pace_seconds=args.pace_seconds,
                out_f=out_f,
            )
        )
        if args.pace_seconds > 0:
            time.sleep(args.pace_seconds)
        results.extend(
            run_batch(
                client,
                safes,
                base_url=args.base_url,
                api_key=args.api_key,
                max_tokens=args.max_tokens,
                pace_seconds=args.pace_seconds,
                out_f=out_f,
            )
        )

    summarize(results)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
