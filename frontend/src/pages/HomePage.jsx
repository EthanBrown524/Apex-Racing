import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { StatStrip } from "../components/StatHero/StatHero.jsx";
import { fetchHealth } from "../api/apexClient.js";
import { SEASONS } from "../data/seasons.js";
import { useShowcase } from "../hooks/useShowcase.js";
import { useStats } from "../hooks/useStats.js";

export default function HomePage() {
  const navigate = useNavigate();
  const { data: stats, status: statsStatus } = useStats();
  const { scenarios } = useShowcase();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const usingSampleData = statsStatus === "sample";
  const ingestionIncomplete =
    health && health.ingestion_complete === false;
  const showStatusBanner = usingSampleData || ingestionIncomplete;

  return (
    <div className="home">
      {showStatusBanner && (
        <div className="home-status-banner" role="status">
          <strong>Heads up:</strong>{" "}
          {usingSampleData
            ? "the backend isn't returning live data, so figures below come from a sample dataset."
            : "ingestion is incomplete - some seasons may be missing."}{" "}
          <span>
            Run{" "}
            <code>python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024</code>
            {" "}
            to fix.
          </span>
        </div>
      )}

      <section className="home-hero">
        <div className="home-hero-eyebrow">RACE DIRECTOR - F1 2019-2024</div>
        <h1 className="home-hero-title">
          Rewrite Formula 1.<br />
          <span className="home-hero-title-accent">Powered by IBM Granite.</span>
        </h1>
        <p className="home-hero-sub">
          APEX is an AI race simulator built on every lap, pit stop, and safety car
          from six seasons of Formula 1. Change a strategy. Trigger a safety car.
          Promote a backmarker. See the championship flip in real time, with
          explanations grounded in the actual race data.
        </p>
        <div className="home-hero-cta">
          <Link to="/seasons" className="button primary big">
            Explore the seasons &rarr;
          </Link>
          <Link to="/showcase" className="button secondary big">
            Try a demo scenario
          </Link>
        </div>
        <div className="home-hero-marquee">
          {SEASONS.map((s) => (
            <Link key={s.year} to={`/seasons/${s.year}`} className="marquee-year">
              {s.year}
            </Link>
          ))}
        </div>
      </section>

      {stats && (
        <section className="home-stats">
          <StatStrip
            items={[
              { label: "Grand Prix", value: stats.headline?.grand_prix ?? 0, accent: "#e8002d" },
              { label: "Laps recorded", value: stats.headline?.laps_recorded ?? 0, accent: "#4cc9f0" },
              { label: "Pit stops", value: stats.headline?.pit_stops ?? 0, accent: "#e7c04b" },
              { label: "Telemetry points", value: stats.headline?.telemetry_points ?? 0, accent: "#2fbf71" },
              { label: "RAG chunks", value: stats.embeddings ?? 0, accent: "#b98cff" },
              { label: "Data points", value: stats.headline?.total_data_points ?? 0, accent: "#ff8700" },
            ]}
          />
        </section>
      )}

      <section className="home-section">
        <div className="home-section-head">
          <div className="home-section-eyebrow">THE THREE MODES</div>
          <h2 className="home-section-title">One simulator. Three angles on every race.</h2>
        </div>
        <div className="home-pillars">
          <Link to="/rewind" className="home-pillar" style={{ "--accent": "#4cc9f0" }}>
            <div className="home-pillar-num">01</div>
            <h3>Time Machine</h3>
            <p>
              Replay any Grand Prix with telemetry-driven cars on the real circuit,
              a live leaderboard, and Granite commentary that updates lap by lap.
              Ask anything; the AI cites the race data behind every answer.
            </p>
            <span className="home-pillar-cta">Open Time Machine &rarr;</span>
          </Link>
          <Link to="/showcase" className="home-pillar" style={{ "--accent": "#e8002d" }}>
            <div className="home-pillar-num">02</div>
            <h3>What-If Lab</h3>
            <p>
              Move a pit stop. Force a DNF. Summon a safety car. Change the weather.
              The deterministic engine recomputes the standings, Granite explains
              the new outcome with citations, and a Realism chip tells you how
              plausible your scenario actually is.
            </p>
            <span className="home-pillar-cta">See sample scenarios &rarr;</span>
          </Link>
          <Link to="/glory" className="home-pillar" style={{ "--accent": "#ffd24a" }}>
            <div className="home-pillar-num">03</div>
            <h3>Glory Path</h3>
            <p>
              Pick a driver. Pick the position you wish they'd finished. Granite
              searches for the smallest set of strategy changes that gets them
              there - and tells the alternate story in three sentences.
            </p>
            <span className="home-pillar-cta">Plot a Glory Path &rarr;</span>
          </Link>
        </div>
      </section>

      <section className="home-section dim">
        <div className="home-section-head">
          <div className="home-section-eyebrow">AI IN F1</div>
          <h2 className="home-section-title">
            How AI changes the way fans experience the sport.
          </h2>
          <p className="home-section-lede">
            Watching a Grand Prix is a stream of context. Why did they pit? What
            was the safety car worth? Who's on the cheaper tyre? APEX uses Granite
            to make every one of those questions answerable - instantly, with the
            evidence right there.
          </p>
        </div>
        <div className="home-beats">
          <div className="home-beat">
            <div className="home-beat-num">1</div>
            <h4>Replay with broadcast-quality commentary</h4>
            <p>
              Granite narrates the race up to whatever lap you've scrubbed to,
              referencing real lead changes, pit windows, and incidents from the
              indexed race library.
            </p>
          </div>
          <div className="home-beat">
            <div className="home-beat-num">2</div>
            <h4>Test "what if?" without writing code</h4>
            <p>
              Seven change types cover the strategic decisions that actually shape
              outcomes - tire calls, retirements, weather, safety cars - and the
              positions update lap by lap.
            </p>
          </div>
          <div className="home-beat">
            <div className="home-beat-num">3</div>
            <h4>Resolve "who would have won?"</h4>
            <p>
              The Championship Impact card recomputes the season standings under
              your counterfactual. Watch the title flip if your scenario was
              decisive.
            </p>
          </div>
          <div className="home-beat">
            <div className="home-beat-num">4</div>
            <h4>Every claim is grounded in the data</h4>
            <p>
              Granite answers cite their sources by index. Hover the chip; see the
              snippet. No hallucinated positions, no invented laps.
            </p>
          </div>
        </div>
      </section>

      <section className="home-section">
        <div className="home-section-head">
          <div className="home-section-eyebrow">START HERE</div>
          <h2 className="home-section-title">Pre-loaded demo scenarios.</h2>
          <p className="home-section-lede">
            Six hand-picked moments where a small change rewrites a season. Click
            any card and watch the AI take over.
          </p>
        </div>
        <div className="home-scenarios">
          {scenarios.slice(0, 6).map((s) => (
            <button
              key={s.id}
              type="button"
              className="home-scenario"
              style={{ "--accent": s.accent ?? "#e8002d" }}
              onClick={() => {
                if (!s.race_id) return;
                const route = s.mode === "glory_path" ? "/glory" : "/rewind";
                navigate(`${route}/${s.race_id}`, { state: s });
              }}
              disabled={!s.race_id}
            >
              <div className="home-scenario-tag">
                {s.mode === "glory_path" ? "GLORY PATH" : "WHAT-IF"}
              </div>
              <div className="home-scenario-title">{s.title}</div>
              <div className="home-scenario-sub">{s.tagline}</div>
              <div className="home-scenario-cta">
                {s.race_id ? "Launch" : "Needs ingestion"}
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="home-section dim">
        <div className="home-section-head">
          <div className="home-section-eyebrow">BUILT ON IBM</div>
          <h2 className="home-section-title">The watsonx stack, end to end.</h2>
        </div>
        <div className="home-stack">
          <div className="home-stack-card">
            <strong>Granite-3-8b-instruct</strong>
            <span>watsonx.ai text generation</span>
            <p>Explanations, narration, free-form Q&A, Glory Path storylines, Realism scoring.</p>
          </div>
          <div className="home-stack-card">
            <strong>Slate-30m-english-rtrvr</strong>
            <span>watsonx.ai embeddings</span>
            <p>RAG vectors for race narratives, pit windows, lead changes, and FIA stewards' decisions.</p>
          </div>
          <div className="home-stack-card">
            <strong>Docling</strong>
            <span>structured PDF extraction</span>
            <p>FIA decision PDFs become RAG chunks with provenance preserved end-to-end.</p>
          </div>
          <div className="home-stack-card">
            <strong>Langflow</strong>
            <span>visual orchestration</span>
            <p>Three exportable flow graphs document the counterfactual, Glory Path, and forecast pipelines.</p>
          </div>
        </div>
      </section>

      <section className="home-cta">
        <h2>Pick a season and start rewriting.</h2>
        <div className="home-cta-row">
          <Link to="/seasons" className="button primary big">Browse seasons &rarr;</Link>
          <Link to="/stats" className="button secondary big">See the numbers</Link>
        </div>
      </section>
    </div>
  );
}
