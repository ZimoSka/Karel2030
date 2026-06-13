/* Karel 2030 — dialóg Nastavenia sveta (učiteľ) so 6 záložkami + editor misií.
 * Číta aktuálny state JSON, na Apply zostaví payload pre ws.applySettings:
 *   { settings:{…}, karel:{x,y,dir}, title, intro_html, success_html,
 *     failure_html, reset_on_failure, goal_conditions:[…] }
 */
'use strict';

const KarelSettings = (function () {
  let T = (k, d) => d || k;
  let st = null;          // referencia na state JSON
  let conds = [];         // pracovná kópia misie
  let onApplyCb = null;
  let progLangs = [];     // [{code,name}] dostupné prog jazyky
  const $ = (id) => document.getElementById(id);

  const CMD_TOKS = ['FORWARD', 'BACK', 'LEFT', 'RIGHT', 'DROP', 'PICK',
                    'DROP_BIG', 'MARK', 'CLEAR', 'SLOWLY', 'QUICKLY'];
  const CMD_LBL = {
    FORWARD: 'cmd_forward', BACK: 'cmd_back', LEFT: 'cmd_left', RIGHT: 'cmd_right',
    DROP: 'cmd_drop', DROP_BIG: 'cmd_drop_big', PICK: 'cmd_pick', MARK: 'cmd_mark',
    CLEAR: 'cmd_clear', SLOWLY: 'cmd_slowly', QUICKLY: 'cmd_quickly',
  };

  /* ---------- malé DOM helpery ---------- */
  function el(tag, attrs, kids) {
    const e = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'text') e.textContent = attrs[k];
      else if (k === 'html') e.innerHTML = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(c => e.appendChild(c));
    return e;
  }
  function field(labelKey, dfltLabel, inputEl) {
    return el('label', { class: 'set-row' }, [
      el('span', { class: 'set-lbl', text: T(labelKey, dfltLabel) }), inputEl,
    ]);
  }
  function num(value, min) {
    const i = el('input', { type: 'number', value: value });
    if (min !== undefined) i.min = min;
    i.className = 'set-num';
    return i;
  }
  // dvojica „neobmedzene + číslo" (-1 = ∞) pre limity zásob
  function limitRow(labelKey, dfltLabel, value) {
    const chk = el('input', { type: 'checkbox' });
    chk.checked = (value === -1 || value == null);
    const n = num(chk.checked ? 0 : value, 0); n.disabled = chk.checked;
    chk.onchange = () => { n.disabled = chk.checked; };
    const wrap = el('span', {}, [
      el('label', { class: 'inline' }, [chk, el('span', { text: ' ' + T('world_settings.inv_unlimited', 'Neobmedzene (∞)') })]),
      n,
    ]);
    wrap._get = () => (chk.checked ? -1 : Math.max(0, parseInt(n.value, 10) || 0));
    return { row: field(labelKey, dfltLabel, wrap), get: () => wrap._get() };
  }

  /* ---------- záložky ---------- */
  function buildTabs() {
    const tabsEl = $('set-tabs'), bodyEl = $('set-body');
    tabsEl.innerHTML = ''; bodyEl.innerHTML = '';
    const tabs = [
      ['world_settings.tab_desc', 'Popis', buildDesc],
      ['world_settings.tab_room', 'Miestnosť', buildRoom],
      ['world_settings.tab_inv', 'Zásoby', buildInv],
      ['world_settings.tab_cmds', 'Príkazy', buildCmds],
      ['world_settings.tab_view', 'Pohľad', buildView],
      ['world_settings.tab_mission', 'Misia', buildMission],
    ];
    const panes = [];
    tabs.forEach(([key, dflt, builder], i) => {
      const btn = el('button', { class: 'set-tab' + (i === 0 ? ' active' : ''), text: T(key, dflt) });
      const pane = el('div', { class: 'set-pane' + (i === 0 ? '' : ' hidden') });
      builder(pane);
      btn.onclick = () => {
        tabsEl.querySelectorAll('.set-tab').forEach((b, j) => b.classList.toggle('active', j === i));
        panes.forEach((p, j) => p.classList.toggle('hidden', j !== i));
      };
      tabsEl.appendChild(btn); bodyEl.appendChild(pane); panes.push(pane);
    });
  }

  let get = {};   // gettery jednotlivých polí (naplnené v builderoch)

  /* U3/U4: jednoduchý rich-text editor (WYSIWYG, contenteditable).
   * Zobrazuje výsledný tvar priamo počas písania. get() vráti HTML. */
  function richText(html) {
    const mkBtn = (label, cmd, val) => {
      const b = el('button', { class: 'rt-btn', text: label, type: 'button' });
      b.onmousedown = (e) => { e.preventDefault(); document.execCommand(cmd, false, val); };
      return b;
    };
    const colorWrap = el('label', { class: 'rt-btn', text: 'A' });
    const color = el('input', { type: 'color', value: '#ffdd44' });
    color.style.width = '0'; color.style.height = '0'; color.style.opacity = '0'; color.style.position = 'absolute';
    color.oninput = () => document.execCommand('foreColor', false, color.value);
    colorWrap.appendChild(color);
    const bar = el('div', { class: 'rt-toolbar' }, [
      mkBtn('B', 'bold'), mkBtn('I', 'italic'), mkBtn('U', 'underline'),
      mkBtn('H', 'formatBlock', 'H3'), mkBtn('•', 'insertUnorderedList'),
      mkBtn('↵', 'insertHTML', '<br>'), colorWrap,
    ]);
    bar.querySelector('.rt-btn:last-child');
    const area = el('div', { class: 'rt-area' });
    area.contentEditable = 'true';
    area.innerHTML = unescapeMaybe(html || '');
    const wrap = el('div', { class: 'rt-wrap' }, [bar, area]);
    return { el: wrap, get: () => area.innerHTML };
  }
  // niektoré staré .karxml majú dvojito-escapovaný HTML (&amp;lt;…) — rozbalíme
  function unescapeMaybe(s) {
    if (/&(amp|lt|gt|quot);/.test(s) && !/<[a-z]/i.test(s)) {
      const d = document.createElement('textarea'); d.innerHTML = s; return d.value;
    }
    return s;
  }

  function buildDesc(p) {
    const title = el('input', { type: 'text', value: st.meta.title || '' }); title.className = 'set-text';
    const intro = richText(st.meta.intro_html || '');
    p.appendChild(field('world_settings.frame_title', 'Názov sveta', title));
    p.appendChild(el('div', { class: 'set-sep', text: T('world_settings.frame_desc', 'Popis / zadanie úlohy') }));
    p.appendChild(intro.el);
    get.title = () => title.value;
    get.intro = () => intro.get();
  }

  function buildRoom(p) {
    const s = st.settings || {};
    const w = num(st.width, 3), h = num(st.height, 3);
    const kx = num(st.karel.x, 0), ky = num(st.karel.y, 0);
    const dir = el('select', { class: 'set-text' });
    [['N', 'dir_n', '↑ Sever'], ['E', 'dir_e', '→ Východ'], ['S', 'dir_s', '↓ Juh'], ['W', 'dir_w', '← Západ']]
      .forEach(([v, k, d]) => { const o = el('option', { value: v, text: T('world_settings.' + k, d) }); if (st.karel.dir === v) o.selected = true; dir.appendChild(o); });
    // F-prog: programovací jazyk sveta (ako Python verzia)
    const prog = el('select', { class: 'set-text' });
    (progLangs.length ? progLangs : [{ code: s.prog_lang || 'sk', name: s.prog_lang || 'sk' }])
      .forEach(l => { const o = el('option', { value: l.code, text: l.name }); if ((s.prog_lang || 'sk') === l.code) o.selected = true; prog.appendChild(o); });
    p.appendChild(field('world_settings.lbl_prog_lang', 'Jazyk programovania:', prog));
    p.appendChild(field('world_settings.lbl_width', 'Šírka:', w));
    p.appendChild(field('world_settings.lbl_height', 'Výška:', h));
    // U5: jasné X / Y (výška = Z, preto nemiešať)
    p.appendChild(field('world_settings.lbl_karel_x', 'Karel X:', kx));
    p.appendChild(field('world_settings.lbl_karel_y', 'Karel Y:', ky));
    p.appendChild(field('world_settings.frame_dir', 'Smer Karla', dir));
    p.appendChild(el('div', { class: 'set-sep', text: T('world_settings.frame_move', 'Pohyb — obmedzenia') }));
    // max_climb: 0..N (0 = nevylezie, default 1) — bez „neobmedzene"
    const climb = num(s.max_climb != null ? s.max_climb : 1, 0);
    p.appendChild(field('world_settings.lbl_max_climb', 'Max. výška výstupu:', climb));
    // U6: ostatné s checkboxom „neobmedzené" (-1) ako pri Zásobách
    const drop = limitRow('world_settings.lbl_max_drop', 'Max. zoskok:', s.max_drop != null ? s.max_drop : -1);
    const steps = limitRow('world_settings.lbl_max_steps', 'Max. krokov:', s.max_steps != null ? s.max_steps : -1);
    const turns = limitRow('world_settings.lbl_max_turns', 'Max. otočení:', s.max_turns != null ? s.max_turns : -1);
    const bh = limitRow('world_settings.lbl_max_bh', 'Max. výška tehál:', s.max_brick_height != null ? s.max_brick_height : -1);
    [drop, steps, turns, bh].forEach(r => p.appendChild(r.row));
    get.room = () => ({
      prog_lang: prog.value,
      width: parseInt(w.value, 10), height: parseInt(h.value, 10),
      karel: { x: parseInt(kx.value, 10), y: parseInt(ky.value, 10), dir: dir.value },
      max_climb: parseInt(climb.value, 10), max_drop: drop.get(),
      max_steps: steps.get(), max_turns: turns.get(), max_brick_height: bh.get(),
    });
  }

  function buildInv(p) {
    const s = st.settings || {};
    p.appendChild(el('div', { class: 'set-note', text: T('world_settings.inv_intro', 'Počet predmetov, ktoré má Karel k dispozícii:') }));
    const b = limitRow('world_settings.inv_brick', 'Malé tehly:', s.brick_limit);
    const bb = limitRow('world_settings.inv_big_brick', 'Veľké tehly:', s.big_brick_limit);
    const mk = limitRow('world_settings.inv_mark', 'Značky:', s.mark_limit);
    p.appendChild(b.row); p.appendChild(bb.row); p.appendChild(mk.row);
    get.inv = () => ({ brick_limit: b.get(), big_brick_limit: bb.get(), mark_limit: mk.get() });
  }

  function buildCmds(p) {
    const s = st.settings || {};
    const dis = new Set(s.disabled_cmds || []);
    // U7: otočená logika — zaškrtnuté = príkaz VIDITEĽNÝ/povolený
    p.appendChild(el('div', { class: 'set-note', text: T('world_settings.cmds_intro', 'Zaškrtnuté príkazy sú pre žiaka viditeľné a povolené. Odškrtnuté = skryté/zakázané.') }));
    const grid = el('div', { class: 'set-cmd-grid' });
    const boxes = {};
    CMD_TOKS.forEach(tok => {
      const c = el('input', { type: 'checkbox' }); c.checked = !dis.has(tok);   // checked = viditeľný
      boxes[tok] = c;
      grid.appendChild(el('label', { class: 'inline' }, [c, el('span', { text: ' ' + T('world_settings.' + CMD_LBL[tok], tok) })]));
    });
    p.appendChild(grid);
    // vlastné príkazy: zaškrtnuté = povolené (negácia disable_procedure)
    const proc = el('input', { type: 'checkbox' }); proc.checked = !s.disable_procedure;
    p.appendChild(el('label', { class: 'inline set-row' }, [proc, el('span', { text: ' ' + T('world_settings.enable_proc', 'Povoliť definovanie vlastných príkazov (prikaz … koniec)') })]));
    // Zákaz manuálneho ovládania Karla (zaškrtnuté = povolené)
    const gfx = el('input', { type: 'checkbox' }); gfx.checked = !s.disable_graphic;
    p.appendChild(el('label', { class: 'inline set-row' }, [gfx, el('span', { text: ' ' + T('world_settings.enable_graphic', 'Povoliť grafické ovládanie Karla (šípky + akčné tlačidlá)') })]));
    const cmd = el('input', { type: 'checkbox' }); cmd.checked = !s.disable_command;
    p.appendChild(el('label', { class: 'inline set-row' }, [cmd, el('span', { text: ' ' + T('world_settings.enable_command', 'Povoliť príkazové ovládanie Karla (textový riadok)') })]));
    get.cmds = () => ({
      disabled_cmds: CMD_TOKS.filter(tok => !boxes[tok].checked),   // ulož NEzaškrtnuté ako zakázané
      disable_procedure: !proc.checked,
      disable_graphic: !gfx.checked,
      disable_command: !cmd.checked,
    });
  }

  function buildView(p) {
    const s = st.settings || {}, cam = s.camera || {};
    const lock = el('input', { type: 'checkbox' }); lock.checked = !!s.camera_locked;
    p.appendChild(el('label', { class: 'inline set-row' }, [lock, el('span', { text: ' ' + T('world_settings.cam_lock', 'Zamknúť pohľad') })]));
    const az = num((cam.az || 0).toFixed ? +(cam.az).toFixed(3) : cam.az);
    const elv = num(cam.el != null ? +(+cam.el).toFixed(3) : 0);
    const dist = num(cam.dist != null ? +(+cam.dist).toFixed(1) : 16);
    p.appendChild(field('world_settings.cam_az', 'Azimut:', az));
    p.appendChild(field('world_settings.cam_el', 'Elevácia:', elv));
    p.appendChild(field('world_settings.cam_dist', 'Vzdialenosť:', dist));
    get.view = () => ({
      camera_locked: lock.checked,
      camera: { az: parseFloat(az.value), el: parseFloat(elv.value), dist: parseFloat(dist.value) },
    });
  }

  /* ---------- záložka Misia + editor podmienok (E) ---------- */
  function condLabel(c, i) {
    const prefix = i === 0 ? '     ' : (c.op === 'and' ? 'AND ' : ' OR ');
    const ev = c.eval === 'failure' ? '✗' : '✓';
    const wh = c.when === 'on_step' ? '⏱' : '⏹';
    const neg = c.negate ? '¬' : '';
    let d = c.check;
    if (c.check === 'karel_pos') d = `Karel @ (${c.x ?? '?'},${c.y ?? '?'})` + (c.z != null ? ` v=${c.z}` : '');
    else if (c.check === 'cell_state') d = `${T('goal_condition.disp_cell','bunka')} (${c.x},${c.y})`;
    else if (c.check === 'sign') d = T('goal_condition.disp_sign','značka pod Karlom');
    else if (c.check === 'brick_ahead') d = T('goal_condition.disp_brick_ahead','tehla pred Karlom');
    else if (c.check === 'wall_ahead') d = T('goal_condition.disp_wall_ahead','stena pred Karlom');
    else if (c.check === 'snapshot') d = T('goal_condition.disp_snapshot','snímok miestnosti');
    return `${prefix}${ev}${wh} ${neg}${d}`;
  }

  function buildMission(p) {
    conds = (st.mission || []).map(c => Object.assign({}, c));
    const rof = el('input', { type: 'checkbox' }); rof.checked = !!(st.settings && st.settings.reset_on_failure);
    const succ = richText(st.meta.success_html || '');
    const fail = richText(st.meta.failure_html || '');

    const list = el('select', { class: 'set-list', size: '6' });
    function refresh() {
      list.innerHTML = '';
      conds.forEach((c, i) => list.appendChild(el('option', { value: i, text: condLabel(c, i) })));
    }
    refresh();
    const btnAdd = el('button', { class: 'set-mini', text: '＋ ' + T('world_settings.btn_add_cond', 'Pridať') });
    const btnEdit = el('button', { class: 'set-mini', text: '✎ ' + T('world_settings.btn_edit_cond', 'Upraviť') });
    const btnDel = el('button', { class: 'set-mini', text: '− ' + T('world_settings.btn_del_cond', 'Odstrániť') });
    btnAdd.onclick = () => editCond(null, c => { conds.push(c); refresh(); });
    btnEdit.onclick = () => { const i = list.value; if (i === '') return; editCond(conds[+i], c => { conds[+i] = c; refresh(); }); };
    btnDel.onclick = () => { const i = list.value; if (i === '') return; conds.splice(+i, 1); refresh(); };
    list.ondblclick = () => btnEdit.onclick();

    p.appendChild(el('div', { class: 'set-note', text: T('world_settings.mission_note', 'Každá podmienka má typ, výsledok a logický operátor voči predchádzajúcej.') }));
    p.appendChild(list);
    p.appendChild(el('div', { class: 'set-btnrow' }, [btnAdd, btnEdit, btnDel]));
    p.appendChild(el('label', { class: 'inline set-row' }, [rof, el('span', { text: ' ' + T('world_settings.reset_on_fail', 'Pri neúspechu resetovať svet') })]));
    p.appendChild(el('div', { class: 'set-sep', text: T('world_settings.msg_success', 'Správa pri úspechu:') }));
    p.appendChild(succ.el);
    p.appendChild(el('div', { class: 'set-sep', text: T('world_settings.msg_failure', 'Správa pri neúspechu:') }));
    p.appendChild(fail.el);
    get.mission = () => ({
      goal_conditions: conds,
      reset_on_failure: rof.checked,
      success_html: succ.get(), failure_html: fail.get(),
    });
  }

  /* editor jednej podmienky — vnorený mini-dialóg (E) */
  function editCond(existing, done) {
    const c = existing || { check: 'karel_pos', eval: 'success', when: 'on_finish', op: 'or', negate: false };
    const wrap = el('div', { class: 'set-cond-edit' });
    const typeSel = el('select', { class: 'set-text' });
    [['karel_pos', 'Poloha Karla'], ['cell_state', 'Stav políčka'], ['sign', 'Značka pod Karlom'],
     ['brick_ahead', 'Tehla pred Karlom'], ['wall_ahead', 'Stena pred Karlom'], ['snapshot', 'Snímok miestnosti']]
      .forEach(([v, d]) => { const o = el('option', { value: v, text: T('goal_condition.type_' + v, d) }); if (c.check === v) o.selected = true; typeSel.appendChild(o); });
    const params = el('div', {});
    function optNum(label, val) {
      const chk = el('input', { type: 'checkbox' }); chk.checked = val != null;
      const n = num(val != null ? val : 0, 0); n.disabled = !chk.checked;
      chk.onchange = () => n.disabled = !chk.checked;
      const row = el('label', { class: 'set-row' }, [el('span', { class: 'set-lbl' }, [chk, el('span', { text: ' ' + label })]), n]);
      row._get = () => chk.checked ? (parseInt(n.value, 10) || 0) : null;
      return row;
    }
    function rebuild() {
      params.innerHTML = '';
      const tp = typeSel.value;
      if (tp === 'karel_pos') {
        params._x = optNum('X', c.x); params._y = optNum('Y', c.y); params._z = optNum(T('goal_condition.kp_height', 'výška'), c.z);
        [params._x, params._y, params._z].forEach(r => params.appendChild(r));
      } else if (tp === 'cell_state') {
        params._x = optNum('X', c.x); params._y = optNum('Y', c.y);
        params._mk = optNum(T('goal_condition.cs_mark', 'značka(1/0)'), c.cell_marks != null ? (c.cell_marks ? 1 : 0) : null);
        params._br = optNum(T('goal_condition.cs_bricks', 'malé tehly'), c.cell_bricks);
        params._bb = optNum(T('goal_condition.cs_big_bricks', 'veľké tehly'), c.cell_big_bricks);
        [params._x, params._y, params._mk, params._br, params._bb].forEach(r => params.appendChild(r));
      } else if (tp === 'snapshot') {
        params.appendChild(el('div', { class: 'set-note', text: T('goal_condition.snap_note', 'Zachytí aktuálny stav miestnosti.') }));
      } else {
        params.appendChild(el('div', { class: 'set-note', text: T('goal_condition.type_' + tp + '_desc', 'Bez parametrov.') }));
      }
    }
    typeSel.onchange = rebuild; rebuild();

    const evalSel = el('select', { class: 'set-text' });
    [['success', 'úspech ✓'], ['failure', 'neúspech ✗']].forEach(([v, d]) => { const o = el('option', { value: v, text: T('goal_condition.eval_' + v, d) }); if (c.eval === v) o.selected = true; evalSel.appendChild(o); });
    const whenSel = el('select', { class: 'set-text' });
    [['on_finish', 'po skončení'], ['on_step', 'po každom kroku']].forEach(([v, d]) => { const o = el('option', { value: v, text: T('goal_condition.when_' + v.replace('on_', ''), d) }); if (c.when === v) o.selected = true; whenSel.appendChild(o); });
    const opSel = el('select', { class: 'set-text' });
    [['or', 'OR'], ['and', 'AND']].forEach(([v, d]) => { const o = el('option', { value: v, text: d }); if (c.op === v) o.selected = true; opSel.appendChild(o); });
    const neg = el('input', { type: 'checkbox' }); neg.checked = !!c.negate;

    wrap.appendChild(field('goal_condition.type_label', 'Typ podmienky:', typeSel));
    wrap.appendChild(params);
    wrap.appendChild(field('goal_condition.lbl_eval', 'Výsledok:', evalSel));
    wrap.appendChild(field('goal_condition.lbl_when', 'Kedy:', whenSel));
    wrap.appendChild(field('goal_condition.lbl_op', 'Operátor:', opSel));
    wrap.appendChild(el('label', { class: 'inline set-row' }, [neg, el('span', { text: ' ' + T('goal_condition.lbl_negate', 'Negácia (NOT)') })]));

    miniDialog(existing ? T('goal_condition.title_edit', 'Upraviť podmienku') : T('goal_condition.title', 'Pridať podmienku'),
      wrap, () => {
        const tp = typeSel.value;
        const out = { check: tp, eval: evalSel.value, when: whenSel.value, op: opSel.value, negate: neg.checked };
        if (tp === 'karel_pos') { out.x = params._x._get(); out.y = params._y._get(); out.z = params._z._get(); }
        else if (tp === 'cell_state') {
          out.x = params._x._get(); out.y = params._y._get();
          const mk = params._mk._get(); out.cell_marks = mk == null ? null : !!mk;
          out.cell_bricks = params._br._get(); out.cell_big_bricks = params._bb._get();
        } else if (tp === 'snapshot') {
          out.snap = snapshotFromState();
        }
        done(out);
      });
  }

  // snímok aktuálnej miestnosti zo sparse state → 2D polia (formát core)
  function snapshotFromState() {
    const w = st.width, h = st.height;
    const z = (fill) => Array.from({ length: h }, () => Array.from({ length: w }, () => fill));
    const br = z(0), bb = z(0), mk = z(false);
    (st.bricks || []).forEach(([x, y, c]) => br[y][x] = c);
    (st.big_bricks || []).forEach(([x, y]) => bb[y][x] = 1);
    (st.marks || []).forEach(([x, y]) => mk[y][x] = true);
    return { bricks: br, big_bricks: bb, marks: mk,
             karel_x: st.karel.x, karel_y: st.karel.y, karel_dir: st.karel.dir };
  }

  /* mini-dialóg (re-použije malý #overlay/#dialog z app — ale aby sme sa nebili,
   * spravíme vlastný jednoduchý overlay nad settings dialógom) */
  function miniDialog(title, contentEl, onOk) {
    const ov = el('div', { class: 'mini-overlay' });
    const dlg = el('div', { class: 'mini-dialog' }, [
      el('h4', { text: title }), contentEl,
      el('div', { class: 'set-btnrow' }, [
        (() => { const b = el('button', { text: T('goal_condition.btn_cancel', 'Zrušiť') }); b.onclick = () => ov.remove(); return b; })(),
        (() => { const b = el('button', { class: 'accent', text: 'OK' }); b.onclick = () => { onOk(); ov.remove(); }; return b; })(),
      ]),
    ]);
    ov.appendChild(dlg);
    $('settings-overlay').appendChild(ov);
  }

  /* ---------- verejné API ---------- */
  function open(opts) {
    T = opts.t || T;
    st = opts.state;
    onApplyCb = opts.onApply;
    progLangs = opts.progLangs || [];
    if (!st) return;
    buildTabs();
    $('settings-overlay').classList.remove('hidden');
  }
  function close() { $('settings-overlay').classList.add('hidden'); }

  function collect() {
    const room = get.room(), inv = get.inv(), cmds = get.cmds(), view = get.view(), mis = get.mission();
    return {
      settings: Object.assign({}, {
        prog_lang: room.prog_lang,
        max_climb: room.max_climb, max_drop: room.max_drop, max_steps: room.max_steps,
        max_turns: room.max_turns, max_brick_height: room.max_brick_height,
        brick_limit: inv.brick_limit, big_brick_limit: inv.big_brick_limit, mark_limit: inv.mark_limit,
        disabled_cmds: cmds.disabled_cmds, disable_procedure: cmds.disable_procedure,
        disable_graphic: cmds.disable_graphic, disable_command: cmds.disable_command,
        camera_locked: view.camera_locked, camera: view.camera,
        width: room.width, height: room.height,
      }),
      karel: room.karel,
      title: get.title(), intro_html: get.intro(),
      success_html: mis.success_html, failure_html: mis.failure_html,
      reset_on_failure: mis.reset_on_failure,
      goal_conditions: mis.goal_conditions,
    };
  }

  // wiring tlačidiel dialógu (raz)
  document.addEventListener('DOMContentLoaded', () => {});
  function wire() {
    $('set-cancel').onclick = close;
    $('set-apply').onclick = () => { if (onApplyCb) onApplyCb(collect()); close(); };
  }

  return { open, close, wire };
})();
