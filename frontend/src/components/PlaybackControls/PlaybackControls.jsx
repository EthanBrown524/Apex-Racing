const speeds = [0.5, 1, 2, 4, 10];

export default function PlaybackControls({ isPlaying, setIsPlaying, speed, setSpeed, currentLap, setCurrentLap, maxLap }) {
  return (
    <section className="panel panel-pad">
      <div className="control-row">
        <button className="button" type="button" onClick={() => setIsPlaying(!isPlaying)}>
          {isPlaying ? "Pause" : "Play"}
        </button>
        <button className="button secondary" type="button" onClick={() => setCurrentLap(1)}>
          Reset
        </button>
        <label className="field">
          <span>Speed</span>
          <select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}>
            {speeds.map((value) => (
              <option key={value} value={value}>
                {value}x
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Lap</span>
          <input
            type="range"
            min="1"
            max={maxLap}
            value={currentLap}
            onChange={(event) => setCurrentLap(Number(event.target.value))}
          />
        </label>
      </div>
    </section>
  );
}

