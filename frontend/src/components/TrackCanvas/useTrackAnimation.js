import { useEffect, useRef } from "react";

import { colorForDriver, driverProgress, pointOnPath } from "./trackUtils.js";

function scalePoint(point, width, height) {
  const padX = width * 0.09;
  const padY = height * 0.12;
  return {
    x: point.x * (width - padX * 2) + padX,
    y: point.y * (height - padY * 2) + padY
  };
}

function drawTrack(ctx, path, width, height) {
  if (!path.length) {
    return;
  }

  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.lineWidth = Math.max(width * 0.035, 18);
  ctx.strokeStyle = "#2b2e35";
  ctx.beginPath();
  path.forEach((point, index) => {
    const scaled = scalePoint(point, width, height);
    if (index === 0) {
      ctx.moveTo(scaled.x, scaled.y);
    } else {
      ctx.lineTo(scaled.x, scaled.y);
    }
  });
  ctx.stroke();

  ctx.lineWidth = Math.max(width * 0.012, 6);
  ctx.strokeStyle = "#f8f4ea";
  ctx.stroke();

  ctx.setLineDash([10, 12]);
  ctx.lineWidth = 2;
  ctx.strokeStyle = "rgba(16, 17, 19, 0.9)";
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawCar(ctx, point, code, color, ghost = false) {
  ctx.save();
  ctx.globalAlpha = ghost ? 0.42 : 1;
  ctx.fillStyle = color;
  ctx.strokeStyle = "#101113";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(point.x, point.y, ghost ? 8 : 10, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = ghost ? "#101113" : "#f8f4ea";
  ctx.font = "700 10px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(code.slice(0, 3), point.x, point.y + 24);
  ctx.restore();
}

export function useTrackAnimation({
  canvasRef,
  laps,
  circuitPath,
  speed,
  isPlaying,
  currentLap,
  onLapChange,
  cfLaps
}) {
  const phaseRef = useRef(0);
  const lastFrameRef = useRef(0);
  const currentLapRef = useRef(currentLap);

  useEffect(() => {
    currentLapRef.current = currentLap;
    phaseRef.current = 0;
  }, [currentLap]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }

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

      if (isPlaying && lastFrameRef.current) {
        const delta = (timestamp - lastFrameRef.current) / 1000;
        phaseRef.current += delta * speed * 0.16;
        if (phaseRef.current >= 1) {
          phaseRef.current = 0;
          const nextLap = Math.min(currentLapRef.current + 1, laps.length);
          currentLapRef.current = nextLap;
          onLapChange(nextLap);
        }
      }
      lastFrameRef.current = timestamp;

      const lapIndex = Math.max(currentLapRef.current - 1, 0);
      const lap = laps[lapIndex] ?? laps[0];
      const ghostLap = cfLaps?.[lapIndex];

      ghostLap?.drivers?.forEach((driver) => {
        const progress = driverProgress(driver, lapIndex, phaseRef.current, laps.length);
        const point = scalePoint(pointOnPath(circuitPath, progress), width, height);
        drawCar(ctx, point, driver.code, colorForDriver(driver.code), true);
      });

      lap?.drivers?.forEach((driver) => {
        const progress = driverProgress(driver, lapIndex, phaseRef.current, laps.length);
        const point = scalePoint(pointOnPath(circuitPath, progress), width, height);
        drawCar(ctx, point, driver.code, driver.color ?? colorForDriver(driver.code));
      });

      frameId = requestAnimationFrame(render);
    }

    frameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frameId);
  }, [canvasRef, laps, circuitPath, speed, isPlaying, onLapChange, cfLaps]);
}

