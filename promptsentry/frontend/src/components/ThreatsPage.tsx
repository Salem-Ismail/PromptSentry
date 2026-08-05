"use client";

import type { RequestLog } from "@/lib/types";
import { LAYER1_RULES, LAYER2_NOT, LAYER2_SCOPE } from "@/lib/scanConfig";
import { LiveFeed } from "./LiveFeed";

type Props = {
  logs: RequestLog[];
};

export function ThreatsPage({ logs }: Props) {
  const threats = logs.filter((l) => l.flagged);
  const byType = new Map<string, number>();
  const byLayer = new Map<string, number>();
  for (const t of threats) {
    const typ = t.threat_type || "unknown";
    byType.set(typ, (byType.get(typ) || 0) + 1);
    const layer = t.layer != null ? `L${t.layer}` : "-";
    byLayer.set(layer, (byLayer.get(layer) || 0) + 1);
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-3">
        <section className="surface rounded-xl p-4 lg:col-span-1">
          <h3 className="font-[family-name:var(--font-display)] text-[15px] text-[var(--text)]">
            What we block
          </h3>
          <p className="mt-1 text-[12px] text-[var(--muted)]">
            Threat model for L1 regex + L2 judge
          </p>
          <ul className="mt-3 space-y-1.5 text-[13px] text-[var(--text-dim)]">
            {LAYER2_SCOPE.map((s) => (
              <li key={s} className="flex gap-2">
                <span className="text-[var(--crit)]">●</span>
                {s}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[12px] uppercase tracking-wide text-[var(--muted)]">
            Not in scope
          </p>
          <ul className="mt-1.5 space-y-1 text-[12px] text-[var(--muted)]">
            {LAYER2_NOT.map((s) => (
              <li key={s}>· {s}</li>
            ))}
          </ul>
        </section>

        <section className="surface rounded-xl p-4">
          <h3 className="font-[family-name:var(--font-display)] text-[15px] text-[var(--text)]">
            By type (poll)
          </h3>
          <div className="mt-3 space-y-2">
            {[...byType.entries()].length === 0 ? (
              <p className="text-[13px] text-[var(--muted)]">No flagged rows in this window.</p>
            ) : (
              [...byType.entries()]
                .sort((a, b) => b[1] - a[1])
                .map(([k, v]) => (
                  <div key={k} className="flex justify-between font-mono text-[13px]">
                    <span className="text-[var(--text-dim)]">{k}</span>
                    <span className="text-[var(--crit)]">{v}</span>
                  </div>
                ))
            )}
          </div>
        </section>

        <section className="surface rounded-xl p-4">
          <h3 className="font-[family-name:var(--font-display)] text-[15px] text-[var(--text)]">
            By layer (poll)
          </h3>
          <div className="mt-3 space-y-2">
            {[...byLayer.entries()].length === 0 ? (
              <p className="text-[13px] text-[var(--muted)]">No flagged rows in this window.</p>
            ) : (
              [...byLayer.entries()].map(([k, v]) => (
                <div key={k} className="flex justify-between font-mono text-[13px]">
                  <span className="text-[var(--text-dim)]">{k}</span>
                  <span className="text-[var(--warn)]">{v}</span>
                </div>
              ))
            )}
          </div>
          <p className="mt-4 text-[12px] text-[var(--muted)]">
            L1 patterns: {LAYER1_RULES.length} intent regexes. See Policies.
          </p>
        </section>
      </div>

      <LiveFeed
        logs={threats}
        flaggedOnly
        title="Blocked / flagged events"
        subtitle="Flagged rows from the latest /admin/logs poll (your API key only)"
      />
    </div>
  );
}
