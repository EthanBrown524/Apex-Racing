import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { SkeletonCard, SkeletonList } from "../components/Skeleton/Skeleton.jsx";
import { StatStrip } from "../components/StatHero/StatHero.jsx";
import { fetchRaces } from "../api/apexClient.js";
import { sampleRaces } from "../data/sampleData.js";
import { findSeason } from "../data/seasons.js";
import { useStats } from "../hooks/useStats.js";

const YEARS = [2024, 2023, 2022, 2021, 2020, 2019];

export default function LibraryPage() {
  const { year: yearParam } = useParams();
  const initialYear = yearParam ? Number(yearParam) : YEARS[0];

  const [races, setRaces] = useState([]);
  const [status, setStatus] = useState("loading");
  const [year, setYear] = useState(initialYear);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { data: stats } = useStats();

  const scoped = Boolean(yearParam);
  const season = scoped ? findSeason(year) : null;

  useEffect(() => {
    if (yearParam) setYear(Number(yearParam));
  }, [yearParam]);

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
      .filter(
        (r) =>
          !q ||
          (r.name && r.name.toLowerCase().includes(q)) ||
          (r.circuit_name && r.circuit_name.toLowerCase().includes(q))
      )
      .sort((a, b) => (a.round ?? 0) - (b.round ?? 0));
  }, [races, year, query]);

  function changeYear(y) {
    setYear(y);
    if (scoped) navigate(`/seasons/${y}`);
  }

  return (
    <div className="library-shell">
      <div className="hero">
        {scoped && (
          <div className="hero-breadcrumb">
            <Link to="/seasons">Seasons</Link> <span>/</span> <span>{year}</span>
          </div>
        )}
        <div className="hero-eyebrow" style={{ color: season?.accent ?? "var(--f1-red)" }}>
          {season ? `${season.year} - ${season.champion.team}` : "RACE LIBRARY"}
        </div>
        <div className="hero-title">
          {season ? season.tagline : "Rewrite the past, race by race."}
        </div>
        {season ? (
          <p className="hero-sub">{season.narrative}</p>
        ) : (
          <p className="hero-sub">
            Browse every Grand Prix from 2019 to 2024. Pick one to replay it on the Time
            Machine, run alternate strategies in the What-If Lab, or have Granite solve
            a Glory Path for your favourite driver.
          </p>
        )}
      </div>

      {stats && (
        <StatStrip
          items={[
            { label: "Grand Prix", value: stats.headline?.grand_prix ?? 0, accent: "#e8002d" },
            { label: "Laps", value: stats.headline?.laps_recorded ?? 0, accent: "#4cc9f0" },
            { label: "Pit stops", value: stats.headline?.pit_stops ?? 0, accent: "#e7c04b" },
            { label: "Data points", value: stats.headline?.total_data_points ?? 0, accent: "#2fbf71" },
          ]}
        />
      )}

      <div className="library-toolbar">
        {(yearsAvailable.length ? yearsAvailable : YEARS).map((y) => (
          <button
            key={y}
            type="button"
            className={`year-pill ${y === year ? "active" : ""}`}
            onClick={() => changeYear(y)}
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

      {status === "loading" ? (
        <div className="race-grid">
          <SkeletonList rows={8} Component={SkeletonCard} />
        </div>
      ) : visible.length === 0 ? (
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
