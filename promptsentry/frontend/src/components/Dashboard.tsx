"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchHealth, fetchLogs } from "@/lib/api";
import type { RequestLog } from "@/lib/types";
import { LiveFeed } from "./LiveFeed";
import { OverviewCharts } from "./OverviewCharts";
import { PoliciesPage } from "./PoliciesPage";
import { SettingsPage } from "./SettingsPage";
import { Sidebar } from "./Sidebar";
import { StatCards } from "./StatCards";
import { ThreatsPage } from "./ThreatsPage";
import { TopBar } from "./TopBar";

const STORAGE_KEY = "promptsentry_api_key";
const POLL_MS = 5000;

const TITLES: Record<string, { eyebrow: string; title: string }> = {
  dashboard: { eyebrow: "Overview", title: "Gateway dashboard" },
  feed: { eyebrow: "Operations", title: "Live Feed" },
  threats: { eyebrow: "Detection", title: "Threats" },
  policies: { eyebrow: "Configuration", title: "Policies" },
  settings: { eyebrow: "Console", title: "Settings" },
};

export function Dashboard() {
  const [active, setActive] = useState("dashboard");
  const [apiKey, setApiKey] = useState("");
  const [logs, setLogs] = useState<RequestLog[]>([]);
  const [total, setTotal] = useState(0);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<string | null>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) setApiKey(saved);
  }, []);

  const persistKey = (value: string) => {
    setApiKey(value);
    if (value) window.localStorage.setItem(STORAGE_KEY, value);
    else window.localStorage.removeItem(STORAGE_KEY);
  };

  const refresh = useCallback(async () => {
    const ok = await fetchHealth();
    setHealthy(ok);

    if (!apiKey.trim()) {
      setError("Paste your PromptSentry API key in the top bar or Settings.");
      return;
    }

    try {
      const data = await fetchLogs(apiKey.trim(), 50);
      setLogs(data.logs);
      setTotal(data.total);
      setError(null);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load logs");
    }
  }, [apiKey]);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), POLL_MS);
    return () => window.clearInterval(id);
  }, [refresh]);

  const stats = useMemo(() => {
    const blocked = logs.filter((l) => l.flagged).length;
    const allowed = logs.length - blocked;
    const layer1 = logs.filter((l) => l.layer === 1).length;
    const layer2 = logs.filter((l) => l.layer === 2).length;
    const piiish = logs.filter((l) => l.prompt && /\[[A-Z_]+\]/.test(l.prompt)).length;

    return [
      {
        label: "Total logged",
        value: total,
        hint: "For your API key",
        tone: "info" as const,
      },
      {
        label: "Blocked (page)",
        value: blocked,
        hint: `L1 ${layer1} · L2 ${layer2} in last ${logs.length}`,
        tone: "crit" as const,
      },
      {
        label: "Allowed (page)",
        value: allowed,
        hint: "In current poll window",
        tone: "ok" as const,
      },
      {
        label: "PII tokens seen",
        value: piiish,
        hint: "Prompts containing [PHONE]/[IP]/…",
        tone: "warn" as const,
      },
    ];
  }, [logs, total]);

  const heading = TITLES[active] ?? TITLES.dashboard;

  return (
    <div className="flex h-screen overflow-hidden text-[var(--text)]">
      <Sidebar active={active} onNavigate={setActive} />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <TopBar
          healthy={healthy}
          apiKey={apiKey}
          onApiKeyChange={persistKey}
          lastRefresh={lastRefresh}
        />

        <main
          className={
            active === "dashboard"
              ? "flex min-h-0 flex-1 flex-col gap-2.5 overflow-hidden px-5 py-3"
              : "flex-1 space-y-4 overflow-auto px-6 py-5"
          }
        >
          <div className="fade-up flex shrink-0 items-baseline justify-between gap-3">
            <div>
              {active !== "dashboard" ? (
                <p className="text-[12px] font-medium tracking-[0.2em] text-[var(--muted)] uppercase">
                  {heading.eyebrow}
                </p>
              ) : null}
              <h1
                className={`font-[family-name:var(--font-display)] tracking-[-0.03em] text-[var(--text)] ${
                  active === "dashboard" ? "text-lg" : "mt-1 text-2xl"
                }`}
              >
                {heading.title}
              </h1>
            </div>
            {active === "dashboard" ? (
              <p className="hidden text-[12px] tracking-wide text-[var(--muted)] sm:block">
                Poll-derived. Live Feed for full table.
              </p>
            ) : null}
          </div>

          {error ? (
            <div className="shrink-0 rounded-xl border border-[var(--crit)]/30 bg-[var(--crit-dim)] px-4 py-2.5 text-sm text-[var(--crit)]">
              {error}
            </div>
          ) : null}

          {active === "dashboard" && (
            <>
              <StatCards cards={stats} compact />
              <OverviewCharts logs={logs} />
              <LiveFeed
                logs={logs.slice(0, 6)}
                flaggedOnly={false}
                compact
                fill
                title="Recent events"
                subtitle="Latest from poll"
              />
            </>
          )}

          {active === "feed" && (
            <LiveFeed logs={logs} flaggedOnly={false} />
          )}

          {active === "threats" && <ThreatsPage logs={logs} />}

          {active === "policies" && <PoliciesPage />}

          {active === "settings" && (
            <SettingsPage
              apiKey={apiKey}
              onApiKeyChange={persistKey}
              healthy={healthy}
              total={total}
            />
          )}
        </main>
      </div>
    </div>
  );
}
