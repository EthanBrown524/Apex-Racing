import { useCallback, useEffect, useState } from "react";

import Citations from "../Citations/Citations.jsx";
import { useCommentary } from "../../hooks/useCommentary.js";

export default function AINarrator({ raceId, upToLap }) {
  const { data, isLoading, error, load } = useCommentary();
  const [requestedLap, setRequestedLap] = useState(upToLap);

  const requestCommentary = useCallback(
    (lap = upToLap) => {
      if (!raceId || isLoading) return;
      setRequestedLap(lap);
      load(raceId, lap);
    },
    [isLoading, load, raceId, upToLap]
  );

  useEffect(() => {
    if (!raceId) return;
    requestCommentary(1);
    // Fetch once per race; users can refresh for the current lap when they want it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raceId]);

  return (
    <div className="narrator">
      <div className="narrator-head">
        <div className="narrator-title">
          Commentary {requestedLap ? `up to lap ${requestedLap}` : ""}
        </div>
        <button
          type="button"
          className="button ghost narrator-action"
          onClick={() => requestCommentary(upToLap)}
          disabled={isLoading}
        >
          {isLoading ? "Composing" : `Generate lap ${upToLap}`}
        </button>
      </div>
      <div className="narrator-body">
        {isLoading && "Granite is composing the story..."}
        {error && `Commentary unavailable: ${error}`}
        {!isLoading && !error && data?.narrative}
        {!isLoading && !error && !data && "Generate commentary when the race reaches a lap you want narrated."}
      </div>
      {data?.citations && <Citations citations={data.citations} />}
    </div>
  );
}
