export default function TrackCanvas({
  laps,
  circuitPath,
  speed,
  isPlaying,
  currentLap,
  onLapChange,
  cfLaps,
  telemetry
}) {
  const canvasRef = useRef(null);
  useTrackAnimation({
    canvasRef, laps, circuitPath, speed,
    isPlaying, currentLap, onLapChange, cfLaps, telemetry
  });

  return (
    <section className="panel track-panel" aria-label="Race track animation">
      <div className="track-stage">
        <canvas ref={canvasRef} className="track-canvas" />
        <div className="track-hud">
          <span className="hud-pill">Lap {currentLap}</span>
          <span className="hud-pill">{speed}x</span>
          <span className="hud-pill live">● Live</span>
        </div>
      </div>
    </section>
  );
}