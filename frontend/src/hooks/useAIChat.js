import { useCallback, useState } from "react";
import { apexClient } from "../api/apexClient.js";

const CITATION_SENTINEL = "[[CITATIONS]]";

/* Reads /ai/ask/stream as a plain-text stream and updates the last
   assistant message in place as fragments arrive. The server appends
   `\n\n[[CITATIONS]]<json>` after the answer body so we can split once. */
export function useAIChat(raceId) {
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);

  const ask = useCallback(
    async (question) => {
      if (!raceId || !question.trim()) return;
      const userMessage = { role: "user", text: question };
      const assistantPlaceholder = { role: "assistant", text: "", citations: [], streaming: true };
      setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
      setIsSending(true);

      const baseURL = apexClient.defaults.baseURL || "";
      const url = `${baseURL.replace(/\/$/, "")}/ai/ask/stream`;

      let buffer = "";

      function updateLast(updater) {
        setMessages((prev) => {
          if (!prev.length) return prev;
          const next = prev.slice();
          const last = next[next.length - 1];
          next[next.length - 1] = updater(last);
          return next;
        });
      }

      function splitOnCitations(text) {
        const idx = text.indexOf(CITATION_SENTINEL);
        if (idx === -1) return { body: text, citations: null };
        const body = text.slice(0, idx).trimEnd();
        const tail = text.slice(idx + CITATION_SENTINEL.length).trim();
        let citations = null;
        try {
          citations = JSON.parse(tail);
        } catch (err) {
          citations = null;
        }
        return { body, citations };
      }

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ race_id: raceId, question }),
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const reader = response.body?.getReader();
        if (!reader) {
          const text = await response.text();
          const { body, citations } = splitOnCitations(text);
          updateLast(() => ({
            role: "assistant",
            text: body,
            citations: citations || [],
            streaming: false,
          }));
          return;
        }
        const decoder = new TextDecoder();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const { body, citations } = splitOnCitations(buffer);
          updateLast(() => ({
            role: "assistant",
            text: body,
            citations: citations || [],
            streaming: citations == null,
          }));
        }
        buffer += decoder.decode();
        const { body, citations } = splitOnCitations(buffer);
        updateLast(() => ({
          role: "assistant",
          text: body,
          citations: citations || [],
          streaming: false,
        }));
      } catch (err) {
        updateLast((last) => ({
          ...last,
          text:
            last?.text ||
            `AI request failed: ${err?.message ?? "unknown"}`,
          streaming: false,
        }));
      } finally {
        setIsSending(false);
      }
    },
    [raceId]
  );

  const reset = useCallback(() => setMessages([]), []);

  return { messages, isSending, ask, reset };
}
