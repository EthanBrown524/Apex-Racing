import { useEffect, useState } from "react";

import CircuitDNA from "../components/CircuitDNA/CircuitDNA.jsx";
import ForecastDashboard from "../components/ForecastDashboard/ForecastDashboard.jsx";
import { fetchForecast } from "../api/apexClient.js";
import { sampleForecast } from "../sampleData.js";

export default function ForecastPage() {
  const [forecast, setForecast] = useState(sampleForecast);

  useEffect(() => {
    let active = true;
    fetchForecast(1)
      .then((data) => {
        if (active && data.predictions?.length) {
          setForecast(data);
        }
      })
      .catch(() => setForecast(sampleForecast));
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="wide-grid">
      <div className="stack">
        <ForecastDashboard forecast={forecast} />
        <section className="panel panel-pad">
          <h2>Risk Factors</h2>
          <ul className="risk-list">
            {forecast.risk_factors.map((factor) => (
              <li key={factor}>{factor}</li>
            ))}
          </ul>
        </section>
      </div>
      <CircuitDNA dna={forecast.circuit_dna} />
    </main>
  );
}

