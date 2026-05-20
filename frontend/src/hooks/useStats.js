import { useEffect, useState } from "react";

import { apexClient } from "../api/apexClient.js";
import { sampleStats } from "../data/sampleData.js";

export function useStats() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    apexClient
      .get("/stats")
      .then((response) => {
        const payload = response?.data;
        if (payload && payload.headline && payload.headline.grand_prix > 0) {
          setData(payload);
          setStatus("live");
        } else {
          setData(sampleStats);
          setStatus("sample");
        }
      })
      .catch(() => {
        setData(sampleStats);
        setStatus("sample");
      });
  }, []);

  return { data, status };
}
