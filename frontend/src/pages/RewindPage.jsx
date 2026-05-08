import { useCallback, useMemo, useState } from "react";

import Leaderboard from "../components/Leaderboard/Leaderboard.jsx";
import PlaybackControls from "../components/PlaybackControls/PlaybackControls.jsx";
import TrackCanvas from "../components/TrackCanvas/TrackCanvas.jsx";
import WhatIfPanel from "../components/WhatIfPanel/WhatIfPanel.jsx";
import { useCounterfactual } from "../hooks/useCounterfactual.js";
import { useRaceData } from "../hooks/useRaceData.js";

export default function RewindPage() {
  const [selectedRaceId, setSelectedRaceId] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [currentLap, setCurrentLap] = useState(1);
  const [changes, setChanges] = useState([]);
  const { races, selectedRace, lapData, circuitPath, status } = useRaceData(selectedRaceId);
  const counterfactual = useCounterfactual();

  const laps = lapData.laps ?? [];
  const activeLap = useMemo(
    () => laps.find((lap) => lap.lap === currentLap) ?? laps[0],
    [currentLap, laps]
  );
  const handleLapChange = useCallback((lap) => setCurrentLap(lap), []);

  return (
    <main className="stack">
      <section className="panel panel-pad">
        <div className="control-row">
          <label className="field">
            <span>Race</span>
            <select
              value={selectedRace?.id ?? selectedRaceId}
              onChange={(event) => {
                setSelectedRaceId(Number(event.target.value));
                setCurrentLap(1);
              }}
            >
              {races.map((race) => (
                <option key={race.id} value={race.id}>
                  {race.season} {race.name}
                </option>
              ))}
            </select>
          </label>
          <div className="metric-strip">
            <div className="metric">
              <span>Circuit</span>
              <strong>{selectedRace?.circuit_name ?? "Pending"}</strong>
            </div>
            <div className="metric">
              <span>Round</span>
              <strong>{selectedRace?.round ?? "-"}</strong>
            </div>
            <div className="metric">
              <span>Source</span>
              <strong>{status}</strong>
            </div>
          </div>
        </div>
      </section>

      <div className="page-grid">
        <div className="stack">
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
        <div className="stack">
          <Leaderboard lap={activeLap} />
          <WhatIfPanel
            raceId={selectedRace?.id ?? selectedRaceId}
            changes={changes}
            setChanges={setChanges}
            onRun={counterfactual.run}
            isRunning={counterfactual.isRunning}
          />
          {counterfactual.result?.explanation && (
            <section className="panel panel-pad">
              <h2>Simulation Note</h2>
              <p>{counterfactual.result.explanation}</p>
            </section>
          )}
        </div>
      </div>
    </main>
  );
}

