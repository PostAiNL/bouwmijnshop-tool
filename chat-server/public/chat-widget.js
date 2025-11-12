/* Minimal floating chat widget
   Uses window.BMS_CHAT_SERVER set by Streamlit.
   Saves small state in localStorage (teaser shown + simple history).
*/
(function(){
  const SERVER = window.BMS_CHAT_SERVER || '';
  if(!SERVER) return;

  // --- helpers
  const qs = s => document.querySelector(s);
  const el = (t, attrs={}, html='')=>{
    const n = document.createElement(t);
    Object.entries(attrs).forEach(([k,v])=> n.setAttribute(k, v));
    if(html) n.innerHTML = html;
    return n;
  };

  // --- launcher (bubble)
  const launch = el('button', { id:'bms-chat-launcher', 'aria-label':'Open chat' }, `
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3c5.523 0 10 3.806 10 8.5S17.523 20 12 20a12.8 12.8 0 0 1-3.73-.55L3 21l1.73-4.33A8.63 8.63 0 0 1 2 11.5C2 6.806 6.477 3 12 3Z" stroke="currentColor" stroke-width="1.6"/>
    </svg>
  `);
  document.body.appendChild(launch);

  // teaser
  const teaser = el('div', { id:'bms-chat-teaser' }, 'Hulp nodig? Chat met PostAi');
  document.body.appendChild(teaser);
  const teaserKey = 'bmsChatTeaseShown';
  const showTeaser = !localStorage.getItem(teaserKey);
  if(showTeaser){
    setTimeout(()=> teaser.classList.add('show'), 600);
    setTimeout(()=>{
      teaser.classList.remove('show');
      localStorage.setItem(teaserKey, '1');
    }, 5500);
  }

  // --- chat window
  const chat = el('div', { id:'bms-chat', role:'dialog', 'aria-label':'PostAi chat' }, `
    <div class="hdr">
      <div class="ttl">PostAi Chat<br><span class="sub">• online</span></div>
      <button class="close" aria-label="Sluiten">✕</button>
    </div>
    <div class="body" id="bms-body"></div>
    <div class="inp">
      <input type="text" id="bms-input" placeholder="Typ je bericht…" />
      <button class="send" id="bms-send">Verstuur</button>
    </div>
  `);
  document.body.appendChild(chat);

  const body = qs('#bms-body');
  const input = qs('#bms-input');
  const sendBtn = qs('#bms-send');

  function openChat(){
    chat.style.display = 'block';
    teaser.classList.remove('show');
    setTimeout(()=> input.focus(), 0);
  }
  function closeChat(){ chat.style.display = 'none'; }
  launch.addEventListener('click', openChat);
  chat.querySelector('.close').addEventListener('click', closeChat);

  // --- history (lightweight)
  const histKey = 'bmsChatHistory';
  try {
    const hist = JSON.parse(localStorage.getItem(histKey) || '[]');
    hist.forEach(msg => append(msg.role, msg.text));
  } catch(_) {}

  function save(role, text){
    const h = JSON.parse(localStorage.getItem(histKey) || '[]');
    h.push({role, text}); localStorage.setItem(histKey, JSON.stringify(h.slice(-40)));
  }

  function append(role, text){
    const row = el('div', { class:`bms-msg ${role}` });
    row.appendChild(el('div', { class:'bubble' }, escapeHtml(text)));
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
  }
  function escapeHtml(s){ return String(s).replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c])); }

  async function send(){
    const txt = (input.value || '').trim();
    if(!txt) return;
    append('user', txt); save('user', txt);
    input.value = ''; input.focus();

    append('bot', '•••'); // typing
    try{
      const r = await fetch(`${SERVER}/api/chat`, {
        method:'POST',
        headers:{ 'Content-Type':'application/json' },
        body: JSON.stringify({ message: txt })
      });
      const data = await r.json();
      const bot = (data && (data.reply || data.message || data.text)) || 'Sorry, er ging iets mis.';
      body.lastChild.querySelector('.bubble').textContent = bot;
      save('bot', bot);
    }catch(e){
      body.lastChild.querySelector('.bubble').textContent = 'Netwerkfout. Probeer later opnieuw.';
    }
  }
  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', e => { if(e.key === 'Enter') send(); });

  // Start met korte welkom
  if(!localStorage.getItem('bmsChatWelcomed')){
    append('bot', 'Hi! Stel me je vraag over je TikTok-data, ik denk mee. 😊');
    save('bot','Hi! Stel me je vraag over je TikTok-data, ik denk mee. 😊');
    localStorage.setItem('bmsChatWelcomed','1');
  }
})();
