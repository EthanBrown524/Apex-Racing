import { useEffect, useState } from "react";

import { fetchHealth } from "../../api/apexClient.js";

export default function Footer() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <footer className="footer">
      <div className="footer-row">
        <span className="footer-brand">APEX RACE DIRECTOR</span>
        <span className="footer-stack">
          <span className="footer-chip">Granite-3-8b</span>
          <span className="footer-chip">Slate embeddings</span>
          <span className="footer-chip">Docling</span>
          <span className="footer-chip">Langflow</span>
          <span className="footer-chip">FastAPI</span>
          <span className="footer-chip">PostgreSQL + pgvector</span>
          <span className="footer-chip">React + Vite</span>
        </span>
      </div>
      {health && (
        <div className="footer-row dim">
          <span>
            {health.counts?.races ?? 0} races ingested
            {" | "}
            {health.counts?.lap_times ?? 0} laps
            {" | "}
            {health.counts?.race_embeddings ?? 0} RAG chunks
            {" | "}
            Granite {health.granite_configured ? "configured" : "fallback"}
            {" | "}
            pgvector {health.pgvector_installed ? "on" : "off"}
          </span>
        </div>
      )}
    </footer>
  );
}
