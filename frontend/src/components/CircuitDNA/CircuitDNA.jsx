import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

export default function CircuitDNA({ dna }) {
  const safeDna = dna || { overtaking: 0, tire_deg: 0, safety_car_prob: 0, weather_risk: 0 };
  const data = [
    { name: "Overtaking", value: safeDna.overtaking ?? 0 },
    { name: "Tire Deg", value: safeDna.tire_deg ?? 0 },
    { name: "Safety Car", value: safeDna.safety_car_prob ?? 0 },
    { name: "Weather", value: safeDna.weather_risk ?? 0 },
  ].map((item) => ({ ...item, value: Math.round((item.value ?? 0) * 100) }));

  return (
    <div style={{ background: "var(--bg-1)", border: "1px solid var(--line)", borderRadius: 12, padding: 16 }}>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <RadarChart data={data}>
            <PolarGrid stroke="rgba(248, 244, 234, 0.18)" />
            <PolarAngleAxis dataKey="name" tick={{ fill: "#f0ece0", fontSize: 12 }} />
            <Radar dataKey="value" fill="#e8002d" fillOpacity={0.32} stroke="#e8002d" strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, marginTop: 12 }}>
        {data.map((d) => (
          <div key={d.name} style={{ fontSize: 11, color: "var(--text-mid)" }}>
            <span style={{ color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: 0.3, fontWeight: 700, fontSize: 10 }}>
              {d.name}
            </span>{" "}
            <strong style={{ color: "var(--text)", marginLeft: 6 }}>{d.value}%</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
