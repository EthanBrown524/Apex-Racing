import { useCallback, useState } from "react";
import { fetchCommentary } from "../api/apexClient.js";

export function useCommentary() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (raceId, upToLap) => {
    if (!raceId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchCommentary(raceId, upToLap);
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail ?? err?.message ?? "Request failed");
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { data, isLoading, error, load };
}
