import axios from "axios";

export const apexClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 10000
});

export async function fetchRaces() {
  const response = await apexClient.get("/races");
  return response.data;
}

export async function fetchRaceLaps(raceId) {
  const response = await apexClient.get(`/races/${raceId}/laps`);
  return response.data;
}

export async function fetchCircuitPath(circuitId) {
  const response = await apexClient.get(`/circuits/${circuitId}/path`);
  return response.data;
}

export async function simulateCounterfactual(raceId, changes) {
  const response = await apexClient.post("/counterfactual/simulate", { race_id: raceId, changes });
  return response.data;
}

export async function fetchForecast(raceId) {
  const response = await apexClient.get(`/forecast/${raceId}`);
  return response.data;
}

export async function saveScenario(label, raceId, changes) {
  const response = await apexClient.post("/scenarios", { label, race_id: raceId, changes });
  return response.data;
}

export async function fetchScenarios() {
  const response = await apexClient.get("/scenarios");
  return response.data;
}

export async function fetchLapTelemetry(raceId, lap) {
  const response = await apexClient.get(`/races/${raceId}/telemetry/${lap}`);
  return response.data;
}