import { Link } from "react-router-dom";

import { SEASONS } from "../data/seasons.js";
import { useStats } from "../hooks/useStats.js";

export default function SeasonsPage() {
  const { data: stats } = useStats();
  const ingestedByYear = new Map(
    (stats?.season_breakdown ?? []).map((s) => [s.year, s])
  );

  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">SIX SEASONS</div>
        <div className="hero-title">Infinite endings.</div>
        <p className="hero-sub">
          Every Grand Prix from 2019 through 2024 - the Mercedes dynasty, the
          closest title fight in a generation, the ground-effect reset, and
          Verstappen's four-peat. Pick a year and start rewriting.
        </p>
      </div>

      <div className="seasons-grid">
        {SEASONS.map((s) => {
          const live = ingestedByYear.get(s.year);
          const ingested = live?.races ?? 0;
          const expected = live?.expected ?? s.rounds;
          const progress = Math.min(1, ingested / Math.max(expected, 1));
          return (
            <Link
              key={s.year}
              to={`/seasons/${s.year}`}
              className="season-card"
              style={{ "--accent": s.accent }}
            >
              <div className="season-card-head">
                <div className="season-card-year">{s.year}</div>
                <div className="season-card-icon">{s.icon}</div>
              </div>
              <div className="season-card-tagline">{s.tagline}</div>
              <div className="season-card-champion">
                <span className="driver-tag" style={{ background: `${s.accent}22`, color: s.accent }}>
                  {s.champion.code}
                </span>
                <div>
                  <div className="season-card-champ-name">{s.champion.name}</div>
                  <div className="season-card-team">
                    Champion - {s.champion.team} - Constructors: {s.constructor}
                  </div>
                </div>
              </div>
              <p className="season-card-narrative">{s.narrative}</p>
              <div className="season-card-headline">
                <span className="season-card-headline-label">Iconic moment</span>
                <span>{s.headline_race.name}</span>
                <span className="season-card-headline-note">{s.headline_race.note}</span>
              </div>
              <div className="season-card-foot">
                <div className="season-card-bar">
                  <div
                    className="season-card-bar-fill"
                    style={{ width: `${progress * 100}%`, background: s.accent }}
                  />
                </div>
                <div className="season-card-meta">
                  <span>{ingested} / {expected} races</span>
                  <span className="season-card-cta">Browse &rarr;</span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
