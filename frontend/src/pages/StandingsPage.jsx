import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { apexClient, fetchRaces } from "../api/apexClient.js";

/* Standings page - aggregates RaceResult.points across the season by hitting
   /races for the season's race list and /races/{id}/results... but we don't
   have a /results endpoint yet, so we instead fan out across
   /drivers/{code}/season-points/{year} for a stable code list seeded from
   the race results we *do* have via /races. Pure client-side aggregation. */

const KNOWN_CODES = [
  "VER", "HAM", "LEC", "PER", "SAI", "NOR", "RUS", "ALO", "OCO", "GAS",
  "STR", "BOT", "ZHO", "ALB", "TSU", "PIA", "MAG", "HUL", "DEV", "SAR",
  "RIC", "MSC", "LAT", "RAI", "GIO", "VET", "KVY", "MAZ", "KUB",
];

export default function StandingsPage() {
  const { year: yearParam } = useParams();
  const year = Number(yearParam) || new Date().getFullYear();
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    setStatus("loading");
    // Fan out one /drivers/.../season-points/year call per known code.
    // Each call is small. Skip 404s silently.
    Promise.all(
      KNOWN_CODES.map((code) =>
        apexClient
          .get(`/drivers/${code}/season-points/${year}`)
          .then((r) => r.data)
          .catch(() => null)
      )
    ).then((results) => {
      const live = results
        .filter((r) => r && r.races && r.races.length > 0)
        .map((r) => ({
          code: r.driver_code,
          name: r.driver_name || r.driver_code,
          points: r.total_points,
          races: r.races.length,
        }));
      live.sort((a, b) => b.points - a.points);
      setRows(live);
      setStatus(live.length ? "live" : "empty");
    });
  }, [year]);

  const top = rows[0];

  return (
    <div className="library-shell">
      <div className="hero">
        <div className="hero-eyebrow">DRIVERS' CHAMPIONSHIP · {year}</div>
        <div className="hero-title">
          {status === "empty"
            ? `No ${year} results ingested yet`
            : top
              ? `${top.name} leads with ${top.points} pts`
              : `Loading ${year} standings...`}
        </div>
        <p className="hero-sub">
          Aggregated client-side from per-driver season-points. Run the bulk
          ingestion (<code>python -m ingestion.run_bulk --years {year}</code>) for
          a complete view.
        </p>
      </div>

      {rows.length > 0 ? (
        <section className="standings-section">
          <table className="table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Driver</th>
                <th>Code</th>
                <th>Races</th>
                <th>Points</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={row.code}>
                  <td>{i + 1}</td>
                  <td>{row.name}</td>
                  <td>
                    <Link to={`/driver/${row.code}/${year}`} className="driver-code">
                      {row.code}
                    </Link>
                  </td>
                  <td>{row.races}</td>
                  <td>
                    <strong>{row.points}</strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : (
        status !== "loading" && (
          <div className="empty">
            No standings available for {year}. Open the
            {" "}
            <Link to="/seasons">Seasons</Link>
            {" "}
            page to ingest data.
          </div>
        )
      )}

      <div className="driver-footer">
        <Link to="/seasons" className="button secondary">
          Browse seasons
        </Link>
      </div>
    </div>
  );
}
