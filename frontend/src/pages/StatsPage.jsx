import StatHero, { StatStrip } from "../components/StatHero/StatHero.jsx";
import { useStats } from "../hooks/useStats.js";

export default function StatsPage() {
  const { data, status } = useStats();

  if (!data) {
    return (
      <div className="library-shell">
        <div className="empty">Loading stats...</div>
      </div>
    );
  }

  const headline = data.headline ?? {};
  const seasons = data.season_breakdown ?? [];
  const sources = data.embedding_sources ?? [];

  const totalRaces = headline.grand_prix ?? 0;
  const expected = data.total_expected_races ?? 132;
  const overall = data.overall_progress ?? 0;

  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">SCALE</div>
        <div className="hero-title">The numbers behind the simulator.</div>
        <p className="hero-sub">
          Every lap, every pit stop, every safety car of every Grand Prix from
          2019 through 2024. Indexed for RAG, accessible to Granite, replayable
          on a real circuit outline. Live counts pulled from <code>/stats</code>.
        </p>
      </div>

      <div className="stats-grid">
        <StatHero
          label="Grand Prix indexed"
          sub={`of ~${expected} target`}
          value={headline.grand_prix}
          accent="#e8002d"
        />
        <StatHero
          label="Laps recorded"
          sub="position + gap + time"
          value={headline.laps_recorded}
          accent="#4cc9f0"
        />
        <StatHero
          label="Pit stops"
          sub="with tire transitions"
          value={headline.pit_stops}
          accent="#e7c04b"
        />
        <StatHero
          label="Telemetry points"
          sub="x/y/speed per lap, normalized"
          value={headline.telemetry_points}
          accent="#2fbf71"
        />
        <StatHero
          label="Race embeddings"
          sub="pgvector RAG chunks"
          value={data.embeddings}
          accent="#b98cff"
        />
        <StatHero
          label="Total data points"
          sub="laps + pits + results + telemetry"
          value={headline.total_data_points}
          accent="#ff8700"
        />
      </div>

      <div className="stats-section">
        <h2>Coverage by season</h2>
        <div className="season-bars">
          {seasons.map((s) => (
            <div className="season-bar-row" key={s.year}>
              <span className="season-bar-year">{s.year}</span>
              <div className="season-bar-track">
                <div
                  className="season-bar-fill"
                  style={{ width: `${Math.min(100, s.progress * 100)}%` }}
                />
              </div>
              <span className="season-bar-count">
                {s.races} / {s.expected} races
              </span>
              {s.complete && <span className="season-bar-badge">FULL</span>}
            </div>
          ))}
        </div>
        <div className="stats-overall">
          Overall ingestion progress: <strong>{Math.round(overall * 100)}%</strong>
          {totalRaces > 0 && (
            <span style={{ color: "var(--text-dim)" }}>
              {" "}({totalRaces} of {expected} target races)
            </span>
          )}
        </div>
      </div>

      <div className="stats-row">
        <div className="stats-card">
          <h3 style={{ margin: 0, fontSize: 13 }}>Catalog</h3>
          <ul className="stats-list">
            <li>Drivers <strong>{data.drivers}</strong></li>
            <li>Constructors <strong>{data.constructors}</strong></li>
            <li>Circuits <strong>{data.circuits}</strong></li>
            <li>Race results <strong>{data.race_results}</strong></li>
            <li>Safety-car windows <strong>{data.safety_cars}</strong></li>
            <li>Saved scenarios <strong>{data.scenarios}</strong></li>
          </ul>
        </div>
        <div className="stats-card">
          <h3 style={{ margin: 0, fontSize: 13 }}>RAG index</h3>
          <ul className="stats-list">
            {sources.length === 0 ? (
              <li>No embeddings yet - run <code>python -m ingestion.embed_races</code></li>
            ) : (
              sources.map((s) => (
                <li key={s.source}>
                  {s.source} <strong>{s.count}</strong>
                </li>
              ))
            )}
            <li>Races with embeddings <strong>{data.races_with_embeddings}</strong></li>
            <li>Races with telemetry <strong>{data.races_with_telemetry}</strong></li>
          </ul>
        </div>
        <div className="stats-card">
          <h3 style={{ margin: 0, fontSize: 13 }}>IBM stack</h3>
          <ul className="stats-list">
            <li>Granite-3-8b-instruct <span className="stats-tag">explain + narrate</span></li>
            <li>Slate-30m-english-rtrvr <span className="stats-tag">RAG vectors</span></li>
            <li>Docling <span className="stats-tag">FIA PDFs</span></li>
            <li>Langflow <span className="stats-tag">3 flows</span></li>
            <li>watsonx.ai <span className="stats-tag">all of the above</span></li>
          </ul>
        </div>
      </div>

      <div className="stats-footer-note">data source: {status}</div>
    </div>
  );
}
