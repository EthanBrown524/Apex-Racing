import { useCallback, useState } from "react";

import { simulateCounterfactual } from "../api/apexClient.js";

export function useCounterfactual() {
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  const run = useCallback(async (raceId, changes) => {
    setIsRunning(true);
    try {
      const data = await simulateCounterfactual(raceId, changes);
      setResult(data);
      return data;
    } catch {
      const fallback = {
        alt_laps: [],
        explanation: "Counterfactual API is not running yet.",
        changes,
      };
      setResult(fallback);
      return fallback;
    } finally {
      setIsRunning(false);
    }
  }, []);

  const reset = useCallback(() => setResult(null), []);

  return { result, isRunning, run, reset };
}
