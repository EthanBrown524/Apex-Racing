import { useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";

import Citations from "../components/Citations/Citations.jsx";
import { fetchRaces } from "../api/apexClient.js";
import { sampleRaces } from "../data/sampleData.js";
import { useGloryPath } from "../hooks/useGloryPath.js";

function useCountdown(target, ms = 700) {
  const [value, setValue] = useState(target);
  useEffect(() => {
    if (target == null) {
      setValue(target);
      return;
    }
    setValue(target);
  }, [target]);
  return value;
}

function AnimatedPosition({ from, to }) {
  const [shown, setShown] = useState(from ?? to);

  useEffect(() => {
    if (from == null || to == null || from === to) {
      setShown(to);
      return;
    }
    setShown(from);
    const step = from > to ? -1 : 1;
    const totalSteps = Math.abs(to - from);
    const delay = Math.max(60, Math.min(120, 700 / Math.max(totalSteps, 1)));
    let current = from;
    const id = setInterval(() => {
      current += step;
      setShown(current);
      if (current === to) clearInterval(id);
    }, delay);
    return () => clearInterval(id);
  }, [from, to]);

  return <span>{shown != null ? `P${shown}` : "-"}</span>;
}

export default function GloryPathPage() {
  const { raceId: paramRaceId } = useParams();
  const location = useLocation();
  const [races, setRaces] = useState([]);
  const [raceId, setRaceId] = useState(paramRaceId ? Number(paramRaceId) : null);
  const scenario = location.state;
  const [driverCode, setDriverCode] = useState(scenario?.driver_code ?? "HAM");
  const [targetPosition, setTargetPosition] = useState(scenario?.target_position ?? 1);
  const glory = useGloryPath();

  useEffect(() => {
    fetchRaces()
      .then((data) => setRaces(data?.length ? data : sampleRaces))
      .catch(() => setRaces(sampleRaces));
  }, []);

  useEffect(() => {
    if (raceId == null && races.length) setRaceId(races[0].id);
  }, [races, raceId]);

  // If we came from the Showcase with a scenario, auto-solve once we have a raceId
  useEffect(() => {
    if (scenario?.mode === "glory_path" && raceId) {
      glory.solve(raceId, scenario.driver_code, scenario.target_position ?? 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raceId]);

  const selectedRace = useMemo(
    () => races.find((r) => r.id === Number(raceId)),
    [races, raceId]
  );

  function onSolve() {
    if (!raceId || !driverCode) return;
    glory.solve(raceId, driverCode, Number(targetPosition));
  }

  return (
    <div className="glory-shell">
      <aside className="glory-form">
        <h3>Glory Path</h3>
        <p style={{ fontSize: 12, color: "var(--text-mid)", lineHeight: 1.55, marginTop: 0 }}>
          Pick a race, a driver, and the finishing position you wish they'd had.
          Granite plans the minimum set of strategic changes that get them there
          and narrates the alternate storyline with citations.
        </p>

        <div className="field" style={{ marginTop: 14 }}>
          <span>Race</span>
          <select value={raceId ?? ""} onChange={(e) => setRaceId(Number(e.target.value))}>
            {races.map((race) => (
              <option key={race.id} value={race.id}>
                {race.season} - {race.name}
              </option>
            ))}
          </select>
        </div>

        <div className="input-grid" style={{ marginTop: 8 }}>
          <div className="field">
            <span>Driver code</span>
            <input
              maxLength={3}
              value={driverCode}
              onChange={(e) => setDriverCode(e.target.value.toUpperCase())}
            />
          </div>
          <div className="field">
            <span>Target position</span>
            <input
              type="number"
              min="1"
              max="20"
              value={targetPosition}
              onChange={(e) => setTargetPosition(e.target.value)}
            />
          </div>
        </div>

        <div className="btn-row">
          <button
            type="button"
            className="button primary"
            onClick={onSolve}
            disabled={glory.isRunning}
          >
            {glory.isRunning ? "Solving..." : "Find Glory Path"}
          </button>
        </div>

        {selectedRace && (
          <div style={{ marginTop: 16, padding: "10px 12px", border: "1px solid var(--line)", borderRadius: 8, fontSize: 12, color: "var(--text-mid)" }}>
            <div style={{ fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
              {selectedRace.name}
            </div>
            <div>Round {selectedRace.round} - {selectedRace.circuit_name}</div>
          </div>
        )}
      </aside>

      <section className="glory-result">
        {!glory.result && !glory.isRunning && (
          <div className="empty">
            Enter a driver and target position, then click <strong>Find Glory Path</strong>.
          </div>
        )}
        {glory.isRunning && (
          <div className="empty">Granite is plotting the alternate storyline...</div>
        )}
        {glory.result && glory.result.error && (
          <div className="empty">Error: {glory.result.error}</div>
        )}
        {glory.result && !glory.result.error && (
          <>
            <div className="glory-headline">
              <div className="glory-pos">
                <div className="label">Actually finished</div>
                <div className="val">
                  {glory.result.starting_position ? `P${glory.result.starting_position}` : "-"}
                </div>
              </div>
              <div className="glory-arrow">&rarr;</div>
              <div className="glory-pos target">
                <div className="label">Glory Path</div>
                <div className="val">
                  <AnimatedPosition
                    from={glory.result.starting_position}
                    to={glory.result.achieved_position}
                  />
                </div>
              </div>
              <div style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-dim)" }}>
                Target was{" "}
                <strong style={{ color: "var(--text)" }}>P{glory.result.target_position}</strong>
              </div>
            </div>

            <div style={{ fontSize: 11, color: "var(--text-dim)", letterSpacing: 0.4, fontWeight: 800, textTransform: "uppercase", marginBottom: 8 }}>
              Interventions ({glory.result.applied?.length ?? 0})
            </div>
            <div className="glory-changes">
              {(glory.result.applied || []).map((change, i) => {
                const rationale = glory.result.rationales?.[i]?.rationale;
                return (
                  <div className="glory-change" key={i}>
                    <div className="glory-change-num">{i + 1}</div>
                    <div>
                      <div className="glory-change-title">{formatChange(change)}</div>
                      {rationale && <div className="glory-change-reason">{rationale}</div>}
                    </div>
                  </div>
                );
              })}
              {(!glory.result.applied || glory.result.applied.length === 0) && (
                <div className="glory-change">
                  <div className="glory-change-num">!</div>
                  <div>
                    <div className="glory-change-title">No interventions found.</div>
                    <div className="glory-change-reason">
                      The race data may be incomplete - try running the bulk ingestion script.
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="narrator" style={{ borderTop: "none", padding: 0, marginTop: 14 }}>
              <div className="narrator-title">AI Storyline</div>
              <div className="narrator-body">{glory.result.explanation}</div>
              <Citations citations={glory.result.citations || []} />
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function formatChange(c) {
  if (c.change_type === "pit_lap") return `${c.driver_code} pit moved to lap ${c.value}`;
  if (c.change_type === "dnf") return `${c.driver_code} retires on lap ${c.lap}`;
  if (c.change_type === "fastest_lap") return `${c.driver_code} sets ${c.value} ms on lap ${c.lap}`;
  if (c.change_type === "mechanical") return `${c.driver_code} mechanical from lap ${c.lap}`;
  if (c.change_type === "weather") return `Weather window from lap ${c.lap}`;
  if (c.change_type === "safety_car") return `Safety car at lap ${c.value ?? c.lap}`;
  if (c.change_type === "grid_swap") return `${c.driver_code} swaps grid with ${c.value}`;
  return `${c.driver_code} ${c.change_type}`;
}
