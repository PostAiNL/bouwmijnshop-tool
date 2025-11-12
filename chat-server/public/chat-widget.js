/* ===== PostAi Chat 2.0 — luxe floating widget ===== */
(function(){
  const SERVER = window.BMS_CHAT_SERVER || "";
  if(!SERVER) return;

  // --- Veilig injecteren in top document
  const DOC = (()=>{try{return window.top.document;}catch{return document;}})();
  if(DOC.getElementById("bms-chat-launcher")) return;

  // --- CSS injectie
  if(!DOC.getElementById("bms-chat-css")){
    const link = DOC.createElement("link");
    link.id="bms-chat-css"; link.rel="stylesheet";
    link.href=SERVER+"/chat-widget.css";
    DOC.head.appendChild(link);
  }

  // --- Helpers
  const el=(t,a={},h="")=>{const n=DOC.createElement(t);Object.entries(a).forEach(([k,v])=>n.setAttribute(k,v));n.innerHTML=h;return n;};
  const qs=s=>DOC.querySelector(s);
  const escapeHtml=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

  // --- Launcher & teaser
  const launcher = el("button",{id:"bms-chat-launcher",ariaLabel:"Open chat"},
    `<svg viewBox="0 0 24 24" fill="none" width="24" height="24"><path d="M12 3c5.5 0 10 3.8 10 8.5S17.5 20 12 20a13 13 0 0 1-3.7-.5L3 21l1.7-4.3A8.6 8.6 0 0 1 2 11.5C2 6.8 6.5 3 12 3Z" stroke="currentColor" stroke-width="1.6"/></svg>`
  );
  const teaser = el("div",{id:"bms-chat-teaser"},"Hulp nodig? Sanne helpt je graag.");
  DOC.body.append(launcher,teaser);
  if(!localStorage.getItem("bmsChatTeaseShown")){
    setTimeout(()=>teaser.classList.add("show"),600);
    setTimeout(()=>{teaser.classList.remove("show");localStorage.setItem("bmsChatTeaseShown","1");},5200);
  }

  // --- Chatwindow
  const chat = el("div",{id:"bms-chat"},`
    <div class="hdr">
      <div class="avatar">S</div>
      <div><div class="ttl">Sanne van PostAi</div><div class="sub">• online</div></div>
      <button class="close">✕</button>
    </div>
    <div id="bms-body"></div>
    <div class="inp">
      <input id="bms-input" placeholder="Typ je bericht…" autocomplete="off"/>
      <button id="bms-send">Verstuur</button>
    </div>`);
  DOC.body.appendChild(chat);

  const body=qs("#bms-body"),input=qs("#bms-input"),sendBtn=qs("#bms-send"),closeBtn=chat.querySelector(".close");
  launcher.onclick=()=>{chat.style.display="block";input.focus();};
  closeBtn.onclick=()=>{chat.style.display="none";};

  // --- Storage
  const HKEY="bmsChatHistory";
  function append(role,text){
    const now=new Date().toLocaleTimeString("nl-NL",{hour:"2-digit",minute:"2-digit"});
    const row=el("div",{class:`bms-msg ${role}`},`
      <div class="bubble">${escapeHtml(text)} <button class="copy-btn" title="Kopieer">📋</button></div>
      <div class="time">${now}</div>`);
    body.appendChild(row);
    body.scrollTop=body.scrollHeight;
    // copy
    row.querySelector(".copy-btn").onclick=()=>{
      navigator.clipboard.writeText(text);
      row.querySelector(".copy-btn").textContent="✅";
      setTimeout(()=>row.querySelector(".copy-btn").textContent="📋",1500);
    };
  }
  function save(role,text){
    const h=JSON.parse(localStorage.getItem(HKEY)||"[]");h.push({role,text});
    localStorage.setItem(HKEY,JSON.stringify(h.slice(-60)));
  }
  try{JSON.parse(localStorage.getItem(HKEY)||"[]").forEach(m=>append(m.role,m.text));}catch{}

  // --- Welcome
  if(!localStorage.getItem("bmsChatWelcomed")){
    ["Hi! Ik ben Sanne. Waar kan ik je mee helpen?",
     "Tip: wil je beste posttijd? Zeg “beste tijd”.",
     "🔒 We bewaren niets zonder jouw actie."].forEach((w,i)=>setTimeout(()=>{append("bot",w);save("bot",w);},i*400));
    localStorage.setItem("bmsChatWelcomed","1");
  }

  // --- Typanimatie
  function showTyping(){append("bot","<span class='typing'>Sanne is aan het typen</span>");}
  function replaceTyping(text){
    const last=body.querySelector(".typing");
    if(last) last.parentElement.innerHTML=escapeHtml(text);
  }

  // --- Suggesties
  function addSuggestions(list){
    const wrap=el("div",{class:"bms-suggestions"});
    list.forEach(label=>{
      const btn=el("button",{},escapeHtml(label));
      btn.onclick=()=>{append("user",label);save("user",label);wrap.remove();sendToAI(label);};
      wrap.appendChild(btn);
    });
    body.appendChild(wrap);
    body.scrollTop=body.scrollHeight;
  }

  // --- Feedback
  function addFeedback(){
    const fb=el("div",{class:"bms-feedback"},`
      <span>Was dit nuttig?</span><button>👍</button><button>👎</button>`);
    fb.querySelectorAll("button").forEach(b=>b.onclick=()=>{
      fb.innerHTML="Bedankt voor je feedback 💜";
    });
    body.appendChild(fb);
  }

  // --- Restart
  function addRestart(){
    const btn=el("button",{class:"bms-restart"},"🔄 Nieuw gesprek");
    btn.onclick=()=>{
      localStorage.removeItem(HKEY);
      body.innerHTML="";
      append("bot","Nieuwe sessie gestart. Waar wil je mee beginnen?");
    };
    body.appendChild(btn);
  }

  // --- Verzenden
  sendBtn.onclick=()=>{sendToAI(input.value);};
  input.addEventListener("keydown",e=>{if(e.key==="Enter")sendToAI(input.value);});

  async function sendToAI(txt){
    txt=(txt||"").trim();
    if(!txt)return;
    append("user",txt);save("user",txt);
    input.value="";input.focus();
    showTyping();

    const mode=localStorage.getItem("postai_mode")||"DEMO";
    const bestHours=JSON.parse(localStorage.getItem("postai_best_hours")||"[]");
    const lastUpload=localStorage.getItem("postai_last_upload")||"";
    const topHashtags=JSON.parse(localStorage.getItem("postai_top_hashtags")||"[]");
    const history=JSON.parse(localStorage.getItem(HKEY)||"[]").slice(-6)
      .map(m=>({role:m.role==="bot"?"assistant":"user",text:m.text}));

    try{
      const res=await fetch(`${SERVER}/api/chat`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:txt,history,meta:{mode,best_hours:bestHours,last_upload:lastUpload,top_hashtags:topHashtags}})
      });
      const data=await res.json();
      const reply=(data&&data.reply)||"Dankje! Ik kijk even met je mee.";
      replaceTyping(reply);save("bot",reply);
      addSuggestions(["Beste posttijd","Analyseer mijn upload","Geef hooks","Toon weekplan"]);
      addFeedback();
      addRestart();
    }catch(e){
      replaceTyping("⚠️ Netwerkfout. Probeer het zo nog eens.");
    }
  }

})();
