import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import WhatIfPanel from "../components/WhatIfPanel/WhatIfPanel.jsx";
import { compareScenarios, fetchRaces } from "../api/apexClient.js";
import { sampleRaces } from "../data/sampleData.js";

function DeltaArrow({ delta }) {
  if (delta == null) return <span className="delta-na">·</span>;
  if (delta === 0) return <span className="delta-flat">0</span>;
  if (delta > 0) return <span className="delta-up">↑ +{delta}</span>;
  return <span className="delta-down">↓ {delta}</span>;
}

export default function ComparePage() {
  const { raceId: paramRaceId } = useParams();
  const [races, setRaces] = useState([]);
  const [raceId, setRaceId] = useState(paramRaceId ? Number(paramRaceId) : null);
  const [scenarioA, setScenarioA] = useState([]);
  const [scenarioB, setScenarioB] = useState([]);
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRaces()
      .then((data) => setRaces(data?.length ? data : sampleRaces))
      .catch(() => setRaces(sampleRaces));
  }, []);

  useEffect(() => {
    if (raceId == null && races.length) setRaceId(races[0].id);
  }, [races, raceId]);

  const selectedRace = useMemo(
    () => races.find((r) => r.id === Number(raceId)),
    [races, raceId]
  );

  async function runCompare() {
    if (!raceId) return;
    setIsRunning(true);
    setError(null);
    try {
      const data = await compareScenarios(
        raceId,
        scenarioA,
        scenarioB,
        "Scenario A",
        "Scenario B"
      );
      setResult(data);
    } catch (err) {
      setError(err?.message || "Compare failed");
    } finally {
      setIsRunning(false);
    }
  }

  const diff = result?.diff ?? [];

  return (
    <>
      <div className="race-bar">
        <select
          className="race-select"
          value={raceId ?? ""}
          onChange={(e) => {
            setRaceId(Number(e.target.value));
            setResult(null);
          }}
        >
          {races.map((race) => (
            <option key={race.id} value={race.id}>
              {race.season} - {race.name}
            </option>
          ))}
        </select>
        <div className="meta-pills">
          <div className="meta-pill">
            Circuit <strong>{selectedRace?.circuit_name ?? "-"}</strong>
          </div>
          <div className="meta-pill">
            Round <strong>{selectedRace?.round ?? "-"}</strong>
          </div>
          <div className="meta-pill">
            Mode <strong>Compare A vs B</strong>
          </div>
        </div>
      </div>

      <div className="compare-shell">
        <div className="compare-rail">
          <div className="compare-rail-head">Scenario A</div>
          <WhatIfPanel
            raceId={raceId}
            changes={scenarioA}
            setChanges={setScenarioA}
            onRun={() => {}}
            isRunning={false}
          />
        </div>

        <div className="compare-center">
          <div className="compare-action">
            <button
              type="button"
              className="button primary big"
              onClick={runCompare}
              disabled={isRunning || (!scenarioA.length && !scenarioB.length)}
            >
              {isRunning ? "Comparing..." : "Compare A vs B"}
            </button>
            <p className="compare-hint">
              Both scenarios run against <strong>{selectedRace?.name ?? "-"}</strong>.
              The final-lap position for each driver is computed under each
              scenario; the delta shows how their finish changes from A to B.
            </p>
          </div>

          {error && <div className="empty">Error: {error}</div>}

          {result && (
            <>
              <div className="compare-summary">
                <div className="compare-summary-col">
                  <div className="compare-summary-eyebrow">A top 5</div>
                  <ol>
                    {(result.a?.alt_top5 ?? []).map((code) => (
                      <li key={`a-${code}`}>{code}</li>
                    ))}
                  </ol>
                </div>
                <div className="compare-summary-col">
                  <div className="compare-summary-eyebrow">B top 5</div>
                  <ol>
                    {(result.b?.alt_top5 ?? []).map((code) => (
                      <li key={`b-${code}`}>{code}</li>
                    ))}
                  </ol>
                </div>
              </div>

              <table className="table compare-table">
                <thead>
                  <tr>
                    <th>Driver</th>
                    <th>A finish</th>
                    <th>B finish</th>
                    <th>Δ (A→B)</th>
                  </tr>
                </thead>
                <tbody>
                  {diff.map((row) => (
                    <tr key={row.code}>
                      <td>
                        <Link
                          to={`/driver/${row.code}/${selectedRace?.season ?? ""}`}
                          className="driver-code"
                        >
                          {row.code}
                        </Link>
                      </td>
                      <td>{row.a_pos != null ? `P${row.a_pos}` : "DNF"}</td>
                      <td>{row.b_pos != null ? `P${row.b_pos}` : "DNF"}</td>
                      <td>
                        <DeltaArrow delta={row.delta} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>

        <div className="compare-rail">
          <div className="compare-rail-head">Scenario B</div>
          <WhatIfPanel
            raceId={raceId}
            changes={scenarioB}
            setChanges={setScenarioB}
            onRun={() => {}}
            isRunning={false}
          />
        </div>
      </div>
    </>
  );
}
