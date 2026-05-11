export default function Leaderboard({ lap }) {
  const drivers = [...(lap?.drivers ?? [])].sort((a, b) => a.position - b.position);

  const posClass = (pos) => {
    if (pos === 1) return "lboard-pos p1";
    if (pos === 2) return "lboard-pos p2";
    if (pos === 3) return "lboard-pos p3";
    return "lboard-pos";
  };

  return (
    <div className="lboard">
      {drivers.map((driver) => (
        <div className="lboard-row" key={driver.code}>
          <div className={posClass(driver.position)}>{driver.position}</div>
          <div
            className="driver-tag"
            style={{
              background: `${driver.color ?? "#888"}22`,
              color: driver.color ?? "#888",
            }}
          >
            {driver.code}
          </div>
          <div className="driver-name">{driver.code}</div>
          <div className={`gap-val${driver.position === 1 ? " leader" : ""}`}>
            {driver.position === 1 ? "Leader" : `+${((driver.gap_ms ?? 0) / 1000).toFixed(1)}s`}
          </div>
          <div className={`tire-badge${driver.in_pit ? " pit" : ""}`}>
            {driver.in_pit ? "PIT" : driver.tire ?? "—"}
          </div>
        </div>
      ))}
    </div>
  );
}