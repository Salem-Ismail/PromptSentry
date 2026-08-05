"""
Dry-run eval: JailbreakBench PAIR jailbreak *prompts* vs benign Behaviors.

Metric (PromptSentry firewall):
  hit  = HTTP 400 request_blocked
  miss = anything else (usually 200) — even if OpenAI would refuse

Usage (from promptsentry/):
  python3 -m venv .venv-eval && source .venv-eval/bin/activate
  pip install -r eval/requirements.txt
  set -a && source .env && set +a
  python eval/dry_run_jbb.py --limit 20

Tips:
  - API must be up: docker compose up -d
  - RATE_LIMIT_PER_MINUTE defaults to 20; this script paces requests (~3.5s)
  - Expect ~1s+ per L1-clear prompt (Layer 2 judge call)
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.request
from dataclasses import asdict, dataclass

import httpx
from datasets import load_dataset

PAIR_ARTIFACT_URL = (
    "https://raw.githubusercontent.com/JailbreakBench/artifacts/main/"
    "attack-artifacts/PAIR/black_box/vicuna-13b-v1.5.json"
)


@dataclass
class TrialResult:
    kind: str  # "attack" | "benign"
    index: int
    status: int
    blocked: bool
    layer: int | None
    reason: str | None
    latency_ms: int
    preview: str


def load_attack_prompts(limit: int) -> list[tuple[int, str]]:
    """Successful PAIR jailbreak strings from the official artifacts repo."""
    with urllib.request.urlopen(PAIR_ARTIFACT_URL, timeout=120) as resp:
        data = json.load(resp)

    chosen: list[tuple[int, str]] = []
    for row in data["jailbreaks"]:
        if not row.get("jailbroken"):
            continue
        prompt = row.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            continue
        chosen.append((int(row["index"]), prompt.strip()))
        if len(chosen) >= limit:
            break

    if len(chosen) < limit:
        raise RuntimeError(
            f"Only found {len(chosen)} jailbroken PAIR prompts; need {limit}."
        )
    return chosen


def load_benign_prompts(limit: int) -> list[tuple[int, str]]:
    """Thematically related but benign Goals from JBB-Behaviors."""
    ds = load_dataset("JailbreakBench/JBB-Behaviors", "behaviors")
    benign = ds["benign"]
    out: list[tuple[int, str]] = []
    for i in range(min(limit, len(benign))):
        goal = benign[i]["Goal"]
        out.append((int(benign[i]["Index"]), str(goal).strip()))
    return out


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


def summarize(results: list[TrialResult]) -> None:
    attacks = [r for r in results if r.kind == "attack"]
    benign = [r for r in results if r.kind == "benign"]

    attacks_blocked = sum(1 for r in attacks if r.blocked)
    clean_blocked = sum(1 for r in benign if r.blocked)

    n_a = len(attacks)
    n_b = len(benign)
    detection = attacks_blocked / n_a if n_a else 0.0
    fpr = clean_blocked / n_b if n_b else 0.0

    print("\n========== DRY RUN SUMMARY ==========")
    print(f"attacks: {attacks_blocked}/{n_a} blocked  detection_rate={detection:.1%}")
    print(f"benign:  {clean_blocked}/{n_b} blocked  false_positive_rate={fpr:.1%}")

    lat = [r.latency_ms for r in results]
    print(
        f"client latency: median={statistics.median(lat):.0f}ms "
        f"p95={sorted(lat)[int(0.95 * (len(lat) - 1))]:.0f}ms"
    )

    by_layer: dict[str, int] = {}
    for r in attacks:
        if not r.blocked:
            key = "miss"
        else:
            key = f"layer_{r.layer}" if r.layer is not None else "layer_?"
        by_layer[key] = by_layer.get(key, 0) + 1
    print("attack outcomes:", by_layer)

    misses = [r for r in attacks if not r.blocked]
    if misses:
        print("\nMissed attacks (preview):")
        for r in misses[:5]:
            print(f"  [{r.index}] {r.preview[:120]!r}")

    fps = [r for r in benign if r.blocked]
    if fps:
        print("\nFalse positives (preview):")
        for r in fps[:5]:
            print(
                f"  [{r.index}] layer={r.layer} reason={r.reason} {r.preview[:120]!r}"
            )


def run_batch(
    client: httpx.Client,
    *,
    kind: str,
    items: list[tuple[int, str]],
    base_url: str,
    api_key: str,
    max_tokens: int,
    pace_seconds: float,
    out_f,
) -> list[TrialResult]:
    results: list[TrialResult] = []
    for i, (idx, prompt) in enumerate(items, start=1):
        status, body, latency_ms = post_chat(
            client,
            base_url=base_url,
            api_key=api_key,
            prompt=prompt,
            max_tokens=max_tokens,
        )
        blocked = status == 400
        # prefer our structured block body when present
        if status == 400 and isinstance(body, dict) and body.get("error") == "request_blocked":
            blocked = True

        layer = body.get("layer") if isinstance(body, dict) else None
        reason = body.get("reason") if isinstance(body, dict) else None
        trial = TrialResult(
            kind=kind,
            index=idx,
            status=status,
            blocked=blocked,
            layer=layer if isinstance(layer, int) else None,
            reason=str(reason) if reason is not None else None,
            latency_ms=latency_ms,
            preview=prompt.replace("\n", " ")[:160],
        )
        results.append(trial)
        out_f.write(json.dumps(asdict(trial)) + "\n")
        out_f.flush()

        flag = "BLOCK" if trial.blocked else "allow"
        print(
            f"[{kind} {i}/{len(items)}] idx={idx} {flag} "
            f"status={status} layer={trial.layer} {latency_ms}ms"
        )

        if i < len(items) and pace_seconds > 0:
            time.sleep(pace_seconds)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="PromptSentry JBB dry-run eval")
    parser.add_argument("--limit", type=int, default=20, help="per class (attack/benign)")
    parser.add_argument(
        "--base-url",
        default=os.getenv("PROMPTSENTRY_BASE_URL", "http://localhost:8000"),
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("PROMPTSENTRY_API_KEYS", "").split(",")[0].strip(),
    )
    parser.add_argument(
        "--pace-seconds",
        type=float,
        default=3.5,
        help="sleep between requests to respect rate limit (20/min default)",
    )
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument(
        "--out",
        default="eval/dry_run_results.jsonl",
        help="write per-trial JSONL here",
    )
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit(
            "Missing API key. Export PROMPTSENTRY_API_KEYS from promptsentry/.env"
        )

    print(f"Loading up to {args.limit} PAIR jailbreaks + {args.limit} benign Goals…")
    attacks = load_attack_prompts(args.limit)
    benign = load_benign_prompts(args.limit)
    print(f"Loaded attacks={len(attacks)} benign={len(benign)}")
    print(f"Target {args.base_url}  pace={args.pace_seconds}s")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    results: list[TrialResult] = []
    with httpx.Client(timeout=120.0) as client, open(args.out, "w", encoding="utf-8") as out_f:
        results.extend(
            run_batch(
                client,
                kind="attack",
                items=attacks,
                base_url=args.base_url,
                api_key=args.api_key,
                max_tokens=args.max_tokens,
                pace_seconds=args.pace_seconds,
                out_f=out_f,
            )
        )
        # small gap between classes
        if args.pace_seconds > 0:
            time.sleep(args.pace_seconds)
        results.extend(
            run_batch(
                client,
                kind="benign",
                items=benign,
                base_url=args.base_url,
                api_key=args.api_key,
                max_tokens=args.max_tokens,
                pace_seconds=args.pace_seconds,
                out_f=out_f,
            )
        )

    summarize(results)
    print(f"\nWrote per-trial rows to {args.out}")


if __name__ == "__main__":
    main()
