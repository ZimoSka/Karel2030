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
  let uiLang = localStorage.getItem('karel_ui_lang') || 'sk';
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
  // staré .karxml môžu mať dvojito-escapovaný HTML — rozbalíme pre čitateľné zobrazenie
  function htmlReadable(s) {
    s = s || '';
    if (/&(amp|lt|gt|quot);/.test(s) && !/<[a-z]/i.test(s)) {
      const d = document.createElement('textarea'); d.innerHTML = s; return d.value;
    }
    return s;
  }
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
    const p = lang.primary;
    // U2: celé šablóny štruktúr — vlož viacriadkový úryvok, nielen kľúčové slovo
    const kw = (tk, dflt) => p[tk] || dflt;
    const structTemplates = [];
    if (!disabled.has('REPEAT'))
      structTemplates.push({ label: `${kw('REPEAT','opakuj')} 3 ${kw('TIMES','krat')} … ${kw('END','koniec')}`,
        snippet: `${kw('REPEAT','opakuj')} 3 ${kw('TIMES','krat')}\n  \n${kw('END','koniec')}\n` });
    if (!disabled.has('WHILE'))
      structTemplates.push({ label: `${kw('WHILE','kym')} … ${kw('DO','rob')} … ${kw('END','koniec')}`,
        snippet: `${kw('WHILE','kym')} ${kw('NOT','nie')} ${kw('WALL','stena')} ${kw('DO','rob')}\n  \n${kw('END','koniec')}\n` });
    structTemplates.push({ label: `${kw('IF','ak')} … ${kw('THEN','potom')} … ${kw('END','koniec')}`,
      snippet: `${kw('IF','ak')} ${kw('WALL','stena')} ${kw('THEN','potom')}\n  \n${kw('END','koniec')}\n` });
    structTemplates.push({ label: `${kw('IF','ak')} … ${kw('THEN','potom')} … ${kw('ELSE','inak')} … ${kw('END','koniec')}`,
      snippet: `${kw('IF','ak')} ${kw('WALL','stena')} ${kw('THEN','potom')}\n  \n${kw('ELSE','inak')}\n  \n${kw('END','koniec')}\n` });
    if (!disabled.has('PROCEDURE') && !(state && state.settings && state.settings.disable_procedure))
      structTemplates.push({ label: `${kw('PROCEDURE','prikaz')} Meno … ${kw('END','koniec')}`,
        snippet: `${kw('PROCEDURE','prikaz')} Meno\n  \n${kw('END','koniec')}\n` });

    const groups = [
      { key: 'program_panel.filter_mov', dflt: '🚶 Pohyb',
        toks: ['FORWARD', 'BACK', 'LEFT', 'RIGHT', 'DROP', 'PICK', 'DROP_BIG', 'MARK', 'CLEAR', 'SLOWLY', 'QUICKLY'], cls: '' },
      { key: 'program_panel.filter_str', dflt: '🔀 Štruktúry', templates: structTemplates, cls: 'struct' },
      { key: 'program_panel.filter_cnd', dflt: '❓ Podmienky',
        toks: ['WALL', 'BRICK', 'FREE', 'SIGN', 'NOT', 'AND', 'OR', 'TRUE', 'FALSE'], cls: 'cond' },
    ];
    const addItem = (parent, word, cls, snippet) => {
      if (filter && word.toLowerCase().indexOf(filter) === -1) return false;
      const d = document.createElement('div');
      d.textContent = word; d.className = 'cmd-item ' + cls;
      d.onclick = () => editor.insert(snippet != null ? snippet : word + ' ');
      parent.appendChild(d); return true;
    };
    groups.forEach(g => {
      const items = document.createDocumentFragment();
      let any = false;
      if (g.templates) {
        g.templates.forEach(tpl => { if (addItem(items, tpl.label, g.cls, tpl.snippet)) any = true; });
      } else {
        g.toks.filter(tk => !disabled.has(tk)).map(tk => p[tk]).filter(Boolean)
          .forEach(w => { if (addItem(items, w, g.cls)) any = true; });
      }
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

  /* efektívne zakázané = svet (disabled_cmds) ∪ jazyk (napr. Pattis DISABLED) */
  function effectiveDisabled(st) {
    return new Set([
      ...((st && st.settings && st.settings.disabled_cmds) || []),
      ...((_lastLang && _lastLang.disabled) || []),
    ]);
  }

  /* ---------- obmedzenia tlačidiel ---------- */
  function applyRestrictions(st) {
    const dis = effectiveDisabled(st);
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

  let _curProgLang = null;          // posledný načítaný prog jazyk editora
  function reloadProgLang(code, disabled) {
    if (code === _curProgLang) { editor.setDisabledCmds(disabled || []); updateCmdsList(); return; }
    _curProgLang = code;
    api.progLang(code).then(lang => {
      primaryKw = lang.primary || {};
      editor.setLang(lang);
      editor.setDisabledCmds(disabled || []);
      updateCmdsList(lang);
      rebuildActionTitles();
      applyRestrictions(state);   // jazykové obmedzenia (Pattis) → sivé tlačidlá
    }).catch(() => {});
  }

  function onState(st, reason) {
    // zlúč s predošlým (full state vždy obsahuje settings/mission, takže ich obnoví)
    state = Object.assign({}, state, st);
    st = state;
    renderer.render(st);
    updateNav(st);
    applyRestrictions(st);
    // presety pohľadu vypnuté pri zamknutej kamere
    const camLocked = !!(st.settings && st.settings.camera_locked);
    document.querySelectorAll('.view-btn').forEach(b => { b.disabled = camLocked; });
    $('world-title').textContent = (st.meta && st.meta.title) || '';
    // prog jazyk sveta → editor + zoznam (prelaď len ak sa zmenil)
    if (st.settings) {
      reloadProgLang(st.settings.prog_lang || 'sk', st.settings.disabled_cmds || []);
    }
    if (reason === 'connect' || reason === 'load') {
      // zadanie sa zobrazí pri pripojení AJ pri načítaní sveta z dropdownu (bug fix)
      if (st.meta && st.meta.intro_html) {
        dialog(t("toolbar.task","Zadanie"), htmlReadable(st.meta.intro_html));
      }
      // program zo sveta (učiteľ) — žiakovi ho prepíše workspace nižšie
      if (!STUDENT) {
        editor.setValue(st.program_text || defaultProgram());
      }
    }
  }

  // U1: default program — štruktúra zaciatok…koniec + úvodný komentár
  function defaultProgram() {
    const p = primaryKw;
    const b = p.BEGIN || 'zaciatok', e = p.END || 'koniec';
    return `# Karel 2030 — napíš svoj program medzi ${b} a ${e}\n` +
           `# Príkazy: ${p.FORWARD||'dopredu'}, ${p.LEFT||'vlavo'}, ${p.RIGHT||'vpravo'}, ${p.DROP||'poloz'}, ${p.PICK||'zdvihni'}\n` +
           `${b}\n  \n${e}\n`;
  }

  function wireWs() {
    ws.on('_open', () => $('conn-dot').classList.add('on'));
    ws.on('_close', () => { $('conn-dot').classList.remove('on'); setRunning(false); });

    ws.on('state', m => onState(m.state, m.reason));
    // step správy neposielajú settings/mission (full=False) — zlúčime, aby ostali
    // zachované (inak by sa po pohybe nedali otvoriť Nastavenia, B2)
    ws.on('step', m => {
      state = Object.assign({}, state, m.state);
      renderer.render(state); updateNav(state);
    });

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
        htmlReadable(m.message_html) || '', null, !ok);
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
    const html = htmlReadable((state && state.meta && state.meta.intro_html) || '');
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
  let _progLangsList = [];
  api.progLangs().then(ls => { _progLangsList = ls; }).catch(() => {});
  $('btn-settings').onclick = () => {
    if (!state) return;
    KarelSettings.open({ state, t, progLangs: _progLangsList, onApply: (payload) => ws.applySettings(payload) });
  };

  /* G. Prepínač jazyka (UI + prog) ------------------------------------- */
  function fillSelect(sel, items, current) {
    sel.innerHTML = '';
    items.forEach(it => { const o = document.createElement('option'); o.value = it.code; o.textContent = it.name; if (it.code === current) o.selected = true; sel.appendChild(o); });
  }
  function loadLangDropdowns() {
    api.uiLangs().then(ls => {
      fillSelect($('ui-lang'), ls, uiLang);
      $('ui-lang').onchange = (e) => {
        uiLang = e.target.value; localStorage.setItem('karel_ui_lang', uiLang);
        api.uiStrings(uiLang).then(s => { T = s; applyI18n(); updateCmdsList(); }).catch(() => {});
      };
    }).catch(() => {});
  }
  // tlačidlá priameho ovládania majú title = primárne slovo (pre ws.direct)
  function rebuildActionTitles() {
    document.querySelectorAll('#dpad [data-cmd]').forEach(b => {
      const w = primaryKw[b.dataset.cmd]; if (w) b.title = w;
    });
  }

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
  let _curWorldId = null;     // id práve načítaného/publikovaného sveta (pre overwrite)
  // F3: dropdown predvyrobených svetov
  function loadWorldsDropdown(selectId) {
    if (STUDENT) return;
    api.worlds().then(ws_ => {
      const sel = $('worlds');
      sel.innerHTML = '<option value="">—</option>';
      ws_.forEach(w => { const o = document.createElement('option'); o.value = w.id; o.textContent = w.title; sel.appendChild(o); });
      if (selectId) sel.value = selectId;
      sel.onchange = () => { if (sel.value) { _curWorldId = sel.value; ws.loadWorld({ world_id: sel.value }); } };
    }).catch(() => {});
  }
  // F1: otvoriť svet zo súboru
  $('btn-world-open').onclick = () => $('file-world').click();
  $('file-world').onchange = (e) => readFile(e.target, (txt) => { _curWorldId = null; ws.loadWorld({ karxml: txt }); });
  // F1: uložiť svet do súboru (cez export_world)
  $('btn-world-save').onclick = () => {
    _pendingExport = (karxml) => download((state.meta.title || 'svet') + '.karxml', karxml, 'application/xml');
    ws.exportWorld(editor.getValue());
  };
  // F2: publikovať / uložiť zdieľaný svet (admin) do volume.
  // Default id = práve editovaný svet → uloženie prepíše (= editovanie zdieľaného sveta).
  $('btn-world-pub').onclick = () => {
    const id = prompt('Uložiť zdieľaný svet pod menom (existujúce meno = prepíše):',
                      _curWorldId || state.meta.title || 'svet');
    if (!id) return;
    _pendingExport = (karxml) => api.publishWorld(id, karxml)
      .then(() => { _curWorldId = id; loadWorldsDropdown(id); setStatus(null, '✓ Uložené: ' + id); })
      .catch(err => dialog(t('goal_condition.err_title', 'Chyba'), '<p>' + (err.detail || err.error || 'chyba') + '</p>', null, true));
    ws.exportWorld(editor.getValue());
  };
  // F-admin: zmazať vybraný publikovaný svet
  $('btn-world-del').onclick = () => {
    const id = $('worlds').value;
    if (!id) { dialog(t('goal_condition.err_title', 'Chyba'), '<p>Vyber svet z dropdownu „Svety".</p>', null, true); return; }
    dialog(t('world_settings.title', 'Nastavenia'), `<p>Zmazať publikovaný svet <b>${id}</b>?</p>`,
      [{ label: t('world_settings.btn_cancel', 'Zrušiť') },
       { label: 'Zmazať', action: () => api.deleteWorld(id)
           .then(() => loadWorldsDropdown())
           .catch(err => dialog(t('goal_condition.err_title', 'Chyba'), '<p>' + (err.message || 'chyba') + '</p>', null, true)) }]);
  };
  // F4: otvoriť/uložiť program
  $('btn-prog-open').onclick = () => $('file-prog').click();
  $('file-prog').onchange = (e) => readFile(e.target, (txt) => editor.setValue(txt));
  $('btn-prog-save').onclick = () => download('program.karel', editor.getValue(), 'text/plain');

  /* ---------- Zdieľanie žiakom (assignment + linky) ---------- */
  $('btn-share').onclick = () => {
    if (!state) return;
    dialog('👥 Zdieľaj žiakom',
      '<p>Zadaj <b>mená žiakov</b> (jeden na riadok) — pre každého vznikne vlastný link:</p>' +
      '<textarea id="share-names" rows="6" style="width:100%;background:var(--bg-dark);color:var(--fg);border:1px solid var(--border);border-radius:6px;padding:6px;font:13px Consolas,monospace" placeholder="Janko\nEva\nPeter"></textarea>' +
      '<p style="color:var(--fg-dim)">…alebo počet anonymných linkov: ' +
      '<input id="share-count" type="number" min="0" value="0" style="width:70px;background:var(--bg-dark);color:var(--fg);border:1px solid var(--border);border-radius:4px;padding:3px"></p>',
      [{ label: t('world_settings.btn_cancel', 'Zrušiť') },
       { label: '🔗 Vytvoriť linky', action: doShare }]);
  };
  function doShare() {
    const namesRaw = ($('share-names') && $('share-names').value || '').trim();
    const count = parseInt($('share-count') && $('share-count').value, 10) || 0;
    const names = namesRaw ? namesRaw.split('\n').map(s => s.trim()).filter(Boolean) : null;
    if (!names && count <= 0) { dialog('👥 Zdieľaj žiakom', '<p>Zadaj aspoň jedno meno alebo počet linkov.</p>'); return; }
    setStatus(null, 'Vytváram linky…');
    // export aktuálneho sveta (karxml) → assignment → share → zobraz linky
    _pendingExport = (karxml) => {
      api.createAssignment(karxml, (state.meta && state.meta.title) || 'Úloha')
        .then(r => api.share(r.assignment_id, names ? { names } : { count }))
        .then(res => showLinks(res.links))
        .catch(err => dialog(t('goal_condition.err_title', 'Chyba'), '<p>' + (err.message || 'chyba') + '</p>', null, true));
    };
    ws.exportWorld(editor.getValue());
  }
  function showLinks(links) {
    const origin = location.origin;
    const rows = (links || []).map((l, i) => {
      const url = origin + l.url;
      return `<div class="share-row"><span class="share-name">${l.name || ('žiak ' + (i + 1))}</span>` +
             `<input class="share-url" readonly value="${url}">` +
             `<button class="share-copy" data-url="${url}">📋</button></div>`;
    }).join('');
    dialog('🔗 Žiacke linky', '<p>Pošli každému žiakovi jeho link (sú trvalé — žiak sa môže vrátiť):</p>' +
      '<div id="share-links">' + rows + '</div>', [{ label: t('world_settings.btn_cancel', 'Zavrieť') }]);
    setStatus('status.ready', 'Pripravený');
    document.querySelectorAll('.share-copy').forEach(b => {
      b.onclick = () => { navigator.clipboard && navigator.clipboard.writeText(b.dataset.url); b.textContent = '✓'; setTimeout(() => b.textContent = '📋', 1200); };
    });
  }

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
    // UI preklady (jazyk z localStorage)
    try {
      T = await api.uiStrings(uiLang);
      applyI18n();
    } catch (e) { /* HTML defaulty sú slovenské */ }
    loadLangDropdowns();

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
    // verzia + build (aby bolo jasné ktorý build sa testuje)
    api.version().then(v => {
      $('version').textContent = 'v' + v.version + ' · ' + v.git_sha;
      $('version').title = 'Karel 2030 v' + v.version + '\nbuild: ' + v.git_sha +
                           (v.build_time ? '\n' + v.build_time : '');
    }).catch(() => {});
    ws.speed(sliderToDelay(+$('speed').value));
    setTimeout(() => editor.refresh(), 100);
  }

  boot();
})();
