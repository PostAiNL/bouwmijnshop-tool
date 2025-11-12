// index.js
import express from "express";
import cors from "cors";
import rateLimit from "express-rate-limit";
import bodyParser from "body-parser";
import fetch from "node-fetch"; // alleen nodig voor Node < 18
import dotenv from "dotenv";
dotenv.config();

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(bodyParser.json({ limit: "1mb" }));
app.set("trust proxy", 1);

const limiter = rateLimit({ windowMs: 60 * 1000, max: 60 });
app.use("/api/", limiter);

// ---- Helpers
function fmtList(arr) {
  if (!arr || !arr.length) return "—";
  return arr.map((h) => `${String(h).padStart(2, "0")}:00`).join(", ");
}

function buildSystem(meta = {}) {
  // Meta uit de widget (optioneel)
  const mode = (meta.mode || "DEMO").toUpperCase();
  const bestHours = meta.best_hours || [];
  const lastUpload = meta.last_upload || "onbekend";
  const topHashtags = meta.top_hashtags || [];

  return [
    {
      role: "system",
      content:
        "Je bent PostAi Coach: kort, concreet, vriendelijk, NL taal. " +
        "Altijd 3 bullets + 1 actie. Focus op beste tijd, hook (8–12 woorden), max 3 hashtags. " +
        "Als data ontbreekt: geef veilige vuistregel.",
    },
    {
      role: "system",
      content:
        `Context:\n` +
        `- Gebruikersmodus: ${mode}\n` +
        `- Beste posturen: ${fmtList(bestHours)}\n` +
        `- Laatste upload: ${lastUpload}\n` +
        `- Voorkeur-hashtags: ${topHashtags.join(" ") || "—"}\n` +
        `- Product: PostAi (TikTok Growth Agent) — geen auto-posting, analytics + advies.`,
    },
    {
      role: "system",
      content:
        "Format strikt: \n" +
        "• Tip 1\n• Tip 2\n• Tip 3\n" +
        "👉 Actie: <één zin>",
    },
  ];
}

async function callOpenAI(messages) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return {
      ok: false,
      text: "⚠️ Server mist OPENAI_API_KEY. Voeg toe als environment variable.",
    };
  }

  try {
    const r = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        temperature: 0.4,
        max_tokens: 550,
        messages,
      }),
    });
    if (!r.ok) {
      const t = await r.text();
      return { ok: false, text: `API-fout (${r.status}): ${t.slice(0, 300)}` };
    }
    const data = await r.json();
    const text = data?.choices?.[0]?.message?.content?.trim() || "—";
    return { ok: true, text };
  } catch (e) {
    return { ok: false, text: "Netwerkfout richting OpenAI." };
  }
}

// ---- Chat endpoint
app.post("/api/chat", async (req, res) => {
  const { message, history = [], meta = {} } = req.body || {};

  // 1) Bouw systeem/context + korte geschiedenis (laatste 6 beurten)
  const sys = buildSystem(meta);
  const trimmedHistory = (Array.isArray(history) ? history : []).slice(-6);

  const msgs = [
    ...sys,
    ...trimmedHistory.map((m) => ({
      role: m.role === "assistant" ? "assistant" : "user",
      content: String(m.text || m.message || ""),
    })),
    { role: "user", content: String(message || "").slice(0, 2000) },
  ];

  // 2) LLM aanroepen
  const out = await callOpenAI(msgs);

  // 3) Antwoord
  res.json({
    ok: out.ok,
    reply: out.text,
  });
});

// Gezondheidscheck
app.get("/api/health", (_req, res) => res.json({ ok: true }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Chat server up on :${PORT}`));
