"use client";

type Props = {
  healthy: boolean | null;
  apiKey: string;
  onApiKeyChange: (value: string) => void;
  lastRefresh: string | null;
};

export function TopBar({ healthy, apiKey, onApiKeyChange, lastRefresh }: Props) {
  const statusLabel =
    healthy === null ? "Checking…" : healthy ? "Firewall Active" : "API unreachable";
  const statusClass =
    healthy === null
      ? "bg-[var(--info-dim)] text-[var(--info)] border-[var(--info)]/20"
      : healthy
        ? "bg-[var(--ok-dim)] text-[var(--ok)] border-[var(--ok)]/20"
        : "bg-[var(--crit-dim)] text-[var(--crit)] border-[var(--crit)]/20";
  const dotClass =
    healthy === null
      ? "bg-[var(--info)]"
      : healthy
        ? "bg-[var(--ok)]"
        : "bg-[var(--crit)]";

  return (
    <header className="flex shrink-0 flex-wrap items-center gap-3 border-b border-[var(--border)] bg-[rgba(10,14,20,0.65)] px-5 py-2.5 backdrop-blur-xl">
      <div className="flex items-center gap-2">
        <span className="rounded-md border border-[var(--border)] bg-white/[0.02] px-2.5 py-1 text-[11px] tracking-[0.08em] text-[var(--muted)] uppercase">
          Local
        </span>
        <span
          className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium tracking-wide ${statusClass}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${dotClass} ${healthy ? "pulse-dot" : ""}`} />
          {statusLabel}
        </span>
      </div>

      <div className="ml-auto flex flex-wrap items-center gap-3">
        {lastRefresh ? (
          <span className="font-mono text-[10px] tracking-wide text-[var(--muted)]">
            sync {lastRefresh}
          </span>
        ) : null}
        <label className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-white/[0.02] px-3 py-1.5 transition focus-within:border-[var(--accent)]/40">
          <span className="text-[10px] tracking-[0.14em] text-[var(--muted)] uppercase">
            Key
          </span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder="••••••••"
            className="w-40 bg-transparent font-mono text-xs text-[var(--text)] outline-none placeholder:text-[var(--muted)]"
          />
        </label>
      </div>
    </header>
  );
}
