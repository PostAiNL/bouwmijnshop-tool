// chat-server/server.js
const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// CORS
const allowed = process.env.CORS_ORIGIN
  ? process.env.CORS_ORIGIN.split(',').map(s => s.trim())
  : [];
app.use(cors({
  origin: function(origin, cb) {
    if (!origin) return cb(null, true);
    if (allowed.some(a => origin.endsWith(a.replace('*', '')) || a === origin)) {
      return cb(null, true);
    }
    return cb(null, false);
  },
  credentials: true
}));

app.use(express.json());

// 🔹 root → redirect naar widget
app.get('/', (req, res) => {
  return res.redirect('/widget');
});

// healthcheck
app.get('/health', (req, res) => res.send('ok'));

// 🔹 widget UI (serveer statische files uit /public)
app.use('/widget', express.static(path.join(__dirname, '..', 'public')));

// (optionele) chat-API endpoints
app.post('/api/message', async (req, res) => {
  // TODO: jouw logic / OpenAI-call
  res.json({ reply: 'Hallo! 👋 (demo-reply)' });
});

app.listen(PORT, () => {
  console.log(`Chat server listening on :${PORT}`);
});
