import { useState } from "react";

import { simulateCounterfactual } from "../api/apexClient.js";

export function useCounterfactual() {
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  async function run(raceId, changes) {
    setIsRunning(true);
    try {
      const data = await simulateCounterfactual(raceId, changes);
      setResult(data);
      return data;
    } catch {
      const fallback = {
        alt_laps: [],
        explanation: "Counterfactual API is not running yet.",
        changes
      };
      setResult(fallback);
      return fallback;
    } finally {
      setIsRunning(false);
    }
  }

  return { result, isRunning, run };
}

