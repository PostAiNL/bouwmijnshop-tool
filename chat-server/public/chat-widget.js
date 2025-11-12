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

  // ---- Status /
