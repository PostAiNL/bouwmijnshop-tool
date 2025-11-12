/* ===== PostAi Chat 2.0 — floating widget (Optie A ready) ===== */
(function (global) {
  "use strict";

  /*** ---------- Config & Env ---------- ***/
  var SERVER = global.BMS_CHAT_SERVER || "";
  var CSS_URL = global.BMS_CHAT_CSS_URL || "/chat-widget.css";

  if (!SERVER) {
    console.warn("[PostAi Chat] BMS_CHAT_SERVER ontbreekt — UI werkt, API-calls mogelijk niet.");
  }

  /*** ---------- Safe document (escape uit iframes) ---------- ***/
  var DOC = (function () {
    try { return global.top.document; } catch (e) { return global.document; }
  })();

  /*** ---------- Idempotent: niet dubbel mounten ---------- ***/
  if (DOC.getElementById("bms-chat-launcher") || DOC.getElementById("bms-overlay")) {
    // Reeds aanwezig → niet opnieuw renderen
    return;
  }

  /*** ---------- Utilities ---------- ***/
  function createEl(tag, attrs, html) {
    var el = DOC.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "style" && typeof attrs[k] === "string") {
        el.style.cssText = attrs[k];
      } else {
        el.setAttribute(k, attrs[k]);
      }
    });
    if (html != null) el.innerHTML = html;
    return el;
  }

  function qs(sel, root) { return (root || DOC).querySelector(sel); }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c];
    });
  }

  /*** ---------- CSS inladen (met duplicate-guard) ---------- ***/
  function ensureCssOnce() {
    var already = DOC.querySelector('link[href="' + CSS_URL + '"]') || DOC.getElementById("bms-chat-css");
    if (already) return;

    var link = DOC.createElement("link");
    link.id = "bms-chat-css";
    link.rel = "stylesheet";
    link.href = CSS_URL;
    link.crossOrigin = "anonymous";
    DOC.head.appendChild(link);

    // (Best effort) fallback: als CSS niet laadt, hebben we inline styles op kritieke elementen
    link.addEventListener("error", function () {
      console.warn("[PostAi Chat] CSS kon niet worden geladen:", CSS_URL);
    });
  }
  ensureCssOnce();

  /*** ---------- Root bepalen (default: BODY) ---------- ***/
  var ROOT = DOC.body;

  /*** ---------- Overlay + basis-structuur ---------- ***/
  var overlay = createEl("div", {
    id: "bms-overlay",
    "aria-hidden": "false",
    // Fallback styles zodat overlay/launcher altijd zichtbaar is
    style: "position:fixed;inset:0;z-index:999998;pointer-events:none;"
  });

  // Launcher (floating button) — altijd zichtbaar via inline styles
  var launcher = createEl("button", {
    id: "bms-chat-launcher",
    "aria-label": "Open chat",
    style: [
      "position:fixed",
      "right:18px",
      "bottom:18px",
      "z-index:999999",
      "display:inline-flex",
      "align-items:center",
      "justify-content:center",
      "width:56px",
      "height:56px",
      "border-radius:999px",
      "border:none",
      "cursor:pointer",
      "background:#2563eb",
      "color:#fff",
      "box-shadow:0 8px 24px rgba(0,0,0,.18)"
    ].join(";")
  }, (
    '<svg viewBox="0 0 24 24" fill="none" width="24" height="24" aria-hidden="true">' +
    '<path d="M12 3c5.5 0 10 3.8 10 8.5S17.5 20 12 20a13 13 0 0 1-3.7-.5L3 21l1.7-4.3A8.6 8.6 0 0 1 2 11.5C2 6.8 6.5 3 12 3Z" stroke="currentColor" stroke-width="1.6"/>' +
    "</svg>"
  ));

  // Teaser (schuift even in beeld)
  var teaser = createEl("div", {
    id: "bms-chat-teaser",
    role: "status"
  }, "Hulp nodig? Sanne helpt je graag.");

  // Chat-paneel
  var chat = createEl("div", {
    id: "bms-chat",
    role: "dialog",
    "aria-modal": "true",
    "aria-label": "Chat met Sanne",
    style: [
      "position:fixed",
      "right:18px",
      "bottom:88px",
      "z-index:999999",
      "width: min(360px, 92vw)",
      "max-height: 70vh",
      "display:none",
      "background:#fff",
      "color:#111",
      "border: 1px solid rgba(0,0,0,.06)",
      "border-radius:16px",
      "box-shadow: 0 14px 40px rgba(0,0,0,.22)",
      "overflow:hidden",
      "pointer-events:auto"
    ].join(";")
  }, (
    '<div class="hdr" style="display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid #eef2f7;">' +
      '<div class="avatar" aria-hidden="true" style="width:28px;height:28px;border-radius:999px;background:#2563eb;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;">S</div>' +
      '<div style="flex:1;">' +
        '<div class="ttl" style="font-weight:700;line-height:1;">Sanne van PostAi</div>' +
        '<div class="sub" style="font-size:12px;color:#16a34a;">• online</div>' +
      '</div>' +
      '<button class="close" aria-label="Sluit chat" style="border:none;background:transparent;font-size:16px;cursor:pointer;">✕</button>' +
    '</div>' +
    '<div id="bms-body" style="padding:12px;height:48vh;overflow:auto;background:#fafbff;"></div>' +
    '<div class="inp" style="display:flex;gap:8px;padding:10px;border-top:1px solid #eef2f7;background:#fff;">' +
      '<input id="bms-input" placeholder="Typ je bericht…" autocomplete="off" aria-label="Bericht" ' +
             'style="flex:1;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;outline:none;" />' +
      '<button id="bms-send" aria-label="Verstuur" ' +
              'style="border:none;background:#2563eb;color:#fff;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer;">Verstuur</button>' +
    '</div>'
  ));

  overlay.appendChild(launcher);
  overlay.appendChild(teaser);
  overlay.appendChild(chat);
  ROOT.appendChild(overlay);

  /*** ---------- Elements & events ---------- ***/
  var body = qs("#bms-body");
  var input = qs("#bms-input");
  var sendBtn = qs("#bms-send");
  var closeBtn = chat.querySelector(".close");

  launcher.onclick = function () {
    chat.style.display = "block";
    input && input.focus();
  };

  closeBtn.onclick = function () {
    chat.style.display = "none";
  };

  // Teaser animatie
  if (!global.localStorage.getItem("bmsChatTeaseShown")) {
    // met CSS zou dit netter, maar minimalistisch:
    teaser.style.cssText = [
      "position:fixed",
      "right:86px",
      "bottom:22px",
      "z-index:999999",
      "background:#111827",
      "color:#fff",
      "padding:8px 10px",
      "border-radius:10px",
      "box-shadow:0 8px 24px rgba(0,0,0,.16)",
      "opacity:0",
      "transition:opacity .25s ease"
    ].join(";");

    setTimeout(function () { teaser.style.opacity = "1"; }, 600);
    setTimeout(function () {
      teaser.style.opacity = "0";
      global.localStorage.setItem("bmsChatTeaseShown", "1");
    }, 5200);
  }

  /*** ---------- History helpers ---------- ***/
  var HKEY = "bmsChatHistory";

  function append(role, text) {
    var now = new Date().toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" });
    var msg = createEl("div", {
      "class": "bms-msg " + role
    }, (
      '<div class="bubble" style="position:relative;display:inline-block;max-width:90%;padding:10px 12px;border-radius:12px;' +
      (role === "user"
        ? 'margin:6px 0 2px auto;background:#2563eb;color:#fff;'
        : 'margin:6px 0 2px 0;background:#fff;color:#111;border:1px solid #eef2f7;') +
      '">' + escapeHtml(text) + ' <button class="copy-btn" title="Kopieer" aria-label="Kopieer" ' +
      'style="position:absolute;right:6px;bottom:-20px;border:none;background:transparent;cursor:pointer;font-size:12px;">📋</button></div>' +
      '<div class="time" style="font-size:11px;color:#94a3b8;margin:' + (role === "user" ? '2px 0 8px auto;text-align:right;' : '2px 0 8px 0;') + '">' + now + "</div>"
    ));
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;

    var copyBtn = msg.querySelector(".copy-btn");
    if (copyBtn) {
      copyBtn.onclick = function () {
        try {
          navigator.clipboard.writeText(text);
          copyBtn.textContent = "✅";
          setTimeout(function () { copyBtn.textContent = "📋"; }, 1500);
        } catch (e) {}
      };
    }
  }

  function save(role, text) {
    try {
      var h = JSON.parse(global.localStorage.getItem(HKEY) || "[]");
      h.push({ role: role, text: text });
      global.localStorage.setItem(HKEY, JSON.stringify(h.slice(-60)));
    } catch (e) {
      // storage kan vol of geblokkeerd zijn – fail silently
    }
  }

  // Restore vorige sessie
  try {
    JSON.parse(global.localStorage.getItem(HKEY) || "[]").forEach(function (m) {
      append(m.role, m.text);
    });
  } catch (e) {}

  /*** ---------- Welcome flow (éénmalig) ---------- ***/
  if (!global.localStorage.getItem("bmsChatWelcomed")) {
    ["Hi! Ik ben Sanne. Waar kan ik je mee helpen?",
     "Tip: wil je beste posttijd? Zeg “beste tijd”.",
     "🔒 We bewaren niets zonder jouw actie."]
      .forEach(function (w, i) {
        setTimeout(function () { append("bot", w); save("bot", w); }, i * 400);
      });
    global.localStorage.setItem("bmsChatWelcomed", "1");
  }

  /*** ---------- Typ-indicator ---------- ***/
  function showTyping() {
    append("bot", "<span class='typing'>Sanne is aan het typen</span>");
  }
  function replaceTyping(text) {
    var last = body.querySelector(".typing");
    if (last) {
      last.parentElement.innerHTML = escapeHtml(text);
      body.scrollTop = body.scrollHeight;
    } else {
      append("bot", text);
    }
  }

  /*** ---------- Suggesties / feedback / restart ---------- ***/
  function addSuggestions(list) {
    var wrap = createEl("div", { "class": "bms-suggestions" });
    wrap.style.cssText = "display:flex;flex-wrap:wrap;gap:8px;margin:8px 0;";
    list.forEach(function (label) {
      var btn = createEl("button", {}, escapeHtml(label));
      btn.style.cssText = "border:1px solid #e5e7eb;background:#fff;border-radius:999px;padding:6px 10px;cursor:pointer;font-size:12px;";
      btn.onclick = function () {
        append("user", label); save("user", label);
        wrap.remove();
        sendToAI(label);
      };
      wrap.appendChild(btn);
    });
    body.appendChild(wrap);
    body.scrollTop = body.scrollHeight;
  }

  function addFeedback() {
    var fb = createEl("div", { "class": "bms-feedback" },
      "<span>Was dit nuttig?</span> " +
      "<button aria-label='Ja'>👍</button> " +
      "<button aria-label='Nee'>👎</button>"
    );
    fb.style.cssText = "display:flex;align-items:center;gap:8px;margin:8px 0;color:#475569;";
    Array.prototype.forEach.call(fb.querySelectorAll("button"), function (b) {
      b.style.cssText = "border:1px solid #e5e7eb;background:#fff;border-radius:8px;padding:6px 10px;cursor:pointer;";
      b.onclick = function () { fb.innerHTML = "Bedankt voor je feedback 💜"; };
    });
    body.appendChild(fb);
  }

  function addRestart() {
    var btn = createEl("button", { "class": "bms-restart" }, "🔄 Nieuw gesprek");
    btn.style.cssText = "border:1px solid #e5e7eb;background:#fff;border-radius:8px;padding:8px 10px;cursor:pointer;margin:8px 0;";
    btn.onclick = function () {
      try { global.localStorage.removeItem(HKEY); } catch (e) {}
      body.innerHTML = "";
      append("bot", "Nieuwe sessie gestart. Waar wil je mee beginnen?");
    };
    body.appendChild(btn);
  }

  /*** ---------- Versturen ---------- ***/
  sendBtn.onclick = function () { sendToAI(input.value); };
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      sendToAI(input.value);
    }
  });

  async function sendToAI(txt) {
    txt = (txt || "").trim();
    if (!txt) return;

    append("user", txt); save("user", txt);
    input.value = ""; input.focus();
    showTyping();

    // Meta uit localStorage (optioneel)
    var mode = global.localStorage.getItem("postai_mode") || "DEMO";
    var bestHours, topHashtags;
    try { bestHours = JSON.parse(global.localStorage.getItem("postai_best_hours") || "[]"); } catch (e) { bestHours = []; }
    var lastUpload = global.localStorage.getItem("postai_last_upload") || "";
    try { topHashtags = JSON.parse(global.localStorage.getItem("postai_top_hashtags") || "[]"); } catch (e) { topHashtags = []; }

    // History voor context (laatste 6)
    var history = [];
    try {
      history = JSON.parse(global.localStorage.getItem(HKEY) || "[]")
        .slice(-6)
        .map(function (m) {
          return { role: (m.role === "bot" ? "assistant" : "user"), text: m.text };
        });
    } catch (e) {}

    try {
      var res = await fetch((SERVER || "") + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: txt,
          history: history,
          meta: { mode: mode, best_hours: bestHours, last_upload: lastUpload, top_hashtags: topHashtags }
        })
      });

      var data = {};
      try { data = await res.json(); } catch (e) {}

      var reply = (data && data.reply) || "Dankje! Ik kijk even met je mee.";
      replaceTyping(reply);
      save("bot", reply);

      addSuggestions(["Beste posttijd", "Analyseer mijn upload", "Geef hooks", "Toon weekplan"]);
      addFeedback();
      addRestart();
    } catch (e) {
      console.error("[PostAi Chat] API-fout:", e);
      replaceTyping("⚠️ Netwerkfout. Probeer het zo nog eens.");
    }
  }

  /*** ---------- Optionele embed-API ---------- ***/
  // Voor Optie B/C: laat je embedder expliciet mounten binnen een root container.
  // In deze implementatie gebruiken we nog steeds fixed positioning (viewport),
  // dus root is alleen relevant voor de DOM-plaatsing.
  global.initBMS = function (root) {
    if (!root || root.contains(overlay)) return;
    try { root.appendChild(overlay); } catch (e) {}
  };

})(window);
