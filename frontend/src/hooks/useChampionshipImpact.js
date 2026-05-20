import { useCallback, useState } from "react";

import { fetchChampionshipImpact } from "../api/apexClient.js";

export function useChampionshipImpact() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (raceId, changes) => {
    if (!raceId) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchChampionshipImpact(raceId, changes ?? []);
      setData(result);
    } catch (err) {
      setError(err?.response?.data?.detail ?? err?.message ?? "Request failed");
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => setData(null), []);

  return { data, isLoading, error, load, reset };
}
