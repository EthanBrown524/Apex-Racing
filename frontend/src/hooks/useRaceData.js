import { useEffect, useMemo, useState } from "react";

import { fetchCircuitPath, fetchRaceLaps, fetchRaces } from "../api/apexClient.js";
import { sampleCircuitPath, sampleLapData, sampleRaces } from "../sampleData.js";

export function useRaceData(selectedRaceId) {
  const [races, setRaces] = useState(sampleRaces);
  const [lapData, setLapData] = useState(sampleLapData);
  const [circuitPath, setCircuitPath] = useState(sampleCircuitPath);
  const [status, setStatus] = useState("sample");

  useEffect(() => {
    let active = true;
    fetchRaces()
      .then((data) => {
        if (active && data.length > 0) {
          setRaces(data);
          setStatus("live");
        }
      })
      .catch(() => setStatus("sample"));
    return () => {
      active = false;
    };
  }, []);

  const selectedRace = useMemo(
    () => races.find((race) => race.id === Number(selectedRaceId)) ?? races[0],
    [races, selectedRaceId]
  );

  useEffect(() => {
    if (!selectedRace) {
      return;
    }

    let active = true;
    fetchRaceLaps(selectedRace.id)
      .then((data) => {
        if (active && data.laps?.length) {
          setLapData(data);
          setStatus("live");
        }
      })
      .catch(() => setLapData(sampleLapData));

    if (selectedRace.circuit_id) {
      fetchCircuitPath(selectedRace.circuit_id)
        .then((data) => {
          if (active && data.path?.length) {
            setCircuitPath(data.path);
          }
        })
        .catch(() => setCircuitPath(sampleCircuitPath));
    }

    return () => {
      active = false;
    };
  }, [selectedRace]);

  return { races, selectedRace, lapData, circuitPath, status };
}

