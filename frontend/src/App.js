import { useState } from "react";
import "./App.css";

const API = process.env.REACT_APP_API_URL || "https://candidaterag-production.up.railway.app";
//const API = process.env.REACT_APP_API_URL

// One session ID per browser tab — persists for the session
const SESSION_ID = Math.random().toString(36).substring(2, 10);

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim() || loading) return;

    const currentMessage = message;

    setMessages((prev) => [...prev, { role: "user", content: currentMessage }]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: currentMessage,
          session_id: SESSION_ID,   // ← Hindsight memory key
        }),
      });

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            typeof data.answer === "object"
              ? JSON.stringify(data.answer, null, 2)
              : data.answer,
          source: data.source || "",
          sources: data.sources || [],
          follow_ups: data.follow_ups || [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Unable to connect to backend.", sources: [] },
      ]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className="app">
      {messages.length === 0 ? (
        <div className="landing">
          <h1>Candidate Complaince Agent</h1>
          <p>
            Ask anything about candidates, parties,
            constituencies, education, assets and
            election affidavits.
          </p>

          <div className="prompt-box">
            <input
              type="text"
              placeholder="Ask anything..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
            />
            <button onClick={sendMessage} disabled={loading}>↑</button>
          </div>

          <div className="suggestions">
            <button onClick={() => setMessage("Compare MKStalin and VSBabu")}>
              Compare Candidates
            </button>
            <button onClick={() => setMessage("summarize candidates")}>
             summarize Candidates
            </button>
            <button onClick={() => setMessage("Top 10 assets")}>
              Top Assets
            </button>
            <button onClick={() => setMessage("Show BCA graduates")}>
              Education Search
            </button>
          </div>

          <div className="footer-note">
            AI responses are generated from election affidavit data.
            Always verify important information using the official
            Election Commission affidavits.
          </div>
        </div>
      ) : (
        <div className="chat-page">
          <div className="chat-container">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="bubble">
                  <div>{msg.content}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources">
                      <strong>Retrieved From</strong>
                      {msg.sources.map((s, i) => (
                        <div key={i}>📄 {s.candidate} • {s.section}</div>
                      ))}
                    </div>
                  )}
                  {msg.follow_ups && msg.follow_ups.length > 0 && (
                    <div className="follow-ups">
                      <p>You might also ask:</p>
                      {msg.follow_ups.map((q, i) => (
                        <button
                          key={i}
                          className="follow-up-btn"
                          onClick={() => {
                            setMessage(q);
                          }}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message assistant">
                <div className="bubble loading">Thinking...</div>
              </div>
            )}
          </div>

          <div className="bottom-input">
            <input
              type="text"
              placeholder="Ask a follow-up..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
            />
            <button onClick={sendMessage} disabled={loading}>↑</button>
          </div>

          <div className="footer-note">
            AI responses are generated from election affidavit data.
            Please verify important information using the official
            Election Commission affidavits.
          </div>
        </div>
      )}
    </div>
  );
}

export default App;