import { useCallback, useState } from "react";

import { fetchRealism } from "../api/apexClient.js";

export function useRealism() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async (raceId, changes) => {
    if (!raceId || !changes?.length) {
      setData(null);
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetchRealism(raceId, changes);
      setData(res);
    } catch {
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => setData(null), []);

  return { data, isLoading, load, reset };
}
