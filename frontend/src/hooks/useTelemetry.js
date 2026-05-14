import { useEffect, useRef, useState } from "react";
import { fetchLapTelemetry } from "../api/apexClient.js";

export function useTelemetry(raceId, currentLap) {
  const [telemetry, setTelemetry] = useState(null);
  const cacheRef = useRef({});

  useEffect(() => {
    if (!raceId || !currentLap) {
      setTelemetry(null);
      return;
    }

    const key = `${raceId}-${currentLap}`;
    let ignore = false;

    // Return cached data immediately
    if (cacheRef.current[key]) {
      setTelemetry(cacheRef.current[key]);
      return;
    }

    setTelemetry(null);

    fetchLapTelemetry(raceId, currentLap)
      .then((data) => {
        if (ignore) return;
        if (data.drivers?.length > 0) {
          cacheRef.current[key] = data;
          setTelemetry(data);
        }
      })
      .catch(() => {
        if (!ignore) setTelemetry(null);
      });

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

    return () => {
      ignore = true;
    };
  }, [raceId, currentLap]);

  return telemetry;
}