// chat-server/server.js
const path = require("path");
const express = require("express");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 10000;

// CORS (pas aan als je specifieke origins wilt)
app.use(cors());
app.use(express.json());

// statische assets uit /public
app.use(express.static(path.join(__dirname, "public")));

// healthcheck
app.get("/health", (req, res) => res.json({ ok: true }));

// widget-pagina
app.get("/widget", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "widget.html"));
});

// optioneel: root netjes laten antwoorden
app.get("/", (req, res) => {
  res.type("text/plain").send("Widget staat op /widget");
});

// start
app.listen(PORT, () => {
  console.log("Chat server running on port:", PORT);
});
