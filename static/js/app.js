/* Karel 2030 — hlavná logika frontendu.
 * Módy: učiteľ (default, /) vs žiak (/s/{token} alebo ?token=...).
 * ?mock=1 → MockApi/MockWS namiesto reálneho backendu.
 */
'use strict';

(function () {
  const qs = new URLSearchParams(location.search);
  const MOCK = qs.get('mock') === '1';
  const pathTok = location.pathname.match(/^\/s\/([A-Za-z0-9_-]+)/);
  const TOKEN = (pathTok && pathTok[1]) || qs.get('token') || null;
  const STUDENT = !!TOKEN;
  const ADMIN = !STUDENT && qs.get('role') === 'admin';   // dev: rola cez URL

  const api = MOCK ? MockApi : Api;
  const $ = (id) => document.getElementById(id);

  let T = {};                       // ui preklady
  const t = (k, dflt) => T[k] || dflt || k;
  let primaryKw = {};               // TOKEN → primárne slovo
  let state = null;                 // posledný state JSON
  let running = false;

  /* ---------- i18n ---------- */
  function applyI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const v = T[el.dataset.i18n];
      if (v) el.textContent = v;
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const v = T[el.dataset.i18nPh];
      if (v) el.placeholder = v;
    });
  }

  /* ---------- dialógy ---------- */
  function dialog(title, bodyHtml, buttons, failure) {
    $('dlg-title').textContent = title;
    $('dlg-body').innerHTML = bodyHtml;
    $('dialog').classList.toggle('failure', !!failure);
    const bb = $('dlg-buttons');
    bb.innerHTML = '';
    (buttons || [{ label: 'OK' }]).forEach(b => {
      const btn = document.createElement('button');
      btn.textContent = b.label;
      btn.onclick = () => { hideDialog(); if (b.action) b.action(); };
      bb.appendChild(btn);
    });
    $('overlay').classList.remove('hidden');
  }
  function hideDialog() { $('overlay').classList.add('hidden'); }
  $('overlay').addEventListener('click', (e) => { if (e.target.id === 'overlay') hideDialog(); });

  /* ---------- status ---------- */
  function setStatus(key, dflt) { $('status').textContent = t(key, dflt); }
  function setRunning(r) {
    running = r;
    $('btn-run').disabled = r;
    $('btn-stop').disabled = !r;
  }

  /* ---------- navigátor / inventár ---------- */
  function fmtInv(v) { return v === -1 || v == null ? '∞' : String(v); }
  function updateNav(st) {
    const inv = st.inventory || {};
    $('inv-bricks').textContent = fmtInv(inv.bricks);
    $('inv-big').textContent = fmtInv(inv.big_bricks);
    $('inv-marks').textContent = fmtInv(inv.marks);
    const s = st.settings || {}, c = st.counters || {};
    const show = (row, cell, max, used) => {
      const on = max != null && max !== -1;
      $(row).classList.toggle('hidden', !on);
      if (on) $(cell).textContent = (max - (used || 0)) + ' / ' + max;
    };
    show('row-steps', 'inv-steps', s.max_steps, c.steps_used);
    show('row-turns', 'inv-turns', s.max_turns, c.turns_used);
    $('karel-pos').textContent =
      `Karel: (${st.karel.x}, ${st.karel.y}) ${st.karel.dir}`;
  }

  /* ---------- zoznam príkazov (zoskupený filter strom) ---------- */
  let _lastLang = null;
  function updateCmdsList(lang) {
    if (lang) _lastLang = lang;
    lang = _lastLang;
    if (!lang) return;
    const cont = $('cmds-groups');
    cont.innerHTML = '';
    const filter = ($('cmds-filter').value || '').toLowerCase();
    const disabled = new Set([...(lang.disabled || []),
                              ...((state && state.settings && state.settings.disabled_cmds) || [])]);
    const groups = [
      { key: 'program_panel.filter_mov', dflt: '🚶 Pohyb',
        toks: ['FORWARD', 'BACK', 'LEFT', 'RIGHT', 'DROP', 'PICK', 'DROP_BIG', 'MARK', 'CLEAR', 'SLOWLY', 'QUICKLY'], cls: '' },
      { key: 'program_panel.filter_str', dflt: '🔀 Štruktúry',
        toks: ['REPEAT', 'WHILE', 'IF', 'PROCEDURE'], cls: 'struct' },
      { key: 'program_panel.filter_cnd', dflt: '❓ Podmienky',
        toks: ['WALL', 'BRICK', 'FREE', 'SIGN', 'NOT', 'AND', 'OR', 'TRUE', 'FALSE'], cls: 'cond' },
    ];
    const addItem = (parent, word, cls) => {
      if (filter && word.toLowerCase().indexOf(filter) === -1) return false;
      const d = document.createElement('div');
      d.textContent = word; d.className = 'cmd-item ' + cls;
      d.onclick = () => editor.insert(word + ' ');
      parent.appendChild(d); return true;
    };
    groups.forEach(g => {
      const words = g.toks.filter(tk => !disabled.has(tk)).map(tk => lang.primary[tk]).filter(Boolean);
      const items = document.createDocumentFragment();
      let any = false;
      words.forEach(w => { if (addItem(items, w, g.cls)) any = true; });
      if (any) {
        const h = document.createElement('div');
        h.className = 'cmd-group-hdr'; h.textContent = t(g.key, g.dflt);
        cont.appendChild(h); cont.appendChild(items);
      }
    });
    // Moje príkazy — procedúry definované v editore (prikaz/procedure <meno>)
    const procWord = (lang.primary.PROCEDURE || 'prikaz');
    const re = new RegExp('(?:' + procWord + '|prikaz|procedure)\\s+([\\p{L}_][\\p{L}\\p{N}_]*)', 'giu');
    const src = editor.getValue(); const seen = new Set(); const procs = [];
    let mm; while ((mm = re.exec(src))) { const n = mm[1]; if (!seen.has(n)) { seen.add(n); procs.push(n); } }
    if (procs.length) {
      const items = document.createDocumentFragment(); let any = false;
      procs.forEach(n => { if (addItem(items, n, 'proc')) any = true; });
      if (any) {
        const h = document.createElement('div');
        h.className = 'cmd-group-hdr'; h.textContent = t('program_panel.filter_usr', '⭐ Moje príkazy');
        cont.appendChild(h); cont.appendChild(items);
      }
    }
  }

  /* ---------- obmedzenia tlačidiel ---------- */
  function applyRestrictions(st) {
    const dis = new Set((st.settings && st.settings.disabled_cmds) || []);
    document.querySelectorAll('[data-cmd]').forEach(b => {
      b.disabled = dis.has(b.dataset.cmd);
    });
  }

  /* ---------- speed slider → delay (0.02–3.0 s, logaritmicky) ---------- */
  function sliderToDelay(v) {
    // v=0 → 3.0 s (pomaly), v=100 → 0.02 s (rýchlo)
    return +(3.0 * Math.pow(0.02 / 3.0, v / 100)).toFixed(3);
  }

  /* ---------- inicializácia ---------- */
  const renderer = new KarelRenderer($('scene'));
  const editor = new KarelEditor($('code'));
  let ws;

  function onState(st, reason) {
    state = st;
    renderer.render(st);
    updateNav(st);
    applyRestrictions(st);
    // presety pohľadu vypnuté pri zamknutej kamere
    const camLocked = !!(st.settings && st.settings.camera_locked);
    document.querySelectorAll('.view-btn').forEach(b => { b.disabled = camLocked; });
    $('world-title').textContent = (st.meta && st.meta.title) || '';
    // po apply_settings (reason 'requested') premietni zakázané príkazy do editora aj zoznamu
    if (reason === 'requested' && st.settings) {
      editor.setDisabledCmds(st.settings.disabled_cmds || []);
      updateCmdsList();
    }
    if (reason === 'connect' || reason === 'load') {
      // prog jazyk sveta → editor + zoznam príkazov
      const code = (st.settings && st.settings.prog_lang) || 'sk';
      api.progLang(code).then(lang => {
        primaryKw = lang.primary || {};
        editor.setLang(lang);
        editor.setDisabledCmds((st.settings && st.settings.disabled_cmds) || []);
        updateCmdsList(lang);
      }).catch(() => {});
      // intro dialóg pri prvom pripojení
      if (reason === 'connect' && st.meta && st.meta.intro_html) {
        dialog(t('toolbar.task', 'Zadanie'), st.meta.intro_html);
      }
      // program zo sveta (učiteľ) — žiakovi ho prepíše workspace nižšie
      if (!STUDENT && st.program_text && !editor.getValue()) {
        editor.setValue(st.program_text);
      }
    }
  }

  function wireWs() {
    ws.on('_open', () => $('conn-dot').classList.add('on'));
    ws.on('_close', () => { $('conn-dot').classList.remove('on'); setRunning(false); });

    ws.on('state', m => onState(m.state, m.reason));
    ws.on('step', m => { state = m.state; renderer.render(m.state); updateNav(m.state); });

    ws.on('started', () => { setRunning(true); setStatus('status.running', 'Beží...'); });
    ws.on('finished', m => {
      setRunning(false);
      setStatus(m.status === 'done' ? 'status.done' : 'status.stopped',
                m.status === 'done' ? 'Hotovo! ✓' : 'Zastavené.');
    });
    ws.on('parse_error', m => {
      setRunning(false);
      dialog(t('limit.title', 'Chyba programu'),
        `<p>${m.message}</p><p style="color:var(--fg-dim)">Riadok: ${m.line}</p>`, null, true);
    });
    ws.on('error', m => {
      setRunning(false);
      dialog(t('goal_condition.err_title', 'Chyba'), `<p>${m.message}</p>`, null, true);
    });
    ws.on('budget', m => {
      setRunning(false);
      dialog(t('budget.title', 'Rozpočet pohybu'),
        '<p>' + t('budget.msg_' + m.kind, 'Rozpočet vyčerpaný!').replace(/\\n/g, '<br>') + '</p>',
        [{ label: 'OK' }, { label: t('budget.reset', 'Reset'), action: () => ws.reset() }], true);
    });
    ws.on('limit', m => {
      setRunning(false);
      dialog(t('limit.title', 'Program zastavený'),
        '<p>' + t('limit.msg_' + m.kind, 'Bezpečnostný limit prekročený.').replace(/\\n/g, '<br>') + '</p>',
        null, true);
    });
    ws.on('mission', m => {
      const ok = m.result === 'success';
      dialog(ok ? '✓ ' + t('goal_condition.eval_success', 'Úspech') : '✗ ' + t('goal_condition.eval_failure', 'Neúspech'),
        m.message_html || '', null, !ok);
    });
    ws.on('direct_result', m => {
      if (cmdMode) { if (!m.ok) logCmd(m.error || 'nevykonané', 'err'); return; }
      if (!m.ok && m.error) dialog(t('goal_condition.err_title', 'Chyba'), `<p>${m.error}</p>`, null, true);
    });
    ws.on('world_export', m => { if (_pendingExport) { _pendingExport(m.karxml); _pendingExport = null; } });

    ws.connect();
  }

  /* ---------- toolbar ---------- */
  $('btn-run').onclick = () => ws.run(editor.getValue());
  $('btn-stop').onclick = () => ws.stop();
  $('btn-reset').onclick = () => { ws.reset(); setStatus('status.reset_done', 'Reset.'); };
  $('btn-task').onclick = () => {
    const html = (state && state.meta && state.meta.intro_html) || '';
    dialog(t('toolbar.task', 'Zadanie'), html || t('status.no_task', 'Tento svet nemá žiadne zadanie.'));
  };
  $('speed').oninput = (e) => ws.speed(sliderToDelay(+e.target.value));

  /* priame ovládanie — posiela primárne slovo aliasu (kontrakt: direct cmd = slovo) */
  document.querySelectorAll('[data-cmd]').forEach(b => {
    b.addEventListener('click', () => {
      const word = primaryKw[b.dataset.cmd] || b.title;
      if (word) ws.direct(word);
    });
  });

  /* A. Tlačidlá pohľadu kamery */
  document.querySelectorAll('.view-btn').forEach(b => {
    b.addEventListener('click', () => renderer.setViewPreset(+b.dataset.az, +b.dataset.el));
  });

  /* B. Taby ovládania (Graficky / Príkazovo) */
  let cmdMode = false;
  document.querySelectorAll('.ctl-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.ctl-tab').forEach(x => x.classList.toggle('active', x === tab));
      cmdMode = tab.dataset.tab === 'command';
      $('tab-graphic').classList.toggle('hidden', cmdMode);
      $('tab-command').classList.toggle('hidden', !cmdMode);
      if (cmdMode) $('cmd-input').focus();
    });
  });
  function logCmd(text, cls) {
    const d = document.createElement('div');
    if (cls) d.className = cls;
    d.textContent = text;
    $('cmd-log').appendChild(d);
    $('cmd-log').scrollTop = $('cmd-log').scrollHeight;
  }
  $('cmd-input').addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const word = e.target.value.trim();
    if (!word) return;
    e.target.value = '';
    logCmd('> ' + word, 'in');
    ws.direct(word.split(/\s+/)[0]);   // priamy príkaz = jedno slovo (kontrakt)
  });

  /* C. Filter príkazov + refresh „Moje príkazy" pri zmene editora */
  $('cmds-filter').addEventListener('input', () => updateCmdsList());
  editor.cm.on('changes', () => updateCmdsList());

  /* D+E. Nastavenia sveta (učiteľ) */
  KarelSettings.wire();
  $('btn-settings').onclick = () => {
    if (!state) return;
    KarelSettings.open({ state, t, onApply: (payload) => ws.applySettings(payload) });
  };

  /* F. Otvoriť/Uložiť svet a program ----------------------------------- */
  let _pendingExport = null;   // callback(karxml) po world_export správe
  function download(name, text, mime) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: mime || 'text/plain' }));
    a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function readFile(input, cb) {
    const f = input.files && input.files[0]; if (!f) return;
    const r = new FileReader(); r.onload = () => cb(r.result, f.name); r.readAsText(f);
    input.value = '';
  }
  // F3: dropdown predvyrobených svetov
  function loadWorldsDropdown() {
    if (STUDENT) return;
    api.worlds().then(ws_ => {
      const sel = $('worlds');
      sel.innerHTML = '<option value="">—</option>';
      ws_.forEach(w => { const o = document.createElement('option'); o.value = w.id; o.textContent = w.title; sel.appendChild(o); });
      sel.onchange = () => { if (sel.value) ws.loadWorld({ world_id: sel.value }); };
    }).catch(() => {});
  }
  // F1: otvoriť svet zo súboru
  $('btn-world-open').onclick = () => $('file-world').click();
  $('file-world').onchange = (e) => readFile(e.target, (txt) => ws.loadWorld({ karxml: txt }));
  // F1: uložiť svet do súboru (cez export_world)
  $('btn-world-save').onclick = () => {
    _pendingExport = (karxml) => download((state.meta.title || 'svet') + '.karxml', karxml, 'application/xml');
    ws.exportWorld(editor.getValue());
  };
  // F2: publikovať svet (admin) do volume
  $('btn-world-pub').onclick = () => {
    const id = prompt(t('world_settings.frame_title', 'Názov sveta') + ' (id):', state.meta.title || 'svet');
    if (!id) return;
    _pendingExport = (karxml) => api.publishWorld(id, karxml)
      .then(() => { loadWorldsDropdown(); setStatus(null, 'Publikované: ' + id); })
      .catch(err => dialog(t('goal_condition.err_title', 'Chyba'), '<p>' + (err.detail || err.error || 'chyba') + '</p>', null, true));
    ws.exportWorld(editor.getValue());
  };
  // F4: otvoriť/uložiť program
  $('btn-prog-open').onclick = () => $('file-prog').click();
  $('file-prog').onchange = (e) => readFile(e.target, (txt) => editor.setValue(txt));
  $('btn-prog-save').onclick = () => download('program.karel', editor.getValue(), 'text/plain');

  /* CodeMirror potrebuje refresh po zmene veľkosti okna (inak sa neprekreslí) */
  let _rfTimer;
  window.addEventListener('resize', () => {
    clearTimeout(_rfTimer);
    _rfTimer = setTimeout(() => editor.refresh(), 150);
  });

  /* príklady */
  function loadExamples() {
    api.examples().then(exs => {
      const sel = $('examples');
      sel.innerHTML = '<option value="">—</option>';
      exs.forEach((ex, i) => {
        const o = document.createElement('option');
        o.value = i; o.textContent = ex.name;
        sel.appendChild(o);
      });
      sel.onchange = () => {
        if (sel.value !== '') editor.setValue(exs[+sel.value].program);
      };
    }).catch(() => $('examples-wrap').classList.add('hidden'));
  }

  /* ---------- štart ---------- */
  async function boot() {
    // UI preklady
    try {
      T = await api.uiStrings('sk');
      applyI18n();
    } catch (e) { /* HTML defaulty sú slovenské */ }

    if (STUDENT) {
      document.body.classList.add('student');     // žiak: bez nastavení (server vynucuje)
      ws = MOCK ? new MockWS() : new KarelWS({ token: TOKEN });
      wireWs();
      // workspace: program žiaka + auto-save
      try {
        const wsp = await api.workspace(TOKEN);
        if (wsp.program_text) editor.setValue(wsp.program_text);
        editor.onAutoSave(text => api.saveWorkspace(TOKEN, text).catch(() => {}));
      } catch (e) {
        dialog(t('goal_condition.err_title', 'Chyba'),
          '<p>Neplatný alebo expirovaný žiacky link.</p>', null, true);
      }
    } else {
      if (ADMIN) document.body.classList.add('admin');
      loadWorldsDropdown();
      // učiteľ: vlastná session — session_id generuje frontend (viď NOTES.md)
      let sid = sessionStorage.getItem('karel_session');
      if (!sid) {
        sid = Math.random().toString(36).slice(2, 14);
        sessionStorage.setItem('karel_session', sid);
      }
      ws = MOCK ? new MockWS() : new KarelWS({ sessionId: sid });
      wireWs();
    }

    loadExamples();
    ws.speed(sliderToDelay(+$('speed').value));
    setTimeout(() => editor.refresh(), 100);
  }

  boot();
})();
