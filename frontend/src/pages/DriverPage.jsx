import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  fetchDriverSeasonPoints,
  fetchDriverSummary,
} from "../api/apexClient.js";
import { getDriverPrimary } from "../data/teamColors.js";

export default function DriverPage() {
  const { code = "", year: yearParam } = useParams();
  const driverCode = code.toUpperCase();
  const year = Number(yearParam) || new Date().getFullYear();

  const [summary, setSummary] = useState(null);
  const [season, setSeason] = useState(null);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    setStatus("loading");
    Promise.all([
      fetchDriverSummary(driverCode).catch(() => null),
      fetchDriverSeasonPoints(driverCode, year).catch(() => null),
    ]).then(([s, sp]) => {
      setSummary(s);
      setSeason(sp);
      if (sp?.races?.length) setStatus("live");
      else if (s) setStatus("partial");
      else setStatus("missing");
    });
  }, [driverCode, year]);

  const accent = useMemo(() => getDriverPrimary(driverCode, year), [driverCode, year]);

  const races = season?.races ?? [];
  const chartData = races.map((r) => ({
    round: `R${r.round}`,
    points: r.cumulative_points,
    race: r.race_name,
  }));

  const displayName =
    season?.driver_name ||
    summary?.driver_name ||
    [summary?.forename, summary?.surname].filter(Boolean).join(" ") ||
    driverCode;

  return (
    <div className="library-shell">
      <div className="driver-header" style={{ "--driver-accent": accent }}>
        <div>
          <div className="hero-eyebrow">
            DRIVER · {year}
          </div>
          <div className="driver-header-name">{displayName}</div>
          <div className="driver-header-meta">
            <span className="driver-header-code" style={{ background: `${accent}33`, color: accent }}>
              {driverCode}
            </span>
            {summary?.nationality && <span>{summary.nationality}</span>}
            <span>
              Source: <strong>{status}</strong>
            </span>
          </div>
        </div>
        <div className="driver-header-total">
          <div className="label">Season points</div>
          <div className="val">{season?.total_points ?? "-"}</div>
        </div>
      </div>

      <section className="driver-section">
        <h2>Cumulative championship points</h2>
        {chartData.length === 0 ? (
          <div className="empty">
            No results found for {driverCode} in {year}. Try a different season,
            or run the bulk ingestion to populate the database.
          </div>
        ) : (
          <div className="driver-chart-wrap">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                <XAxis dataKey="round" stroke="#888" fontSize={11} />
                <YAxis stroke="#888" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "#0c1118",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelFormatter={(label, payload) => {
                    const point = payload?.[0]?.payload;
                    return point ? `${label} - ${point.race}` : label;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="points"
                  stroke={accent}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: accent }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="driver-section">
        <h2>Race-by-race</h2>
        {races.length === 0 ? null : (
          <table className="table">
            <thead>
              <tr>
                <th>Round</th>
                <th>Race</th>
                <th>Grid</th>
                <th>Finish</th>
                <th>Points</th>
                <th>Cumulative</th>
              </tr>
            </thead>
            <tbody>
              {races.map((r) => (
                <tr key={r.round}>
                  <td>{r.round}</td>
                  <td>{r.race_name}</td>
                  <td>{r.grid_position ?? "-"}</td>
                  <td>{r.final_position ?? "-"}</td>
                  <td>{r.points}</td>
                  <td>
                    <strong>{r.cumulative_points}</strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="driver-footer">
        <Link to="/seasons" className="button secondary">
          Browse seasons
        </Link>
        <Link to={`/standings/${year}`} className="button ghost">
          {year} standings
        </Link>
      </div>
    </div>
  );
}
