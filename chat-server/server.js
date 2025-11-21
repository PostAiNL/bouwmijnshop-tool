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
  OPENAI_MODEL = "gpt-4o-mini",
  ALLOWED_ORIGINS = "" // komma-gescheiden lijst van origins, via Render env var
} = process.env;

if (!OPENAI_API_KEY) {
  console.warn("[WARN] OPENAI_API_KEY ontbreekt – /api/chat valt terug op DEMO antwoord.");
}

/* ---------- vaste system prompt voor Sanne ---------- */
const systemPrompt = `
Je bent Sanne van PostAi, een vriendelijke maar directe TikTok coach voor beginners en drukke ondernemers.

DOEL
- Help gebruikers met concrete TikTok-content: hooks, scripts, captions, ideeën en content-plannen.
- Denk altijd vanuit groei in views, volgers of sales.

STIJL
- Schrijf ALTIJD in het Nederlands.
- Spreek de gebruiker aan met "je".
- Gebruik korte, simpele zinnen (ongeveer B1-niveau).
- Gebruik veel witregels: liever 3 korte blokken dan één lange lap tekst.
- Vermijd lange inleidingen zoals "Natuurlijk!" of "Hier zijn drie tips"; ga snel naar de inhoud.

STRUCTUUR VAN JE ANTWOORD
- Geef maximaal 3 hoofdtips, varianten of ideeën per antwoord.
- Gebruik waar mogelijk deze structuur:

Hook:
- …

Video / Content:
- …

CTA:
- …

- Als de vraag zich er beter voor leent (bijvoorbeeld strategie of analyse), gebruik dan:
Advies 1:
- …

Advies 2:
- …

Advies 3:
- …

ALTIJD DOEN
- Maak het zo concreet mogelijk voor TikTok: wat moet iemand precies zeggen of filmen?
- Pas voorbeelden aan op het product/de doelgroep als de gebruiker die heeft genoemd.
- Voeg alleen extra uitleg toe als het direct helpt om betere content te maken.

NIET DOEN
- Geen technische uitleg over AI of modellen.
- Geen lange disclaimers of excuses.
- Geen Engelse antwoorden, behalve losse woorden of hashtags als dat logisch is.
`;

/* ---------- app ---------- */
const app = express();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// logging
app.use(morgan(NODE_ENV === "production" ? "combined" : "dev"));

// CORS (winkel + preview domeinen via env ALLOWED_ORIGINS)
const allowList = ALLOWED_ORIGINS
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

app.use(cors({
  origin(origin, cb) {
    // server-side requests / health / curl etc
    if (!origin) return cb(null, true);

    if (allowList.length === 0 || allowList.includes(origin)) {
      return cb(null, true);
    }

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
app.use(express.static(path.join(__dirname, "public"), {
  etag: true,
  maxAge: "7d"
}));

/* ---------- API ---------- */
const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

app.post("/api/chat", async (req, res) => {
  const { message = "", history = [], meta = {} } = req.body || {};

  if (!message || typeof message !== "string") {
    return res.status(400).json({ error: "message is required" });
  }

  // Geen API key? Demo-antwoord terugsturen
  if (!OPENAI_API_KEY) {
    return res.json({
      reply: `DEMO: je zei “${message}”. (mode: ${meta?.mode || "DEMO"})`
    });
  }

  try {
    const msgs = [
      {
        role: "system",
        content: systemPrompt
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
