import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { fetchRaces } from "../api/apexClient.js";
import { sampleRaces } from "../sampleData.js";

const YEARS = [2024, 2023, 2022, 2021, 2020, 2019];

export default function LibraryPage() {
  const [races, setRaces] = useState([]);
  const [status, setStatus] = useState("loading");
  const [year, setYear] = useState(YEARS[0]);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchRaces()
      .then((data) => {
        if (data?.length) {
          setRaces(data);
          setStatus("live");
        } else {
          setRaces(sampleRaces);
          setStatus("sample");
        }
      })
      .catch(() => {
        setRaces(sampleRaces);
        setStatus("sample");
      });
  }, []);

  const yearsAvailable = useMemo(() => {
    const years = new Set(races.map((r) => r.season).filter(Boolean));
    return YEARS.filter((y) => years.has(y));
  }, [races]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return races
      .filter((r) => r.season === year)
      .filter((r) =>
        !q ||
        (r.name && r.name.toLowerCase().includes(q)) ||
        (r.circuit_name && r.circuit_name.toLowerCase().includes(q))
      )
      .sort((a, b) => (a.round ?? 0) - (b.round ?? 0));
  }, [races, year, query]);

  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">RACE LIBRARY</div>
        <div className="hero-title">Rewrite the past, race by race.</div>
        <p className="hero-sub">
          Browse every Grand Prix from 2019 to 2024. Pick one to replay it on the Time
          Machine, run alternate strategies in the What-If Lab, or have Granite solve
          a Glory Path for your favourite driver.
        </p>
      </div>

      <div className="library-toolbar">
        {(yearsAvailable.length ? yearsAvailable : YEARS).map((y) => (
          <button
            key={y}
            type="button"
            className={`year-pill ${y === year ? "active" : ""}`}
            onClick={() => setYear(y)}
          >
            {y}
          </button>
        ))}
        <input
          className="search-input"
          placeholder="Search race or circuit..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <span className="meta-pill">Source <strong>{status}</strong></span>
      </div>

      {visible.length === 0 ? (
        <div className="empty">
          No races for {year}. Run <code>python -m ingestion.run_bulk --years {year}</code> to ingest them.
        </div>
      ) : (
        <div className="race-grid">
          {visible.map((race) => (
            <button
              key={race.id}
              className="race-card"
              type="button"
              onClick={() => navigate(`/rewind/${race.id}`)}
            >
              <div className="race-card-year">{race.season} - Round {race.round}</div>
              <div className="race-card-title">{race.name}</div>
              <div className="race-card-meta">
                <span>{race.circuit_name ?? "Unknown circuit"}</span>
                <span className="race-card-round">{race.total_laps ?? "?"} laps</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
