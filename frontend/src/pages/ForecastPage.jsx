import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import CircuitDNA from "../components/CircuitDNA/CircuitDNA.jsx";
import ForecastDashboard from "../components/ForecastDashboard/ForecastDashboard.jsx";
import { fetchForecast, fetchRaces } from "../api/apexClient.js";
import { sampleRaces } from "../data/sampleData.js";

const SAMPLE_FORECAST = {
  predictions: [
    { code: "VER", win_pct: 0.62, strategy: "Track-position cover - undercut on lap 18" },
    { code: "NOR", win_pct: 0.18, strategy: "Aggressive 1-stop, overcut middle stint" },
    { code: "HAM", win_pct: 0.12, strategy: "Off-set 2-stop for traffic-free air" },
    { code: "LEC", win_pct: 0.08, strategy: "Long first stint, gamble on safety car" },
  ],
  circuit_dna: {
    overtaking: 0.6,
    tire_deg: 0.45,
    safety_car_prob: 0.4,
    weather_risk: 0.3,
  },
  risk_factors: ["Balanced circuit - free strategic choice"],
};

export default function ForecastPage() {
  const { raceId: paramRaceId } = useParams();
  const [races, setRaces] = useState([]);
  const [raceId, setRaceId] = useState(paramRaceId ? Number(paramRaceId) : null);
  const [forecast, setForecast] = useState(SAMPLE_FORECAST);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    fetchRaces()
      .then((data) => setRaces(data?.length ? data : sampleRaces))
      .catch(() => setRaces(sampleRaces));
  }, []);

  useEffect(() => {
    if (raceId == null && races.length) setRaceId(races[0].id);
  }, [races, raceId]);

  useEffect(() => {
    if (!raceId) return;
    fetchForecast(raceId)
      .then((data) => {
        if (data?.predictions?.length || data?.circuit_dna) {
          setForecast(data);
          setStatus("live");
        } else {
          setForecast(SAMPLE_FORECAST);
          setStatus("sample");
        }
      })
      .catch(() => {
        setForecast(SAMPLE_FORECAST);
        setStatus("sample");
      });
  }, [raceId]);

  const selectedRace = useMemo(
    () => races.find((r) => r.id === Number(raceId)),
    [races, raceId]
  );

  return (
    <>
      <div className="race-bar">
        <select
          className="race-select"
          value={raceId ?? ""}
          onChange={(e) => setRaceId(Number(e.target.value))}
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
        {forecast?.source && (
          <div className="meta-pill">
            Ranking <strong>{forecast.source === "granite" ? "Granite" : "Heuristic"}</strong>
          </div>
        )}
        </div>
      </div>

      <div className="forecast-shell">
        <section>
          <h2>Win probabilities</h2>
          <ForecastDashboard predictions={forecast.predictions ?? []} />

          {forecast.risk_factors?.length > 0 && (
            <div style={{ marginTop: 18 }}>
              <h2>Risk factors</h2>
              <ul className="risk-list">
                {forecast.risk_factors.map((risk, i) => (
                  <li key={i}>{risk}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section>
          <h2>Circuit DNA</h2>
          <CircuitDNA dna={forecast.circuit_dna} />
        </section>
      </div>
    </>
  );
}
