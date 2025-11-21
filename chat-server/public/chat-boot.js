/* postai chat bootloader (CSP-vriendelijk, geen inline) */
(function (w, d) {
  var s = d.currentScript;
  var server = s.getAttribute("data-server") || "";
  var cssUrl = s.getAttribute("data-css") || (server ? server + "/chat-widget.css" : "/chat-widget.css");
  if (!server) { console.error("[PostAi boot] data-server ontbreekt"); return; }

  // globals voor de widget
  w.BMS_CHAT_SERVER = server;
  w.BMS_CHAT_CSS_URL = cssUrl;

  // css toevoegen
  var link = d.createElement("link");
  link.rel = "stylesheet";
  link.href = cssUrl;
  link.id = "bms-chat-css";
  d.head.appendChild(link);

  // widget JS toevoegen (de volledige chat-widget.js die we net maakten)
  var js = d.createElement("script");
  js.src = server + "/chat-widget.js";
  js.defer = true;
  js.onload = function(){ console.log("[PostAi boot] widget geladen"); };
  js.onerror = function(){ console.error("[PostAi boot] widget laden mislukt"); };
  d.head.appendChild(js);
})(window, document);
