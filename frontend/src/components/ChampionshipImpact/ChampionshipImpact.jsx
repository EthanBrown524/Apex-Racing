export default function ChampionshipImpact({ data, isLoading, error }) {
  if (isLoading) {
    return (
      <div className="impact-card">
        <div className="impact-title">Championship impact</div>
        <div className="empty" style={{ padding: 20 }}>Recomputing season standings...</div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="impact-card">
        <div className="impact-title">Championship impact</div>
        <div className="empty" style={{ padding: 20 }}>Couldn't compute: {error}</div>
      </div>
    );
  }
  if (!data) return null;

  if (data.error) {
    return (
      <div className="impact-card">
        <div className="impact-title">Championship impact</div>
        <div className="empty" style={{ padding: 20 }}>{data.error}</div>
      </div>
    );
  }

  const changed = data.championship_changed;
  const actual = data.actual_standings ?? [];
  const alt = data.alternate_standings ?? [];

  return (
    <div className={`impact-card ${changed ? "flipped" : ""}`}>
      <div className="impact-title">
        Championship impact - {data.season} season
        {changed ? (
          <span className="impact-tag flip">TITLE CHANGES</span>
        ) : (
          <span className="impact-tag steady">Title holds</span>
        )}
      </div>

      <div className="impact-headline">
        <div className="impact-half">
          <div className="impact-label">Actual champion</div>
          <div className="impact-val">{data.actual_champion || "-"}</div>
        </div>
        <div className="impact-arrow">{changed ? "->" : "="}</div>
        <div className="impact-half target">
          <div className="impact-label">Alternate champion</div>
          <div className="impact-val">{data.alternate_champion || "-"}</div>
        </div>
      </div>

      <div className="impact-narrative">{data.narrative}</div>

      {data.biggest_movers?.length > 0 && (
        <div className="impact-movers">
          {data.biggest_movers.map((m, i) => (
            <span key={i} className="impact-mover">{m}</span>
          ))}
        </div>
      )}

      <div className="impact-tables">
        <div>
          <div className="impact-subtitle">Actual</div>
          <ol className="impact-list">
            {actual.slice(0, 5).map((row) => (
              <li key={row.driver_id}>
                <span className="impact-driver">{row.code}</span>
                <span className="impact-pts">{row.points} pts</span>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <div className="impact-subtitle">Alternate</div>
          <ol className="impact-list">
            {alt.slice(0, 5).map((row) => (
              <li key={row.driver_id}>
                <span className="impact-driver">{row.code}</span>
                <span className="impact-pts">
                  {row.points} pts
                  {row.delta !== 0 && (
                    <span
                      className={`impact-delta ${row.delta > 0 ? "up" : "down"}`}
                    >
                      {row.delta > 0 ? "+" : ""}{row.delta}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
