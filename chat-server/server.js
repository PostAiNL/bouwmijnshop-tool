// chat-server/server.js  (CommonJS)
const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// CORS & JSON
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.sendStatus(200);
  next();
});

// Statische assets uit ./public
app.use(express.static(path.join(__dirname, "public")));

// Healthcheck
app.get("/health", (_req, res) => res.json({ ok: true }));

// Widget pagina (IFRAME-content)
app.get("/widget", (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "widget.html"));
});

// Dummy endpoint waar de widget zijn bericht naartoe post
app.post("/api/message", (req, res) => {
  // Hier kun je later doorsturen naar Slack, e-mail, database, etc.
  console.log("Nieuw chatbericht:", req.body);
  res.json({ ok: true, received: req.body });
});

app.listen(PORT, () => {
  console.log(`Chat server running on :${PORT}`);
});
