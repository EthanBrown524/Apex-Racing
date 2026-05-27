export default function Citations({ citations }) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="citations" role="list">
      {citations.map((c) => {
        const snippet = (c.snippet || "").slice(0, 240);
        const score = typeof c.score === "number" ? c.score.toFixed(2) : null;
        return (
          <span
            key={c.index}
            className="citation"
            role="listitem"
            tabIndex={0}
          >
            [{c.index}] {c.source}
            <span className="citation-popover" role="tooltip">
              <span className="citation-popover-head">
                <strong>{c.title || c.source}</strong>
                {score !== null && (
                  <span className="citation-popover-score">{score}</span>
                )}
              </span>
              {snippet && <span className="citation-popover-body">{snippet}</span>}
            </span>
          </span>
        );
      })}
    </div>
  );
}
