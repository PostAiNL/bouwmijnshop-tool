/* ===== PostAi Chat — floating widget in TOP window (outside Streamlit iframe) ===== */
(function () {
  const SERVER = window.BMS_CHAT_SERVER || '';
  if (!SERVER) return;

  /* Avoid double-inject */
  try {
    if (window.top.document.getElementById('bms-chat-launcher')) return;
  } catch (_) {
    if (document.getElementById('bms-chat-launcher')) return;
  }

  /* ---- Work in TOP document so position:fixed pins to viewport ---- */
  const DOC = (function () {
    try {
      return (window.top && window.top.document) ? window.top.document : document;
    } catch (e) {
      return document;
    }
  })();

  /* Inject CSS once (served by your Render server) */
  (function injectCssOnce() {
    if (DOC.getElementById('bms-chat-css')) return;
    const link = DOC.createElement('link');
    link.id = 'bms-chat-css';
    link.rel = 'stylesheet';
    link.href = SERVER + '/chat-widget.css';
    DOC.head.appendChild(link);

    /* Minimal hard safety styles so it always floats even if CSS fails to load */
    const fallback = DOC.createElement('style');
    fallback.id = 'bms-chat-fallback';
    fallback.textContent = `
      #bms-chat-launcher{position:fixed;right:16px;bottom:16px;z-index:999999;border:0;width:56px;height:56px;border-radius:50%;background:#111827;color:#fff;box-shadow:0 10px 24px rgba(0,0,0,.18);cursor:pointer}
      #bms-chat{position:fixed;right:16px;bottom:84px;z-index:999999;display:none;width:340px;max-height:70vh;background:#fff;border:1px solid #e5e7eb;border-radius:16px;box-shadow:0 20px 48px rgba(0,0,0,.18);overflow:hidden;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto}
      #bms-chat .hdr{display:flex;gap:10px;align-items:center;padding:12px 14px;border-bottom:1px solid #eef2f7;background:#fff}
      #bms-chat .avatar{width:28px;height:28px;border-radius:8px;background:#111827;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800}
      #bms-chat .ttl{font-weight:700}
      #bms-chat .close{margin-left:auto;border:0;background:transparent;font-size:16px;cursor:pointer}
      #bms-trust{padding:6px 14px;font-size:12px;color:#475569;background:#fafafa;border-bottom:1px solid #f1f5f9}
      #bms-body{padding:10px 12px;overflow:auto;max-height:44vh;font-size:14px}
      .bms-msg{margin:6px 0;display:flex}
      .bms-msg.user{justify-content:flex-end}
      .bms-msg .bubble{max-width:85%;padding:8px 10px;border:1px solid #e5e7eb;border-radius:12px;white-space:pre-wrap;line-height:1.35}
      .bms-msg.user .bubble{background:#111827;color:#fff}
      .bms-msg.bot .bubble{background:#fff;color:#111827}
      #bms-chat .inp{display:flex;gap:6px;padding:10px;border-top:1px solid #eef2f7;background:#fff}
      #bms-input{flex:1;padding:10px 12px;border:1px solid #e5e7eb;border-radius:10px}
      #bms-send{padding:10px 12px;background:#111827;color:#fff;border:0;border-radius:10px;font-weight:700;cursor:pointer}
      #bms-chat-teaser{position:fixed;right:84px;bottom:24px;z-index:999999;background:#111827;color:#fff;padding:8px 12px;border-radius:12px;opacity:0;transform:translateY(8px);transition:all .25s ease;pointer-events:none}
      #bms-chat-teaser.show{opacity:1;transform:translateY(0)}
      @media (max-width:480px){
        #bms-chat{right:12px;left:12px;width:auto;bottom:88px;max-height:70vh}
        #bms-chat-launcher{right:12px;bottom:12px}
        #bms-chat-teaser{right:76px;bottom:20px}
      }
    `;
    DOC.head.appendChild(fallback);
  })();

  /* -------- Persona / tekstjes -------- */
  const AGENT_NAME = 'Sanne van PostAi';
  const AGENT_INITS = 'S';
  const TEASER_TEXT = 'Hulp nodig? Sanne helpt je graag.';
  const WELCOME = [
    'Hi! Ik ben Sanne. Waar kan ik je mee helpen?',
    'Tip: wil je beste posttijd? Zeg “beste tijd”.',
    '🔒 We bewaren niets zonder jouw actie.'
  ];
  const SLA_TEXT = 'Meestal reageren we binnen enkele minuten.';
  const PRIV_TEXT = '🔒 Privacy · <a href="?page=privacy" target="_blank" rel="noopener">Bekijk</a>';

  /* Helpers */
  const qs = (s) => DOC.querySelector(s);
  const el = (t, attrs = {}, html = '') => {
    const n = DOC.createElement(t);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    if (html) n.innerHTML = html;
    return n;
  };
  const escapeHtml = (s) =>
    String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* Derive some context to send along */
  const isPro = !!(DOC.querySelector('.pro-badge') && DOC.querySelector('.pro-badge').textContent.includes('PRO'));
  const appMode = isPro ? 'PRO' : 'DEMO';

  /* ---- Launcher button (always fixed bottom-right) ---- */
  const launcher = el(
    'button',
    { id: 'bms-chat-launcher', 'aria-label': 'Open chat', type: 'button' },
    `
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" width="24" height="24">
      <path d="M12 3c5.523 0 10 3.806 10 8.5S17.523 20 12 20a12.8 12.8 0 0 1-3.73-.55L3 21l1.73-4.33A8.63 8.63 0 0 1 2 11.5C2 6.806 6.477 3 12 3Z" stroke="currentColor" stroke-width="1.6"/>
    </svg>
  `
  );
  DOC.body.appendChild(launcher);

  /* Teaser badge (one-time per browser) */
  const teaser = el('div', { id: 'bms-chat-teaser' }, TEASER_TEXT);
  DOC.body.appendChild(teaser);
  const teaserKey = 'bmsChatTeaseShown';
  try {
    if (!window.top.localStorage.getItem(teaserKey)) {
      setTimeout(() => teaser.classList.add('show'), 600);
      setTimeout(() => {
        teaser.classList.remove('show');
        window.top.localStorage.setItem(teaserKey, '1');
      }, 5200);
    }
  } catch (_) {}

  /* ---- Chat window ---- */
  const chat = el(
    'div',
    { id: 'bms-chat', role: 'dialog', 'aria-label': 'PostAi chat' },
    `
    <div class="hdr">
      <div class="id" style="display:flex;gap:10px;align-items:center;">
        <div class="avatar">${AGENT_INITS}</div>
        <div>
          <div class="ttl">${AGENT_NAME}</div>
          <div class="sub" aria-live="polite">• online</div>
        </div>
      </div>
      <button class="close" aria-label="Sluiten" type="button">✕</button>
    </div>
    <div id="bms-trust">${SLA_TEXT}<br>${PRIV_TEXT}</div>
    <div class="body" id="bms-body"></div>
    <div class="inp">
      <input type="text" id="bms-input" placeholder="Typ je bericht…" autocomplete="off" />
      <button class="send" id="bms-send" type="button">Verstuur</button>
    </div>
  `
  );
  DOC.body.appendChild(chat);

  const body = qs('#bms-body');
  const input = qs('#bms-input');
  const sendBtn = qs('#bms-send');
  const closeBtn = chat.querySelector('.close');

  function openChat() {
    chat.style.display = 'block';
    teaser.classList.remove('show');
    setTimeout(() => input && input.focus(), 0);
  }
  function closeChat() {
    chat.style.display = 'none';
  }

  launcher.addEventListener('click', openChat);
  closeBtn.addEventListener('click', closeChat);
  DOC.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeChat();
  });

  /* Persist history in top window (survives Streamlit rerenders) */
  const store = (function () {
    try {
      return window.top.localStorage;
    } catch (_) {
      return window.localStorage;
    }
  })();
  const HKEY = 'bmsChatHistory';

  function append(role, text) {
    const row = el('div', { class: `bms-msg ${role}` });
    row.appendChild(el('div', { class: 'bubble' }, escapeHtml(text)));
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
  }
  function save(role, text) {
    try {
      const h = JSON.parse(store.getItem(HKEY) || '[]');
      h.push({ role, text });
      store.setItem(HKEY, JSON.stringify(h.slice(-60)));
    } catch (_) {}
  }
  try {
    (JSON.parse(store.getItem(HKEY) || '[]')).forEach((m) => append(m.role, m.text));
  } catch (_) {}

  /* Friendly welcome (only once) */
  try {
    if (!store.getItem('bmsChatWelcomed')) {
      append('bot', WELCOME[0]); save('bot', WELCOME[0]);
      setTimeout(() => { append('bot', WELCOME[1]); save('bot', WELCOME[1]); }, 400);
      setTimeout(() => { append('bot', WELCOME[2]); save('bot', WELCOME[2]); }, 800);
      store.setItem('bmsChatWelcomed', '1');
    }
  } catch (_) {}

  /* Send to API with meta + timeout */
  async function send() {
    const txt = (input.value || '').trim();
    if (!txt) return;

    append('user', txt); save('user', txt);
    input.value = ''; input.focus();
    append('bot', '•••');

    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 20_000);

    try {
      const res = await fetch(`${SERVER}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          message: txt,
          meta: {
            page: DOC.location ? DOC.location.pathname : '/',
            origin: DOC.location ? DOC.location.origin : '',
            mode: appMode,
            userAgent: navigator.userAgent,
          }
        })
      });
      clearTimeout(t);

      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const bot = (data && (data.reply || data.message || data.text)) || 'Dankje! Ik kijk even met je mee.';
      body.lastChild.querySelector('.bubble').textContent = bot;
      save('bot', bot);
    } catch (e) {
      clearTimeout(t);
      body.lastChild.querySelector('.bubble').textContent = 'Oeps, een netwerkfout. Probeer het zo nog eens.';
    }
  }

  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') send(); });

  /* Optional: auto-open on hash deep-links like #help */
  try {
    if ((DOC.location.hash || '').toLowerCase().includes('help')) openChat();
  } catch (_) {}
})();
