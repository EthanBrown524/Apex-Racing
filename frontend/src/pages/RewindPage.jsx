import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import AIChatBox from "../components/AIChatBox/AIChatBox.jsx";
import AINarrator from "../components/AINarrator/AINarrator.jsx";
import Citations from "../components/Citations/Citations.jsx";
import Leaderboard from "../components/Leaderboard/Leaderboard.jsx";
import PlaybackControls from "../components/PlaybackControls/PlaybackControls.jsx";
import TrackCanvas from "../components/TrackCanvas/TrackCanvas.jsx";
import WhatIfPanel from "../components/WhatIfPanel/WhatIfPanel.jsx";
import { useCounterfactual } from "../hooks/useCounterfactual.js";
import { useRaceData } from "../hooks/useRaceData.js";
import { useTelemetry } from "../hooks/useTelemetry.js";

export default function RewindPage() {
  const { raceId: paramRaceId } = useParams();
  const navigate = useNavigate();
  const initialId = paramRaceId ? Number(paramRaceId) : 1;
  const [selectedRaceId, setSelectedRaceId] = useState(initialId);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [currentLap, setCurrentLap] = useState(1);
  const [resetSignal, setResetSignal] = useState(0);
  const [changes, setChanges] = useState([]);
  const [rightPanel, setRightPanel] = useState("whatif"); // whatif | ask
  const { races, selectedRace, lapData, circuitPath, status } = useRaceData(selectedRaceId);
  const counterfactual = useCounterfactual();
  const telemetry = useTelemetry(selectedRace?.id, currentLap);

  const laps = useMemo(() => lapData.laps ?? [], [lapData]);
  const activeLap = useMemo(
    () => laps.find((lap) => lap.lap === currentLap) ?? laps[0],
    [currentLap, laps]
  );

  useEffect(() => {
    if (paramRaceId && Number(paramRaceId) !== selectedRaceId) {
      setSelectedRaceId(Number(paramRaceId));
      setCurrentLap(1);
    }
  }, [paramRaceId, selectedRaceId]);

  const handleLapChange = useCallback((lap) => setCurrentLap(lap), []);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setCurrentLap(1);
    setResetSignal((value) => value + 1);
  }, []);

  function onSelectRace(id) {
    setSelectedRaceId(id);
    setCurrentLap(1);
    if (paramRaceId) navigate(`/rewind/${id}`);
  }

  return (
    <>
      <div className="race-bar">
        <select
          className="race-select"
          value={selectedRace?.id ?? selectedRaceId}
          onChange={(e) => onSelectRace(Number(e.target.value))}
        >
          {races.map((race) => (
            <option key={race.id} value={race.id}>
              {race.season} - {race.name}
            </option>
          ))}
        </select>
        <div className="meta-pills">
          <div className="meta-pill">Circuit <strong>{selectedRace?.circuit_name ?? "-"}</strong></div>
          <div className="meta-pill">Round <strong>{selectedRace?.round ?? "-"}</strong></div>
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
            telemetry={telemetry}
            resetSignal={resetSignal}
          />
          <PlaybackControls
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
            speed={speed}
            setSpeed={setSpeed}
            currentLap={currentLap}
            setCurrentLap={setCurrentLap}
            maxLap={laps.length || 1}
            onReset={handleReset}
          />
          {selectedRace?.id && (
            <AINarrator raceId={selectedRace.id} upToLap={currentLap} />
          )}
        </div>

        <div className="right-col">
          <div className="section-header">
            <span className="section-title">Leaderboard - Lap {currentLap}</span>
            <div style={{ display: "flex", gap: 4 }}>
              <button
                type="button"
                className={`button ${rightPanel === "whatif" ? "primary" : "ghost"}`}
                style={{ fontSize: 10, padding: "4px 8px", minHeight: 0 }}
                onClick={() => setRightPanel("whatif")}
              >
                What-If
              </button>
              <button
                type="button"
                className={`button ${rightPanel === "ask" ? "primary" : "ghost"}`}
                style={{ fontSize: 10, padding: "4px 8px", minHeight: 0 }}
                onClick={() => setRightPanel("ask")}
              >
                Ask APEX
              </button>
            </div>
          </div>
          <Leaderboard lap={activeLap} />

          {rightPanel === "whatif" && (
            <>
              <WhatIfPanel
                raceId={selectedRace?.id ?? selectedRaceId}
                changes={changes}
                setChanges={setChanges}
                onRun={counterfactual.run}
                isRunning={counterfactual.isRunning}
              />
              {counterfactual.result?.explanation && (
                <div className="sim-note" style={{ margin: "0 14px 12px" }}>
                  <strong>Granite:</strong> {counterfactual.result.explanation}
                  <Citations citations={counterfactual.result.citations || []} />
                </div>
              )}
            </>
          )}

          {rightPanel === "ask" && selectedRace?.id && (
            <AIChatBox raceId={selectedRace.id} />
          )}
        </div>
      </div>
    </>
  );
}
