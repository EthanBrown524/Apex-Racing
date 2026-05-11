import { getDriverPrimary } from "../../teamColors.js";

export function pointOnPath(path, progress) {
  if (!path.length) return { x: 0.5, y: 0.5 };
  const wrapped = ((progress % 1) + 1) % 1;
  const scaled = wrapped * (path.length - 1);
  const index = Math.floor(scaled);
  const nextIndex = Math.min(index + 1, path.length - 1);
  const local = scaled - index;
  const current = path[index];
  const next = path[nextIndex];
  return {
    x: current.x + (next.x - current.x) * local,
    y: current.y + (next.y - current.y) * local,
  };
}

export function colorForDriver(code, year = 2023) {
  return getDriverPrimary(code, year);
}