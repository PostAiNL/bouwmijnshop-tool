// public/chat-widget.js
(function () {
  const SERVER = (document.currentScript && document.currentScript.dataset.server)
    || window.CHAT_SERVER
    || '';

  // Styles (mini)
  const style = document.createElement('style');
  style.textContent = `
    .bmw-chat-btn {
      position: fixed; right: 20px; bottom: 20px; z-index: 999999;
      background: #111827; color:#fff; border:0; border-radius: 999px;
      padding: 12px 16px; font-weight: 700; box-shadow: 0 8px 24px rgba(0,0,0,.18);
      cursor: pointer;
    }
    .bmw-chat-frame {
      position: fixed; right: 20px; bottom: 80px; width: 360px; height: 520px; 
      max-width: 90vw; max-height: 75vh; border: 1px solid #e5e7eb; border-radius: 16px;
      box-shadow: 0 18px 40px rgba(0,0,0,.22); overflow: hidden; z-index: 999998; display:none;
    }
    .bmw-chat-overlay { position:fixed; inset:0; background:rgba(0,0,0,.35); display:none; z-index:999997; }
    @media (max-width: 520px) {
      .bmw-chat-frame { right: 0; bottom: 0; width: 100vw; height: 100vh; border-radius: 0; }
    }
  `;
  document.head.appendChild(style);

  // Overlay + iframe
  const overlay = document.createElement('div');
  overlay.className = 'bmw-chat-overlay';
  overlay.addEventListener('click', () => {
    frame.style.display = 'none';
    overlay.style.display = 'none';
  });

  const frame = document.createElement('iframe');
  frame.className = 'bmw-chat-frame';
  frame.src = (SERVER || '') + '/widget';
  frame.allow = 'clipboard-write *; clipboard-read *;';

  // Button
  const btn = document.createElement('button');
  btn.className = 'bmw-chat-btn';
  btn.textContent = 'Chat met ons';
  btn.addEventListener('click', () => {
    const vis = frame.style.display === 'block';
    frame.style.display = vis ? 'none' : 'block';
    overlay.style.display = vis ? 'none' : 'block';
  });

  document.body.appendChild(overlay);
  document.body.appendChild(frame);
  document.body.appendChild(btn);
})();
