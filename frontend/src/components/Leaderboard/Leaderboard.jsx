import { useNavigate } from "react-router-dom";

import { SkeletonList, SkeletonRow } from "../Skeleton/Skeleton.jsx";
import { getDriverPrimary } from "../../data/teamColors.js";

const TIRE_CLASS = {
  S: "soft",
  M: "medium",
  H: "hard",
  I: "inter",
  W: "wet",
};

const TIRE_DONUT_FILL = {
  soft: "#ff2e3a",
  medium: "#f5c441",
  hard: "#f0f0f0",
  inter: "#2fbf71",
  wet: "#2a6cc9",
};

function TireDonut({ kind }) {
  const fill = TIRE_DONUT_FILL[kind] ?? "#888";
  return (
    <svg
      className="tire-donut"
      aria-hidden="true"
      viewBox="0 0 14 14"
      width="11"
      height="11"
    >
      <circle cx="7" cy="7" r="6" fill="none" stroke={fill} strokeWidth="2.5" />
      <circle cx="7" cy="7" r="2" fill={fill} />
    </svg>
  );
}

export default function Leaderboard({ lap, year = 2023 }) {
  const navigate = useNavigate();
  const drivers = [...(lap?.drivers ?? [])].sort((a, b) => a.position - b.position);

  if (!drivers.length) {
    return (
      <div className="lboard">
        <SkeletonList rows={6} Component={SkeletonRow} />
      </div>
    );
  }

  const posClass = (pos) => {
    if (pos === 1) return "lboard-pos p1";
    if (pos === 2) return "lboard-pos p2";
    if (pos === 3) return "lboard-pos p3";
    return "lboard-pos";
  };

  function openDriver(code) {
    if (!code || !year) return;
    navigate(`/driver/${code}/${year}`);
  }

  return (
    <div className="lboard">
      {drivers.map((driver) => {
        const color = driver.color ?? getDriverPrimary(driver.code, year);
        const tire = driver.tire?.toUpperCase?.()?.[0] ?? "-";
        const tireClass = TIRE_CLASS[tire] ?? "";
        return (
          <div className="lboard-row" key={driver.code}>
            <div className={posClass(driver.position)}>{driver.position}</div>
            <button
              type="button"
              className="driver-tag"
              style={{
                background: `${color}22`,
                color: color,
              }}
              onClick={() => openDriver(driver.code)}
              title={`Open ${driver.code} season`}
            >
              {driver.code}
            </button>
            <div className="driver-name">{driver.code}</div>
            <div className={`gap-val${driver.position === 1 ? " leader" : ""}`}>
              {driver.position === 1 ? "Leader" : `+${((driver.gap_ms ?? 0) / 1000).toFixed(1)}s`}
            </div>
            <div className={`tire-badge ${driver.in_pit ? "pit" : tireClass}`}>
              {driver.in_pit ? (
                "PIT"
              ) : (
                <>
                  {tireClass && <TireDonut kind={tireClass} />}
                  <span>{tire}</span>
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
