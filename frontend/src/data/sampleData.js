export const sampleRaces = [
  {
    id: 1,
    name: "British Grand Prix",
    season: 2023,
    round: 10,
    circuit_id: 1,
    circuit_name: "Silverstone Circuit",
    date: "2023-07-09",
    total_laps: 18
  }
];

export const sampleCircuitPath = [
  { x: 0.14, y: 0.56 },
  { x: 0.19, y: 0.38 },
  { x: 0.34, y: 0.25 },
  { x: 0.52, y: 0.21 },
  { x: 0.68, y: 0.28 },
  { x: 0.82, y: 0.42 },
  { x: 0.86, y: 0.62 },
  { x: 0.76, y: 0.77 },
  { x: 0.58, y: 0.81 },
  { x: 0.43, y: 0.72 },
  { x: 0.29, y: 0.79 },
  { x: 0.16, y: 0.72 },
  { x: 0.14, y: 0.56 }
];

const drivers = [
  { code: "VER", color: "#4cc9f0" },
  { code: "NOR", color: "#f24822" },
  { code: "HAM", color: "#b98cff" },
  { code: "PIA", color: "#2fbf71" },
  { code: "LEC", color: "#e7c04b" },
  { code: "RUS", color: "#f8f4ea" }
];

export const sampleLapData = {
  race_id: 1,
  laps: Array.from({ length: 18 }, (_, index) => {
    const lap = index + 1;
    const order = drivers
      .map((driver, driverIndex) => ({
        ...driver,
        score:
          driverIndex +
          Math.sin((lap + driverIndex) * 0.65) * 0.48 +
          (driver.code === "HAM" && lap > 9 ? -0.55 : 0) +
          (driver.code === "NOR" && lap > 12 ? 0.35 : 0)
      }))
      .sort((a, b) => a.score - b.score);

    return {
      lap,
      drivers: order.map((driver, positionIndex) => ({
        code: driver.code,
        color: driver.color,
        position: positionIndex + 1,
        gap_ms: positionIndex === 0 ? 0 : positionIndex * 1850 + lap * 75,
        tire: lap < 8 ? "MED" : lap < 14 ? "HARD" : "SOFT",
        in_pit: (driver.code === "HAM" && lap === 9) || (driver.code === "NOR" && lap === 12)
      }))
    };
  })
};

export const sampleForecast = {
  race_id: 1,
  predictions: [
    { driver: "VER", win_pct: 38, podium_pct: 76, strategy: "Medium-Hard" },
    { driver: "NOR", win_pct: 24, podium_pct: 63, strategy: "Medium-Hard-Soft" },
    { driver: "HAM", win_pct: 18, podium_pct: 57, strategy: "Hard-Medium" },
    { driver: "LEC", win_pct: 11, podium_pct: 41, strategy: "Soft-Hard" }
  ],
  circuit_dna: {
    overtaking: 0.54,
    tire_deg: 0.68,
    safety_car_prob: 0.32,
    weather_risk: 0.46
  },
  risk_factors: [
    "High-speed tire load increases late-stint degradation.",
    "Undercut window opens earlier if track temperature climbs.",
    "Safety car probability favors split strategy calls after lap 12."
  ]
};

