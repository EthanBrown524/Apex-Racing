export default function Citations({ citations }) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="citations" role="list">
      {citations.map((c) => (
        <span
          key={c.index}
          className="citation"
          role="listitem"
          title={`${c.title}\n${c.snippet}`}
        >
          [{c.index}] {c.source}
        </span>
      ))}
    </div>
  );
}
