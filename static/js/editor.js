/* Karel 2030 — CodeMirror 5 editor s custom módom pre Karel jazyk.
 * Kľúčové slová prídu z /api/langs/prog/{code}: all_words = {slovo: TOKEN}.
 * Triedy: štruktúry (modré bold), príkazy (žlté), podmienky (tyrkys),
 * komentáre (// # {..} zelené kurzíva), čísla; zakázané príkazy červeno.
 */
'use strict';

const STRUCT_T = new Set(['BEGIN', 'END', 'PROCEDURE', 'REPEAT', 'TIMES', 'END_REPEAT',
  'WHILE', 'DO', 'END_WHILE', 'IF', 'THEN', 'ELSE', 'END_IF', 'NOT', 'AND', 'OR']);
const CMD_T = new Set(['FORWARD', 'BACK', 'LEFT', 'RIGHT', 'DROP', 'PICK', 'DROP_BIG',
  'MARK', 'CLEAR', 'SLOWLY', 'QUICKLY']);
const COND_T = new Set(['WALL', 'BRICK', 'FREE', 'SIGN', 'TRUE', 'FALSE']);

class KarelEditor {
  constructor(textarea) {
    this._words = {};        // slovo → TOKEN
    this._disabled = new Set();
    this._saveCb = null;
    this._saveTimer = null;

    this.cm = CodeMirror.fromTextArea(textarea, {
      mode: 'karel',
      lineNumbers: true,
      indentUnit: 2,
      theme: 'default',
    });
    this._defineMode();

    this.cm.on('change', () => {
      if (!this._saveCb) return;
      clearTimeout(this._saveTimer);                  // debounce 2 s
      this._saveTimer = setTimeout(() => this._saveCb(this.getValue()), 2000);
    });
  }

  /* Mode definovaný dynamicky — siaha na this._words/this._disabled,
   * takže zmena jazyka/zákazov = len refresh, nie nová definícia. */
  _defineMode() {
    const self = this;
    CodeMirror.defineMode('karel', () => ({
      token(stream, st) {
        if (st.brace) {                                // {...} komentár cez riadky
          if (stream.skipTo('}')) { stream.next(); st.brace = false; }
          else stream.skipToEnd();
          return 'karel-comment';
        }
        if (stream.eatSpace()) return null;
        if (stream.match('//') || stream.match('#')) { stream.skipToEnd(); return 'karel-comment'; }
        if (stream.peek() === '{') { stream.next(); st.brace = true;
          if (stream.skipTo('}')) { stream.next(); st.brace = false; } else stream.skipToEnd();
          return 'karel-comment'; }
        if (stream.match(/^\d+/)) return 'karel-number';
        const m = stream.match(/^[*\p{L}_][\p{L}\p{N}_]*/u);
        if (m) {
          const tok = self._words[m[0].toLowerCase()];
          if (tok && self._disabled.has(tok)) return 'karel-disabled';
          if (tok && STRUCT_T.has(tok)) return 'karel-struct';
          if (tok && CMD_T.has(tok)) return 'karel-cmd';
          if (tok && COND_T.has(tok)) return 'karel-cond';
          return 'karel-proc';                          // vlastná procedúra/neznáme
        }
        stream.next();
        return null;
      },
      startState: () => ({ brace: false }),
    }));
    this.cm.setOption('mode', 'karel');
  }

  /* lang = odpoveď /api/langs/prog/{code} */
  setLang(lang) {
    this._words = lang.all_words || {};
    this._langDisabled = new Set(lang.disabled || []);
    this._refreshDisabled();
  }
  setDisabledCmds(cmds) {
    this._worldDisabled = new Set(cmds || []);
    this._refreshDisabled();
  }
  _refreshDisabled() {
    this._disabled = new Set([...(this._langDisabled || []), ...(this._worldDisabled || [])]);
    this.cm.setOption('mode', 'karel');   // re-tokenizuj
  }

  onAutoSave(cb) { this._saveCb = cb; }
  getValue() { return this.cm.getValue(); }
  setValue(v) {
    const cb = this._saveCb; this._saveCb = null;   // setValue ≠ user edit
    this.cm.setValue(v || '');
    this._saveCb = cb;
  }
  insert(text) { this.cm.replaceSelection(text); this.cm.focus(); }
  refresh() { this.cm.refresh(); }
}
