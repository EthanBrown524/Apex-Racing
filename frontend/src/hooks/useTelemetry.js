import { useEffect, useRef, useState } from "react";
import { fetchLapTelemetry } from "../api/apexClient.js";

export function useTelemetry(raceId, currentLap) {
  const [telemetry, setTelemetry] = useState(null);
  const cacheRef = useRef({});

  useEffect(() => {
    if (!raceId || !currentLap) return;

    const key = `${raceId}-${currentLap}`;

    // Return cached data immediately
    if (cacheRef.current[key]) {
      setTelemetry(cacheRef.current[key]);
      return;
    }

    fetchLapTelemetry(raceId, currentLap)
      .then((data) => {
        if (data.drivers?.length > 0) {
          cacheRef.current[key] = data;
          setTelemetry(data);
        }
      })
      .catch(() => setTelemetry(null));

    // Prefetch next lap
    const nextKey = `${raceId}-${currentLap + 1}`;
    if (!cacheRef.current[nextKey]) {
      fetchLapTelemetry(raceId, currentLap + 1)
        .then((data) => {
          if (data.drivers?.length > 0) {
            cacheRef.current[nextKey] = data;
          }
        })
        .catch(() => {});
    }
  }, [raceId, currentLap]);

  return telemetry;
}