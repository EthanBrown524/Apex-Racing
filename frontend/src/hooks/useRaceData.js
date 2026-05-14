import { useEffect, useRef, useState } from "react";

import { fetchCircuitPath, fetchRaceLaps, fetchRaces } from "../api/apexClient.js";
import { sampleLapData, sampleRaces } from "../sampleData.js";

export function useRaceData(selectedRaceId) {
  const [races, setRaces] = useState([]);
  const [lapData, setLapData] = useState(sampleLapData);
  const [circuitPath, setCircuitPath] = useState([]);
  const [status, setStatus] = useState("loading");
  const lastFetchedRaceId = useRef(null);
  const circuitCache = useRef({});
  const lapCache = useRef({});

  useEffect(() => {
    fetchRaces()
      .then((data) => {
        if (data.length > 0) {
          setRaces(data);
          setStatus("live");
        }
      })
      .catch(() => {
        setRaces(sampleRaces);
        setStatus("sample");
      });
  }, []);

  const selectedRace = races.length > 0
    ? (races.find((r) => r.id === Number(selectedRaceId)) ?? races[0])
    : null;

  useEffect(() => {
    if (!selectedRace) return;

    // Set circuit path immediately from cache if available
    if (selectedRace.circuit_id && circuitCache.current[selectedRace.circuit_id]) {
      setCircuitPath(circuitCache.current[selectedRace.circuit_id]);
    } else {
      setCircuitPath([]);
    }

    // Fetch circuit path if not cached yet
    if (selectedRace.circuit_id && !circuitCache.current[selectedRace.circuit_id]) {
      fetchCircuitPath(selectedRace.circuit_id)
        .then((data) => {
          if (data.path?.length) {
            circuitCache.current[selectedRace.circuit_id] = data.path;
            setCircuitPath(data.path);
          }
        })
        .catch(() => {});
    }

    // Skip if already fetched laps for this race
    if (lastFetchedRaceId.current === selectedRace.id) return;
    lastFetchedRaceId.current = selectedRace.id;

    // Use cached laps if available
    if (lapCache.current[selectedRace.id]) {
      setLapData(lapCache.current[selectedRace.id]);
      return;
    }

    fetchRaceLaps(selectedRace.id)
      .then((data) => {
        if (data.laps?.length) {
          lapCache.current[selectedRace.id] = data;
          setLapData(data);
        }
      })
      .catch(() => setLapData(sampleLapData));
  }, [selectedRace]);

  return { races, selectedRace, lapData, circuitPath, status };
}
