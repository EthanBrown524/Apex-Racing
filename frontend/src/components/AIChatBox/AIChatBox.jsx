import { useState } from "react";

import Citations from "../Citations/Citations.jsx";
import { useAIChat } from "../../hooks/useAIChat.js";

const SUGGESTIONS = [
  "Why did the leader pit when they did?",
  "Which driver gained the most positions?",
  "What was the impact of the safety car?",
  "Why did the championship leader struggle?",
];

export default function AIChatBox({ raceId }) {
  const [input, setInput] = useState("");
  const chat = useAIChat(raceId);

  function submit(text) {
    const value = (text ?? input).trim();
    if (!value) return;
    chat.ask(value);
    setInput("");
  }

  return (
    <div className="ai-chat">
      <div className="whatif-title">Ask APEX</div>
      <div className="ai-chat-input-row">
        <input
          placeholder="Ask anything about this race..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
        />
        <button
          type="button"
          className="button primary"
          onClick={() => submit()}
          disabled={chat.isSending || !raceId}
        >
          {chat.isSending ? "..." : "Ask"}
        </button>
      </div>

      {chat.messages.length === 0 && (
        <div className="ai-chat-empty">
          Try:{" "}
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              type="button"
              className="button ghost"
              style={{ margin: "4px 4px 0 0", fontSize: 10 }}
              onClick={() => submit(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {chat.messages.length > 0 && (
        <div className="ai-chat-history">
          {chat.messages.map((m, i) => (
            <div key={i} className={`ai-chat-message ${m.role}`}>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  letterSpacing: 0.5,
                  color: "var(--text-dim)",
                  marginBottom: 4,
                }}
              >
                {m.role === "user" ? "YOU" : "GRANITE"}
              </div>
              <div>{m.text}</div>
              {m.citations && <Citations citations={m.citations} />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
