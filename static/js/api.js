/* Karel 2030 — REST klient (§2) + WS klient (§3) podľa docs/api.md v1 */
'use strict';

const API_V = 1;

/* ---------- REST ---------- */
const Api = {
  async _get(path) {
    const r = await fetch('/api' + path);
    if (!r.ok) throw await Api._err(r);
    return r.json();
  },
  async _send(method, path, body) {
    const r = await fetch('/api' + path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) throw await Api._err(r);
    return r.json();
  },
  async _err(r) {
    let d = {};
    try { d = await r.json(); } catch (e) { /* nie JSON */ }
    const e = new Error(d.detail || d.error || ('HTTP ' + r.status));
    e.code = d.error; e.status = r.status;
    return e;
  },

  version:        ()     => Api._get('/version'),
  // admin autentifikácia (cookie session na serveri)
  adminLogin:     (password) => Api._send('POST', '/admin/login', { password }),
  adminStatus:    ()         => Api._get('/admin/status'),
  adminLogout:    ()         => Api._send('POST', '/admin/logout'),
  // jazyky
  uiLangs:        ()     => Api._get('/langs/ui'),
  uiStrings:      (code) => Api._get('/langs/ui/' + code),
  progLangs:      ()     => Api._get('/langs/prog'),
  progLang:       (code) => Api._get('/langs/prog/' + code),

  // svety a príklady
  examples:       ()     => Api._get('/examples'),
  worlds:         ()     => Api._get('/worlds'),
  world:          (id)   => Api._get('/worlds/' + encodeURIComponent(id)),
  publishWorld:   (id, karxml) => Api._send('POST', '/worlds', { id, karxml }),
  deleteWorld:    (id)         => Api._send('DELETE', '/worlds/' + encodeURIComponent(id)),
  parseKarxml:    (xml)  => fetch('/api/worlds/parse-karxml', { method: 'POST', body: xml })
                              .then(r => r.ok ? r.json() : Api._err(r).then(e => { throw e; })),

  // assignmenty (učiteľ)
  createAssignment: (karxml, title) => Api._send('POST', '/assignments', { karxml, title }),
  assignment:       (id)            => Api._get('/assignments/' + id),
  share:            (id, opts)      => Api._send('POST', `/assignments/${id}/share`, opts),
  links:            (id)            => Api._get('/assignments/' + id + '/links'),
  assignments:      ()             => Api._get('/assignments'),
  progress:         (id)            => Api._get('/assignments/' + id + '/progress'),
  ensureAssignment: (world_key, karxml, title) => Api._send('POST', '/assignments/ensure', { world_key, karxml, title }),
  addLink:          (id, name)     => Api._send('POST', '/assignments/' + id + '/links', { name }),
  deleteLink:       (token)        => Api._send('DELETE', '/links/' + token),

  // workspace (žiak)
  workspace:     (token)       => Api._get('/workspace/' + token),
  saveWorkspace: (token, text) => Api._send('PUT', '/workspace/' + token, { program_text: text }),
};

/* ---------- WebSocket klient ---------- */
/* Použitie:
 *   const ws = new KarelWS({ token: 'x7..' });          // žiak  → /ws/{token}
 *   const ws = new KarelWS({ sessionId: 'abc' });       // učiteľ → /ws/teacher/{session_id}
 *   ws.on('state', msg => ...); ws.connect();
 * Auto-reconnect s exponenciálnym backoff; po reconnect-e pošle get_state.
 */
class KarelWS {
  constructor(opts) {
    this._url = opts.token
      ? `/ws/${opts.token}`
      : `/ws/teacher/${opts.sessionId}`;
    this._handlers = {};        // type -> [fn]
    this._sock = null;
    this._closed = false;
    this._retry = 0;
    this._queue = [];           // správy čakajúce na open
  }

  on(type, fn) {
    (this._handlers[type] = this._handlers[type] || []).push(fn);
    return this;
  }
  _emit(type, msg) {
    (this._handlers[type] || []).forEach(fn => fn(msg));
  }

  connect() {
    this._closed = false;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const sock = new WebSocket(proto + '//' + location.host + this._url);
    this._sock = sock;

    sock.onopen = () => {
      this._emit('_open', {});
      const wasRetry = this._retry > 0;
      this._retry = 0;
      this._queue.splice(0).forEach(m => sock.send(m));
      if (wasRetry) this.send('get_state');   // po reconnect-e plný stav
    };
    sock.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (msg.v !== API_V) return;            // neznáma verzia kontraktu
      this._emit(msg.type, msg);
      this._emit('*', msg);
    };
    sock.onclose = () => {
      this._emit('_close', {});
      if (this._closed) return;
      const delay = Math.min(500 * 2 ** this._retry++, 8000);
      setTimeout(() => this.connect(), delay);
    };
    sock.onerror = () => { /* onclose nasleduje */ };
  }

  close() {
    this._closed = true;
    if (this._sock) this._sock.close();
  }

  /* Klient → server: run/stop/reset/direct/speed/get_state (+ teacher: load_world/apply_settings) */
  send(type, fields) {
    const m = JSON.stringify(Object.assign({ v: API_V, type }, fields || {}));
    if (this._sock && this._sock.readyState === WebSocket.OPEN) this._sock.send(m);
    else this._queue.push(m);
  }

  run(program)   { this.send('run', { program }); }
  stop()         { this.send('stop'); }
  reset()        { this.send('reset'); }
  direct(cmd)    { this.send('direct', { cmd }); }
  speed(delay)   { this.send('speed', { delay }); }
  getState()     { this.send('get_state'); }
  loadWorld(o)   { this.send('load_world', o); }   // {karxml} | {world_id}
  applySettings(o){ this.send('apply_settings', o); }
  exportWorld(program, camera) {
    const f = {};
    if (program != null) f.program = program;
    if (camera) f.camera = camera;
    this.send('export_world', f);
  }
}
