import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import AIChatBox from "../components/AIChatBox/AIChatBox.jsx";
import AINarrator from "../components/AINarrator/AINarrator.jsx";
import ChampionshipImpact from "../components/ChampionshipImpact/ChampionshipImpact.jsx";
import Citations from "../components/Citations/Citations.jsx";
import KeyboardHints from "../components/KeyboardHints/KeyboardHints.jsx";
import Leaderboard from "../components/Leaderboard/Leaderboard.jsx";
import PlaybackControls from "../components/PlaybackControls/PlaybackControls.jsx";
import RealismChip from "../components/RealismChip/RealismChip.jsx";
import TrackCanvas from "../components/TrackCanvas/TrackCanvas.jsx";
import WhatIfPanel from "../components/WhatIfPanel/WhatIfPanel.jsx";
import { useChampionshipImpact } from "../hooks/useChampionshipImpact.js";
import { useCounterfactual } from "../hooks/useCounterfactual.js";
import { useRaceData } from "../hooks/useRaceData.js";
import { useRealism } from "../hooks/useRealism.js";
import { useTelemetry } from "../hooks/useTelemetry.js";

export default function RewindPage() {
  const { raceId: paramRaceId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const initialId = paramRaceId ? Number(paramRaceId) : 1;
  const [selectedRaceId, setSelectedRaceId] = useState(initialId);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [currentLap, setCurrentLap] = useState(1);
  const [resetSignal, setResetSignal] = useState(0);
  const [changes, setChanges] = useState([]);
  const [rightPanel, setRightPanel] = useState("whatif");
  const [showChampionship, setShowChampionship] = useState(false);

  const { races, selectedRace, lapData, circuitPath, status } = useRaceData(selectedRaceId);
  const counterfactual = useCounterfactual();
  const realism = useRealism();
  const championship = useChampionshipImpact();
  const telemetry = useTelemetry(selectedRace?.id, currentLap);

  const laps = useMemo(() => lapData.laps ?? [], [lapData]);
  const activeLap = useMemo(
    () => laps.find((lap) => lap.lap === currentLap) ?? laps[0],
    [currentLap, laps]
  );
  const maxLap = laps.length || 1;

  // Preload scenario from showcase navigation
  useEffect(() => {
    const scenario = location.state;
    if (scenario?.mode === "counterfactual" && scenario.changes) {
      setChanges(scenario.changes);
    }
  }, [location.state]);

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

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((p) => !p);
      } else if (e.key === "ArrowLeft") {
        setCurrentLap((l) => Math.max(1, l - 1));
        setIsPlaying(false);
      } else if (e.key === "ArrowRight") {
        setCurrentLap((l) => Math.min(maxLap, l + 1));
        setIsPlaying(false);
      } else if (e.key === "r" || e.key === "R") {
        handleReset();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [maxLap, handleReset]);

  function onSelectRace(id) {
    setSelectedRaceId(id);
    setCurrentLap(1);
    setChanges([]);
    counterfactual.reset?.();
    realism.reset();
    championship.reset();
    if (paramRaceId) navigate(`/rewind/${id}`);
  }

  function onRunCounterfactual(raceId, list) {
    counterfactual.run(raceId, list);
    realism.load(raceId, list);
    if (showChampionship) championship.load(raceId, list);
  }

  function toggleChampionship() {
    const next = !showChampionship;
    setShowChampionship(next);
    if (next && selectedRace?.id) {
      championship.load(selectedRace.id, changes);
    }
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
            maxLap={maxLap}
            onReset={handleReset}
          />
          <KeyboardHints />
          {selectedRace?.id && (
            <AINarrator raceId={selectedRace.id} upToLap={currentLap} />
          )}
          {showChampionship && (
            <ChampionshipImpact
              data={championship.data}
              isLoading={championship.isLoading}
              error={championship.error}
            />
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
          <Leaderboard lap={activeLap} year={selectedRace?.season} />

          {rightPanel === "whatif" && (
            <>
              <WhatIfPanel
                raceId={selectedRace?.id ?? selectedRaceId}
                changes={changes}
                setChanges={setChanges}
                onRun={onRunCounterfactual}
                isRunning={counterfactual.isRunning}
              />

              {counterfactual.result?.explanation && (
                <div className="sim-note" style={{ margin: "0 14px 12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <strong>Granite</strong>
                    <RealismChip realism={realism.data} isLoading={realism.isLoading} />
                  </div>
                  {counterfactual.result.explanation}
                  <Citations citations={counterfactual.result.citations || []} />
                  <div style={{ marginTop: 8 }}>
                    <button
                      type="button"
                      className={`button ${showChampionship ? "primary" : "ghost"}`}
                      style={{ fontSize: 10, padding: "5px 10px", minHeight: 0 }}
                      onClick={toggleChampionship}
                    >
                      {showChampionship ? "Hide" : "Show"} championship impact
                    </button>
                  </div>
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
