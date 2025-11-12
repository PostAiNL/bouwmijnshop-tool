/* ===== PostAi Chat — AI-upgrade: stuurt context + history mee ===== */
(function () {
  const SERVER = window.BMS_CHAT_SERVER || '';
  if (!SERVER) return;

  /* Avoid double inject */
  try {
    if (window.top.document.getElementById('bms-chat-launcher')) return;
  } catch (_) {
    if (document.getElementById('bms-chat-launcher')) return;
  }

  /* ---- Work in TOP document ---- */
  const DOC = (() => {
    try { return (window.top && window.top.document) ? window.top.document : document; }
    catch { return document; }
  })();

  /* ---- Inject fallback CSS ---- */
  (function injectCssOnce() {
    if (DOC.getElementById('bms-chat-css')) return;
    const link = DOC.createElement('link');
    link.id = 'bms-chat-css';
    link.rel = 'stylesheet';
    link.href = SERVER + '/chat-widget.css';
    DOC.head.appendChild(link);

    const style = DOC.createElement('style');
    style.textContent = `
      #bms-chat-launcher{position:fixed;right:16px;bottom:16px;z-index:999999;width:56px;height:56px;border-radius:50%;background:#111827;color:#fff;border:0;cursor:pointer;box-shadow:0 10px 24px rgba(0,0,0,.2)}
      #bms-chat{position:fixed;right:16px;bottom:84px;z-index:999999;display:none;width:340px;max-height:70vh;background:#fff;border:1px solid #e5e7eb;border-radius:16px;box-shadow:0 20px 48px rgba(0,0,0,.18);overflow:hidden;font-family:system-ui}
      #bms-body{padding:10px 12px;overflow:auto;max-height:44vh;font-size:14px}
      .bms-msg{margin:6px 0;display:flex}
      .bms-msg.user{justify-content:flex-end}
      .bms-msg .bubble{max-width:85%;padding:8px 10px;border-radius:12px;border:1px solid #e5e7eb;line-height:1.35}
      .bms-msg.user .bubble{background:#111827;color:#fff}
      .bms-msg.bot .bubble{background:#fff;color:#111827}
      #bms-input{flex:1;padding:10px;border:1px solid #e5e7eb;border-radius:10px}
      #bms-send{padding:10px 12px;background:#111827;color:#fff;border:0;border-radius:10px;font-weight:600;cursor:pointer}
      #bms-chat-teaser{position:fixed;right:84px;bottom:24px;z-index:999999;background:#111827;color:#fff;padding:8px 12px;border-radius:12px;opacity:0;transform:translateY(8px);transition:all .25s ease}
      #bms-chat-teaser.show{opacity:1;transform:translateY(0)}
      @media(max-width:480px){#bms-chat{right:12px;left:12px;width:auto}}
    `;
    DOC.head.appendChild(style);
  })();

  /* ---- Persona ---- */
  const AGENT_NAME = 'Sanne van PostAi';
  const AGENT_INITS = 'S';
  const TEASER_TEXT = 'Hulp nodig? Sanne helpt je graag.';
  const WELCOME = [
    'Hi! Ik ben Sanne. Waar kan ik je mee helpen?',
    'Tip: wil je beste posttijd? Zeg “beste tijd”.',
    '🔒 We bewaren niets zonder jouw actie.'
  ];

  /* Helpers */
  const qs = s => DOC.querySelector(s);
  const el = (t, attrs = {}, html = '') => {
    const n = DOC.createElement(t);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    n.innerHTML = html;
    return n;
  };
  const escapeHtml = s =>
    String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* Launcher + teaser */
  const launcher = el('button', { id: 'bms-chat-launcher' },
    `<svg viewBox="0 0 24 24" fill="none" width="24" height="24"><path d="M12 3c5.5 0 10 3.8 10 8.5S17.5 20 12 20a13 13 0 0 1-3.7-.5L3 21l1.7-4.3A8.6 8.6 0 0 1 2 11.5C2 6.8 6.5 3 12 3Z" stroke="currentColor" stroke-width="1.6"/></svg>`);
  const teaser = el('div', { id: 'bms-chat-teaser' }, TEASER_TEXT);
  DOC.body.append(launcher, teaser);
  if (!window.top.localStorage.getItem('bmsChatTeaseShown')) {
    setTimeout(() => teaser.classList.add('show'), 600);
    setTimeout(() => {
      teaser.classList.remove('show');
      window.top.localStorage.setItem('bmsChatTeaseShown', '1');
    }, 5200);
  }

  /* Chat window */
  const chat = el('div', { id: 'bms-chat' }, `
    <div class="hdr" style="display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid #eee;">
      <div class="avatar" style="width:28px;height:28px;border-radius:8px;background:#111827;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;">${AGENT_INITS}</div>
      <div><div class="ttl" style="font-weight:700;">${AGENT_NAME}</div><div style="font-size:12px;color:#10b981;">• online</div></div>
      <button class="close" style="margin-left:auto;border:0;background:transparent;font-size:16px;cursor:pointer;">✕</button>
    </div>
    <div id="bms-body"></div>
    <div class="inp" style="display:flex;gap:6px;padding:10px;border-top:1px solid #eee;">
      <input type="text" id="bms-input" placeholder="Typ je bericht…" autocomplete="off"/>
      <button id="bms-send">Verstuur</button>
    </div>`);
  DOC.body.appendChild(chat);

  const body = qs('#bms-body');
  const input = qs('#bms-input');
  const sendBtn = qs('#bms-send');
  const closeBtn = chat.querySelector('.close');

  launcher.onclick = () => { chat.style.display = 'block'; input.focus(); };
  closeBtn.onclick = () => { chat.style.display = 'none'; };

  /* History */
  const store = window.top.localStorage;
  const HKEY = 'bmsChatHistory';
  function append(role, text) {
    const row = el('div', { class: `bms-msg ${role}` });
    row.appendChild(el('div', { class: 'bubble' }, escapeHtml(text)));
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
  }
  function save(role, text) {
    const h = JSON.parse(store.getItem(HKEY) || '[]');
    h.push({ role, text });
    store.setItem(HKEY, JSON.stringify(h.slice(-60)));
  }
  try { JSON.parse(store.getItem(HKEY) || '[]').forEach(m => append(m.role, m.text)); } catch {}

  /* Welcome */
  if (!store.getItem('bmsChatWelcomed')) {
    WELCOME.forEach((w, i) => setTimeout(() => { append('bot', w); save('bot', w); }, i * 400));
    store.setItem('bmsChatWelcomed', '1');
  }

  /* Send to API (context + history) */
  async function send() {
    const txt = (input.value || '').trim();
    if (!txt) return;
    append('user', txt); save('user', txt);
    input.value = ''; input.focus();
    append('bot', '•••');

    // context uit localStorage
    const mode = window.top.localStorage.getItem('postai_mode') || 'DEMO';
    const bestHours = JSON.parse(window.top.localStorage.getItem('postai_best_hours') || '[]');
    const lastUpload = window.top.localStorage.getItem('postai_last_upload') || '';
    const topHashtags = JSON.parse(window.top.localStorage.getItem('postai_top_hashtags') || '[]');
    const history = JSON.parse(store.getItem(HKEY) || '[]').slice(-6).map(m => ({
      role: m.role === 'bot' ? 'assistant' : 'user', text: m.text
    }));

    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 20000);

    try {
      const res = await fetch(`${SERVER}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          message: txt,
          history,
          meta: { mode, best_hours: bestHours, last_upload: lastUpload, top_hashtags: topHashtags }
        })
      });
      clearTimeout(t);
      const data = await res.json();
      const reply = (data && (data.reply || data.message || data.text)) || 'Dankje! Ik kijk even met je mee.';
      body.lastChild.querySelector('.bubble').textContent = reply;
      save('bot', reply);
    } catch {
      clearTimeout(t);
      body.lastChild.querySelector('.bubble').textContent = 'Oeps, een netwerkfout. Probeer het zo nog eens.';
    }
  }

  sendBtn.onclick = send;
  input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
})();
