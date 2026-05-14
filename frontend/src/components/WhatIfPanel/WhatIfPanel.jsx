import { useState } from "react";

const changeTypes = ["pit_lap", "dnf", "fastest_lap"];

export default function WhatIfPanel({ raceId, changes, setChanges, onRun, isRunning }) {
  const [driverCode, setDriverCode] = useState("HAM");
  const [changeType, setChangeType] = useState("pit_lap");
  const [lap, setLap] = useState(14);
  const [value, setValue] = useState(20);

  function addChange() {
    setChanges([
      ...changes,
      {
        driver_code: driverCode.toUpperCase(),
        change_type: changeType,
        lap: Number(lap),
        value,
      },
    ]);
  }

  return (
    <div className="whatif-panel">
      <div className="whatif-title">What-If Simulator</div>
      <div className="input-grid">
        <div className="field">
          <span>Driver</span>
          <input
            value={driverCode}
            maxLength={3}
            onChange={(e) => setDriverCode(e.target.value)}
          />
        </div>
        <div className="field">
          <span>Change</span>
          <select value={changeType} onChange={(e) => setChangeType(e.target.value)}>
            {changeTypes.map((type) => (
              <option key={type} value={type}>{type}</option>
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
          <input value={value} onChange={(e) => setValue(e.target.value)} />
        </div>
      </div>
      <div className="btn-row">
        <button className="button secondary" type="button" onClick={addChange}>
          + Add
        </button>
        <button
          className="button"
          type="button"
          onClick={() => onRun(raceId, changes)}
          disabled={isRunning || changes.length === 0}
        >
          {isRunning ? "Running..." : "Simulate"}
        </button>
        <button className="button danger" type="button" onClick={() => setChanges([])}>
          Clear
        </button>
      </div>
      {changes.length > 0 && (
        <ul className="change-list">
          {changes.map((change, index) => (
            <li key={`${change.driver_code}-${change.change_type}-${change.lap}-${index}`}>
              {change.driver_code} {change.change_type} L{change.lap} -&gt; {String(change.value)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
