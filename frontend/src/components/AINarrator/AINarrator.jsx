import { useEffect } from "react";

import Citations from "../Citations/Citations.jsx";
import { useCommentary } from "../../hooks/useCommentary.js";

export default function AINarrator({ raceId, upToLap }) {
  const { data, isLoading, error, load } = useCommentary();

  useEffect(() => {
    if (!raceId) return;
    load(raceId, upToLap);
  }, [raceId, upToLap, load]);

  return (
    <div className="narrator">
      <div className="narrator-title">Commentary {upToLap ? `up to lap ${upToLap}` : ""}</div>
      <div className="narrator-body">
        {isLoading && "Granite is composing the story..."}
        {error && `Commentary unavailable: ${error}`}
        {!isLoading && !error && data?.narrative}
        {!isLoading && !error && !data && "Pick a race to hear the AI broadcast."}
      </div>
      {data?.citations && <Citations citations={data.citations} />}
    </div>
  );
}
