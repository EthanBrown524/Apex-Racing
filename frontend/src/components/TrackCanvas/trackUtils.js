export function pointOnPath(path, progress) {
  if (!path.length) {
    return { x: 0.5, y: 0.5 };
  }

  const wrapped = ((progress % 1) + 1) % 1;
  const scaled = wrapped * (path.length - 1);
  const index = Math.floor(scaled);
  const nextIndex = Math.min(index + 1, path.length - 1);
  const local = scaled - index;
  const current = path[index];
  const next = path[nextIndex];

  return {
    x: current.x + (next.x - current.x) * local,
    y: current.y + (next.y - current.y) * local
  };
}

export function colorForDriver(code) {
  const colors = {
    VER: "#4cc9f0",
    NOR: "#f24822",
    HAM: "#b98cff",
    PIA: "#2fbf71",
    LEC: "#e7c04b",
    RUS: "#f8f4ea"
  };
  return colors[code] ?? "#f8f4ea";
}

export function driverProgress(driver, lapIndex, phase, totalLaps) {
  const rankOffset = (driver.position - 1) * 0.018;
  const gapOffset = Math.min((driver.gap_ms ?? 0) / 180000, 0.08);
  return (lapIndex + phase) / Math.max(totalLaps, 1) - rankOffset - gapOffset;
}

