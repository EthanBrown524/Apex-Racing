export default function ForecastDashboard({ predictions = [] }) {
  if (!predictions.length) {
    return <div className="empty">No predictions available.</div>;
  }

  const maxPct = Math.max(...predictions.map((p) => p.win_pct ?? 0));

  return (
    <div className="forecast-list">
      {predictions.map((prediction, i) => {
        const winPct = (prediction.win_pct ?? 0) * 100;
        const widthPct = maxPct ? (prediction.win_pct / maxPct) * 100 : 0;
        return (
          <div className="forecast-row" key={prediction.code ?? i}>
            <span className="driver-code">{prediction.code}</span>
            <div>
              <div className="bar">
                <span style={{ width: `${widthPct}%` }} />
              </div>
              <div className="forecast-strategy">{prediction.strategy}</div>
            </div>
            <strong>{winPct.toFixed(1)}%</strong>
          </div>
        );
      })}
    </div>
  );
}
