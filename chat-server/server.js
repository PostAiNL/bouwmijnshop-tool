import express from "express";
import cors from "cors";
const app = express();

const PORT = process.env.PORT || 10000;
const CORS_ORIGIN = (process.env.CORS_ORIGIN || "")
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

app.use(cors({ origin: CORS_ORIGIN.length ? CORS_ORIGIN : true }));
app.use(express.json());
app.use(express.static("public"));

app.get("/health", (req, res) => res.json({ ok: true }));

// simpele echo endpoint (later vervangen door echte chatlogica)
app.post("/api/chat", (req, res) => {
  const { message } = req.body || {};
  res.json({ reply: `Echo: ${message || ""}` });
});

app.listen(PORT, () => console.log(`Chat server on :${PORT}`));

