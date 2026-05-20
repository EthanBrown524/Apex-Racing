import { getDriverPrimary } from "../../data/teamColors.js";

const TIRE_CLASS = {
  S: "soft",
  M: "medium",
  H: "hard",
  I: "inter",
  W: "wet",
};

export default function Leaderboard({ lap, year = 2023 }) {
  const drivers = [...(lap?.drivers ?? [])].sort((a, b) => a.position - b.position);

  const posClass = (pos) => {
    if (pos === 1) return "lboard-pos p1";
    if (pos === 2) return "lboard-pos p2";
    if (pos === 3) return "lboard-pos p3";
    return "lboard-pos";
  };

  return (
    <div className="lboard">
      {drivers.map((driver) => {
        const color = driver.color ?? getDriverPrimary(driver.code, year);
        const tire = driver.tire?.toUpperCase?.()?.[0] ?? "-";
        const tireClass = TIRE_CLASS[tire] ?? "";
        return (
          <div className="lboard-row" key={driver.code}>
            <div className={posClass(driver.position)}>{driver.position}</div>
            <div
              className="driver-tag"
              style={{
                background: `${color}22`,
                color: color,
              }}
            >
              {driver.code}
            </div>
            <div className="driver-name">{driver.code}</div>
            <div className={`gap-val${driver.position === 1 ? " leader" : ""}`}>
              {driver.position === 1 ? "Leader" : `+${((driver.gap_ms ?? 0) / 1000).toFixed(1)}s`}
            </div>
            <div className={`tire-badge ${driver.in_pit ? "pit" : tireClass}`}>
              {driver.in_pit ? "PIT" : tire}
            </div>
          </div>
        );
      })}
    </div>
  );
}
