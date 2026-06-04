import { useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = {
      role: "user",
      content: message,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
          }),
        }
      );

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Unable to connect to backend.",
        },
      ]);
    }

    setMessage("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  return (
    <div className="app">

      {messages.length === 0 ? (

        <div className="landing">

          <h1>
            Candidate Intelligence AI
          </h1>

          <p>
            Ask anything about candidates,
            parties, constituencies,
            education, assets and affidavits.
          </p>

          <div className="prompt-box">

            <input
              type="text"
              placeholder="Ask anything..."
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
              onKeyDown={handleKeyPress}
            />

            <button onClick={sendMessage}>
              ↑
            </button>

          </div>

          <div className="suggestions">

            <button
              onClick={() =>
                setMessage(
                  "Compare MKStalin and VSBabu"
                )
              }
            >
              Compare Candidates
            </button>

            <button
              onClick={() =>
                setMessage(
                  "Show DMK candidates"
                )
              }
            >
              DMK Candidates
            </button>

            <button
              onClick={() =>
                setMessage(
                  "Top 10 assets"
                )
              }
            >
              Top Assets
            </button>

            <button
              onClick={() =>
                setMessage(
                  "Show BCA graduates"
                )
              }
            >
              Education Search
            </button>

          </div>

        </div>

      ) : (

        <div className="chat-page">

          <div className="chat-container">

            {messages.map(
              (msg, index) => (
                <div
                  key={index}
                  className={`message ${msg.role}`}
                >
                  <div className="bubble">
                    {msg.content}
                  </div>
                </div>
              )
            )}

          </div>

          <div className="bottom-input">

            <input
              type="text"
              placeholder="Ask a follow-up..."
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
              onKeyDown={handleKeyPress}
            />

            <button onClick={sendMessage}>
              ↑
            </button>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;