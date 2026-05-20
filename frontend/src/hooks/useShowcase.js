import { useEffect, useState } from "react";

import { fetchShowcase } from "../api/apexClient.js";

const FALLBACK = [
  {
    id: "abu-dhabi-2021",
    title: "Abu Dhabi 2021 - the title-deciding lap",
    subtitle: "Don't restart the race behind the safety car. Who wins the championship?",
    season: 2021,
    round: 22,
    mode: "counterfactual",
    tagline: "Hamilton vs Verstappen",
    accent: "#e8002d",
    race_id: null,
  },
  {
    id: "monaco-2022",
    title: "Monaco 2022 - if Ferrari hadn't double-stacked",
    subtitle: "Move LEC's pit stop two laps earlier; does he keep the win at home?",
    season: 2022,
    round: 7,
    mode: "counterfactual",
    tagline: "Charles's home cathedral",
    accent: "#dc0000",
    race_id: null,
  },
];

export function useShowcase() {
  const [scenarios, setScenarios] = useState([]);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    fetchShowcase()
      .then((data) => {
        if (Array.isArray(data) && data.length) {
          setScenarios(data);
          setStatus("live");
        } else {
          setScenarios(FALLBACK);
          setStatus("sample");
        }
      })
      .catch(() => {
        setScenarios(FALLBACK);
        setStatus("sample");
      });
  }, []);

  return { scenarios, status };
}
