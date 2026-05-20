import axios from "axios";

export const apexClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 60000,
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
  const response = await apexClient.post("/counterfactual/simulate", {
    race_id: raceId,
    changes,
  });
  return response.data;
}

export async function fetchRealism(raceId, changes) {
  const response = await apexClient.post("/counterfactual/realism", {
    race_id: raceId,
    changes,
  });
  return response.data;
}

export async function fetchChampionshipImpact(raceId, changes) {
  const response = await apexClient.post("/championship/impact", {
    race_id: raceId,
    changes,
  });
  return response.data;
}

export async function fetchForecast(raceId) {
  const response = await apexClient.get(`/forecast/${raceId}`);
  return response.data;
}

export async function saveScenario(label, raceId, changes) {
  const response = await apexClient.post("/scenarios", {
    label,
    race_id: raceId,
    changes,
  });
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

export async function solveGloryPath(raceId, driverCode, targetPosition) {
  const response = await apexClient.post("/glory-path/solve", {
    race_id: raceId,
    driver_code: driverCode,
    target_position: targetPosition,
  });
  return response.data;
}

export async function fetchCommentary(raceId, upToLap) {
  const params = upToLap ? { up_to_lap: upToLap } : {};
  const response = await apexClient.get(`/ai/commentary/${raceId}`, { params });
  return response.data;
}

export async function askAI(raceId, question) {
  const response = await apexClient.post("/ai/ask", {
    race_id: raceId,
    question,
  });
  return response.data;
}

export async function fetchShowcase() {
  const response = await apexClient.get("/showcase");
  return response.data;
}

export async function fetchShowcaseScenario(scenarioId) {
  const response = await apexClient.get(`/showcase/${scenarioId}`);
  return response.data;
}

export async function fetchHealth() {
  const response = await apexClient.get("/health");
  return response.data;
}
