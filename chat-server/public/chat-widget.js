/* ===== PostAi Chat 2.0 — JS (werkt met absolute overlay CSS + click-proxy) ===== */
(function (global) {
  "use strict";

  /*** ---------- Config ---------- ***/
  var SERVER  = global.BMS_CHAT_SERVER   || "";
  var CSS_URL = global.BMS_CHAT_CSS_URL  || "/chat-widget.css";

  if (!SERVER) {
    console.warn("[PostAi Chat] BMS_CHAT_SERVER ontbreekt — UI werkt, API-calls mogelijk niet.");
  }

  /*** ---------- Safe document ---------- ***/
  var DOC = (function () { try { return global.document; } catch (e) { return global.document; } })();

  /*** ---------- Idempotent mount ---------- ***/
  if (DOC.getElementById("bms-chat-launcher") || DOC.getElementById("bms-overlay")) return;

  /*** ---------- Utils ---------- ***/
  var qs = function(sel, root){ return (root || DOC).querySelector(sel); };
  var el = function(tag, attrs, html){
    var n = DOC.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function(k){ n.setAttribute(k, attrs[k]); });
    if (html != null) n.innerHTML = html;
    return n;
  };
  var escapeHtml = function(s){
    return String(s).replace(/[&<>"]/g, function(c){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  };

  /*** ---------- CSS laden (1x) ---------- ***/
  (function ensureCss(){
    if (DOC.querySelector('link[href="'+CSS_URL+'"]') || DOC.getElementById("bms-chat-css")) return;
    var link = DOC.createElement("link");
    link.id  = "bms-chat-css";
    link.rel = "stylesheet";
    link.href = CSS_URL;
    DOC.head.appendChild(link);
  })();

  /*** ---------- DOM structuur ---------- ***/
  var overlay = el("div", { id:"bms-overlay", "aria-hidden":"false" });

  var launcher = el("button", { id:"bms-chat-launcher", "aria-label":"Open chat" },
    '<svg viewBox="0 0 24 24" fill="none" width="24" height="24" aria-hidden="true">' +
      '<path d="M12 3c5.5 0 10 3.8 10 8.5S17.5 20 12 20a13 13 0 0 1-3.7-.5L3 21l1.7-4.3A8.6 8.6 0 0 1 2 11.5C2 6.8 6.5 3 12 3Z" stroke="currentColor" stroke-width="1.6"/>' +
    '</svg>'
  );

  var teaser = el("div", { id:"bms-chat-teaser", role:"status" }, "Hulp nodig? Sanne helpt je graag.");

  var chat = el("div", {
    id:"bms-chat",
    role:"dialog",
    "aria-modal":"true",
    "aria-label":"Chat met Sanne"
  }, (
    '<div class="hdr">' +
      '<div class="avatar" aria-hidden="true">S</div>' +
      '<div><div class="ttl">Sanne van PostAi</div><div class="sub">• online</div></div>' +
      '<button class="close" aria-label="Sluit chat">✕</button>' +
    '</div>' +
    '<div id="bms-body"></div>' +
    '<div class="inp">' +
      '<input id="bms-input" placeholder="Typ je bericht…" autocomplete="off" aria-label="Bericht"/>' +
      '<button id="bms-send" aria-label="Verstuur">Verstuur</button>' +
    '</div>'
  ));

  overlay.appendChild(launcher);
  overlay.appendChild(teaser);
  overlay.appendChild(chat);
  DOC.body.appendChild(overlay);

  /*** ---------- Elements & events ---------- ***/
  var body    = qs("#bms-body");
  var input   = qs("#bms-input");
  var sendBtn = qs("#bms-send");
  var closeBtn= chat.querySelector(".close");

  launcher.addEventListener("click", function(){
    chat.style.display = "block";
    if (input) input.focus();
  });
  closeBtn.addEventListener("click", function(){
    chat.style.display = "none";
  });

  // Teaser show (eenmalig)
  if (!global.localStorage.getItem("bmsChatTeaseShown")) {
    setTimeout(function(){ teaser.classList.add("show"); }, 600);
    setTimeout(function(){
      teaser.classList.remove("show");
      global.localStorage.setItem("bmsChatTeaseShown","1");
    }, 5200);
  }

  /*** ---------- History ---------- ***/
  var HKEY = "bmsChatHistory";

  function append(role, text){
    var now = new Date().toLocaleTimeString("nl-NL",{hour:"2-digit",minute:"2-digit"});
    var row = el("div", { "class":"bms-msg "+role }, (
      '<div class="bubble">' + escapeHtml(text) + ' <button class="copy-btn" title="Kopieer" aria-label="Kopieer">📋</button></div>' +
      '<div class="time">' + now + '</div>'
    ));
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
    var copyBtn = row.querySelector(".copy-btn");
    if (copyBtn) {
      copyBtn.onclick = function(){
        try { navigator.clipboard.writeText(text); copyBtn.textContent="✅"; setTimeout(function(){ copyBtn.textContent="📋"; }, 1500); }
        catch(e){}
      };
    }
  }

  function save(role, text){
    try {
      var h = JSON.parse(global.localStorage.getItem(HKEY) || "[]");
      h.push({ role:role, text:text });
      global.localStorage.setItem(HKEY, JSON.stringify(h.slice(-60)));
    } catch(e){}
  }

  // Restore vorige sessie
  try { JSON.parse(global.localStorage.getItem(HKEY) || "[]").forEach(function(m){ append(m.role, m.text); }); } catch(e){}

  /*** ---------- Welcome (éénmalig) ---------- ***/
  if (!global.localStorage.getItem("bmsChatWelcomed")) {
    ["Hi! Ik ben Sanne. Waar kan ik je mee helpen?",
     "Tip: wil je beste posttijd? Zeg “beste tijd”.",
     "🔒 We bewaren niets zonder jouw actie."]
      .forEach(function(w,i){ setTimeout(function(){ append("bot", w); save("bot", w); }, i*400); });
    global.localStorage.setItem("bmsChatWelcomed","1");
  }

  /*** ---------- Typing ---------- ***/
  function showTyping(){
    var now = new Date().toLocaleTimeString("nl-NL",{hour:"2-digit",minute:"2-digit"});
    var row = el("div", { "class":"bms-msg bot typing-row" }, (
      '<div class="bubble"><span class="typing">Sanne is aan het typen</span></div>' +
      '<div class="time">' + now + '</div>'
    ));
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
  }
  function replaceTyping(text){
    var row  = body.querySelector(".typing-row");
    if (row) {
      var bubble = row.querySelector(".bubble");
      if (bubble) bubble.innerHTML = escapeHtml(text) + ' <button class="copy-btn" title="Kopieer" aria-label="Kopieer">📋</button>';
      row.classList.remove("typing-row");
      var copyBtn = row.querySelector(".copy-btn");
      if (copyBtn) {
        copyBtn.onclick = function(){
          try { navigator.clipboard.writeText(text); copyBtn.textContent="✅"; setTimeout(function(){ copyBtn.textContent="📋"; }, 1500); }
          catch(e){}
        };
      }
    } else {
      append("bot", text);
    }
    body.scrollTop = body.scrollHeight;
  }

  /*** ---------- UX helpers ---------- ***/
  function addSuggestions(list){
    var wrap = el("div", { "class":"bms-suggestions" });
    list.forEach(function(label){
      var btn = el("button", {}, escapeHtml(label));
      btn.onclick = function(){
        append("user", label); save("user", label);
        wrap.remove();
        sendToAI(label);
      };
      wrap.appendChild(btn);
    });
    body.appendChild(wrap);
    body.scrollTop = body.scrollHeight;
  }
  function addFeedback(){
    var fb = el("div", { "class":"bms-feedback" },
      "<span>Was dit nuttig?</span><button aria-label='Ja'>👍</button><button aria-label='Nee'>👎</button>"
    );
    Array.prototype.forEach.call(fb.querySelectorAll("button"), function(b){
      b.onclick = function(){ fb.innerHTML = "Bedankt voor je feedback 💜"; };
    });
    body.appendChild(fb);
  }
  function addRestart(){
    var btn = el("button", { "class":"bms-restart" }, "🔄 Nieuw gesprek");
    btn.onclick = function(){
      try { global.localStorage.removeItem(HKEY); } catch(e){}
      body.innerHTML = "";
      append("bot","Nieuwe sessie gestart. Waar wil je mee beginnen?");
    };
    body.appendChild(btn);
  }

  /*** ---------- Verzenden ---------- ***/
  sendBtn.addEventListener("click", function(){ sendToAI(input.value); });
  input.addEventListener("keydown", function(e){
    if (e.key === "Enter") { e.preventDefault(); sendToAI(input.value); }
  });

  async function sendToAI(txt){
    txt = (txt || "").trim();
    if (!txt) return;

    append("user", txt); save("user", txt);
    input.value = ""; input.focus();
    showTyping();

    var mode = global.localStorage.getItem("postai_mode") || "DEMO";
    var bestHours = []; var topHashtags = [];
    try { bestHours   = JSON.parse(global.localStorage.getItem("postai_best_hours") || "[]"); } catch(e){}
    var lastUpload = global.localStorage.getItem("postai_last_upload") || "";
    try { topHashtags = JSON.parse(global.localStorage.getItem("postai_top_hashtags") || "[]"); } catch(e){}

    var history = [];
    try {
      history = JSON.parse(global.localStorage.getItem(HKEY) || "[]")
        .slice(-6)
        .map(function(m){ return { role: (m.role==="bot"?"assistant":"user"), text: m.text }; });
    } catch(e){}

    try {
      var res = await fetch(SERVER + "/api/chat", {
        method: "POST",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify({
          message: txt,
          history: history,
          meta: { mode: mode, best_hours: bestHours, last_upload: lastUpload, top_hashtags: topHashtags }
        })
      });
      var data = {};
      try { data = await res.json(); } catch(e){}
      var reply = (data && data.reply) || "Dankje! Ik kijk even met je mee.";
      replaceTyping(reply);
      save("bot", reply);

      addSuggestions(["Beste posttijd","Analyseer mijn upload","Geef hooks","Toon weekplan"]);
      addFeedback();
      addRestart();
    } catch (e) {
      console.error("[PostAi Chat] API-fout:", e);
      replaceTyping("⚠️ Netwerkfout. Probeer het zo nog eens.");
    }
  }

  /*** ---------- CLICK-PROXY rechtsonder ---------- ***/
  function installClickProxy(){
    if (!launcher) return;
    DOC.addEventListener("click", function(e){
      try {
        var r = launcher.getBoundingClientRect();
        var x = e.clientX, y = e.clientY;
        if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) {
          // forceer klik op launcher, blokkeer andere handlers
          e.stopPropagation();
          e.preventDefault();
          launcher.click();
        }
      } catch(err){}
    }, true); // capture-fase
  }
  installClickProxy();

  /*** ---------- Optionele embed-API ---------- **/
  global.initBMS = function(root){
    if (!root) return;
    if (!overlay.parentNode || overlay.parentNode !== root) {
      try { root.appendChild(overlay); } catch(e){}
    }
  };

})(window);
  /*** ---------- Pro-badge / overlay neutraliseren ---------- ***/
  function disableForeignBadges(){
    try {
      // Streamlit / host "pro badge" die in je hoek zit
      var badge = DOC.querySelector('div.pro-badge');
      if (badge) {
        badge.style.pointerEvents = 'none';
        // desnoods nog extra omlaag duwen
        badge.style.zIndex = '0';
      }
    } catch (e) {}
  }

  // meteen uitvoeren en daarna blijven herhalen (mocht hij terugkomen)
  disableForeignBadges();
  setInterval(disableForeignBadges, 1000);

})(window);
