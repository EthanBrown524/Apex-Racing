const TONE_CLASS = {
  Plausible: "ok",
  Borderline: "warn",
  Stretch: "bad",
  Fantasy: "bad",
};

export default function RealismChip({ realism, isLoading }) {
  if (isLoading) {
    return (
      <span className="realism-chip loading" title="Granite is judging realism...">
        ... realism
      </span>
    );
  }
  if (!realism) return null;
  const tone = TONE_CLASS[realism.label] ?? "warn";
  const pct = Math.round((realism.score ?? 0) * 100);
  return (
    <span
      className={`realism-chip ${tone}`}
      title={`${realism.reasoning} (source: ${realism.source})`}
    >
      <span className="realism-dot" />
      Realism {pct}% <strong>{realism.label}</strong>
    </span>
  );
}
