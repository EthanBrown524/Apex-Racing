// Offline-mode fallback. Lets the Library + hero stats look impressive
// even before any ingestion has happened.

export const sampleRaces = [
  // 2024
  { id: 1001, season: 2024, round: 1,  name: "Bahrain Grand Prix",          circuit_id: 1,  circuit_name: "Bahrain International Circuit",   date: "2024-03-02", total_laps: 57 },
  { id: 1002, season: 2024, round: 7,  name: "Monaco Grand Prix",           circuit_id: 2,  circuit_name: "Circuit de Monaco",                date: "2024-05-26", total_laps: 78 },
  { id: 1003, season: 2024, round: 12, name: "British Grand Prix",          circuit_id: 3,  circuit_name: "Silverstone Circuit",              date: "2024-07-07", total_laps: 52 },
  { id: 1004, season: 2024, round: 18, name: "Singapore Grand Prix",        circuit_id: 4,  circuit_name: "Marina Bay Street Circuit",        date: "2024-09-22", total_laps: 62 },
  { id: 1005, season: 2024, round: 24, name: "Abu Dhabi Grand Prix",        circuit_id: 5,  circuit_name: "Yas Marina Circuit",               date: "2024-12-08", total_laps: 58 },

  // 2023
  { id: 1101, season: 2023, round: 1,  name: "Bahrain Grand Prix",          circuit_id: 1,  circuit_name: "Bahrain International Circuit",   date: "2023-03-05", total_laps: 57 },
  { id: 1102, season: 2023, round: 6,  name: "Monaco Grand Prix",           circuit_id: 2,  circuit_name: "Circuit de Monaco",                date: "2023-05-28", total_laps: 78 },
  { id: 1103, season: 2023, round: 10, name: "British Grand Prix",          circuit_id: 3,  circuit_name: "Silverstone Circuit",              date: "2023-07-09", total_laps: 52 },
  { id: 1104, season: 2023, round: 16, name: "Singapore Grand Prix",        circuit_id: 4,  circuit_name: "Marina Bay Street Circuit",        date: "2023-09-17", total_laps: 62 },
  { id: 1105, season: 2023, round: 22, name: "Abu Dhabi Grand Prix",        circuit_id: 5,  circuit_name: "Yas Marina Circuit",               date: "2023-11-26", total_laps: 58 },

  // 2022
  { id: 1201, season: 2022, round: 1,  name: "Bahrain Grand Prix",          circuit_id: 1,  circuit_name: "Bahrain International Circuit",   date: "2022-03-20", total_laps: 57 },
  { id: 1202, season: 2022, round: 7,  name: "Monaco Grand Prix",           circuit_id: 2,  circuit_name: "Circuit de Monaco",                date: "2022-05-29", total_laps: 78 },
  { id: 1203, season: 2022, round: 14, name: "Belgian Grand Prix",          circuit_id: 6,  circuit_name: "Circuit de Spa-Francorchamps",     date: "2022-08-28", total_laps: 44 },
  { id: 1204, season: 2022, round: 17, name: "Japanese Grand Prix",         circuit_id: 7,  circuit_name: "Suzuka Circuit",                   date: "2022-10-09", total_laps: 28 },
  { id: 1205, season: 2022, round: 21, name: "Brazilian Grand Prix",        circuit_id: 8,  circuit_name: "Autodromo Jose Carlos Pace",       date: "2022-11-13", total_laps: 71 },

  // 2021
  { id: 1301, season: 2021, round: 1,  name: "Bahrain Grand Prix",          circuit_id: 1,  circuit_name: "Bahrain International Circuit",   date: "2021-03-28", total_laps: 56 },
  { id: 1302, season: 2021, round: 5,  name: "Monaco Grand Prix",           circuit_id: 2,  circuit_name: "Circuit de Monaco",                date: "2021-05-23", total_laps: 78 },
  { id: 1303, season: 2021, round: 14, name: "Italian Grand Prix",          circuit_id: 9,  circuit_name: "Autodromo Nazionale di Monza",     date: "2021-09-12", total_laps: 53 },
  { id: 1304, season: 2021, round: 22, name: "Abu Dhabi Grand Prix",        circuit_id: 5,  circuit_name: "Yas Marina Circuit",               date: "2021-12-12", total_laps: 58 },

  // 2020
  { id: 1401, season: 2020, round: 1,  name: "Austrian Grand Prix",         circuit_id: 10, circuit_name: "Red Bull Ring",                    date: "2020-07-05", total_laps: 71 },
  { id: 1402, season: 2020, round: 7,  name: "Belgian Grand Prix",          circuit_id: 6,  circuit_name: "Circuit de Spa-Francorchamps",     date: "2020-08-30", total_laps: 44 },
  { id: 1403, season: 2020, round: 13, name: "Emilia Romagna Grand Prix",   circuit_id: 11, circuit_name: "Autodromo Enzo e Dino Ferrari",    date: "2020-11-01", total_laps: 63 },
  { id: 1404, season: 2020, round: 17, name: "Abu Dhabi Grand Prix",        circuit_id: 5,  circuit_name: "Yas Marina Circuit",               date: "2020-12-13", total_laps: 55 },

  // 2019
  { id: 1501, season: 2019, round: 1,  name: "Australian Grand Prix",       circuit_id: 12, circuit_name: "Albert Park Circuit",              date: "2019-03-17", total_laps: 58 },
  { id: 1502, season: 2019, round: 6,  name: "Monaco Grand Prix",           circuit_id: 2,  circuit_name: "Circuit de Monaco",                date: "2019-05-26", total_laps: 78 },
  { id: 1503, season: 2019, round: 11, name: "German Grand Prix",           circuit_id: 13, circuit_name: "Hockenheimring",                   date: "2019-07-28", total_laps: 64 },
  { id: 1504, season: 2019, round: 16, name: "Japanese Grand Prix",         circuit_id: 7,  circuit_name: "Suzuka Circuit",                   date: "2019-10-13", total_laps: 52 },
  { id: 1505, season: 2019, round: 21, name: "Abu Dhabi Grand Prix",        circuit_id: 5,  circuit_name: "Yas Marina Circuit",               date: "2019-12-01", total_laps: 55 },
];

export const sampleCircuitPath = [
  { x: 0.14, y: 0.56 }, { x: 0.19, y: 0.38 }, { x: 0.34, y: 0.25 },
  { x: 0.52, y: 0.21 }, { x: 0.68, y: 0.28 }, { x: 0.82, y: 0.42 },
  { x: 0.86, y: 0.62 }, { x: 0.76, y: 0.77 }, { x: 0.58, y: 0.81 },
  { x: 0.43, y: 0.72 }, { x: 0.29, y: 0.79 }, { x: 0.16, y: 0.72 },
  { x: 0.14, y: 0.56 },
];

const drivers = [
  { code: "VER", color: "#3671C6" },
  { code: "NOR", color: "#ff8700" },
  { code: "HAM", color: "#00d2be" },
  { code: "PIA", color: "#ff8700" },
  { code: "LEC", color: "#dc0000" },
  { code: "RUS", color: "#00d2be" },
];

export const sampleLapData = {
  race_id: 1102,
  laps: Array.from({ length: 18 }, (_, index) => {
    const lap = index + 1;
    const order = drivers
      .map((driver, driverIndex) => ({
        ...driver,
        score:
          driverIndex +
          Math.sin((lap + driverIndex) * 0.65) * 0.48 +
          (driver.code === "HAM" && lap > 9 ? -0.55 : 0) +
          (driver.code === "NOR" && lap > 12 ? 0.35 : 0),
      }))
      .sort((a, b) => a.score - b.score);

    return {
      lap,
      drivers: order.map((driver, idx) => ({
        code: driver.code,
        color: driver.color,
        position: idx + 1,
        gap_ms: idx === 0 ? 0 : (idx * 1500) + Math.round(Math.random() * 800),
        time_ms: 84000 + Math.round(Math.random() * 1500),
        tire: ["M", "S", "H"][idx % 3],
        in_pit: lap === 14 && driver.code === "HAM",
      })),
    };
  }),
};

export const sampleForecast = {
  predictions: [
    { code: "VER", win_pct: 0.62, strategy: "Track-position cover - undercut on lap 18" },
    { code: "NOR", win_pct: 0.18, strategy: "Aggressive 1-stop, overcut middle stint" },
    { code: "HAM", win_pct: 0.12, strategy: "Off-set 2-stop for traffic-free air" },
    { code: "LEC", win_pct: 0.08, strategy: "Long first stint, gamble on safety car" },
  ],
  circuit_dna: { overtaking: 0.6, tire_deg: 0.45, safety_car_prob: 0.4, weather_risk: 0.3 },
  risk_factors: ["Balanced circuit - free strategic choice"],
};

export const sampleStats = {
  headline: {
    grand_prix: 28,
    laps_recorded: 12400,
    pit_stops: 1180,
    telemetry_points: 84200,
    total_data_points: 97608,
  },
  drivers: 32,
  constructors: 12,
  circuits: 13,
  safety_cars: 41,
  race_results: 560,
  embeddings: 112,
  scenarios: 0,
  telemetry_rows: 280,
  races_with_telemetry: 28,
  races_with_embeddings: 28,
  season_breakdown: [
    { year: 2019, races: 5, expected: 22, progress: 0.23, complete: false },
    { year: 2020, races: 4, expected: 22, progress: 0.18, complete: false },
    { year: 2021, races: 4, expected: 22, progress: 0.18, complete: false },
    { year: 2022, races: 5, expected: 22, progress: 0.23, complete: false },
    { year: 2023, races: 5, expected: 22, progress: 0.23, complete: false },
    { year: 2024, races: 5, expected: 22, progress: 0.23, complete: false },
  ],
  embedding_sources: [
    { source: "race_narrative", count: 100 },
    { source: "fia_decision", count: 12 },
  ],
  years_target: [2019, 2020, 2021, 2022, 2023, 2024],
  total_expected_races: 132,
  overall_progress: 0.21,
};
