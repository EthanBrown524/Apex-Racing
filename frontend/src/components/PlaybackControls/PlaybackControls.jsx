import { useEffect, useState } from "react";

import { useEngineDrone } from "../../hooks/useEngineDrone.js";

const speeds = [0.5, 1, 2, 4, 10];
const STORAGE_KEY = "apex.drone";

export default function PlaybackControls({
  isPlaying,
  setIsPlaying,
  speed,
  setSpeed,
  currentLap,
  setCurrentLap,
  maxLap,
  onReset,
}) {
  const [droneEnabled, setDroneEnabled] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch (err) {
      return false;
    }
  });

  useEngineDrone({ enabled: droneEnabled, isPlaying, speed });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, droneEnabled ? "1" : "0");
    } catch (err) {
      /* ignore storage failures */
    }
  }, [droneEnabled]);

  return (
    <div className="controls-bar">
      <button className="button" type="button" onClick={() => setIsPlaying(!isPlaying)}>
        {isPlaying ? "Pause" : "Play"}
      </button>
      <button className="button secondary" type="button" onClick={onReset}>
        Reset
      </button>
      <div className="field">
        <span>Speed</span>
        <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
          {speeds.map((value) => (
            <option key={value} value={value}>{value}x</option>
          ))}
        </select>
      </div>
      <div className="field" style={{ flex: 1 }}>
        <span>Lap {currentLap} / {maxLap}</span>
        <input
          type="range"
          min="1"
          max={maxLap}
          value={currentLap}
          onChange={(e) => setCurrentLap(Number(e.target.value))}
        />
      </div>
      <button
        type="button"
        className={`button ${droneEnabled ? "primary" : "ghost"}`}
        title={droneEnabled ? "Mute engine drone" : "Play engine drone"}
        onClick={() => setDroneEnabled((v) => !v)}
        style={{ minWidth: 38, padding: "4px 10px" }}
      >
        {droneEnabled ? "🔊" : "🔇"}
      </button>
    </div>
  );
}
