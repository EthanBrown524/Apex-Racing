import { useState } from "react";

const changeTypes = ["pit_lap", "tire_compound", "safety_car", "weather", "dnf"];

export default function WhatIfPanel({ raceId, changes, setChanges, onRun, isRunning }) {
  const [driverCode, setDriverCode] = useState("HAM");
  const [changeType, setChangeType] = useState("pit_lap");
  const [lap, setLap] = useState(14);
  const [value, setValue] = useState(19);

  function addChange() {
    setChanges([
      ...changes,
      {
        driver_code: driverCode.toUpperCase(),
        change_type: changeType,
        lap: Number(lap),
        value
      }
    ]);
  }

  return (
    <section className="panel panel-pad">
      <h2>What-If</h2>
      <div className="stack">
        <div className="control-row">
          <label className="field">
            <span>Driver</span>
            <input value={driverCode} maxLength={3} onChange={(event) => setDriverCode(event.target.value)} />
          </label>
          <label className="field">
            <span>Change</span>
            <select value={changeType} onChange={(event) => setChangeType(event.target.value)}>
              {changeTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Lap</span>
            <input type="number" min="1" value={lap} onChange={(event) => setLap(event.target.value)} />
          </label>
          <label className="field">
            <span>Value</span>
            <input value={value} onChange={(event) => setValue(event.target.value)} />
          </label>
        </div>
        <div className="control-row">
          <button className="button secondary" type="button" onClick={addChange}>
            Add
          </button>
          <button className="button" type="button" onClick={() => onRun(raceId, changes)} disabled={isRunning}>
            {isRunning ? "Running" : "Simulate"}
          </button>
          <button className="button secondary" type="button" onClick={() => setChanges([])}>
            Clear
          </button>
        </div>
        {changes.length > 0 && (
          <ul className="change-list">
            {changes.map((change, index) => (
              <li key={`${change.driver_code}-${change.change_type}-${index}`}>
                {change.driver_code} {change.change_type} L{change.lap}: {String(change.value)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

