"use client";

import {
  LAYER1_RULES,
  LAYER2_NOT,
  LAYER2_SCOPE,
  PII_ENTITIES,
  PII_OUT_OF_SCOPE,
} from "@/lib/scanConfig";

export function PoliciesPage() {
  return (
    <div className="space-y-4">
      <p className="max-w-2xl text-[14px] leading-relaxed text-[var(--muted)]">
        Read-only view of what PromptSentry scans for. Rules live in the API (
        <span className="font-mono text-[var(--text-dim)]">rule_engine.py</span>,{" "}
        <span className="font-mono text-[var(--text-dim)]">pii.py</span>,{" "}
        <span className="font-mono text-[var(--text-dim)]">llm_judge.py</span>
        ). This page does not edit them.
      </p>

      <section className="surface rounded-xl p-5">
        <h3 className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)]">
          Layer 1 - intent regex
        </h3>
        <p className="mt-1 text-[13px] text-[var(--muted)]">
          High-precision only. Topic words like &quot;jailbreak&quot; alone do not block.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-[var(--border)] text-[12px] tracking-[0.14em] text-[var(--muted)] uppercase">
              <tr>
                <th className="py-2 pr-4 font-medium">ID</th>
                <th className="py-2 pr-4 font-medium">Threat</th>
                <th className="py-2 font-medium">Match summary</th>
              </tr>
            </thead>
            <tbody>
              {LAYER1_RULES.map((r) => (
                <tr key={r.id} className="border-t border-[var(--border)]">
                  <td className="py-2.5 pr-4 font-mono text-[12px] text-[var(--accent)]">{r.id}</td>
                  <td className="py-2.5 pr-4 font-mono text-[12px] text-[var(--crit)]">{r.threat}</td>
                  <td className="py-2.5 text-[13px] text-[var(--text-dim)]">{r.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-3 lg:grid-cols-2">
        <section className="surface rounded-xl p-5">
          <h3 className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)]">
            Layer 2 - LLM judge
          </h3>
          <p className="mt-1 text-[13px] text-[var(--muted)]">
            gpt-4o-mini · JSON · confidence &gt; 0.7 · redacted prompt only
          </p>
          <ul className="mt-3 space-y-1.5 text-[13px] text-[var(--text-dim)]">
            {LAYER2_SCOPE.map((s) => (
              <li key={s}>● {s}</li>
            ))}
          </ul>
          <p className="mt-3 text-[12px] tracking-wide text-[var(--muted)] uppercase">Out of scope</p>
          <ul className="mt-1.5 space-y-1 text-[12px] text-[var(--muted)]">
            {LAYER2_NOT.map((s) => (
              <li key={s}>· {s}</li>
            ))}
          </ul>
        </section>

        <section className="surface rounded-xl p-5">
          <h3 className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)]">
            Input PII - Presidio
          </h3>
          <p className="mt-1 text-[13px] text-[var(--muted)]">
            Pattern entities · redact-and-continue
          </p>
          <ul className="mt-3 space-y-1.5 font-mono text-[13px] text-[var(--warn)]">
            {PII_ENTITIES.map((e) => (
              <li key={e.entity}>
                {e.token}{" "}
                <span className="text-[var(--muted)]">{"<-"} {e.entity}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[12px] tracking-wide text-[var(--muted)] uppercase">Not scrubbed</p>
          <ul className="mt-1.5 space-y-1 text-[12px] text-[var(--muted)]">
            {PII_OUT_OF_SCOPE.map((s) => (
              <li key={s}>· {s}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
