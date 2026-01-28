import { useState } from "react";
import { sendMessage } from "./api";

function App() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!message) return;

    setLoading(true);
    try {
      const res = await sendMessage(message);
      setResponse(res.data);
    } catch (error) {
      console.error(error);
      alert("Error communicating with backend");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h2>AI Clinical Scheduling System</h2>

      <textarea
        rows="4"
        style={{ width: "100%", marginBottom: "10px" }}
        placeholder="Type your request..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />

      <button onClick={handleSend} disabled={loading}>
        {loading ? "Processing..." : "Send"}
      </button>

      {response && (
        <div style={{ marginTop: "20px" }}>
          <h3>System Response</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
