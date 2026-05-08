import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

export default function CircuitDNA({ dna }) {
  const data = [
    { name: "Overtaking", value: dna.overtaking },
    { name: "Tire Deg", value: dna.tire_deg },
    { name: "Safety Car", value: dna.safety_car_prob },
    { name: "Weather", value: dna.weather_risk }
  ].map((item) => ({ ...item, value: Math.round(item.value * 100) }));

  return (
    <section className="panel panel-pad">
      <h2>Circuit DNA</h2>
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <RadarChart data={data}>
            <PolarGrid stroke="rgba(248, 244, 234, 0.2)" />
            <PolarAngleAxis dataKey="name" tick={{ fill: "#f8f4ea", fontSize: 12 }} />
            <Radar dataKey="value" fill="#2fbf71" fillOpacity={0.35} stroke="#2fbf71" />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

