import { useEffect, useRef, useState } from "react";

import { fetchCircuitPath, fetchRaceLaps, fetchRaces } from "../api/apexClient.js";
import { sampleCircuitPath, sampleLapData, sampleRaces } from "../sampleData.js";

export function useRaceData(selectedRaceId) {
  const [races, setRaces] = useState([]);
  const [lapData, setLapData] = useState(sampleLapData);
  const [circuitPath, setCircuitPath] = useState(sampleCircuitPath);
  const [status, setStatus] = useState("loading");
  const lastFetchedRaceId = useRef(null);

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
    if (lastFetchedRaceId.current === selectedRace.id) return;
    lastFetchedRaceId.current = selectedRace.id;

    fetchRaceLaps(selectedRace.id)
      .then((data) => {
        if (data.laps?.length) {
          setLapData(data);
        }
      })
      .catch(() => setLapData(sampleLapData));

    if (selectedRace.circuit_id) {
      fetchCircuitPath(selectedRace.circuit_id)
        .then((data) => {
          if (data.path?.length) {
            setCircuitPath(data.path);
          }
        })
        .catch(() => setCircuitPath(sampleCircuitPath));
    }
  }, [selectedRace]);

  return { races, selectedRace, lapData, circuitPath, status };
}