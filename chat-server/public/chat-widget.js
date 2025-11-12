/* ===== PostAi Chat — Luxury / Trust variant ===== */
(function(){
  const SERVER = window.BMS_CHAT_SERVER || '';
  if(!SERVER) return;

  /* Personalisatie */
  const AGENT_NAME   = 'Sanne van PostAi';
  const AGENT_INITS  = 'S';
  const TEASER_TEXT  = 'Hulp nodig? Sanne helpt je graag.';
  const WELCOME_LINES = [
    'Hi! Ik ben Sanne. Waar kan ik je vandaag mee helpen?',
    'Wil je snel weten wanneer je het best post? Deel je vraag gerust.',
    'Goed om te weten: we bewaren niets zonder jouw actie.'
  ];
  const SLA_TEXT     = 'Meestal reageren we binnen enkele minuten.';
  const PRIVACY_TEXT = '🔒 Privacy-vriendelijk · <a href="?page=privacy" target="_blank" rel="noopener">Privacy</a>';

  /* ===== Helpers */
  const qs = s => document.querySelector(s);
  const el = (t, attrs={}, html='')=>{
    const n = document.createElement(t);
    Object.entries(attrs).forEach(([k,v])=> n.setAttribute(k, v));
    if(html) n.innerHTML = html;
    return n;
  };
  const escapeHtml = s => String(s).replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));

  /* ===== Launcher */
  const launch = el('button', { id:'bms-chat-launcher', 'aria-label':'Open chat' }, `
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3c5.523 0 10 3.806 10 8.5S17.523 20 12 20a12.8 12.8 0 0 1-3.73-.55L3 21l1.73-4.33A8.63 8.63 0 0 1 2 11.5C2 6.806 6.477 3 12 3Z" stroke="currentColor" stroke-width="1.6"/>
    </svg>
  `);
  document.body.appendChild(launch);

  /* Teaser */
  const teaser = el('div', { id:'bms-chat-teaser' }, TEASER_TEXT);
  document.body.appendChild(teaser);
  const teaserKey='bmsChatTeaseShown';
  if(!localStorage.getItem(teaserKey)){
    setTimeout(()=> teaser.classList.add('show'), 600);
    setTimeout(()=>{ teaser.classList.remove('show'); localStorage.setItem(teaserKey,'1'); }, 5200);
  }

  /* ===== Window */
  const chat = el('div', { id:'bms-chat', role:'dialog', 'aria-label':'PostAi chat' }, `
    <div class="hdr">
      <div class="id">
        <div class="avatar">${AGENT_INITS}</div>
        <div>
          <div class="ttl">${AGENT_NAME}</div>
          <div class="sub">• online</div>
        </div>
      </div>
      <button class="close" aria-label="Sluiten">✕</button>
    </div>
    <div id="bms-trust">${SLA_TEXT}<br>${PRIVACY_TEXT}</div>
    <div class="body" id="bms-body"></div>
    <div class="inp">
      <input type="text" id="bms-input" placeholder="Typ je bericht…" />
      <button class="send" id="bms-send">Verstuur</button>
    </div>
  `);
  document.body.appendChild(chat);

  const body   = qs('#bms-body');
  const input  = qs('#bms-input');
  const sendBtn= qs('#bms-send');

  function openChat(){ chat.style.display='block'; teaser.classList.remove('show'); setTimeout(()=>input.focus(),0); }
  function closeChat(){ chat.style.display='none'; }
  launch.addEventListener('click', openChat);
  chat.querySelector('.close').addEventListener('click', closeChat);

  /* ===== History */
  const histKey='bmsChatHistory';
  function append(role,text){
    const row = el('div',{ class:`bms-msg ${role}` });
    row.appendChild(el('div',{ class:'bubble' }, escapeHtml(text)));
    body.appendChild(row); body.scrollTop = body.scrollHeight;
  }
  function save(role,text){
    const h = JSON.parse(localStorage.getItem(histKey)||'[]'); 
    h.push({role,text}); localStorage.setItem(histKey, JSON.stringify(h.slice(-40)));
  }
  try{ (JSON.parse(localStorage.getItem(histKey)||'[]')).forEach(m=>append(m.role,m.text)); }catch(_){}

  /* Welcome (persoonlijk) – alleen 1e keer */
  if(!localStorage.getItem('bmsChatWelcomed')){
    append('bot', WELCOME_LINES[0]); save('bot', WELCOME_LINES[0]);
    setTimeout(()=>{ append('bot', WELCOME_LINES[1]); save('bot', WELCOME_LINES[1]); }, 400);
    setTimeout(()=>{ append('bot', WELCOME_LINES[2]); save('bot', WELCOME_LINES[2]); }, 800);
    localStorage.setItem('bmsChatWelcomed','1');
  }

  /* ===== Send */
  async function send(){
    const txt = (input.value||'').trim();
    if(!txt) return;
    append('user', txt); save('user', txt);
    input.value=''; input.focus();
    append('bot','•••'); // typing

    try{
      const r = await fetch(`${SERVER}/api/chat`, {
        method:'POST', headers:{ 'Content-Type':'application/json' },
        body: JSON.stringify({ message: txt })
      });
      const data = await r.json();
      const bot = (data && (data.reply || data.message || data.text)) || 'Dankje! Ik kijk even met je mee.';
      body.lastChild.querySelector('.bubble').textContent = bot;
      save('bot', bot);
    }catch(e){
      body.lastChild.querySelector('.bubble').textContent = 'Oeps, een netwerkfout. Probeer het zo nog eens.';
    }
  }
  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', e=>{ if(e.key==='Enter') send(); });
})();
