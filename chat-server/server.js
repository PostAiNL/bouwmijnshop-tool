import express from "express";
import cors from "cors";
import rateLimit from "express-rate-limit";
import morgan from "morgan";
import { OpenAI } from "openai";

const app = express();

// ---- Config via env
const PORT = process.env.PORT || 10000;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*"; // zet dit in Render op je site-URL

// ---- Middlewares
app.use(morgan("tiny"));
app.use(express.json({ limit: "1mb" }));
app.use(
  cors({
    origin: (origin, cb) => {
      if (!origin || ALLOWED_ORIGIN === "*" || origin === ALLOWED_ORIGIN) {
        return cb(null, true);
      }
      return cb(new Error("Not allowed by CORS"), false);
    },
    credentials: false,
  })
);

// simpele rate limit
app.use(
  "/api/",
  rateLimit({
    windowMs: 60 * 1000,
    max: 20,
    standardHeaders: true,
    legacyHeaders: false,
  })
);

// static files (widget)
app.use(express.static("public"));

// health
app.get("/healthz", (req, res) =>
  res.json({ ok: true, ts: Date.now(), hasKey: Boolean(OPENAI_API_KEY) })
);

// ---- CHAT endpoint
app.post("/api/chat", async (req, res) => {
  try {
    if (!OPENAI_API_KEY) {
      return res
        .status(500)
        .json({ error: "OPENAI_API_KEY ontbreekt op de server." });
    }

    const { message, meta } = req.body || {};
    const userText = String(message || "").slice(0, 1000);

    if (!userText) return res.status(400).json({ error: "Lege vraag." });

    const client = new OpenAI({ apiKey: OPENAI_API_KEY });

    const systemPrompt =
      "Je bent de PostAi Assistent. Je helpt ondernemers met TikTok-analytics. " +
      "Antwoord kort, helder en vriendelijk. Bied 1 concrete vervolgstap.";

    const metaLine = meta
      ? `Context: ${JSON.stringify(meta).slice(0, 400)}`
      : "";

    const resp = await client.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.4,
      max_tokens: 350,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `${userText}\n\n${metaLine}` },
      ],
    });

    const text = resp.choices?.[0]?.message?.content?.trim() || "…";
    res.json({ reply: text });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Serverfout bij /api/chat." });
  }
});

// start
app.listen(PORT, () => {
  console.log(`Chat server up on :${PORT}`);
});
