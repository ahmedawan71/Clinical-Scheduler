import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const sendMessage = (message) => {
  return api.post("/chat", {
    message: message,
  });
};

export async function streamMessage(message, onChunk) {
  const response = await fetch("http://127.0.0.1:8000/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value));
  }
}
