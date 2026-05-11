import { useEffect, useRef } from "react";
import { colorForDriver, pointOnPath } from "./trackUtils.js";

function scalePoint(point, width, height) {
  const padX = width * 0.09;
  const padY = height * 0.12;
  return {
    x: point.x * (width - padX * 2) + padX,
    y: point.y * (height - padY * 2) + padY,
  };
}

function drawTrack(ctx, path, width, height) {
  if (!path.length) return;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.lineWidth = Math.max(width * 0.038, 20);
  ctx.strokeStyle = "#1e2028";
  ctx.beginPath();
  path.forEach((point, i) => {
    const s = scalePoint(point, width, height);
    i === 0 ? ctx.moveTo(s.x, s.y) : ctx.lineTo(s.x, s.y);
  });
  ctx.stroke();

  for (let i = 0; i < path.length - 1; i++) {
    const speed = path[i].speed ?? 200;
    const t = Math.min(Math.max((speed - 60) / (330 - 60), 0), 1);
    const r = Math.round(t * 220);
    const g = Math.round((1 - Math.abs(t - 0.5) * 2) * 160);
    const b = Math.round((1 - t) * 220);
    const a = scalePoint(path[i], width, height);
    const b2 = scalePoint(path[i + 1], width, height);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b2.x, b2.y);
    ctx.lineWidth = Math.max(width * 0.018, 9);
    ctx.strokeStyle = `rgb(${r},${g},${b})`;
    ctx.stroke();
  }

  ctx.setLineDash([8, 10]);
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = "rgba(255,255,255,0.07)";
  ctx.beginPath();
  path.forEach((point, i) => {
    const s = scalePoint(point, width, height);
    i === 0 ? ctx.moveTo(s.x, s.y) : ctx.lineTo(s.x, s.y);
  });
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawCar(ctx, point, code, color, angle = 0, ghost = false) {
  ctx.save();
  ctx.translate(point.x, point.y);
  ctx.rotate(angle);
  ctx.globalAlpha = ghost ? 0.35 : 1;
  const w = 18, h = 8;
  ctx.beginPath();
  ctx.moveTo(w / 2, 0);
  ctx.lineTo(w / 4, -h / 2);
  ctx.lineTo(-w / 2, -h / 2.5);
  ctx.lineTo(-w / 2, h / 2.5);
  ctx.lineTo(w / 4, h / 2);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.7)";
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(2, 0, 4, 2.5, 0, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(0,0,0,0.55)";
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(w / 2, -3);
  ctx.lineTo(w / 2 + 5, -3);
  ctx.lineTo(w / 2 + 5, 3);
  ctx.lineTo(w / 2, 3);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.5)";
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-w / 2, -5);
  ctx.lineTo(-w / 2 - 3, -5);
  ctx.lineTo(-w / 2 - 3, 5);
  ctx.lineTo(-w / 2, 5);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.stroke();
  ctx.restore();
  ctx.save();
  ctx.globalAlpha = ghost ? 0.35 : 1;
  ctx.font = "700 9px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.shadowColor = "rgba(0,0,0,0.9)";
  ctx.shadowBlur = 4;
  ctx.fillStyle = ghost ? "rgba(255,255,255,0.4)" : "#ffffff";
  ctx.fillText(code.slice(0, 3), point.x, point.y + 13);
  ctx.restore();
}

// Get interpolated X/Y position from telemetry path at a given time
function getTelemetryPosition(path, elapsedMs, totalMs) {
  if (!path || path.length < 2) return null;
  const progress = Math.min(elapsedMs / totalMs, 1);
  const targetMs = progress * (path[path.length - 1].t_ms || totalMs);

  // Binary search for the right segment
  let lo = 0, hi = path.length - 1;
  while (lo < hi - 1) {
    const mid = Math.floor((lo + hi) / 2);
    if (path[mid].t_ms <= targetMs) lo = mid;
    else hi = mid;
  }

  const a = path[lo];
  const b = path[hi];
  const span = (b.t_ms - a.t_ms) || 1;
  const t = Math.min((targetMs - a.t_ms) / span, 1);

  return {
    x: a.x + (b.x - a.x) * t,
    y: a.y + (b.y - a.y) * t,
    angle: Math.atan2(b.y - a.y, b.x - a.x),
  };
}

export function useTrackAnimation({
  canvasRef,
  laps,
  circuitPath,
  speed,
  isPlaying,
  currentLap,
  onLapChange,
  cfLaps,
  telemetry,
}) {
  const elapsedMsRef = useRef(0);
  const lastFrameRef = useRef(0);
  const currentLapRef = useRef(currentLap);

  useEffect(() => {
    currentLapRef.current = currentLap;
    elapsedMsRef.current = 0;
  }, [currentLap]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext("2d");
    let frameId = 0;

    function render(timestamp) {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * ratio);
      canvas.height = Math.round(rect.height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      const width = rect.width;
      const height = rect.height;
      ctx.clearRect(0, 0, width, height);
      drawTrack(ctx, circuitPath, width, height);

      const lapIndex = Math.max(currentLapRef.current - 1, 0);
      const lap = laps[lapIndex] ?? laps[0];
      const leaderDriver = lap?.drivers?.find(d => d.position === 1);
      const leaderLapTimeMs = leaderDriver?.time_ms ?? 90000;

      if (isPlaying && lastFrameRef.current) {
        const delta = (timestamp - lastFrameRef.current) / 1000;
        elapsedMsRef.current += delta * speed * 1000;
        if (elapsedMsRef.current >= leaderLapTimeMs) {
          elapsedMsRef.current = 0;
          const nextLap = Math.min(currentLapRef.current + 1, laps.length);
          currentLapRef.current = nextLap;
          onLapChange(nextLap);
        }
      }
      lastFrameRef.current = timestamp;

      const elapsed = elapsedMsRef.current;
      const hasTelemetry = telemetry?.drivers?.length > 0;

      if (hasTelemetry) {
        // Real GPS telemetry mode
        telemetry.drivers.forEach((driverTel) => {
          const pos = getTelemetryPosition(
            driverTel.path, elapsed, leaderLapTimeMs
          );
          if (!pos) return;
          const point = scalePoint(pos, width, height);
          drawCar(
            ctx, point, driverTel.code,
            colorForDriver(driverTel.code), pos.angle
          );
        });
      } else {
        // Fallback: estimated position using gap data
        lap?.drivers?.forEach((driver) => {
          const gapFraction = Math.min(
            (driver.gap_ms ?? 0) / leaderLapTimeMs, 0.99
          );
          const progress = ((elapsed / leaderLapTimeMs) - gapFraction + 1) % 1;
          const pt = pointOnPath(circuitPath, progress);
          const ptNext = pointOnPath(circuitPath, (progress + 0.005) % 1);
          const angle = Math.atan2(ptNext.y - pt.y, ptNext.x - pt.x);
          const point = scalePoint(pt, width, height);
          drawCar(
            ctx, point, driver.code,
            driver.color ?? colorForDriver(driver.code), angle
          );
        });
      }

      frameId = requestAnimationFrame(render);
    }

    frameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frameId);
  }, [canvasRef, laps, circuitPath, speed, isPlaying, onLapChange, cfLaps, telemetry]);
}