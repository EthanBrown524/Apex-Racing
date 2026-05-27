import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useShowcase } from "../hooks/useShowcase.js";

const AUTO_INTERVAL_MS = 6000;

export default function ShowcasePage() {
  const { scenarios, status } = useShowcase();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const autoMode = params.get("auto") === "1";
  const [autoIndex, setAutoIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  function launch(scenario) {
    if (!scenario?.race_id) return;
    if (scenario.mode === "glory_path") {
      navigate(`/glory/${scenario.race_id}`, { state: scenario });
    } else {
      navigate(`/rewind/${scenario.race_id}`, { state: scenario });
    }
  }

  const playable = scenarios.filter((s) => s.race_id);

  // Auto-rotation: cycle through playable scenarios every AUTO_INTERVAL_MS.
  useEffect(() => {
    if (!autoMode || paused || playable.length === 0) return;
    const id = setInterval(() => {
      setAutoIndex((i) => (i + 1) % playable.length);
    }, AUTO_INTERVAL_MS);
    return () => clearInterval(id);
  }, [autoMode, paused, playable.length]);

  // When the rotation index advances, navigate to the current scenario.
  useEffect(() => {
    if (!autoMode || paused || !playable.length) return;
    const target = playable[autoIndex];
    if (!target) return;
    // Don't auto-navigate to glory because the solve itself takes ~5s.
    if (target.mode === "glory_path") return;
    navigate(`/rewind/${target.race_id}`, { state: target });
  }, [autoMode, autoIndex, paused, playable, navigate]);

  function toggleAuto() {
    const next = !autoMode;
    if (next) {
      params.set("auto", "1");
    } else {
      params.delete("auto");
    }
    setParams(params, { replace: true });
    setAutoIndex(0);
    setPaused(false);
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
        <span className="meta-pill">
          Source <strong>{status}</strong>
        </span>
        <span className="meta-pill">
          Mode <strong>{autoMode ? `Auto (${AUTO_INTERVAL_MS / 1000}s)` : "Manual"}</strong>
        </span>
        <button
          type="button"
          className={`button ${autoMode ? "primary" : "secondary"}`}
          onClick={toggleAuto}
          style={{ marginLeft: "auto" }}
        >
          {autoMode ? "Stop hands-free" : "Play hands-free"}
        </button>
        {autoMode && (
          <button
            type="button"
            className="button ghost"
            onClick={() => setPaused((p) => !p)}
          >
            {paused ? "Resume" : "Pause"}
          </button>
        )}
      </div>

      <div className="race-grid" style={{ padding: "0 24px 32px" }}>
        {scenarios.map((s, i) => {
          const disabled = !s.race_id;
          const playableIdx = playable.indexOf(s);
          const isActiveAuto =
            autoMode && playableIdx === autoIndex && playableIdx !== -1;
          return (
            <button
              key={s.id}
              type="button"
              className={`showcase-card${isActiveAuto ? " active-auto" : ""}`}
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
                  {disabled ? "Ingest first" : isActiveAuto ? "Now playing" : "Launch"}
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
