/* TalkToClaude — floating per-entry Claude Code terminal widget.
 *
 * Used by wiki.html, audit.html, review.html. Lazy-loads @wterm/dom and
 * @wterm/ghostty from esm.sh on first open.
 *
 *   TalkToClaude.open({
 *     mode: 'entry' | 'audit' | 'review',
 *     target: '<vault-relative-path-or-rec-id>',
 *     label: 'Display title',
 *     sublabel: 'Path or id, monospace subtitle',
 *   })
 */
(function () {
  let term = null;
  let ws = null;
  let keyHandler = null;
  let ghosttyCore = null;
  let depsLoaded = false;
  let mounted = false;
  let overlay, headerEl, titleEl, subtitleEl, statusEl, termEl;

  const ESM_DOM = 'https://esm.sh/@wterm/dom@0.3.0';
  const ESM_GHOSTTY = 'https://esm.sh/@wterm/ghostty@0.3.0';
  const CDN_CSS = 'https://cdn.jsdelivr.net/npm/@wterm/dom@0.3.0/src/terminal.css';

  function ensureDom() {
    if (mounted) return;
    overlay = document.createElement('div');
    overlay.className = 'tt-overlay';
    overlay.id = 'tt-overlay';
    overlay.innerHTML = [
      '<div class="tt-header" id="tt-header">',
      '  <div class="meta">',
      '    <div class="tt-title" id="tt-title">Talk to Claude</div>',
      '    <div class="tt-subtitle" id="tt-subtitle"></div>',
      '  </div>',
      '  <button class="tt-btn" id="tt-max-btn" title="Maximize / restore">&#9974;</button>',
      '  <button class="tt-btn close" id="tt-close-btn" title="Close (ESC)">&#10005;</button>',
      '</div>',
      '<div class="tt-term" id="tt-term"></div>',
      '<div class="tt-status" id="tt-status">disconnected</div>',
    ].join('\n');
    document.body.appendChild(overlay);
    titleEl    = overlay.querySelector('#tt-title');
    subtitleEl = overlay.querySelector('#tt-subtitle');
    statusEl   = overlay.querySelector('#tt-status');
    termEl     = overlay.querySelector('#tt-term');
    headerEl   = overlay.querySelector('#tt-header');
    overlay.querySelector('#tt-max-btn').addEventListener('click', toggleMax);
    overlay.querySelector('#tt-close-btn').addEventListener('click', close);
    setupDrag();
    mounted = true;
  }

  function setStatus(text, cls) {
    statusEl.textContent = text;
    statusEl.className = 'tt-status ' + (cls || '');
  }

  function setupDrag() {
    headerEl.addEventListener('mousedown', function (e) {
      if (overlay.classList.contains('fullscreen')) return;
      if (e.target.closest('button')) return;
      const start = { x: e.clientX, y: e.clientY };
      const r = overlay.getBoundingClientRect();
      const init = { left: r.left, top: r.top, w: r.width, h: r.height };
      function onMove(m) {
        const left = Math.max(4, Math.min(window.innerWidth - init.w - 4,
          init.left + m.clientX - start.x));
        const top  = Math.max(4, Math.min(window.innerHeight - init.h - 4,
          init.top + m.clientY - start.y));
        overlay.style.left = left + 'px';
        overlay.style.top = top + 'px';
        overlay.style.right = 'auto';
        overlay.style.bottom = 'auto';
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
      e.preventDefault();
    });
  }

  function toggleMax() {
    overlay.classList.toggle('fullscreen');
    // Terminal's autoResize ResizeObserver picks up the new size.
  }

  function resizeFrame(cols, rows) {
    const json = JSON.stringify({ type: 'resize', cols: cols, rows: rows });
    const buf = new Uint8Array(json.length + 1);
    buf[0] = 0x1f;
    for (let i = 0; i < json.length; i++) buf[i + 1] = json.charCodeAt(i);
    return buf;
  }

  async function loadDeps() {
    if (depsLoaded) return;
    const [domMod, ghosttyMod] = await Promise.all([
      import(ESM_DOM),
      import(ESM_GHOSTTY),
    ]);
    window.WTerm = domMod.WTerm;
    window.WebSocketTransport = domMod.WebSocketTransport;
    window.GhosttyCore = ghosttyMod.GhosttyCore;
    if (!document.getElementById('wterm-css')) {
      const link = document.createElement('link');
      link.id = 'wterm-css';
      link.rel = 'stylesheet';
      link.href = CDN_CSS;
      document.head.appendChild(link);
    }
    depsLoaded = true;
  }

  async function open(opts) {
    opts = opts || {};
    const mode = opts.mode || 'entry';
    const target = opts.target || '';
    if (!target) {
      alert('No target provided to Talk to Claude.');
      return;
    }
    ensureDom();
    if (overlay.classList.contains('open')) {
      // Already open — close current session first so we land on a fresh PTY.
      close();
    }
    overlay.classList.add('open');
    titleEl.textContent = opts.label || 'Talk to Claude';
    subtitleEl.textContent = opts.sublabel || (mode + ': ' + target);
    setStatus('loading wterm + ghostty core…', '');

    try {
      await loadDeps();
      if (!ghosttyCore) {
        ghosttyCore = await window.GhosttyCore.load({ scrollbackLimit: 500 });
      }
    } catch (e) {
      setStatus('failed to load wterm: ' + (e && e.message ? e.message : e), 'error');
      return;
    }

    termEl.innerHTML = '';
    term = new window.WTerm(termEl, {
      core: ghosttyCore,
      cols: 100,
      rows: 32,
      cursorBlink: false,
      autoResize: true,
      onResize: function (cols, rows) {
        if (ws && ws.connected) ws.send(resizeFrame(cols, rows));
      },
    });
    await term.init();

    const wsScheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = wsScheme + '//' + location.host + '/wterm'
      + '?mode=' + encodeURIComponent(mode)
      + '&target=' + encodeURIComponent(target);

    setStatus('connecting…', '');
    ws = new window.WebSocketTransport({
      url: url,
      reconnect: false,
      onOpen:  function () { setStatus('connected — claude is starting up…', 'connected'); },
      onClose: function () { setStatus('disconnected', ''); },
      onError: function () { setStatus('websocket error', 'error'); },
      onData:  function (d) { if (term) term.write(d); },
    });
    ws.connect();
    term.onData = function (d) { if (ws) ws.send(d); };

    keyHandler = function (e) {
      if (e.key === 'Escape' && document.activeElement.tagName !== 'INPUT'
          && document.activeElement.tagName !== 'TEXTAREA') {
        close();
      }
    };
    document.addEventListener('keydown', keyHandler);
    setTimeout(function () { if (term) term.focus(); }, 100);
  }

  function close() {
    if (!mounted) return;
    overlay.classList.remove('open');
    if (keyHandler) {
      document.removeEventListener('keydown', keyHandler);
      keyHandler = null;
    }
    if (ws)   { try { ws.close(); }     catch (e) {} ws = null; }
    if (term) { try { term.destroy(); } catch (e) {} term = null; }
    if (termEl) termEl.innerHTML = '';
    setStatus('disconnected', '');
  }

  window.TalkToClaude = { open: open, close: close, toggleMax: toggleMax };
})();
