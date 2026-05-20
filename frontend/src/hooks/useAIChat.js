import { useCallback, useState } from "react";
import { askAI } from "../api/apexClient.js";

export function useAIChat(raceId) {
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);

  const ask = useCallback(
    async (question) => {
      if (!raceId || !question.trim()) return;
      const userMessage = { role: "user", text: question };
      setMessages((prev) => [...prev, userMessage]);
      setIsSending(true);
      try {
        const res = await askAI(raceId, question);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: res.answer, citations: res.citations || [] },
        ]);
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: `AI request failed: ${err?.response?.data?.detail ?? err?.message ?? "unknown"}`,
            citations: [],
          },
        ]);
      } finally {
        setIsSending(false);
      }
    },
    [raceId]
  );

  const reset = useCallback(() => setMessages([]), []);

  return { messages, isSending, ask, reset };
}
