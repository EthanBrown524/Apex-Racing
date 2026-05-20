import { useEffect, useState } from "react";

/**
 * Animate a number from 0 to `target` over `duration` ms.
 * Returns the current displayed value.
 */
export function useCountUp(target, duration = 1000) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (target == null || isNaN(target)) {
      setValue(0);
      return undefined;
    }
    if (target === 0) {
      setValue(0);
      return undefined;
    }
    const start = performance.now();
    let frame;
    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    }
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return value;
}

export function formatLargeNumber(n) {
  if (n == null) return "-";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return String(n);
}
