import { useNavigate } from "react-router-dom";

import { useShowcase } from "../hooks/useShowcase.js";

export default function ShowcasePage() {
  const { scenarios, status } = useShowcase();
  const navigate = useNavigate();

  function launch(scenario) {
    if (!scenario.race_id) return;
    if (scenario.mode === "glory_path") {
      navigate(`/glory/${scenario.race_id}`, { state: scenario });
    } else {
      navigate(`/rewind/${scenario.race_id}`, { state: scenario });
    }
  }

  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">SHOWCASE</div>
        <div className="hero-title">One-click demo scenarios.</div>
        <p className="hero-sub">
          Hand-picked counterfactuals and Glory Paths that load with their
          changes pre-filled. Skip the driver-code hunting and see the AI
          rewrite history immediately.
        </p>
      </div>

      <div className="library-toolbar" style={{ paddingLeft: 24, paddingRight: 24 }}>
        <span className="meta-pill">Source <strong>{status}</strong></span>
      </div>

      <div className="race-grid" style={{ padding: "0 24px 32px" }}>
        {scenarios.map((s) => {
          const disabled = !s.race_id;
          return (
            <button
              key={s.id}
              type="button"
              className="showcase-card"
              disabled={disabled}
              onClick={() => launch(s)}
              style={{ "--accent": s.accent ?? "#e8002d" }}
            >
              <div className="showcase-tag">{s.mode === "glory_path" ? "GLORY PATH" : "WHAT-IF"}</div>
              <div className="race-card-title">{s.title}</div>
              <div className="showcase-sub">{s.subtitle}</div>
              <div className="race-card-meta">
                <span>{s.season} round {s.round}</span>
                <span className="race-card-round">
                  {disabled ? "Ingest first" : "Launch"}
                </span>
              </div>
              <div className="showcase-tagline">{s.tagline}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
