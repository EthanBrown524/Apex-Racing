import { useEffect, useRef } from "react";
import { colorForDriver, pointOnPath } from "./trackUtils.js";

// Only resize canvas when dimensions actually change
function syncCanvasSize(canvas, ratio) {
  const rect = canvas.getBoundingClientRect();
  const w = Math.round(rect.width * ratio);
  const h = Math.round(rect.height * ratio);
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w;
    canvas.height = h;
    return true;
  }
  return false;
}

function scalePoint(point, width, height, viewport = null) {
  if (viewport) {
    // Follow-cam mode: map from viewport space
    const x = (point.x - viewport.x) * viewport.scale + width / 2;
    const y = (point.y - viewport.y) * viewport.scale + height / 2;
    return { x, y };
  }
  const padX = width * 0.09;
  const padY = height * 0.12;
  return {
    x: point.x * (width - padX * 2) + padX,
    y: point.y * (height - padY * 2) + padY,
  };
}

function drawTrack(ctx, path, width, height, showHeatmap, viewport = null) {
  if (!path.length) return;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  // Base track
  ctx.lineWidth = Math.max(width * 0.038, 20);
  ctx.strokeStyle = "#1e2028";
  ctx.beginPath();
  path.forEach((point, i) => {
    const s = scalePoint(point, width, height, viewport);
    i === 0 ? ctx.moveTo(s.x, s.y) : ctx.lineTo(s.x, s.y);
  });
  ctx.stroke();

  if (showHeatmap) {
    // Speed gradient
    for (let i = 0; i < path.length - 1; i++) {
      const speed = path[i].speed ?? 200;
      const t = Math.min(Math.max((speed - 60) / (330 - 60), 0), 1);
      const r = Math.round(t * 220);
      const g = Math.round((1 - Math.abs(t - 0.5) * 2) * 160);
      const b = Math.round((1 - t) * 220);
      const a = scalePoint(path[i], width, height, viewport);
      const b2 = scalePoint(path[i + 1], width, height, viewport);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b2.x, b2.y);
      ctx.lineWidth = Math.max(width * 0.018, 9);
      ctx.strokeStyle = `rgb(${r},${g},${b})`;
      ctx.stroke();
    }
  } else {
    // Solid racing line
    ctx.lineWidth = Math.max(width * 0.018, 9);
    ctx.strokeStyle = "#3a3c44";
    ctx.beginPath();
    path.forEach((point, i) => {
      const s = scalePoint(point, width, height, viewport);
      i === 0 ? ctx.moveTo(s.x, s.y) : ctx.lineTo(s.x, s.y);
    });
    ctx.stroke();
  }

  // Center dashes
  ctx.setLineDash([8, 10]);
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = "rgba(255,255,255,0.07)";
  ctx.beginPath();
  path.forEach((point, i) => {
    const s = scalePoint(point, width, height, viewport);
    i === 0 ? ctx.moveTo(s.x, s.y) : ctx.lineTo(s.x, s.y);
  });
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawCar(ctx, point, code, color, angle = 0, ghost = false, isLocked = false) {
  ctx.save();
  ctx.translate(point.x, point.y);
  ctx.rotate(angle);
  ctx.globalAlpha = ghost ? 0.35 : 1;

  const scale = isLocked ? 1.6 : 1;
  ctx.scale(scale, scale);

  // Shadow
  ctx.shadowColor = "rgba(0,0,0,0.6)";
  ctx.shadowBlur = 6;

  // Main body: sleek teardrop shape
  ctx.beginPath();
  ctx.moveTo(14, 0);           // nose
  ctx.bezierCurveTo(10, -4, -4, -5, -12, -4);  // left side
  ctx.lineTo(-14, -3);         // rear left
  ctx.lineTo(-14, 3);          // rear right
  ctx.lineTo(-12, 4);
  ctx.bezierCurveTo(-4, 5, 10, 4, 14, 0);      // right side
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.8)";
  ctx.lineWidth = 1.2;
  ctx.stroke();

  // Cockpit canopy
  ctx.beginPath();
  ctx.ellipse(2, 0, 5, 2.5, 0, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(10,10,20,0.85)";
  ctx.fill();

  // Front wing: thin horizontal bar
  ctx.beginPath();
  ctx.moveTo(13, -6);
  ctx.lineTo(16, -6);
  ctx.lineTo(16, 6);
  ctx.lineTo(13, 6);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.6)";
  ctx.lineWidth = 0.8;
  ctx.stroke();

  // Rear wing: wider bar
  ctx.beginPath();
  ctx.moveTo(-12, -7);
  ctx.lineTo(-15, -7);
  ctx.lineTo(-15, 7);
  ctx.lineTo(-12, 7);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.stroke();

  // Sidepod highlights
  ctx.beginPath();
  ctx.moveTo(6, -4.5);
  ctx.lineTo(-6, -4.5);
  ctx.strokeStyle = "rgba(255,255,255,0.25)";
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(6, 4.5);
  ctx.lineTo(-6, 4.5);
  ctx.stroke();

  ctx.shadowBlur = 0;
  ctx.restore();

  // Driver code label
  ctx.save();
  ctx.globalAlpha = ghost ? 0.35 : 1;

  // Background pill
  if (!ghost) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(point.x - 10, point.y + 14 * scale, 20, 12, 3);
    ctx.fill();
  }

  ctx.font = `700 ${isLocked ? 10 : 8}px Inter, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.shadowColor = "rgba(0,0,0,0.9)";
  ctx.shadowBlur = 3;
  ctx.fillStyle = ghost ? "rgba(255,255,255,0.4)" : "#ffffff";
  ctx.fillText(code.slice(0, 3), point.x, point.y + 15 * scale);
  ctx.restore();
}

function getTelemetryPosition(path, elapsedMs, totalMs) {
  if (!path || path.length < 2) return null;
  const progress = Math.min(elapsedMs / totalMs, 1);
  const startMs = path[0].t_ms ?? 0;
  const endMs = path[path.length - 1].t_ms ?? totalMs;
  const targetMs = startMs + progress * Math.max(endMs - startMs, 1);

  let lo = 0, hi = path.length - 1;
  while (lo < hi - 1) {
    const mid = Math.floor((lo + hi) / 2);
    if (path[mid].t_ms <= targetMs) lo = mid;
    else hi = mid;
  }

  const a = path[lo];
  const b = path[hi];
  const span = (b.t_ms - a.t_ms) || 1;
  const t = Math.min(Math.max((targetMs - a.t_ms) / span, 0), 1);

  // Smooth angle using lookahead
  const lookAhead = Math.min(hi + 3, path.length - 1);
  const angleTarget = path[lookAhead];

  return {
    x: a.x + (b.x - a.x) * t,
    y: a.y + (b.y - a.y) * t,
    angle: Math.atan2(angleTarget.y - a.y, angleTarget.x - a.x),
  };
}

// Smooth angle interpolation (avoid flipping)
function lerpAngle(a, b, t) {
  let diff = b - a;
  while (diff > Math.PI) diff -= 2 * Math.PI;
  while (diff < -Math.PI) diff += 2 * Math.PI;
  return a + diff * t;
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
  resetSignal,
  showHeatmap = true,
  lockedDriver = null,
}) {
  const elapsedMsRef = useRef(0);
  const lastFrameRef = useRef(0);
  const currentLapRef = useRef(currentLap);
  const anglesRef = useRef({});
  const viewportRef = useRef({ x: 0.5, y: 0.5, scale: 1, targetX: 0.5, targetY: 0.5, targetScale: 1 });

  useEffect(() => {
    currentLapRef.current = currentLap;
    elapsedMsRef.current = 0;
  }, [currentLap]);

  useEffect(() => {
    elapsedMsRef.current = 0;
    lastFrameRef.current = 0;
    anglesRef.current = {};
    viewportRef.current = { x: 0.5, y: 0.5, scale: 1, targetX: 0.5, targetY: 0.5, targetScale: 1 };
  }, [resetSignal]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext("2d");
    const ratio = window.devicePixelRatio || 1;
    let frameId = 0;

    function render(timestamp) {
      syncCanvasSize(canvas, ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

      const width = canvas.width / ratio;
      const height = canvas.height / ratio;
      ctx.clearRect(0, 0, width, height);

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

      // Compute car positions first
      const carPositions = {};
      if (hasTelemetry) {
        telemetry.drivers.forEach((driverTel) => {
          const pos = getTelemetryPosition(driverTel.path, elapsed, leaderLapTimeMs);
          if (pos) carPositions[driverTel.code] = { ...pos, driverTel };
        });
      }

      // Compute viewport for follow-cam
      let viewport = null;
      if (lockedDriver && carPositions[lockedDriver]) {
        const target = carPositions[lockedDriver];
        const vp = viewportRef.current;
        const zoomScale = Math.min(width, height) * 2.2;

        // Smooth pan to locked car
        vp.targetX = target.x;
        vp.targetY = target.y;
        vp.targetScale = zoomScale;
        vp.x += (vp.targetX - vp.x) * 0.08;
        vp.y += (vp.targetY - vp.y) * 0.08;
        vp.scale += (vp.targetScale - vp.scale) * 0.08;
        viewport = vp;
      } else {
        // Reset viewport smoothly when unlocking
        const vp = viewportRef.current;
        vp.targetX = 0.5;
        vp.targetY = 0.5;
        vp.targetScale = 1;
        vp.x += (vp.targetX - vp.x) * 0.08;
        vp.y += (vp.targetY - vp.y) * 0.08;
        vp.scale += (vp.targetScale - vp.scale) * 0.08;
        if (Math.abs(vp.scale - 1) > 0.01) viewport = vp;
      }

      drawTrack(ctx, circuitPath, width, height, showHeatmap, viewport);

      if (hasTelemetry) {
        Object.entries(carPositions).forEach(([code, pos]) => {
          // Smooth angles to prevent jitter
          const prevAngle = anglesRef.current[code] ?? pos.angle;
          const smoothAngle = lerpAngle(prevAngle, pos.angle, 0.3);
          anglesRef.current[code] = smoothAngle;

          const point = scalePoint(pos, width, height, viewport);
          const isLocked = lockedDriver === code;
          drawCar(ctx, point, code, colorForDriver(code), smoothAngle, false, isLocked);
        });
      } else {
        lap?.drivers?.forEach((driver) => {
          const gapFraction = Math.min((driver.gap_ms ?? 0) / leaderLapTimeMs, 0.99);
          const progress = ((elapsed / leaderLapTimeMs) - gapFraction + 1) % 1;
          const pt = pointOnPath(circuitPath, progress);
          const ptNext = pointOnPath(circuitPath, (progress + 0.01) % 1);
          const rawAngle = Math.atan2(ptNext.y - pt.y, ptNext.x - pt.x);
          const prevAngle = anglesRef.current[driver.code] ?? rawAngle;
          const smoothAngle = lerpAngle(prevAngle, rawAngle, 0.3);
          anglesRef.current[driver.code] = smoothAngle;
          const point = scalePoint(pt, width, height, viewport);
          const isLocked = lockedDriver === driver.code;
          drawCar(ctx, point, driver.code, driver.color ?? colorForDriver(driver.code), smoothAngle, false, isLocked);
        });
      }

      frameId = requestAnimationFrame(render);
    }

    frameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frameId);
  }, [canvasRef, laps, circuitPath, speed, isPlaying, onLapChange, cfLaps, telemetry, showHeatmap, lockedDriver, resetSignal]);
}
