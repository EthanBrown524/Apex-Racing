import { useEffect, useRef, useState } from "react";

/* Synthesized engine drone using Web Audio - no binary asset required.
   A pair of detuned sawtooth oscillators piped through a low-pass filter
   gives a credible idle hum. Pitch tracks the playback speed so 4x sounds
   meaningfully faster than 1x. State persists across speed changes; only
   `enabled` and `isPlaying` start/stop the audio graph.
*/

const BASE_FREQ = 70;       // ~F2 - sits below most UI sounds
const DETUNE_HZ = 1.5;
const FILTER_HZ = 320;

export function useEngineDrone({ enabled, isPlaying, speed }) {
  const ctxRef = useRef(null);
  const oscARef = useRef(null);
  const oscBRef = useRef(null);
  const gainRef = useRef(null);
  const filterRef = useRef(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!enabled || !isPlaying) {
      // Stop everything and forget the context. Browsers cap the number of
      // long-lived AudioContext instances; tear down rather than pause.
      if (ctxRef.current) {
        try { oscARef.current?.stop(); } catch (err) { /* noop */ }
        try { oscBRef.current?.stop(); } catch (err) { /* noop */ }
        try { ctxRef.current.close(); } catch (err) { /* noop */ }
        ctxRef.current = null;
        oscARef.current = null;
        oscBRef.current = null;
        gainRef.current = null;
        filterRef.current = null;
      }
      setRunning(false);
      return;
    }

    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const oscA = ctx.createOscillator();
    const oscB = ctx.createOscillator();
    const gain = ctx.createGain();
    const filter = ctx.createBiquadFilter();

    oscA.type = "sawtooth";
    oscB.type = "sawtooth";
    oscA.frequency.value = BASE_FREQ;
    oscB.frequency.value = BASE_FREQ + DETUNE_HZ;
    filter.type = "lowpass";
    filter.frequency.value = FILTER_HZ;
    gain.gain.value = 0.0;

    oscA.connect(filter);
    oscB.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);

    oscA.start();
    oscB.start();

    // Fade in to mask the click of the oscillator turning on.
    gain.gain.exponentialRampToValueAtTime(0.04, ctx.currentTime + 0.6);

    ctxRef.current = ctx;
    oscARef.current = oscA;
    oscBRef.current = oscB;
    gainRef.current = gain;
    filterRef.current = filter;
    setRunning(true);

    return () => {
      try { oscA.stop(); } catch (err) { /* noop */ }
      try { oscB.stop(); } catch (err) { /* noop */ }
      try { ctx.close(); } catch (err) { /* noop */ }
    };
  }, [enabled, isPlaying]);

  // Track speed: higher playback rate -> higher pitch, brighter filter.
  useEffect(() => {
    if (!running || !oscARef.current || !filterRef.current) return;
    const factor = Math.max(0.4, Math.min(2.5, Math.sqrt(Number(speed) || 1)));
    const t = ctxRef.current.currentTime;
    oscARef.current.frequency.linearRampToValueAtTime(BASE_FREQ * factor, t + 0.25);
    oscBRef.current.frequency.linearRampToValueAtTime(BASE_FREQ * factor + DETUNE_HZ, t + 0.25);
    filterRef.current.frequency.linearRampToValueAtTime(FILTER_HZ * factor, t + 0.25);
  }, [speed, running]);

  return { running };
}
