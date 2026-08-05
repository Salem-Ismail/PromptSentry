"use client";

import { Fragment, useState } from "react";
import type { RequestLog } from "@/lib/types";

type Props = {
  logs: RequestLog[];
  flaggedOnly?: boolean;
  title?: string;
  subtitle?: string;
  /** denser rows + shorter chrome for one-screen dashboard */
  compact?: boolean;
  /** fill remaining flex space; table body scrolls inside if needed */
  fill?: boolean;
};

function actionFor(log: RequestLog): { label: string; className: string } {
  if (log.flagged) {
    if (log.threat_type === "rate_limit") {
      return { label: "rate limited", className: "bg-[var(--warn-dim)] text-[var(--warn)]" };
    }
    return { label: "blocked", className: "bg-[var(--crit-dim)] text-[var(--crit)]" };
  }
  if (log.prompt && /\[[A-Z_]+\]/.test(log.prompt)) {
    return { label: "sanitized", className: "bg-[var(--warn-dim)] text-[var(--warn)]" };
  }
  return { label: "allowed", className: "bg-[var(--ok-dim)] text-[var(--ok)]" };
}

function typeLabel(log: RequestLog): string {
  if (log.threat_type) return log.threat_type;
  if (log.prompt && /\[[A-Z_]+\]/.test(log.prompt)) return "pii_redacted";
  return "clean";
}

function formatTime(ts: string | null, compact: boolean): string {
  if (!ts) return "-";
  try {
    const d = new Date(ts);
    return compact ? d.toLocaleTimeString() : d.toLocaleString();
  } catch {
    return ts;
  }
}

export function LiveFeed({
  logs,
  flaggedOnly = false,
  title = "Live threat feed",
  subtitle = "Newest first · expands show stored prompt (already scrubbed)",
  compact = false,
  fill = false,
}: Props) {
  const [openId, setOpenId] = useState<number | null>(null);
  const rows = flaggedOnly ? logs.filter((l) => l.flagged) : logs;
  const cellY = compact ? "py-1.5" : "py-3";

  return (
    <div
      className={[
        "surface fade-up flex min-h-0 flex-col overflow-hidden rounded-xl",
        fill ? "flex-1" : "",
      ].join(" ")}
    >
      <div
        className={`flex shrink-0 items-center justify-between border-b border-[var(--border)] ${
          compact ? "px-4 py-2" : "px-5 py-4"
        }`}
      >
        <div>
          <h2
            className={`font-[family-name:var(--font-display)] tracking-tight text-[var(--text)] ${
              compact ? "text-[14px]" : "text-[17px]"
            }`}
          >
            {title}
          </h2>
          {!compact ? (
            <p className="mt-0.5 text-[12px] tracking-wide text-[var(--muted)]">{subtitle}</p>
          ) : null}
        </div>
        <span className="rounded-full border border-[var(--border)] bg-white/[0.02] px-2 py-0.5 font-mono text-[12px] tracking-wide text-[var(--muted)]">
          {rows.length}
        </span>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 border-b border-[var(--border)] bg-[var(--panel-solid)] text-[12px] tracking-[0.14em] text-[var(--muted)] uppercase">
            <tr>
              <th className={`px-4 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Time</th>
              <th className={`px-3 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Source</th>
              <th className={`px-3 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Type</th>
              <th className={`px-3 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Layer</th>
              <th className={`px-3 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Action</th>
              <th className={`px-3 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Latency</th>
              <th className={`px-3 ${compact ? "py-1.5" : "py-2.5"} font-medium`}>Prompt</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-8 text-center text-[13px] text-[var(--muted)]">
                  No events yet. Hit the proxy, then wait for the next poll.
                </td>
              </tr>
            ) : (
              rows.map((log) => {
                const action = actionFor(log);
                const open = openId === log.id;
                return (
                  <Fragment key={log.id}>
                    <tr
                      onClick={() => setOpenId(open ? null : log.id)}
                      className={[
                        "cursor-pointer border-t border-[var(--border)] transition-colors hover:bg-white/[0.025]",
                        log.flagged ? "bg-[var(--crit-dim)]/40" : "",
                      ].join(" ")}
                    >
                      <td
                        className={`whitespace-nowrap px-4 ${cellY} font-mono text-[12px] text-[var(--text-dim)]`}
                      >
                        {formatTime(log.timestamp, compact)}
                      </td>
                      <td className={`px-3 ${cellY} font-mono text-[12px] text-[var(--text-dim)]`}>
                        {log.ip_address || "-"}
                      </td>
                      <td className={`px-3 ${cellY}`}>
                        <span className="rounded-md border border-[var(--border)] bg-white/[0.02] px-1.5 py-0.5 font-mono text-[12px] text-[var(--text-dim)]">
                          {typeLabel(log)}
                        </span>
                      </td>
                      <td className={`px-3 ${cellY} font-mono text-[12px] text-[var(--muted)]`}>
                        {log.layer ?? "-"}
                      </td>
                      <td className={`px-3 ${cellY}`}>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[12px] font-medium tracking-wide ${action.className}`}
                        >
                          {action.label}
                        </span>
                      </td>
                      <td
                        className={`px-3 ${cellY} font-mono text-[12px] tabular-nums text-[var(--muted)]`}
                      >
                        {log.latency_ms != null ? `${log.latency_ms}ms` : "-"}
                      </td>
                      <td
                        className={`max-w-[22rem] truncate px-3 ${cellY} font-mono text-[12px] text-[var(--text-dim)]`}
                      >
                        {log.prompt || "-"}
                      </td>
                    </tr>
                    {open ? (
                      <tr className="border-t border-[var(--border)] bg-black/25">
                        <td colSpan={7} className="px-4 py-3">
                          <div className="text-[12px] tracking-[0.14em] text-[var(--muted)] uppercase">
                            Stored prompt
                          </div>
                          <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3 font-mono text-[12px] leading-relaxed text-[var(--text)]">
                            {log.prompt || "(empty)"}
                          </pre>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
