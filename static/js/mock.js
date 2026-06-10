/* Karel 2030 — mock backend čisto v prehliadači (?mock=1).
 * Implementuje rovnaké rozhranie ako Api a KarelWS z api.js,
 * aby app.js fungoval bez reálneho servera (vývoj / predvedenie).
 */
'use strict';

/* ---------- Mock World ---------- */
const DIRS = ['N', 'E', 'S', 'W'];
const DVEC = { N: [0, 1], E: [1, 0], S: [0, -1], W: [-1, 0] };

class MockWorld {
  constructor(w = 8, h = 6) {
    this.width = w; this.height = h;
    this.karel = { x: 1, y: 1, dir: 'E' };
    this.bricks = {};      // "x,y" -> count
    this.bigBricks = {};   // "x,y" -> 1
    this.marks = {};       // "x,y" -> true
    this.bricks['4,1'] = 2;
    this.bricks['5,2'] = 1;
    this.bigBricks['2,4'] = 1;
    this.marks['6,1'] = true;
    this._start = JSON.stringify(this._dump());
  }
  _dump() {
    return { karel: { ...this.karel }, bricks: { ...this.bricks },
             bigBricks: { ...this.bigBricks }, marks: { ...this.marks } };
  }
  reset() {
    const s = JSON.parse(this._start);
    this.karel = s.karel; this.bricks = s.bricks;
    this.bigBricks = s.bigBricks; this.marks = s.marks;
  }
  _front() {
    const [dx, dy] = DVEC[this.karel.dir];
    return [this.karel.x + dx, this.karel.y + dy];
  }
  _in(x, y) { return x >= 0 && x < this.width && y >= 0 && y < this.height; }
  _h(x, y) {
    const k = x + ',' + y;
    return (this.bricks[k] || 0) + (this.bigBricks[k] || 0) * 5;
  }
  // príkazy — tichý skip ako desktop
  forward(back) {
    const [dx, dy] = DVEC[this.karel.dir];
    const s = back ? -1 : 1;
    const nx = this.karel.x + dx * s, ny = this.karel.y + dy * s;
    if (!this._in(nx, ny)) return;                              // okrajová stena
    if ((this.bigBricks[nx + ',' + ny] || 0) > 0) return;       // kvader = stena
    const dh = this._h(nx, ny) - this._h(this.karel.x, this.karel.y);
    if (dh > 1) return;                                          // max_climb 1
    this.karel.x = nx; this.karel.y = ny;
  }
  left()  { this.karel.dir = DIRS[(DIRS.indexOf(this.karel.dir) + 3) % 4]; }
  right() { this.karel.dir = DIRS[(DIRS.indexOf(this.karel.dir) + 1) % 4]; }
  drop() {
    const [x, y] = this._front();
    if (!this._in(x, y)) return;
    this.bricks[x + ',' + y] = (this.bricks[x + ',' + y] || 0) + 1;
  }
  pick() {
    const [x, y] = this._front();
    const k = x + ',' + y;
    if (!this._in(x, y) || !(this.bricks[k] > 0)) return;
    if (--this.bricks[k] === 0) delete this.bricks[k];
  }
  dropBig() {
    const [x, y] = this._front();
    const k = x + ',' + y;
    if (!this._in(x, y) || this.bigBricks[k]) return;
    this.bigBricks[k] = 1;
  }
  mark()  { this.marks[this.karel.x + ',' + this.karel.y] = true; }
  clear() { delete this.marks[this.karel.x + ',' + this.karel.y]; }
  checkWall() {
    const [x, y] = this._front();
    return !this._in(x, y) || (this.bigBricks[x + ',' + y] || 0) > 0;
  }
  checkBrick() {
    const [x, y] = this._front();
    return (this.bricks[x + ',' + y] || 0) > 0;
  }
  checkSign() { return !!this.marks[this.karel.x + ',' + this.karel.y]; }

  /* State JSON podľa §4 */
  state() {
    const tup = (o, withCount) => Object.keys(o).map(k => {
      const [x, y] = k.split(',').map(Number);
      return withCount ? [x, y, o[k]] : [x, y];
    });
    return {
      width: this.width, height: this.height,
      karel: { ...this.karel },
      bricks: tup(this.bricks, true),
      big_bricks: tup(this.bigBricks, false),
      marks: tup(this.marks, false),
      walls: [],
      inventory: { bricks: -1, big_bricks: -1, marks: -1 },
      counters: { steps_used: 0, turns_used: 0 },
      settings: {
        prog_lang: 'sk', disabled_cmds: [], disable_procedure: false,
        max_climb: 1, max_drop: -1, max_steps: -1, max_turns: -1,
        max_brick_height: -1, camera_locked: false,
        camera: { az: 3.93, el: 0.49, dist: 16.0 },
      },
      meta: {
        title: 'Mock svet', intro_html: '<b>Mock režim</b> — backend simulovaný v prehliadači.<br>Skús: <code>opakuj 3 krat dopredu poloz *opakuj</code>',
        success_html: '', failure_html: '',
      },
      mission: [],
    };
  }
}

/* ---------- Mock interpreter ---------- */
/* Podporuje: dopredu/vlavo/vpravo/dozadu/poloz/zdvihni/oznac/odznac/kvader
 * + opakuj N krat ... *opakuj (vnorené). Bez diakritiky aj s ňou. */
const MOCK_KW = {
  dopredu: 'FORWARD', dozadu: 'BACK', vzad: 'BACK',
  vlavo: 'LEFT', 'vľavo': 'LEFT', dolava: 'LEFT', 'doľava': 'LEFT',
  vpravo: 'RIGHT', doprava: 'RIGHT',
  poloz: 'DROP', 'polož': 'DROP', zdvihni: 'PICK', zodvihni: 'PICK',
  kvader: 'DROP_BIG',
  oznac: 'MARK', 'označ': 'MARK', odznac: 'CLEAR', 'odznač': 'CLEAR',
  opakuj: 'REPEAT', krat: 'TIMES', 'krát': 'TIMES', '*opakuj': 'END_REPEAT',
  zaciatok: 'BEGIN', 'začiatok': 'BEGIN', koniec: 'END',
};

function mockParse(text) {
  // tokenizácia: odstráň komentáre // # {..}
  const clean = text.replace(/\{[^}]*\}/g, ' ').replace(/(\/\/|#).*$/gm, ' ');
  const words = clean.toLowerCase().split(/\s+/).filter(Boolean);
  let i = 0;
  function block(endTok) {
    const out = [];
    while (i < words.length) {
      const w = words[i];
      const t = MOCK_KW[w];
      // 'koniec' (END) uzatvára aj opakuj blok — ako v reálnom jazyku (CLOSE_T)
      if (endTok && (t === endTok || t === 'END')) { i++; return out; }
      i++;
      if (t === 'REPEAT') {
        const n = parseInt(words[i], 10);
        if (isNaN(n)) throw { line: 1, message: 'opakuj: chýba číslo' };
        i++;
        if (MOCK_KW[words[i]] === 'TIMES') i++;
        out.push({ rep: n, body: block('END_REPEAT') });
      } else if (t === 'BEGIN' || t === 'END') {
        // ignoruj obal
      } else if (t && t !== 'TIMES' && t !== 'END_REPEAT') {
        out.push({ cmd: t });
      } else if (!t) {
        throw { line: 1, message: 'Neznáme slovo: ' + w };
      }
    }
    if (endTok) throw { line: 1, message: 'Chýba koniec (alebo *opakuj)' };
    return out;
  }
  return block(null);
}

/* ---------- MockWS — rovnaké API ako KarelWS ---------- */
class MockWS {
  constructor() {
    this._handlers = {};
    this._world = new MockWorld();
    this._delay = 300;
    this._running = false;
    this._stopFlag = false;
  }
  on(type, fn) {
    (this._handlers[type] = this._handlers[type] || []).push(fn);
    return this;
  }
  _emit(type, extra) {
    const msg = Object.assign({ v: 1, type }, extra || {});
    (this._handlers[type] || []).forEach(fn => fn(msg));
    (this._handlers['*'] || []).forEach(fn => fn(msg));
  }
  connect() {
    setTimeout(() => {
      this._emit('_open', {});
      this._emit('state', { state: this._world.state(), reason: 'connect' });
    }, 50);
  }
  close() {}
  send(type, fields) {
    // generická cesta (app.js používa pomocné metódy nižšie)
    const f = fields || {};
    if (type === 'run') this.run(f.program);
    else if (type === 'stop') this.stop();
    else if (type === 'reset') this.reset();
    else if (type === 'direct') this.direct(f.cmd);
    else if (type === 'speed') this.speed(f.delay);
    else if (type === 'get_state') this.getState();
  }
  getState() { this._emit('state', { state: this._world.state(), reason: 'requested' }); }
  reset() {
    this._stopFlag = true;
    this._world.reset();
    this._emit('state', { state: this._world.state(), reason: 'reset' });
  }
  stop() { this._stopFlag = true; }
  speed(delay) { this._delay = Math.max(0.02, Math.min(3, delay)) * 1000; }
  direct(word) {
    const t = MOCK_KW[(word || '').toLowerCase()];
    if (!t) { this._emit('direct_result', { ok: false, error: 'Neznámy príkaz: ' + word }); return; }
    this._exec(t);
    this._emit('direct_result', { ok: true });
    this._emit('step', { state: this._world.state() });
  }
  _exec(t) {
    const w = this._world;
    if (t === 'FORWARD') w.forward(false);
    else if (t === 'BACK') w.forward(true);
    else if (t === 'LEFT') w.left();
    else if (t === 'RIGHT') w.right();
    else if (t === 'DROP') w.drop();
    else if (t === 'PICK') w.pick();
    else if (t === 'DROP_BIG') w.dropBig();
    else if (t === 'MARK') w.mark();
    else if (t === 'CLEAR') w.clear();
  }
  run(program) {
    if (this._running) return;
    let ast;
    try { ast = mockParse(program || ''); }
    catch (e) { this._emit('parse_error', { message: e.message, line: e.line || 1 }); return; }

    // sploštenie AST na zoznam príkazov (opakuj rozbalené)
    const steps = [];
    const flat = (nodes) => nodes.forEach(n => {
      if (n.cmd) steps.push(n.cmd);
      else if (n.rep) for (let k = 0; k < n.rep; k++) flat(n.body);
    });
    flat(ast);
    if (steps.length > 100000) { this._emit('limit', { kind: 'loop' }); return; }

    this._running = true; this._stopFlag = false;
    this._emit('started', {});
    let i = 0;
    const tick = () => {
      if (this._stopFlag) {
        this._running = false;
        this._emit('finished', { status: 'stopped' });
        return;
      }
      if (i >= steps.length) {
        this._running = false;
        this._emit('finished', { status: 'done' });
        return;
      }
      this._exec(steps[i++]);
      this._emit('step', { state: this._world.state() });
      setTimeout(tick, this._delay);
    };
    setTimeout(tick, this._delay);
  }
  loadWorld() { /* mock: ignorované */ }
  applySettings() { /* mock: ignorované */ }
  exportWorld() { this._emit('world_export', { karxml: '<world width="8" height="6"></world>', title: 'Mock' }); }
}

/* ---------- MockApi — podmnožina Api ---------- */
const MockApi = {
  uiLangs: async () => [{ code: 'sk', name: 'Slovenčina' }],
  uiStrings: async () => ({}),   // app.js nechá HTML defaulty (slovenské)
  progLangs: async () => [{ code: 'sk', name: 'Slovenčina' }],
  progLang: async () => ({
    primary: {
      BEGIN: 'zaciatok', END: 'koniec', PROCEDURE: 'prikaz', REPEAT: 'opakuj',
      TIMES: 'krat', END_REPEAT: '*opakuj', WHILE: 'kym', DO: 'rob',
      END_WHILE: '*kym', IF: 'ak', THEN: 'potom', ELSE: 'inak', END_IF: '*ak',
      NOT: 'nie', AND: 'a', OR: 'alebo',
      FORWARD: 'dopredu', BACK: 'dozadu', LEFT: 'vlavo', RIGHT: 'vpravo',
      DROP: 'poloz', PICK: 'zdvihni', DROP_BIG: 'kvader',
      MARK: 'oznac', CLEAR: 'odznac',
      WALL: 'stena', BRICK: 'tehla', FREE: 'volno', SIGN: 'znacka',
      TRUE: 'pravda', FALSE: 'nepravda', SLOWLY: 'pomaly', QUICKLY: 'rychlo',
    },
    disabled: [],
    all_words: Object.assign({}, ...Object.entries(MOCK_KW).map(([w, t]) => ({ [w]: t })), {
      kym: 'WHILE', 'kým': 'WHILE', rob: 'DO', '*kym': 'END_WHILE', '*kým': 'END_WHILE',
      ak: 'IF', potom: 'THEN', tak: 'THEN', inak: 'ELSE', '*ak': 'END_IF',
      nie: 'NOT', a: 'AND', aj: 'AND', alebo: 'OR',
      prikaz: 'PROCEDURE', 'príkaz': 'PROCEDURE',
      stena: 'WALL', tehla: 'BRICK', volno: 'FREE', 'voľno': 'FREE',
      znacka: 'SIGN', 'značka': 'SIGN', pravda: 'TRUE', nepravda: 'FALSE',
      pomaly: 'SLOWLY', rychlo: 'QUICKLY', 'rýchlo': 'QUICKLY',
    }),
  }),
  examples: async () => [
    { name: 'Štvorec', program: 'opakuj 4 krat\n  dopredu\n  vlavo\n*opakuj' },
    { name: 'Múrik', program: 'opakuj 3 krat\n  poloz\n  vlavo\n  vlavo\n  dopredu\n  vlavo\n  vlavo\n*opakuj' },
  ],
  worlds: async () => [],
  world: async () => { throw new Error('mock'); },
  publishWorld: async () => ({ published: true }),
  workspace: async () => ({ assignment_id: 'mock', name: 'Mock žiak', program_text: '', state: new MockWorld().state() }),
  saveWorkspace: async () => ({}),
};
