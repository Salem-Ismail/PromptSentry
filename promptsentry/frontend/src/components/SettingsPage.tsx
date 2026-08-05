"use client";

type Props = {
  apiKey: string;
  onApiKeyChange: (value: string) => void;
  healthy: boolean | null;
  total: number;
};

export function SettingsPage({ apiKey, onApiKeyChange, healthy, total }: Props) {
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <section className="surface rounded-xl p-5">
        <h3 className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)]">
          API access
        </h3>
        <p className="mt-1 text-[12px] text-[var(--muted)]">
          PromptSentry bearer key (stored in this browser’s localStorage only)
        </p>
        <label className="mt-4 flex flex-col gap-2">
          <span className="text-[12px] tracking-[0.14em] text-[var(--muted)] uppercase">
            Bearer key
          </span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder="Paste PROMPTSENTRY_API_KEYS value"
            className="rounded-lg border border-[var(--border)] bg-black/25 px-3 py-2.5 font-mono text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]/40"
          />
        </label>
        <button
          type="button"
          onClick={() => onApiKeyChange("")}
          className="mt-3 text-[12px] text-[var(--muted)] underline-offset-2 hover:text-[var(--text-dim)] hover:underline"
        >
          Clear saved key
        </button>
      </section>

      <section className="surface rounded-xl p-5">
        <h3 className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)]">
          Runtime status
        </h3>
        <dl className="mt-3 space-y-2 text-[13px]">
          <div className="flex justify-between gap-4">
            <dt className="text-[var(--muted)]">API health</dt>
            <dd className="font-mono text-[var(--text)]">
              {healthy === null ? "…" : healthy ? "ok" : "unreachable"}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-[var(--muted)]">Audit rows (your key)</dt>
            <dd className="font-mono text-[var(--text)]">{total}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-[var(--muted)]">Dashboard poll</dt>
            <dd className="font-mono text-[var(--text)]">5s → /admin/logs</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-[var(--muted)]">API base</dt>
            <dd className="truncate font-mono text-[12px] text-[var(--text-dim)]">
              {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}
            </dd>
          </div>
        </dl>
      </section>

      <section className="surface rounded-xl p-5">
        <h3 className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)]">
          Pipeline
        </h3>
        <ol className="mt-3 list-decimal space-y-1.5 pl-4 text-[12px] text-[var(--text-dim)]">
          <li>API key + Redis rate limit</li>
          <li>Layer 1 intent regex (block → 400)</li>
          <li>Presidio input redact (always continue)</li>
          <li>Layer 2 LLM judge (block → 400)</li>
          <li>Forward redacted body to OpenAI</li>
          <li>Audit scrubbed prompt to Postgres</li>
        </ol>
      </section>
    </div>
  );
}
