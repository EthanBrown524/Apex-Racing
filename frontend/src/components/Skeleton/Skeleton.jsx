export function SkeletonRow() {
  return (
    <div className="lboard-row skeleton-row">
      <div className="skeleton-block" style={{ width: 18, height: 12 }} />
      <div className="skeleton-block" style={{ width: 36, height: 16 }} />
      <div className="skeleton-block" style={{ width: 80, height: 12 }} />
      <div className="skeleton-block" style={{ width: 40, height: 10 }} />
      <div className="skeleton-block" style={{ width: 22, height: 14 }} />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="race-card skeleton-card">
      <div className="skeleton-block" style={{ width: 90, height: 11 }} />
      <div className="skeleton-block" style={{ width: "70%", height: 16, marginTop: 6 }} />
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10 }}>
        <div className="skeleton-block" style={{ width: 120, height: 10 }} />
        <div className="skeleton-block" style={{ width: 40, height: 14 }} />
      </div>
    </div>
  );
}

export function SkeletonList({ rows = 6, Component = SkeletonRow }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <Component key={i} />
      ))}
    </>
  );
}
