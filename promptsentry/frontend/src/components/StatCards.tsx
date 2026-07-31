"use client";

type Card = {
  label: string;
  value: string | number;
  hint: string;
  tone: "neutral" | "crit" | "ok" | "info" | "warn";
};

const toneAccent: Record<Card["tone"], string> = {
  neutral: "from-white/10",
  crit: "from-[var(--crit)]/40",
  ok: "from-[var(--ok)]/40",
  info: "from-[var(--info)]/40",
  warn: "from-[var(--warn)]/40",
};

const toneValue: Record<Card["tone"], string> = {
  neutral: "text-[var(--text)]",
  crit: "text-[var(--crit)]",
  ok: "text-[var(--ok)]",
  info: "text-[var(--info)]",
  warn: "text-[var(--warn)]",
};

type Props = {
  cards: Card[];
  compact?: boolean;
};

export function StatCards({ cards, compact = false }: Props) {
  return (
    <div className="grid shrink-0 gap-2 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`surface surface-hover fade-up relative overflow-hidden rounded-xl ${
            compact ? "px-3 py-2.5" : "px-4 py-4"
          } fade-up-delay-${Math.min(i + 1, 3)}`}
        >
          <div
            className={`pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r ${toneAccent[card.tone]} via-transparent to-transparent`}
          />
          <div className="text-[9px] font-medium tracking-[0.16em] text-[var(--muted)] uppercase">
            {card.label}
          </div>
          <div
            className={`mt-1.5 font-[family-name:var(--font-display)] leading-none tracking-[-0.04em] tabular-nums ${
              compact ? "text-[1.45rem]" : "text-[2rem]"
            } ${toneValue[card.tone]}`}
          >
            {card.value}
          </div>
          {!compact ? (
            <div className="mt-2 text-[11px] leading-snug text-[var(--muted)]">{card.hint}</div>
          ) : (
            <div className="mt-1 truncate text-[10px] text-[var(--muted)]">{card.hint}</div>
          )}
        </div>
      ))}
    </div>
  );
}
