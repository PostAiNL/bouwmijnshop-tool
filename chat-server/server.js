// server.js
import express from "express";
import cors from "cors";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import path from "path";
import { fileURLToPath } from "url";
import OpenAI from "openai";

/* ---------- config ---------- */
const {
  PORT = 3000,
  NODE_ENV = "production",
  OPENAI_API_KEY,
  OPENAI_MODEL = "gpt-4o-mini", // kies wat je wilt gebruiken
  ALLOWED_ORIGINS = ""          // komma-gescheiden lijst van origins
} = process.env;

if (!OPENAI_API_KEY) {
  console.warn("[WARN] OPENAI_API_KEY ontbreekt – /api/chat valt terug op DEMO antwoord.");
}

/* ---------- app ---------- */
const app = express();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// logging
app.use(morgan(NODE_ENV === "production" ? "combined" : "dev"));

// CORS (winkel + preview domeinen toelaten)
const allowList = ALLOWED_ORIGINS
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

app.use(cors({
  origin(origin, cb) {
    if (!origin) return cb(null, true); // server-side/health/ping
    if (allowList.length === 0 || allowList.includes(origin)) return cb(null, true);
    return cb(new Error("CORS blocked for origin: " + origin));
  }
}));

// body parser
app.use(express.json({ limit: "1mb" }));

// rate limit (per IP)
app.use("/api/", rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false
}));

/* ---------- static widget assets ---------- */
// Zorg dat je chat-widget.js en chat-widget.css in /public staan
app.use(express.static(path.join(__dirname, "public"), {
  etag: true,
  maxAge: "7d",
}));

/* ---------- API ---------- */
const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

app.post("/api/chat", async (req, res) => {
  const { message = "", history = [], meta = {} } = req.body || {};

  // Guardrails
  if (!message || typeof message !== "string") {
    return res.status(400).json({ error: "message is required" });
  }

  // Als er geen API key is, stuur demo response terug zodat de widget blijft werken
  if (!OPENAI_API_KEY) {
    return res.json({ reply: `DEMO: je zei “${message}”. (mode: ${meta?.mode || "DEMO"})` });
  }

  try {
    // Bouw messages op uit geschiedenis
    const msgs = [
      {
        role: "system",
        content:
          "Je bent Sanne van PostAi. Antwoord kort en behulpzaam in het Nederlands. " +
          "Als het over social posts gaat, geef concrete tips."
      },
      ...history.map(m => ({
        role: m.role === "assistant" ? "assistant" : "user",
        content: String(m.text || m.content || "")
      })),
      { role: "user", content: message }
    ];

    const completion = await openai.chat.completions.create({
      model: OPENAI_MODEL,
      messages: msgs,
      temperature: 0.7,
      max_tokens: 500
    });

    const reply =
      completion?.choices?.[0]?.message?.content?.trim() ||
      "Dankje! Ik kijk even met je mee.";

    res.json({ reply });
  } catch (err) {
    console.error("OpenAI/Server error:", err?.response?.data || err);
    res.status(500).json({ error: "Server error" });
  }
});

/* ---------- health ---------- */
app.get("/api/health", (_req, res) => res.json({ ok: true }));

/* ---------- start ---------- */
app.listen(PORT, () => {
  console.log(`[PostAi] Chat-server draait op http://localhost:${PORT}`);
  if (allowList.length) {
    console.log("[PostAi] CORS allowlist:", allowList.join(", "));
  } else {
    console.log("[PostAi] CORS allowlist leeg — alle origins toegestaan.");
  }
});
