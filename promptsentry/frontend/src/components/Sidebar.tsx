"use client";

const NAV = [
  { id: "dashboard", label: "Dashboard", soon: false },
  { id: "feed", label: "Live Feed", soon: false },
  { id: "threats", label: "Threats", soon: true },
  { id: "pii", label: "PII Log", soon: true },
  { id: "policies", label: "Policies", soon: true },
  { id: "analytics", label: "Analytics", soon: true },
  { id: "settings", label: "Settings", soon: true },
] as const;

type Props = {
  active: string;
  onNavigate: (id: string) => void;
};

export function Sidebar({ active, onNavigate }: Props) {
  return (
    <aside className="flex w-[9.5rem] shrink-0 flex-col border-r border-[var(--border)] bg-[rgba(8,12,18,0.92)] backdrop-blur-xl">
      <div className="border-b border-[var(--border)] px-3.5 py-4">
        <div className="font-[family-name:var(--font-display)] text-[1.15rem] leading-[1.1] tracking-[-0.03em] text-[var(--text)]">
          Prompt
          <span className="text-[var(--accent)]">Sentry</span>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 p-2">
        {NAV.map((item) => {
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              type="button"
              disabled={item.soon}
              onClick={() => onNavigate(item.id)}
              className={[
                "relative flex items-center justify-between rounded-md px-2.5 py-2 text-left text-[12.5px] tracking-wide transition-colors",
                isActive
                  ? "bg-[var(--accent-dim)] text-[var(--accent)]"
                  : "text-[var(--muted)] hover:bg-white/[0.03] hover:text-[var(--text-dim)]",
                item.soon ? "cursor-not-allowed opacity-40" : "",
              ].join(" ")}
            >
              {isActive ? (
                <span className="absolute top-1/2 left-0 h-4 w-[2px] -translate-y-1/2 rounded-r bg-[var(--accent)]" />
              ) : null}
              <span>{item.label}</span>
              {item.soon ? (
                <span className="rounded px-1 py-0.5 text-[8px] uppercase tracking-[0.12em] text-[var(--muted)]">
                  soon
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] px-3 py-3 text-[10px] tracking-wide text-[var(--muted)]">
        <span className="font-mono text-[var(--text-dim)]/70">/admin/logs</span>
      </div>
    </aside>
  );
}
