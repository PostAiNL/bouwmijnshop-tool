/* ===== PostAi Chat 2.0 — JS (absolute overlay) ===== */
(function (global) {
  "use strict";

  // ---------- Config ----------
  var SERVER = global.BMS_CHAT_SERVER || "";
  var CSS_URL = global.BMS_CHAT_CSS_URL || "/chat-widget.css?v=6";

  if (!SERVER) {
    console.warn(
      "[PostAi Chat] BMS_CHAT_SERVER ontbreekt – UI werkt, API-calls zijn nu een demo."
    );
  }

  // ---------- Safe document ----------
  var DOC = (function () {
    try {
      return global.top.document;
    } catch (e) {
      return global.document;
    }
  })();

  // ---------- Idempotent ----------
  if (
    DOC.getElementById("bms-chat-launcher") ||
    DOC.getElementById("bms-chat")
  ) {
    return;
  }

  // ---------- CSS injecteren ----------
  (function ensureCss() {
    var head = DOC.head || DOC.getElementsByTagName("head")[0];
    if (!head) return;
    var existing = DOC.querySelector('link[data-bms-chat-css="1"]');
    if (existing) return;

    var link = DOC.createElement("link");
    link.rel = "stylesheet";
    link.href = CSS_URL;
    link.setAttribute("data-bms-chat-css", "1");
    head.appendChild(link);
  })();

  // ---------- DOM opbouwen ----------

  var launcher = DOC.createElement("div");
  launcher.id = "bms-chat-launcher";
  launcher.setAttribute("aria-label", "Open chat met Sanne");
  launcher.textContent = "💬";

  var chat = DOC.createElement("div");
  chat.id = "bms-chat";
  chat.setAttribute("aria-live", "polite");
  chat.setAttribute("role", "dialog");
  chat.setAttribute("aria-label", "PostAi TikTok coach");

  chat.innerHTML =
    '<div class="hdr">' +
    '  <div class="avatar">S</div>' +
    '  <div class="titles">' +
    '    <div class="ttl">Sanne van PostAi</div>' +
    '    <div class="sub">online • TikTok coach</div>' +
    "  </div>" +
    '  <button class="close" id="bms-close" aria-label="Sluit chat">&times;</button>' +
    "</div>" +
    '<div id="bms-body"></div>' +
    '<div class="bms-suggestions" id="bms-suggestions"></div>' +
    '<div class="inp">' +
    '  <input id="bms-input" type="text" placeholder="Typ je bericht..." autocomplete="off" />' +
    '  <input type="file" id="bms-upload" accept="image/*" style="display:none" />' +
    '  <button id="bms-upload-btn" title="Upload productfoto">📷</button>' +
    '  <button id="bms-send">Verstuur</button>' +
    "</div>";

  var teaser = DOC.createElement("div");
  teaser.id = "bms-chat-teaser";
  teaser.textContent = "Vraag Sanne om TikTok-advies 👋";

  DOC.body.appendChild(launcher);
  DOC.body.appendChild(chat);
  DOC.body.appendChild(teaser);

  // ---------- State ----------
  var STORAGE_KEY = "postai_profile_v1";
  var STATE_KEY = "postai_returning_v1";

  var closeBtn = DOC.getElementById("bms-close");
  var bodyEl = DOC.getElementById("bms-body");
  var inputEl = DOC.getElementById("bms-input");
  var sendBtn = DOC.getElementById("bms-send");
  var suggestionsEl = DOC.getElementById("bms-suggestions");
  var uploadInput = DOC.getElementById("bms-upload");
  var uploadBtn = DOC.getElementById("bms-upload-btn");

  var profile = loadProfile();
  var onboardingStep = profile ? 0 : 1; // 0 = klaar
  var messageIdCounter = 1;
  var lastBotType = null;

  function loadProfile() {
    try {
      var raw = global.localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function saveProfile(newProfile) {
    profile = newProfile;
    try {
      global.localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    } catch (e) {}
  }

  // ---------- UI helpers ----------

  function openChat() {
    chat.style.display = "block";
    teaser.classList.remove("show");
    try {
      if (!global.localStorage.getItem(STATE_KEY)) {
        global.localStorage.setItem(STATE_KEY, "1");
      }
    } catch (e) {}

    if (!bodyEl.childElementCount) {
      startConversation();
    }
    setTimeout(scrollToBottom, 50);
  }

  function closeChat() {
    chat.style.display = "none";
  }

  function scrollToBottom() {
    bodyEl.scrollTop = bodyEl.scrollHeight;
  }

  function addMessage(text, sender, opts) {
    if (sender === void 0) sender = "bot";
    opts = opts || {};

    var msgId = messageIdCounter++;

    var wrapper = DOC.createElement("div");
    wrapper.className = "bms-msg " + (sender === "user" ? "user" : "bot");

    var bubble = DOC.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    wrapper.appendChild(bubble);

    var time = DOC.createElement("div");
    time.className = "time";
    try {
      time.textContent = new Date().toLocaleTimeString("nl-NL", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (e) {
      time.textContent = "";
    }
    wrapper.appendChild(time);

    // Feedback alleen bij echte AI-answers (geen onboarding, geen korte regels)
    var shouldFeedback =
      sender === "bot" &&
      opts.feedback !== false &&
      onboardingStep === 0 &&
      typeof text === "string" &&
      text.length > 80;

    if (shouldFeedback) {
      var fb = DOC.createElement("div");
      fb.className = "bms-feedback";
      var label = DOC.createElement("span");
      label.textContent = "Was dit nuttig?";
      fb.appendChild(label);

      var btnUp = DOC.createElement("button");
      btnUp.type = "button";
      btnUp.textContent = "👍";
      btnUp.addEventListener("click", function () {
        handleFeedback(msgId, "up");
      });
      fb.appendChild(btnUp);

      var btnDown = DOC.createElement("button");
      btnDown.type = "button";
      btnDown.textContent = "👎";
      btnDown.addEventListener("click", function () {
        handleFeedback(msgId, "down");
      });
      fb.appendChild(btnDown);

      bubble.appendChild(fb);
    }

    bodyEl.appendChild(wrapper);
    scrollToBottom();
  }

  function setSuggestions(list) {
    suggestionsEl.innerHTML = "";
    if (!list || !list.length) return;
    list.forEach(function (label) {
      var btn = DOC.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.addEventListener("click", function () {
        handleSuggestion(label);
      });
      suggestionsEl.appendChild(btn);
    });
  }

  function handleFeedback(msgId, type) {
    // later naar backend sturen indien gewenst
    // console.log("Feedback:", msgId, type);
  }

  // ---------- Onboarding ----------

  function startConversation() {
    if (!profile) {
      addMessage(
        "Hi! Ik ben Sanne, je TikTok coach in PostAi. Ik stel je 3 snelle vragen zodat ik je beter kan helpen. 👇",
        "bot",
        { feedback: false }
      );
      setTimeout(function () {
        askOnboardingQuestion(1);
      }, 600);
    } else {
      addMessage(
        'Hi! Goed je weer te zien 👋 Ik help je met TikTok voor je product "' +
          profile.product +
          '". Waar wil je vandaag aan werken?',
        "bot"
      );
      setSuggestions(getDefaultSuggestions(profile));
    }
  }

  function askOnboardingQuestion(step) {
    onboardingStep = step;
    if (step === 1) {
      addMessage(
        "1/3 • Wat verkoop je? Beschrijf je product in één zin.",
        "bot",
        { feedback: false }
      );
    } else if (step === 2) {
      addMessage(
        "2/3 • Voor wie is je product bedoeld? (bijv. moeders, studenten, sporters)",
        "bot",
        { feedback: false }
      );
    } else if (step === 3) {
      addMessage(
        "3/3 • Wat is je grootste TikTok-doel nu? (meer bereik, meer sales, meer volgers)",
        "bot",
        { feedback: false }
      );
    }
  }

  function processOnboardingAnswer(text) {
    if (onboardingStep === 1) {
      profile = {
        product: text,
        audience: "",
        goal: "",
        level: "starter",
      };
      saveProfile(profile);
      askOnboardingQuestion(2);
    } else if (onboardingStep === 2) {
      profile.audience = text;
      saveProfile(profile);
      askOnboardingQuestion(3);
    } else if (onboardingStep === 3) {
      profile.goal = text;
      saveProfile(profile);
      onboardingStep = 0;
      addMessage(
        "Top, dankjewel! 🎉 Ik gebruik deze info om betere TikTok-ideeën te geven. Waar wil je mee beginnen?",
        "bot"
      );
      setSuggestions(getDefaultSuggestions(profile));
    }
  }

  function getDefaultSuggestions(profileObj) {
    var prod = (profileObj && profileObj.product) || "mijn product";
    return [
      "Maak een TikTok-weekplan voor " + prod,
      "Maak 3 hooks voor " + prod,
      "Wat is de beste posttijd voor mijn doelgroep?",
      "Check mijn TikTok-account",
    ];
  }

  // ---------- Typing indicator ----------

  function showTyping() {
    var id = "typing-" + Date.now();
    var wrapper = DOC.createElement("div");
    wrapper.className = "bms-msg bot";
    wrapper.id = id;

    var bubble = DOC.createElement("div");
    bubble.className = "bubble typing-dots";
    bubble.textContent = " ";
    wrapper.appendChild(bubble);

    bodyEl.appendChild(wrapper);
    scrollToBottom();
    return id;
  }

  function hideTyping(id) {
    var el = DOC.getElementById(id);
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  // ---------- AI-koppeling ----------

  function guessTypeFromMessage(text) {
    var t = text.toLowerCase();
    if (t.indexOf("hook") !== -1) return "hooks";
    if (t.indexOf("weekplan") !== -1 || t.indexOf("week planning") !== -1)
      return "weekplan";
    return null;
  }

  function getFollowUpSuggestions(type, profileObj) {
    var base = [
      "Maak het korter",
      "Maak het concreter voor mijn doelgroep",
      "Maak 3 variaties",
    ];
    if (!type) return base;

    if (type === "hooks") {
      return [
        "Maak 5 extra hooks",
        "Schrijf een script voor 1 van deze hooks",
        base[0],
        base[2],
      ];
    }

    if (type === "weekplan") {
      var prod = (profileObj && profileObj.product) || "mijn product";
      return [
        "Maak nu 3 hooks per dag voor " + prod,
        "Schrijf caption-ideeën bij dit weekplan",
        base[0],
        base[2],
      ];
    }
    return base;
  }

function sendToPostAi(userMessage) {
  // bouw payload voor je backend
  var payload = {
    message: userMessage,
    profile: profile || null,
    history: [],              // later kun je hier echte history in stoppen
    meta: { mode: "default" }
  };

  // als er geen SERVER is ingesteld → val terug op demo
  if (!SERVER) {
    return new Promise(function (resolve) {
      setTimeout(function () {
        resolve({
          text:
            "DEMO: ik ben nog niet gekoppeld aan een server. Vraag je developer om BMS_CHAT_SERVER in te stellen.",
          type: guessTypeFromMessage(userMessage),
        });
      }, 600);
    });
  }

  // echte call naar jouw Node-server
  return fetch(SERVER + "/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(function (res) {
      if (!res.ok) {
        throw new Error("Server error " + res.status);
      }
      return res.json();
    })
    .then(function (data) {
      return {
        text:
          data.reply ||
          "Ik kan even geen antwoord geven. Probeer het zo nog een keer.",
        type: data.type || guessTypeFromMessage(userMessage),
      };
    })
    .catch(function (err) {
      console.error("[PostAi Chat] Fout bij /api/chat:", err);
      return {
        text:
          "Er gaat iets mis met de verbinding. Probeer het zo nog een keer.",
        type: guessTypeFromMessage(userMessage),
      };
    });
}

  // ---------- Input & send ----------

  function handleSuggestion(label) {
    inputEl.value = label;
    handleSend();
  }

  function handleSend() {
    var text = inputEl.value.trim();
    if (!text) return;

    addMessage(text, "user");
    inputEl.value = "";
    setSuggestions([]);

    if (onboardingStep > 0) {
      processOnboardingAnswer(text);
      return;
    }

    var typingId = showTyping();

    sendToPostAi(text)
      .then(function (reply) {
        hideTyping(typingId);
        addMessage(reply.text, "bot");
        lastBotType = reply.type || null;
        setSuggestions(getFollowUpSuggestions(lastBotType, profile));
      })
      .catch(function () {
        hideTyping(typingId);
        addMessage(
          "Hmm, er gaat iets mis met de verbinding. Probeer het zo nog een keer. 🙈",
          "bot",
          { feedback: false }
        );
      });
  }

  // ---------- File upload (productfoto) ----------

  uploadBtn.addEventListener("click", function () {
    uploadInput && uploadInput.click();
  });

  uploadInput.addEventListener("change", function (e) {
    var file = e.target.files && e.target.files[0];
    if (!file) return;

    addMessage(
      "📷 Productfoto toegevoegd. Ik gebruik deze om betere ideeën te geven.",
      "bot",
      { feedback: false }
    );

    // Koppelen met backend:
    // var formData = new FormData();
    // formData.append("image", file);
    // formData.append("profile", JSON.stringify(profile || {}));
    // fetch(SERVER + "/image", { method: "POST", body: formData });
  });

  // ---------- Teaser ----------

  function showTeaserOnce() {
    try {
      if (global.localStorage.getItem(STATE_KEY)) return;
    } catch (e) {}
    setTimeout(function () {
      teaser.classList.add("show");
    }, 2500);
  }

  // ---------- Event listeners ----------

  launcher.addEventListener("click", openChat);
  closeBtn.addEventListener("click", closeChat);
  sendBtn.addEventListener("click", handleSend);

  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  uploadBtn.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      uploadInput && uploadInput.click();
    }
  });

  // ---------- Init ----------
  showTeaserOnce();
})(window);
