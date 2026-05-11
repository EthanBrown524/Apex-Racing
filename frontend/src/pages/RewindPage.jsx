import { useCallback, useMemo, useState } from "react";

import Leaderboard from "../components/Leaderboard/Leaderboard.jsx";
import PlaybackControls from "../components/PlaybackControls/PlaybackControls.jsx";
import TrackCanvas from "../components/TrackCanvas/TrackCanvas.jsx";
import WhatIfPanel from "../components/WhatIfPanel/WhatIfPanel.jsx";
import { useCounterfactual } from "../hooks/useCounterfactual.js";
import { useRaceData } from "../hooks/useRaceData.js";
import { useTelemetry } from "../hooks/useTelemetry.js";

export default function RewindPage() {
  const [selectedRaceId, setSelectedRaceId] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [currentLap, setCurrentLap] = useState(1);
  const [changes, setChanges] = useState([]);
  const { races, selectedRace, lapData, circuitPath, status } = useRaceData(selectedRaceId);
  const counterfactual = useCounterfactual();
  const telemetry = useTelemetry(selectedRace?.id, currentLap);

  const laps = lapData.laps ?? [];
  const activeLap = useMemo(
    () => laps.find((lap) => lap.lap === currentLap) ?? laps[0],
    [currentLap, laps]
  );
  const handleLapChange = useCallback((lap) => setCurrentLap(lap), []);

  return (
    <>
      <div className="race-bar">
        <select
          className="race-select"
          value={selectedRace?.id ?? selectedRaceId}
          onChange={(e) => {
            setSelectedRaceId(Number(e.target.value));
            setCurrentLap(1);
          }}
        >
          {races.map((race) => (
            <option key={race.id} value={race.id}>
              {race.season} {race.name}
            </option>
          ))}
        </select>
        <div className="meta-pills">
          <div className="meta-pill">Circuit <strong>{selectedRace?.circuit_name ?? "—"}</strong></div>
          <div className="meta-pill">Round <strong>{selectedRace?.round ?? "—"}</strong></div>
          <div className="meta-pill">Source <strong>{status}</strong></div>
        </div>
      </div>

      <div className="page-grid">
        <div className="left-col">
          <TrackCanvas
            laps={laps}
            circuitPath={circuitPath}
            speed={speed}
            isPlaying={isPlaying}
            currentLap={currentLap}
            onLapChange={handleLapChange}
            cfLaps={counterfactual.result?.alt_laps}
          />
          <PlaybackControls
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
            speed={speed}
            setSpeed={setSpeed}
            currentLap={currentLap}
            setCurrentLap={setCurrentLap}
            maxLap={laps.length || 1}
          />
        </div>

        <div className="right-col">
          <div className="section-header">
            <span className="section-title">Leaderboard — Lap {currentLap}</span>
          </div>
          <Leaderboard lap={activeLap} />
          <WhatIfPanel
            raceId={selectedRace?.id ?? selectedRaceId}
            changes={changes}
            setChanges={setChanges}
            onRun={counterfactual.run}
            isRunning={counterfactual.isRunning}
          />
          {counterfactual.result?.explanation && (
            <div className="sim-note" style={{ margin: "0 14px 12px" }}>
              ✓ {counterfactual.result.explanation}
            </div>
          )}
        </div>
      </div>
    </>
  );
}