(function (global) {
"use strict";

var SERVER = global.BMS_CHAT_SERVER || "";
var CSS_URL = global.BMS_CHAT_CSS_URL || "/chat-widget.css?v=1228";
var DEBUG = !!global.BMS_CHAT_DEBUG;

var PLAN = global.POSTAI_PLAN || "demo";
var IS_PRO = PLAN === "pro";

var PRO_URL =
global.BMS_PRO_URL ||
"https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2";

if (!SERVER) {
console.warn(
"[PostAi Chat] BMS_CHAT_SERVER ontbreekt – UI werkt, API-calls zijn nu een demo."
);
}

var DOC = global.document;

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

var launcher = DOC.createElement("div");
launcher.id = "bms-chat-launcher";
launcher.setAttribute("aria-label", "Open chat met Sanne");
launcher.textContent = "💬";
launcher.style.display = "block";

var chat = DOC.createElement("div");
chat.id = "bms-chat";
chat.setAttribute("aria-live", "polite");
chat.setAttribute("role", "dialog");
chat.setAttribute("aria-label", "PostAi TikTok coach");
chat.style.display = "none";

chat.innerHTML =
'<div class="hdr">' +
' <div class="avatar">S</div>' +
' <div class="titles">' +
' <div class="ttl">Sanne van PostAi</div>' +
' <div class="sub">online • TikTok coach</div>' +
" </div>" +
' <button class="close" id="bms-close" aria-label="Sluit chat">×</button>' +
"</div>" +
'<div id="bms-body"></div>' +
'<div class="bms-suggestions" id="bms-suggestions"></div>' +
'<div class="inp">' +
' <div class="inp-row">' +
' <input id="bms-input" type="text" placeholder="Typ je bericht..." autocomplete="off" />' +
' <button id="bms-send">Verstuur</button>' +
" </div>" +
' <div class="bms-usps">' +
' <div class="bms-usps-item">' +
' <span class="bms-usps-icon">✓</span>' +
" <span>Je data blijft privé</span>" +
" </div>" +
' <div class="bms-usps-item">' +
' <span class="bms-usps-icon">✓</span>' +
" <span>100% AVG-proof</span>" +
" </div>" +
" </div>" +
"</div>";

var teaser = DOC.createElement("div");
teaser.id = "bms-chat-teaser";
teaser.textContent = "Vraag Sanne alles over tiktok 👋";

DOC.body.appendChild(launcher);
DOC.body.appendChild(chat);
DOC.body.appendChild(teaser);

var STORAGE_KEY = "postai_profile_v1";
var STATE_KEY = "postai_returning_v1";
var START_MODE_KEY = "postai_start_mode_v1";

var closeBtn = DOC.getElementById("bms-close");
var bodyEl = DOC.getElementById("bms-body");
var inputEl = DOC.getElementById("bms-input");
var sendBtn = DOC.getElementById("bms-send");
var suggestionsEl = DOC.getElementById("bms-suggestions");

var profile = loadProfile();
var startMode = loadStartMode();
var onboardingStep = 0; // onboarding uitgezet
var messageIdCounter = 1;
var lastBotType = null;
var history = [];
var lastImageUrl = null;

function loadProfile() {
try {
var raw = global.localStorage.getItem(STORAGE_KEY);
if (!raw) return null;
var obj = JSON.parse(raw);
if (!obj || typeof obj !== "object") return null;
if (typeof obj.product !== "string") return null;
if (typeof obj.audience !== "string") obj.audience = "";
if (typeof obj.goal !== "string") obj.goal = "";
if (!obj.level) obj.level = "starter";
return obj;
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

function loadStartMode() {
try {
var v = global.localStorage.getItem(START_MODE_KEY);
if (v === "demo" || v === "upload") return v;
return null;
} catch (e) {
return null;
}
}

function setStartMode(mode) {
startMode = mode;
try {
global.localStorage.setItem(START_MODE_KEY, mode);
} catch (e) {}
}

function openChat() {
chat.style.display = "flex";
teaser.classList.remove("show");
try {
if (!global.localStorage.getItem(STATE_KEY)) {
global.localStorage.setItem(STATE_KEY, "1");
}
} catch (e) {}

if (!bodyEl.childElementCount) {
startConversation();
}
setTimeout(function () {
scrollToBottom();
try {
inputEl.focus();
} catch (e) {}
}, 50);
}

function closeChat() {
chat.style.display = "none";
try {
launcher.focus();
} catch (e) {}
}

function scrollToBottom() {
bodyEl.scrollTop = bodyEl.scrollHeight;
}

function formatBotText(text) {
if (!text) return "";

var safe = String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

// dikgedrukte tekst tussen dubbele sterretjes
safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

// headings zoals Hook:, Body:, CTA:
safe = safe.replace(
    /^(Hook|Body|CTA|Advies\s*\d?|Tip\s*\d?|Script\s*\d?)\s*:/gim,
    '<span class="bms-heading">$1:</span>'
);

// urls klikbaar maken
var urlRegex = new RegExp("(https?:\\/\\/[^\\s<]+)", "g");
safe = safe.replace(
    urlRegex,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
);

var lines = safe.split(/\r?\n/);
var out = [];
var inList = false;

lines.forEach(function (line) {
    if (/^\s*[-•]\s+/.test(line)) {
        if (!inList) {
            out.push('<ul class="bms-list">');
            inList = true;
        }
        out.push("<li>" + line.replace(/^\s*[-•]\s+/, "") + "</li>");
    } else {
        if (inList) {
            out.push("</ul>");
            inList = false;
        }
        if (line.trim() === "") {
            out.push("<br>");
        } else {
            out.push("<p>" + line + "</p>");
        }
    }
});

if (inList) out.push("</ul>");

return out.join("");


}

function addMessage(text, sender, opts) {
if (sender === void 0) sender = "bot";
opts = opts || {};

var msgId = messageIdCounter++;

var wrapper = DOC.createElement("div");
wrapper.className = "bms-msg " + (sender === "user" ? "user" : "bot");

var bubble = DOC.createElement("div");
bubble.className = "bubble";

if (sender === "bot") {
bubble.innerHTML = formatBotText(text);
} else {
bubble.textContent = text;
}

if (sender === "bot" && typeof text === "string" && text.length > 600) {
var btnMore = DOC.createElement("button");
btnMore.type = "button";
btnMore.className = "bms-more";
btnMore.textContent = "Toon volledig antwoord";
btnMore.addEventListener("click", function () {
var expanded = bubble.classList.toggle("expanded");
btnMore.textContent = expanded
? "Toon minder"
: "Toon volledig antwoord";
});
bubble.appendChild(btnMore);
}

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

if (typeof text === "string") {
if (sender === "user") {
history.push({ role: "user", content: text });
} else if (sender === "bot") {
history.push({ role: "assistant", content: text });
}
if (history.length > 20) {
history = history.slice(-20);
}
}
}

function setSuggestions(list) {
suggestionsEl.innerHTML = "";
if (!list || !list.length) return;

var limited = list.slice(0, 2);

limited.forEach(function (label) {
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
if (!SERVER) return;
try {
fetch(SERVER + "/api/feedback", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({
messageId: msgId,
rating: type,
profile: profile || null,
}),
}).catch(function (e) {
if (DEBUG) console.log("Feedback error", e);
});
} catch (e) {
if (DEBUG) console.log("Feedback exception", e);
}
}

function startConversation() {
if (!profile) {
addMessage(
"Hi! Ik ben Sanne. Ik help je met je eerste TikTok ideeën.\nWat verkoop je?",
"bot",
{ feedback: false }
);
setSuggestions([]);
return;
}

if (!profile) {
addMessage(
"Hi! Ik ben Sanne, je TikTok coach in PostAi. Ik kan je helpen met scripts, hooks en TikTok plannen voor jouw product.",
"bot",
{ feedback: false }
);
setSuggestions([
"Maak een 7 dagen TikTok plan",
"Schrijf 3 complete TikTok scripts"
]);
} else {
var audText =
profile.audience && profile.audience.trim()
? profile.audience
: "je doelgroep";
var goalText =
profile.goal && profile.goal.trim()
? profile.goal
: "beter scoren met TikTok";

addMessage(
'Hi! Goed je weer te zien 👋 Je verkoopt "' +
profile.product +
'" aan ' +
audText +
" en je doel is: " +
goalText +
".\nWil je dat ik je eerste 7 TikTok video ideeën maak of ergens anders mee begin?",
"bot"
);
setSuggestions(getDefaultSuggestions(profile));
}
}

function getDefaultSuggestions(profileObj) {
var prod =
profileObj && profileObj.product ? profileObj.product : "mijn product";
var aud =
profileObj && profileObj.audience
? profileObj.audience
: "mijn doelgroep";
var goal =
profileObj && profileObj.goal ? profileObj.goal.toLowerCase() : "";

var goalPhrase;
if (goal.indexOf("sale") !== -1 || goal.indexOf("omzet") !== -1) {
goalPhrase = "meer sales uit TikTok";
} else if (goal.indexOf("bereik") !== -1) {
goalPhrase = "meer bereik op TikTok";
} else if (goal.indexOf("volger") !== -1) {
goalPhrase = "meer volgers op TikTok";
} else {
goalPhrase = "betere TikTok content";
}

return [
"Maak een 7 dagen TikTok plan met 1 video per dag voor " +
prod +
" voor " +
aud,
"Schrijf 3 complete TikTok scripts met hook, tekst en call to action voor " +
prod,
"Geef 5 hook ideeën die " +
goalPhrase +
" opleveren voor " +
prod,
"Optimaliseer mijn TikTok profielnaam en bio voor " +
prod +
" voor " +
aud +
" [PRO]",
"Laat zien hoe ik bestaande content kan hergebruiken op TikTok voor " +
prod +
" [PRO]",
];
}

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

function guessTypeFromMessage(text) {
var t = text.toLowerCase();

if (t.indexOf("script") !== -1) return "scripts";
if (t.indexOf("hook") !== -1) return "hooks";
if (
t.indexOf("7 dagen") !== -1 ||
t.indexOf("7-daags") !== -1 ||
t.indexOf("7 dagen plan") !== -1
)
return "7day_plan";
if (
t.indexOf("weekplan") !== -1 ||
t.indexOf("week planning") !== -1 ||
t.indexOf("contentkalender") !== -1 ||
t.indexOf("content kalender") !== -1 ||
t.indexOf("planning") !== -1 ||
t.indexOf("schema") !== -1
)
return "weekplan";
if (
t.indexOf("account") !== -1 ||
t.indexOf("profiel") !== -1 ||
t.indexOf("bio") !== -1 ||
t.indexOf("omschrijving") !== -1
)
return "profile_opt";
if (
t.indexOf("hergebruik") !== -1 ||
t.indexOf("bestaande content") !== -1 ||
t.indexOf("recycle") !== -1
)
return "content_reuse";
if (
t.indexOf("gepost") !== -1 ||
t.indexOf("views") !== -1 ||
t.indexOf("likes") !== -1 ||
t.indexOf("analyse") !== -1 ||
t.indexOf("analyseer") !== -1
)
return "analysis";

return null;
}

function guessModeFromSuggestion(label) {
var t = label.toLowerCase();
if (t.indexOf("maak het korter") !== -1) return "shorten";
if (t.indexOf("maak het concreter") !== -1) return "refine";
if (
t.indexOf("maak 3 variaties") !== -1 ||
t.indexOf("maak drie variaties") !== -1
)
return "variations";
if (t.indexOf("caption") !== -1) return "captions";
if (
t.indexOf("check mijn tiktok account") !== -1 ||
t.indexOf("verbeterpunten") !== -1
)
return "profile_opt";
if (t.indexOf("7 dagen") !== -1) return "7day_plan";
if (t.indexOf("script") !== -1) return "scripts";
if (t.indexOf("bio") !== -1 || t.indexOf("profielnaam") !== -1)
return "profile_opt";
if (
t.indexOf("hergebruiken") !== -1 ||
t.indexOf("content kan hergebruiken") !== -1
)
return "content_reuse";

return guessTypeFromMessage(label);
}

function getFollowUpSuggestions(type, profileObj) {
var base = [
"Maak het korter",
"Maak het concreter voor mijn doelgroep",
"Maak 3 variaties",
];
if (!type) return base;

var prod = (profileObj && profileObj.product) || "mijn product";

if (type === "hooks") {
return [
"Maak 5 extra hooks",
"Schrijf een script voor 1 van deze hooks",
base[0],
base[2],
];
}

if (type === "weekplan" || type === "7day_plan") {
return [
"Maak nu 3 hooks per dag voor " + prod,
"Schrijf caption ideeën bij dit plan",
"Maak 3 complete scripts van 1 dag uit dit plan [PRO]",
];
}

if (type === "scripts") {
return [
"Maak 3 nieuwe scripts in een andere stijl",
"Maak korte versies van deze scripts",
"Schrijf er passende captions bij",
];
}

if (type === "profile_opt") {
return [
"Geef 3 nieuwe bio varianten [PRO]",
"Geef 3 ideeën voor profielfoto en highlights [PRO]",
base[0],
base[2],
];
}

if (type === "content_reuse") {
return [
"Maak een plan om 5 bestaande posts om te zetten naar TikTok [PRO]",
"Maak 3 voice over ideeën voor bestaande beelden",
base[0],
base[2],
];
}

if (type === "analysis") {
return [
"Geef 3 acties voor mijn volgende video",
"Schrijf een verbeterde hook op basis van deze analyse [PRO]",
base[0],
base[1],
];
}

return base;
}

function sendToPostAi(userMessage, typeHint) {
var inferred = typeHint || guessTypeFromMessage(userMessage);
var mode = inferred || "default";

var payload = {
message: userMessage,
profile: profile || null,
history: history.slice(-10),
meta: {
mode: mode,
imageUrl: lastImageUrl || null,
},
};

if (!SERVER) {
return new Promise(function (resolve) {
setTimeout(function () {
resolve({
text:
"DEMO: ik ben nog niet gekoppeld aan een server. Vraag je developer om BMS_CHAT_SERVER in te stellen.",
type: inferred || guessTypeFromMessage(userMessage),
});
}, 600);
});
}

if (DEBUG) {
console.log("[PostAi Chat] Payload naar /api/chat:", payload);
}

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
if (DEBUG) {
console.log("[PostAi Chat] Response van /api/chat:", data);
}
return {
text:
data.reply ||
"Ik kan even geen antwoord geven. Probeer het zo nog een keer.",
type: data.type || inferred || guessTypeFromMessage(userMessage),
};
})
.catch(function (err) {
console.error("[PostAi Chat] Fout bij /api/chat:", err);
return {
text:
"Er gaat iets mis met de verbinding. Probeer het zo nog een keer.",
type: inferred || guessTypeFromMessage(userMessage),
};
});
}

function isProLabel(label) {
return label.indexOf("[PRO]") !== -1;
}

function handleStartChoice(mode) {
setStartMode(mode);

try {
if (typeof global.postaiOnStartChoice === "function") {
global.postaiOnStartChoice(mode);
} else if (DEBUG) {
console.log("[PostAi Chat] start choice:", mode);
}
} catch (e) {}

if (mode === "demo") {
addMessage(
"Top, ik zet je nu op de DEMO-versie. Je kunt altijd later nog eigen data uploaden.",
"bot",
{ feedback: false }
);
} else {
addMessage(
"Top, dan help ik je met je eigen data. Je kunt je bestand zo uploaden in de tool.",
"bot",
{ feedback: false }
);
}

setTimeout(function () {
closeChat();
}, 1200);
}

function handleSuggestion(label) {

if (label === "Upgrade naar PRO") {
global.open(PRO_URL, "_blank");
return;
}

if (isProLabel(label) && !IS_PRO) {
addMessage(
"Deze functie hoort bij PRO. Klik op de knop hieronder om PRO te openen.",
"bot",
{ feedback: false }
);
setSuggestions(["Upgrade naar PRO"]);
return;
}

inputEl.value = label.replace(" [PRO]", "");
var typeHint = guessModeFromSuggestion(label);
handleSend(typeHint);
}

function handleSend(typeHint) {
var text = inputEl.value.trim();
if (!text) return;

addMessage(text, "user");
inputEl.value = "";
setSuggestions([]);

var typingId = showTyping();
var hint = typeHint || guessTypeFromMessage(text);

sendToPostAi(text, hint)
.then(function (reply) {
hideTyping(typingId);
addMessage(reply.text, "bot");
lastBotType = reply.type || hint || null;
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

function showTeaserOnce() {
try {
if (global.localStorage.getItem(STATE_KEY)) return;
} catch (e) {}
setTimeout(function () {
teaser.classList.add("show");
}, 2500);
}

function isEnabledPage() {
try {
if (global.BMS_CHAT_ENABLED === "off") return false;
if (global.BMS_CHAT_ENABLED === "on") return true;

// als er niets gezet is: standaard aan
return true;


} catch (e) {
return true;
}
}

function setupAutoOpen() {
try {
var hasOpened = !!global.localStorage.getItem(STATE_KEY);
if (!isEnabledPage()) return;
if (hasOpened) return;

setTimeout(function () {
openChat();
}, 2000);
} catch (e) {}
}

launcher.addEventListener("click", openChat);
closeBtn.addEventListener("click", closeChat);
sendBtn.addEventListener("click", function () {
handleSend();
});

inputEl.addEventListener("keydown", function (e) {
if (e.key === "Enter" && !e.shiftKey) {
e.preventDefault();
handleSend();
}
});

DOC.addEventListener("keydown", function (e) {
if (e.key === "Escape") {
if (chat.style.display === "flex" || chat.style.display === "") {
closeChat();
}
}
});

if (!isEnabledPage()) {
launcher.style.display = "none";
chat.style.display = "none";
teaser.style.display = "none";
} else {
showTeaserOnce();
setupAutoOpen();
}
})(window);
