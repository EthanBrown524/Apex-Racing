import GlossaryTerm from "../components/Glossary/GlossaryTerm.jsx";
import { StatStrip } from "../components/StatHero/StatHero.jsx";
import { useStats } from "../hooks/useStats.js";

export default function AboutPage() {
  const { data: stats } = useStats();

  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">APEX RACE DIRECTOR</div>
        <div className="hero-title">An AI simulator for Formula 1's alternate histories.</div>
        <p className="hero-sub">
          APEX combines every lap, pit stop, and safety car from the 2019-2024 F1 seasons
          with IBM Granite, retrieval-augmented context from race narratives and FIA stewards'
          decisions, and a counterfactual engine that recomputes the standings as you
          change the past. Master the{" "}
          <GlossaryTerm term="undercut" />, weather your way through the{" "}
          <GlossaryTerm term="VSC" />, or rewrite your favourite driver's championship.
        </p>
      </div>

      {stats && (
        <StatStrip
          items={[
            { label: "Grand Prix", value: stats.headline?.grand_prix ?? 0, accent: "#e8002d" },
            { label: "Laps", value: stats.headline?.laps_recorded ?? 0, accent: "#4cc9f0" },
            { label: "Telemetry points", value: stats.headline?.telemetry_points ?? 0, accent: "#2fbf71" },
            { label: "RAG chunks", value: stats.embeddings ?? 0, accent: "#b98cff" },
          ]}
        />
      )}

      <div className="feature-grid">
        <div className="feature-card">
          <h4>Time Machine</h4>
          <p>
            Replay any race with telemetry-driven car positions on a real circuit outline
            and a live leaderboard. Ask Granite anything about what's happening.
          </p>
        </div>
        <div className="feature-card">
          <h4>What-If Lab</h4>
          <p>
            Move a pit stop, retire a driver, summon a{" "}
            <GlossaryTerm term="SC" />, change the weather - the engine re-simulates
            and Granite explains the new outcome with citations from the indexed race library.
          </p>
        </div>
        <div className="feature-card">
          <h4>Glory Path</h4>
          <p>
            Pick a driver and a target position. Granite searches for the smallest
            set of changes that gets them there and narrates the alternate storyline.
          </p>
        </div>
        <div className="feature-card">
          <h4>Championship Impact</h4>
          <p>
            Every What-If shows how the season standings would have shifted - the killer
            "Hamilton would have won 2021" moment, computed in real time.
          </p>
        </div>
        <div className="feature-card">
          <h4>Realism Score</h4>
          <p>
            Granite judges every counterfactual on a 0-1 scale. Stretch your scenarios
            into Fantasy territory or stay Plausible.
          </p>
        </div>
        <div className="feature-card">
          <h4>IBM stack</h4>
          <p>
            <strong>Granite-3-8b</strong> reasoning, <strong>Slate</strong>
            {" "}embeddings for RAG, <strong>Docling</strong> for FIA decisions, and a
            <strong> Langflow</strong> graph for the counterfactual pipeline.
          </p>
        </div>
      </div>
    </div>
  );
}
