export default function Leaderboard({ lap }) {
  const drivers = [...(lap?.drivers ?? [])].sort((a, b) => a.position - b.position);

  return (
    <section className="panel panel-pad">
      <h2>Leaderboard</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Pos</th>
            <th>Driver</th>
            <th>Gap</th>
            <th>Tire</th>
          </tr>
        </thead>
        <tbody>
          {drivers.map((driver) => (
            <tr key={driver.code}>
              <td>{driver.position}</td>
              <td>
                <span className="driver-code">{driver.code}</span>
              </td>
              <td>{driver.gap_ms ? `+${(driver.gap_ms / 1000).toFixed(1)}s` : "Leader"}</td>
              <td>{driver.in_pit ? "PIT" : driver.tire ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

