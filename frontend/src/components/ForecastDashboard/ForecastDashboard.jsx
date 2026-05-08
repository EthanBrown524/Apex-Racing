export default function ForecastDashboard({ forecast }) {
  return (
    <section className="panel panel-pad">
      <h2>Race Forecast</h2>
      <div className="forecast-list">
        {forecast.predictions.map((prediction) => (
          <div className="forecast-row" key={prediction.driver}>
            <span className="driver-code">{prediction.driver}</span>
            <div>
              <div className="bar">
                <span style={{ width: `${prediction.win_pct}%` }} />
              </div>
              <small>{prediction.strategy}</small>
            </div>
            <strong>{prediction.win_pct}%</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

