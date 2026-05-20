export default function AboutPage() {
  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">APEX RACE DIRECTOR</div>
        <div className="hero-title">An AI simulator for Formula 1's alternate histories.</div>
        <p className="hero-sub">
          APEX combines every lap, pit stop, and safety car from the 2019-2024 F1 seasons
          with IBM Granite, retrieval-augmented context from race narratives and FIA stewards'
          decisions, and a counterfactual engine that recomputes the standings as you
          change the past.
        </p>
      </div>

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
            Move a pit stop, retire a driver, summon a safety car, change the weather -
            the engine re-simulates the race and Granite explains the new outcome with
            citations from the indexed race library.
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
          <h4>IBM stack</h4>
          <p>
            <strong>Granite-3-8b</strong> (watsonx.ai) reasoning, <strong>Slate</strong>
            embeddings for RAG, <strong>Docling</strong> for FIA decisions, and a
            <strong> Langflow</strong> graph for the counterfactual pipeline.
          </p>
        </div>
      </div>
    </div>
  );
}
