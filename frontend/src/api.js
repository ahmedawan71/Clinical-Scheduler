import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const sendMessage = (message) => {
  return api.post("/chat", {
    message: message,
  });
};
