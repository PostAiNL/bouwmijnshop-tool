// chat-server/server.js
const express = require("express");
const cors = require("cors");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// ===== CORS =====
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*";
app.use((req, res, next) => {
  // assets mogen overal vandaan (handig voor testen)
  if (req.path.startsWith("/chat")) {
    return cors({ origin: ALLOWED_ORIGIN, credentials: false })(req, res, next);
  }
  return cors({ origin: "*" })(req, res, next);
});

app.use(express.json({ limit: "1mb" }));

// ===== Healthcheck =====
app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

// ===== Static voor widget-bestanden =====
const pub = path.join(__dirname, "public");
app.use(express.static(pub)); // hiermee werken /chat-widget.css en /chat-widget.js

// ===== Chat endpoint (stub / voorbeeld) =====
app.post("/chat", async (req, res) => {
  try {
    // -> Hier zou je OpenAI aanroepen. Voor nu als proof:
    const { message } = req.body || {};
    res.json({ ok: true, reply: `Echo: ${message || "Hallo!"}` });
  } catch (e) {
    console.error(e);
    res.status(500).json({ ok: false, error: "Server error" });
  }
});

// ===== Start =====
app.listen(PORT, () => {
  console.log(`chat-server listening on :${PORT}`);
});
