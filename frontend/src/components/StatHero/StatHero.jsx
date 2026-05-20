import { formatLargeNumber, useCountUp } from "../../hooks/useCountUp.js";

export default function StatHero({ label, value, sub, accent }) {
  const counted = useCountUp(value, 1200);
  return (
    <div className="stat-hero" style={{ "--accent": accent ?? "var(--f1-red)" }}>
      <div className="stat-hero-value">{formatLargeNumber(counted)}</div>
      <div className="stat-hero-label">{label}</div>
      {sub && <div className="stat-hero-sub">{sub}</div>}
    </div>
  );
}

export function StatStrip({ items, status }) {
  return (
    <div className="stat-strip">
      {items.map((it) => (
        <StatHero
          key={it.label}
          label={it.label}
          value={it.value}
          sub={it.sub}
          accent={it.accent}
        />
      ))}
      {status && (
        <span className="stat-strip-source">data source: {status}</span>
      )}
    </div>
  );
}
