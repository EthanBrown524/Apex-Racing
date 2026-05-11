const speeds = [0.5, 1, 2, 4, 10];

export default function PlaybackControls({
  isPlaying, setIsPlaying, speed, setSpeed,
  currentLap, setCurrentLap, maxLap
}) {
  return (
    <div className="controls-bar">
      <button className="button" type="button" onClick={() => setIsPlaying(!isPlaying)}>
        {isPlaying ? "⏸ Pause" : "▶ Play"}
      </button>
      <button className="button secondary" type="button" onClick={() => setCurrentLap(1)}>
        ↺ Reset
      </button>
      <div className="field">
        <span>Speed</span>
        <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
          {speeds.map((v) => (
            <option key={v} value={v}>{v}x</option>
          ))}
        </select>
      </div>
      <div className="field" style={{ flex: 1 }}>
        <span>Lap {currentLap} / {maxLap}</span>
        <input
          type="range"
          min="1"
          max={maxLap}
          value={currentLap}
          onChange={(e) => setCurrentLap(Number(e.target.value))}
        />
      </div>
    </div>
  );
}