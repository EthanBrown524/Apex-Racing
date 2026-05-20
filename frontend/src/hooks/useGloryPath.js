import { useState } from "react";
import { solveGloryPath } from "../api/apexClient.js";

export function useGloryPath() {
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  async function solve(raceId, driverCode, targetPosition = 1) {
    setIsRunning(true);
    try {
      const data = await solveGloryPath(raceId, driverCode, targetPosition);
      setResult(data);
    } catch (err) {
      setResult({
        race_id: raceId,
        driver_code: driverCode,
        target_position: targetPosition,
        error: err?.response?.data?.detail ?? err?.message ?? "Request failed",
        applied: [],
        citations: [],
      });
    } finally {
      setIsRunning(false);
    }
  }

  return { result, isRunning, solve };
}
