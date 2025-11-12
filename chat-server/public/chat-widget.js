/* global window, document, localStorage, fetch */
(() => {
  const SERVER = window.BMS_CHAT_SERVER || ""; // bijv. https://chatbot-2-0-3v8l.onrender.com
  if (!SERVER) {
    console.warn("[BMS-Chat] Geen BMS_CHAT_SERVER gezet.");
    return;
  }

  // ---- Helpers
  const qs = (s, r = document) => r.querySelector(s);
  const save = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  const load = (k, d) => {
    try { return JSON.parse(localStorage.getItem(k)) ?? d; }
    catch { return d; }
  };

  // ---- UI opbouwen
  const toggle = document.createElement("button");
  toggle.id = "bms-chat-toggle";
  toggle.setAttribute("aria-label", "Open chat");
  toggle.innerHTML = "💬";

  const panel = document.createElement("div");
  panel.id = "bms-chat-panel";
  panel.innerHTML = `
    <div class="bms-chat-header">
      <div class="bms-chat-title">PostAi Chat</div>
      <div class="bms-chat-status" id="bms-status">• checking…</div>
    </div>
    <div id="bms-chat-messages"></div>
    <div class="bms-chat-input">
      <input id="bms-chat-text" type="text" placeholder="Typ je bericht..." />
      <button id="bms-chat-send">Verstuur</button>
    </div>
  `;

  document.body.appendChild(toggle);
  document.body.appendChild(panel);

  const statusEl = qs("#bms-status", panel);
  const messagesEl = qs("#bms-chat-messages", panel);
  const inputEl = qs("#bms-chat-text", panel);
  const sendBtn = qs("#bms-chat-send", panel);

  // ---- Status / health
  const setStatus = (ok) => {
    statusEl.textContent = ok ? "• online" : "• offline";
    statusEl.style.color = ok ? "#16a34a" : "#ef4444";
  };
  fetch(`${SERVER}/health`).then(r => r.json()).then(d => setStatus(!!d.ok)).catch(() => setStatus(false));

  // ---- Historie
  const STORE_KEY = "bms-chat-history";
  const history = load(STORE_KEY, []); // [{role:'user'|'bot', text:'...'}]
  const append = (role, text) => {
    const div = document.createElement("div");
    div.className = `bms-msg ${role}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };
  history.forEach(m => append(m.role, m.text));

  const pushHistory = (role, text) => {
    history.push({ role, text });
    save(STORE_KEY, history.slice(-50)); // bewaar laatste 50
  };

  // ---- Typing indicator
  let typingEl = null;
  const showTyping = () => {
    typingEl = document.createElement("div");
    typingEl.className = "bms-typing";
    typingEl.textContent = "Assistent is aan het typen…";
    messagesEl.appendChild(typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };
  const hideTyping = () => {
    if (typingEl && typingEl.parentNode) typingEl.parentNode.removeChild(typingEl);
    typingEl = null;
  };

  // ---- Verzenden
  async function sendMessage() {
    const text = (inputEl.value || "").trim();
    if (!text) return;

    append("user", text);
    pushHistory("user", text);
    inputEl.value = "";
    inputEl.focus();

    sendBtn.disabled = true;
    showTyping();

    try {
      const r = await fetch(`${SERVER}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await r.json().catch(() => ({}));
      hideTyping();

      if (!r.ok || !data.ok) {
        const msg = data?.error || `Er ging iets mis (${r.status})`;
        append("bot", msg);
        pushHistory("bot", msg);
      } else {
        const reply = (data.reply || "Oké.").toString();
        append("bot", reply);
        pushHistory("bot", reply);
      }
    } catch (e) {
      hideTyping();
      const msg = "Verbinding mislukt. Probeer later opnieuw.";
      append("bot", msg);
      pushHistory("bot", msg);
    } finally {
      sendBtn.disabled = false;
    }
  }

  // ---- Events
  toggle.addEventListener("click", () => {
    const open = panel.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) inputEl.focus();
  });

  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  // Optioneel: begroeting 1x
  if (!history.length) {
    const hi = "Hi! Stel me je vraag over je TikTok-data, ik denk mee. 😊";
    append("bot", hi);
    pushHistory("bot", hi);
  }
})();
