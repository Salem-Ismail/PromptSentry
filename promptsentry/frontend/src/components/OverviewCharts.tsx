"use client";

import { useMemo } from "react";
import type { RequestLog } from "@/lib/types";

type Props = {
  logs: RequestLog[];
};

type Slice = { label: string; count: number; color: string };

function Donut({ slices }: { slices: Slice[] }) {
  const total = slices.reduce((s, x) => s + x.count, 0) || 1;
  let angle = -90;
  const paths = slices.map((slice) => {
    const sweep = (slice.count / total) * 360;
    const start = angle;
    angle += sweep;
    const large = sweep > 180 ? 1 : 0;
    const r = 42;
    const cx = 50;
    const cy = 50;
    const toRad = (d: number) => (d * Math.PI) / 180;
    const x1 = cx + r * Math.cos(toRad(start));
    const y1 = cy + r * Math.sin(toRad(start));
    const x2 = cx + r * Math.cos(toRad(start + sweep));
    const y2 = cy + r * Math.sin(toRad(start + sweep));
    if (slice.count === 0) return null;
    // full circle edge case
    if (slice.count === total) {
      return (
        <circle
          key={slice.label}
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={slice.color}
          strokeWidth="14"
        />
      );
    }
    return (
      <path
        key={slice.label}
        d={`M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`}
        fill="none"
        stroke={slice.color}
        strokeWidth="14"
      />
    );
  });

  return (
    <div className="flex items-center gap-3">
      <svg viewBox="0 0 100 100" className="h-20 w-20 shrink-0">
        <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" />
        {paths}
        <text
          x="50"
          y="53"
          textAnchor="middle"
          className="fill-[var(--text)]"
          style={{ fontSize: "13px", fontFamily: "var(--font-ibm-mono)" }}
        >
          {slices.reduce((s, x) => s + x.count, 0)}
        </text>
      </svg>
      <ul className="space-y-1 text-[12px]">
        {slices.map((s) => (
          <li key={s.label} className="flex items-center gap-2 text-[var(--text-dim)]">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: s.color }} />
            <span className="min-w-14">{s.label}</span>
            <span className="font-mono text-[var(--text)]">{s.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Bars({ items }: { items: Slice[] }) {
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <div className="space-y-2">
      {items.length === 0 ? (
        <p className="text-[12px] text-[var(--muted)]">No threat types in this window.</p>
      ) : (
        items.map((item) => (
          <div key={item.label}>
            <div className="mb-0.5 flex justify-between text-[12px]">
              <span className="font-mono text-[var(--text-dim)]">{item.label}</span>
              <span className="font-mono text-[var(--text)]">{item.count}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${(item.count / max) * 100}%`,
                  background: item.color,
                }}
              />
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export function OverviewCharts({ logs }: Props) {
  const { outcome, threats, layers } = useMemo(() => {
    const blocked = logs.filter((l) => l.flagged).length;
    const allowed = logs.length - blocked;
    const outcome: Slice[] = [
      { label: "allowed", count: allowed, color: "#34d399" },
      { label: "blocked", count: blocked, color: "#fb7185" },
    ];

    const threatCounts = new Map<string, number>();
    for (const log of logs) {
      if (!log.flagged || !log.threat_type) continue;
      threatCounts.set(log.threat_type, (threatCounts.get(log.threat_type) || 0) + 1);
    }
    const threatColors = ["#fb7185", "#f59e0b", "#38bdf8", "#2dd4bf", "#a78bfa"];
    const threats: Slice[] = [...threatCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([label, count], i) => ({
        label,
        count,
        color: threatColors[i % threatColors.length],
      }));

    const l1 = logs.filter((l) => l.layer === 1).length;
    const l2 = logs.filter((l) => l.layer === 2).length;
    const layers: Slice[] = [
      { label: "layer 1", count: l1, color: "#f59e0b" },
      { label: "layer 2", count: l2, color: "#fb7185" },
    ];

    return { outcome, threats, layers };
  }, [logs]);

  return (
    <div className="grid shrink-0 gap-2 lg:grid-cols-3">
      <section className="surface fade-up fade-up-delay-1 rounded-xl p-3.5">
        <h3 className="font-[family-name:var(--font-display)] text-[13px] tracking-tight text-[var(--text)]">
          Outcomes
        </h3>
        <p className="mb-2.5 text-[12px] tracking-wide text-[var(--muted)]">
          Last {logs.length} polled events
        </p>
        <Donut slices={outcome} />
      </section>

      <section className="surface fade-up fade-up-delay-2 rounded-xl p-3.5">
        <h3 className="font-[family-name:var(--font-display)] text-[13px] tracking-tight text-[var(--text)]">
          Threat types
        </h3>
        <p className="mb-2.5 text-[12px] tracking-wide text-[var(--muted)]">
          Blocked only · current page
        </p>
        <Bars items={threats} />
      </section>

      <section className="surface fade-up fade-up-delay-3 rounded-xl p-3.5">
        <h3 className="font-[family-name:var(--font-display)] text-[13px] tracking-tight text-[var(--text)]">
          Catch layer
        </h3>
        <p className="mb-2.5 text-[12px] tracking-wide text-[var(--muted)]">Where blocks fired</p>
        <Bars items={layers} />
      </section>
    </div>
  );
}
