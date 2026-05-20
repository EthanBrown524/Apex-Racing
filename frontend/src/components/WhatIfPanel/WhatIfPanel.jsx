import { useMemo, useState } from "react";

const CHANGE_TYPES = [
  { value: "pit_lap",      label: "Move pit stop" },
  { value: "dnf",          label: "Force DNF" },
  { value: "fastest_lap",  label: "Set lap time (ms)" },
  { value: "mechanical",   label: "Mechanical issue" },
  { value: "weather",      label: "Weather window" },
  { value: "safety_car",   label: "Safety car" },
  { value: "grid_swap",    label: "Grid swap" },
];

const VALUE_PLACEHOLDER = {
  pit_lap: "New pit lap",
  dnf: "(unused)",
  fastest_lap: "Lap time in ms (e.g. 84000)",
  mechanical: "Penalty ms/lap (default 800)",
  weather: "Drivers helped (CSV)",
  safety_car: "Start lap",
  grid_swap: "Partner driver code",
};

export default function WhatIfPanel({ raceId, changes, setChanges, onRun, isRunning }) {
  const [driverCode, setDriverCode] = useState("HAM");
  const [changeType, setChangeType] = useState("pit_lap");
  const [lap, setLap] = useState(14);
  const [value, setValue] = useState(20);
  const [aiDirector, setAiDirector] = useState(true);

  const driverNeeded = useMemo(
    () => !["safety_car", "weather"].includes(changeType),
    [changeType]
  );

  function addChange() {
    let coercedValue = value;
    if (changeType === "weather" && typeof value === "string") {
      const benefits = value
        .split(/[\s,]+/)
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);
      coercedValue = { benefits, penalty_ms: 1200 };
    }
    setChanges([
      ...changes,
      {
        driver_code: driverNeeded ? driverCode.toUpperCase() : "",
        change_type: changeType,
        lap: Number(lap),
        value: coercedValue,
      },
    ]);
  }

  return (
    <div className="whatif-panel">
      <div className="whatif-title">What-If Simulator</div>
      <div className="input-grid">
        <div className="field">
          <span>{driverNeeded ? "Driver" : "Driver (unused)"}</span>
          <input
            value={driverCode}
            maxLength={3}
            disabled={!driverNeeded}
            onChange={(e) => setDriverCode(e.target.value)}
          />
        </div>
        <div className="field">
          <span>Change</span>
          <select value={changeType} onChange={(e) => setChangeType(e.target.value)}>
            {CHANGE_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <span>Lap</span>
          <input
            type="number"
            min="1"
            value={lap}
            onChange={(e) => setLap(e.target.value)}
          />
        </div>
        <div className="field">
          <span>Value</span>
          <input
            value={value}
            placeholder={VALUE_PLACEHOLDER[changeType] ?? "value"}
            onChange={(e) => setValue(e.target.value)}
          />
        </div>
      </div>
      <label className="director-toggle" title="Have Granite plan strategic responses for other drivers, then re-simulate.">
        <input
          type="checkbox"
          checked={aiDirector}
          onChange={(e) => setAiDirector(e.target.checked)}
        />
        <span className="director-toggle-label">
          AI Race Director
          <span className="director-toggle-sub">
            Granite expands triggers into per-driver responses
          </span>
        </span>
      </label>
      <div className="btn-row">
        <button className="button secondary" type="button" onClick={addChange}>
          + Add
        </button>
        <button
          className="button primary"
          type="button"
          onClick={() => onRun(raceId, changes, aiDirector)}
          disabled={isRunning || changes.length === 0}
        >
          {isRunning ? "Simulating..." : "Simulate"}
        </button>
        <button className="button danger" type="button" onClick={() => setChanges([])}>
          Clear
        </button>
      </div>
      {changes.length > 0 && (
        <ul className="change-list">
          {changes.map((change, index) => (
            <li key={`${change.driver_code}-${change.change_type}-${change.lap}-${index}`}>
              {change.driver_code || "*"} {change.change_type} L{change.lap} &rarr;{" "}
              {formatValue(change.value)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function formatValue(v) {
  if (v == null) return "-";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}
