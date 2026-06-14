/* blockly_karel.js — Karel 2030 Blockly editor
 * Jednosmerné: bloky → Karel textový kód (nie naopak).
 * Zavolaj KarelBlockly.init(divId, onCodeChange) pre inicializáciu.
 * Zavolaj KarelBlockly.setLang(primaryKwMap) pri zmene prog_lang.
 */
'use strict';

const KarelBlockly = (() => {

  // ── Farby (Scratch-like paleta) ────────────────────────────────────────────
  const C_MOTION  = '#4C97FF';
  const C_ACTION  = '#9966FF';
  const C_CONTROL = '#FFAB19';
  const C_COND    = '#5CB1D6';
  const C_LOGIC   = '#FF6680';

  // ── Programovacie kľúčové slová (TOKEN → slovo). Default SK; reálne hodnoty
  // dodá init/setLang z prog jazyka sveta (lang/interpreter/*.lng). ────────────
  let KW = {
    BEGIN:'zaciatok', END:'koniec', PROCEDURE:'prikaz',
    FORWARD:'dopredu', BACK:'dozadu', LEFT:'vlavo', RIGHT:'vpravo',
    DROP:'poloz', PICK:'zdvihni', DROP_BIG:'kvader',
    MARK:'oznac', CLEAR:'odznac',
    SLOWLY:'pomaly', QUICKLY:'rychlo',
    REPEAT:'opakuj', TIMES:'krat',
    WHILE:'kym', DO:'rob',
    IF:'ak', THEN:'potom', ELSE:'inak',
    WALL:'stena', FREE:'volno', BRICK:'tehla', SIGN:'znacka',
    TRUE:'pravda', FALSE:'nepravda', NOT:'nie',
  };

  // ── GUI texty (názvy kategórií, tooltipy). Default SK; reálne hodnoty dodá
  // init/setLang z ui jazyka (lang/{ui_lang}.ini → program_panel.*). ───────────
  let _labels = {
    cat_motion:'Pohyb', cat_action:'Akcie', cat_struct:'Štruktúry',
    cat_cond:'Podmienky', cat_proc:'Procedúry',
    tip_program:'Hlavný program', tip_proc_def:'Definícia vlastnej procedúry',
    tip_proc_call:'Volanie vlastnej procedúry',
  };

  // ── Definície blokov ───────────────────────────────────────────────────────

  function defineBlocks() {

    // ── Hlavný blok programu (hat, nedeletovateľný) ─────────────────────────
    Blockly.Blocks['karel_program'] = {
      init: function() {
        this.appendDummyInput('TOP')
            .appendField(new Blockly.FieldLabel(KW.BEGIN, 'karel-hat-label'));
        this.appendStatementInput('BODY').setCheck(null);
        this.appendDummyInput()
            .appendField(new Blockly.FieldLabel(KW.END, 'karel-hat-label'));
        this.setColour('#7C4DFF');
        this.setDeletable(false);
        this.setMovable(false);
        this.setTooltip(_labels.tip_program);
      }
    };

    // ── Pohybové bloky ───────────────────────────────────────────────────────
    const motionDefs = [
      ['karel_forward', () => KW.FORWARD],
      ['karel_back',    () => KW.BACK],
      ['karel_left',    () => KW.LEFT],
      ['karel_right',   () => KW.RIGHT],
    ];
    motionDefs.forEach(([type, labelFn]) => {
      Blockly.Blocks[type] = {
        init: function() {
          this.appendDummyInput().appendField(labelFn());
          this.setPreviousStatement(true, null);
          this.setNextStatement(true, null);
          this.setColour(C_MOTION);
        }
      };
    });

    // ── Akčné bloky ─────────────────────────────────────────────────────────
    // Pozn.: pick_big nie je programový príkaz (len GUI), preto tu nie je blok.
    const actionDefs = [
      ['karel_drop',      () => KW.DROP],
      ['karel_pick',      () => KW.PICK],
      ['karel_drop_big',  () => KW.DROP_BIG],
      ['karel_mark',      () => KW.MARK],
      ['karel_clear',     () => KW.CLEAR],
      ['karel_slowly',    () => KW.SLOWLY],
      ['karel_quickly',   () => KW.QUICKLY],
    ];
    actionDefs.forEach(([type, labelFn]) => {
      Blockly.Blocks[type] = {
        init: function() {
          this.appendDummyInput().appendField(labelFn());
          this.setPreviousStatement(true, null);
          this.setNextStatement(true, null);
          this.setColour(C_ACTION);
        }
      };
    });

    // ── Číslo (pre opakuj) ───────────────────────────────────────────────────
    Blockly.Blocks['karel_number'] = {
      init: function() {
        this.appendDummyInput()
            .appendField(new Blockly.FieldNumber(4, 1, 999), 'NUM');
        this.setOutput(true, 'Number');
        this.setColour(C_CONTROL);
      }
    };

    // ── opakuj N krat ────────────────────────────────────────────────────────
    Blockly.Blocks['karel_repeat'] = {
      init: function() {
        this.appendValueInput('COUNT')
            .setCheck('Number')
            .appendField(KW.REPEAT);
        this.appendDummyInput().appendField(KW.TIMES);
        this.appendStatementInput('DO').setCheck(null);
        this.appendDummyInput().appendField(KW.END);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(C_CONTROL);
      }
    };

    // ── kym podmienka rob ────────────────────────────────────────────────────
    Blockly.Blocks['karel_while'] = {
      init: function() {
        this.appendValueInput('COND')
            .setCheck('Boolean')
            .appendField(KW.WHILE);
        this.appendDummyInput().appendField(KW.DO);
        this.appendStatementInput('DO').setCheck(null);
        this.appendDummyInput().appendField(KW.END);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(C_CONTROL);
      }
    };

    // ── ak podmienka potom ───────────────────────────────────────────────────
    Blockly.Blocks['karel_if'] = {
      init: function() {
        this.appendValueInput('COND')
            .setCheck('Boolean')
            .appendField(KW.IF);
        this.appendDummyInput().appendField(KW.THEN);
        this.appendStatementInput('THEN').setCheck(null);
        this.appendDummyInput().appendField(KW.END);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(C_CONTROL);
      }
    };

    // ── ak podmienka potom ... inak ──────────────────────────────────────────
    Blockly.Blocks['karel_if_else'] = {
      init: function() {
        this.appendValueInput('COND')
            .setCheck('Boolean')
            .appendField(KW.IF);
        this.appendDummyInput().appendField(KW.THEN);
        this.appendStatementInput('THEN').setCheck(null);
        this.appendDummyInput().appendField(KW.ELSE);
        this.appendStatementInput('ELSE').setCheck(null);
        this.appendDummyInput().appendField(KW.END);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(C_CONTROL);
      }
    };

    // ── Podmienky (boolean output) ───────────────────────────────────────────
    const condDefs = [
      ['karel_wall',  () => KW.WALL],
      ['karel_free',  () => KW.FREE],
      ['karel_brick', () => KW.BRICK],
      ['karel_sign',  () => KW.SIGN],
      ['karel_true',  () => KW.TRUE],
      ['karel_false', () => KW.FALSE],
    ];
    condDefs.forEach(([type, labelFn]) => {
      Blockly.Blocks[type] = {
        init: function() {
          this.appendDummyInput().appendField(labelFn());
          this.setOutput(true, 'Boolean');
          this.setColour(C_COND);
        }
      };
    });

    // ── nie (NOT) ────────────────────────────────────────────────────────────
    Blockly.Blocks['karel_not'] = {
      init: function() {
        this.appendValueInput('COND')
            .setCheck('Boolean')
            .appendField(KW.NOT);
        this.setOutput(true, 'Boolean');
        this.setColour(C_LOGIC);
      }
    };

    // ── Definícia procedúry (prikaz X ... koniec) ───────────────────────────
    Blockly.Blocks['karel_procedure'] = {
      init: function() {
        this.appendDummyInput()
            .appendField(KW.PROCEDURE)
            .appendField(new Blockly.FieldTextInput(_PROC_DEFAULT), 'NAME');
        this.appendStatementInput('BODY').setCheck(null);
        this.appendDummyInput().appendField(KW.END);
        this.setColour('#B87333');
        this.setTooltip(_labels.tip_proc_def);
      }
    };

    // ── Volanie procedúry ────────────────────────────────────────────────────
    Blockly.Blocks['karel_call'] = {
      init: function() {
        this.appendDummyInput()
            .appendField(new Blockly.FieldTextInput(_PROC_DEFAULT), 'NAME');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#B87333');
        this.setTooltip(_labels.tip_proc_call);
      }
    };
  }
  const _PROC_DEFAULT = 'Procedura';

  // ── Generátor kódu ─────────────────────────────────────────────────────────

  let gen = null;

  function createGenerator() {
    gen = new Blockly.Generator('Karel');
    gen.ORDER_ATOMIC = 0;
    const fb = gen.forBlock;

    // scrub_ reťazí nasledujúce bloky v stohu (next connection).
    // Bez tejto definície sa vygeneruje len prvý blok a ďalšie v stohu sa
    // zahodia (napr. príkaz za vnútorným cyklom).
    gen.scrub_ = function(block, code, opt_thisOnly) {
      const next = block.nextConnection && block.nextConnection.targetBlock();
      const nextCode = (opt_thisOnly || !next) ? '' : gen.blockToCode(next);
      return code + nextCode;
    };

    fb['karel_program'] = function(block) {
      const body = gen.statementToCode(block, 'BODY');
      return KW.BEGIN + '\n' + body + KW.END + '\n';
    };

    fb['karel_forward']  = () => KW.FORWARD  + '\n';
    fb['karel_back']     = () => KW.BACK     + '\n';
    fb['karel_left']     = () => KW.LEFT     + '\n';
    fb['karel_right']    = () => KW.RIGHT    + '\n';
    fb['karel_drop']     = () => KW.DROP     + '\n';
    fb['karel_pick']     = () => KW.PICK     + '\n';
    fb['karel_drop_big'] = () => KW.DROP_BIG + '\n';
    fb['karel_mark']     = () => KW.MARK     + '\n';
    fb['karel_clear']    = () => KW.CLEAR    + '\n';
    fb['karel_slowly']   = () => KW.SLOWLY   + '\n';
    fb['karel_quickly']  = () => KW.QUICKLY  + '\n';

    fb['karel_number'] = function(block) {
      return [block.getFieldValue('NUM'), gen.ORDER_ATOMIC];
    };

    fb['karel_repeat'] = function(block) {
      const count = gen.valueToCode(block, 'COUNT', gen.ORDER_ATOMIC) || '1';
      const body  = gen.statementToCode(block, 'DO');
      return KW.REPEAT + ' ' + count + ' ' + KW.TIMES + '\n' + body + KW.END + '\n';
    };

    fb['karel_while'] = function(block) {
      const cond = gen.valueToCode(block, 'COND', gen.ORDER_ATOMIC) || KW.TRUE;
      const body = gen.statementToCode(block, 'DO');
      return KW.WHILE + ' ' + cond + ' ' + KW.DO + '\n' + body + KW.END + '\n';
    };

    fb['karel_if'] = function(block) {
      const cond = gen.valueToCode(block, 'COND', gen.ORDER_ATOMIC) || KW.TRUE;
      const then = gen.statementToCode(block, 'THEN');
      return KW.IF + ' ' + cond + ' ' + KW.THEN + '\n' + then + KW.END + '\n';
    };

    fb['karel_if_else'] = function(block) {
      const cond  = gen.valueToCode(block, 'COND', gen.ORDER_ATOMIC) || KW.TRUE;
      const then  = gen.statementToCode(block, 'THEN');
      const els   = gen.statementToCode(block, 'ELSE');
      return KW.IF + ' ' + cond + ' ' + KW.THEN + '\n' + then +
             KW.ELSE + '\n' + els + KW.END + '\n';
    };

    fb['karel_wall']  = () => [KW.WALL,  gen.ORDER_ATOMIC];
    fb['karel_free']  = () => [KW.FREE,  gen.ORDER_ATOMIC];
    fb['karel_brick'] = () => [KW.BRICK, gen.ORDER_ATOMIC];
    fb['karel_sign']  = () => [KW.SIGN,  gen.ORDER_ATOMIC];
    fb['karel_true']  = () => [KW.TRUE,  gen.ORDER_ATOMIC];
    fb['karel_false'] = () => [KW.FALSE, gen.ORDER_ATOMIC];

    fb['karel_not'] = function(block) {
      const cond = gen.valueToCode(block, 'COND', gen.ORDER_ATOMIC) || KW.TRUE;
      return [KW.NOT + ' ' + cond, gen.ORDER_ATOMIC];
    };

    fb['karel_procedure'] = function(block) {
      const name = block.getFieldValue('NAME') || _PROC_DEFAULT;
      const body = gen.statementToCode(block, 'BODY');
      return KW.PROCEDURE + ' ' + name + '\n' + KW.BEGIN + '\n' + body + KW.END + '\n\n';
    };

    fb['karel_call'] = function(block) {
      return (block.getFieldValue('NAME') || _PROC_DEFAULT) + '\n';
    };
  }

  // ── Toolbox (JSON) ─────────────────────────────────────────────────────────

  function buildToolbox() {
    return {
      kind: 'categoryToolbox',
      contents: [
        {
          kind: 'category', name: _labels.cat_motion, colour: C_MOTION,
          contents: [
            { kind: 'block', type: 'karel_forward' },
            { kind: 'block', type: 'karel_back' },
            { kind: 'block', type: 'karel_left' },
            { kind: 'block', type: 'karel_right' },
          ]
        },
        {
          kind: 'category', name: _labels.cat_action, colour: C_ACTION,
          contents: [
            { kind: 'block', type: 'karel_drop' },
            { kind: 'block', type: 'karel_pick' },
            { kind: 'block', type: 'karel_drop_big' },
            { kind: 'block', type: 'karel_mark' },
            { kind: 'block', type: 'karel_clear' },
            { kind: 'block', type: 'karel_slowly' },
            { kind: 'block', type: 'karel_quickly' },
          ]
        },
        {
          kind: 'category', name: _labels.cat_struct, colour: C_CONTROL,
          contents: [
            {
              kind: 'block', type: 'karel_repeat',
              inputs: { COUNT: { block: { type: 'karel_number' } } }
            },
            { kind: 'block', type: 'karel_while' },
            { kind: 'block', type: 'karel_if' },
            { kind: 'block', type: 'karel_if_else' },
          ]
        },
        {
          kind: 'category', name: _labels.cat_cond, colour: C_COND,
          contents: [
            { kind: 'block', type: 'karel_wall' },
            { kind: 'block', type: 'karel_free' },
            { kind: 'block', type: 'karel_brick' },
            { kind: 'block', type: 'karel_sign' },
            { kind: 'block', type: 'karel_true' },
            { kind: 'block', type: 'karel_false' },
            { kind: 'block', type: 'karel_not' },
          ]
        },
        {
          kind: 'category', name: _labels.cat_proc, colour: '#B87333',
          contents: [
            { kind: 'block', type: 'karel_procedure' },
            { kind: 'block', type: 'karel_call' },
          ]
        },
      ]
    };
  }

  // ── Workspace ──────────────────────────────────────────────────────────────

  let workspace = null;
  let _onCodeChange = null;
  let _suppressChange = false;

  function initWorkspace(divId) {
    workspace = Blockly.inject(divId, {
      toolbox: buildToolbox(),
      toolboxPosition: 'end',   // toolbox + flyout vpravo (nezakrýva kód vľavo)
      grid: { spacing: 20, length: 3, colour: '#2a2a2a', snap: true },
      zoom: { controls: true, wheel: true, startScale: 0.65 },
      trashcan: true,
      theme: Blockly.Themes.Dark || Blockly.Theme.defineTheme('karelDark', {
        base: Blockly.Themes.Classic,
        componentStyles: {
          workspaceBackgroundColour: '#1a1a1a',
          toolboxBackgroundColour: '#141414',
          toolboxForegroundColour: '#ccc',
          flyoutBackgroundColour: '#1e1e1e',
          flyoutForegroundColour: '#ccc',
          flyoutOpacity: 1,
          scrollbarColour: '#444',
          insertionMarkerColour: '#fff',
          insertionMarkerOpacity: 0.3,
          scrollbarOpacity: 0.4,
          cursorColour: '#d0d0ff',
        },
      }),
      renderer: 'zelos',  // Scratch-like rounded blocks
    });

    // Vložíme základný blok zaciatok/koniec
    _suppressChange = true;
    const dom = Blockly.utils.xml.textToDom(
      '<xml><block type="karel_program" x="30" y="30" deletable="false" movable="false"></block></xml>'
    );
    Blockly.Xml.domToWorkspace(dom, workspace);
    _suppressChange = false;

    workspace.addChangeListener(e => {
      if (_suppressChange) return;
      if (e.isUiEvent) return;                       // zoom/scroll/klik — nič negenerujeme
      if (!_onCodeChange) return;
      const code = generateCode();
      if (code !== null) _onCodeChange(code);
    });

    // Toolbox je vpravo → Blockly automaticky dá zoom+smetiak doľava, kde ich
    // zakrýva program. Prepíšeme transform doprava (a smetiak zmenšíme).
    _setupControlReposition();
  }

  // ── Reposícia zoom ovládačov + smetiaka doprava ────────────────────────────
  let _ctrlObserver = null;

  function _ctrlEls(svg) {
    // .blocklyZoom matchuje jednotlivé tlačidlá → kontajner je ich rodič
    const zoomBtn = svg.querySelector('.blocklyZoom');
    return {
      zoom:  zoomBtn ? zoomBtn.parentNode : null,
      trash: svg.querySelector('.blocklyTrash'),
    };
  }

  // Blockly dáva ovládače doľava (opačne než toolbox vpravo). Necháme Blockly
  // vypočítané Y a prepíšeme len X na pravú stranu (vedľa toolboxu). Smetiak
  // navyše zmenšíme.
  function _flipRight(el, W, tbW, scale) {
    if (!el) return;
    const t = el.getAttribute('transform') || '';
    const m = t.match(/translate\(\s*([-\d.]+)[ ,]+([-\d.]+)/);
    if (!m) return;
    const y = parseFloat(m[2]);
    let w = 48;
    try { w = el.getBBox().width * (scale || 1); } catch (e) { /* getBBox môže zlyhať */ }
    const x = W - tbW - w - 14;
    el.setAttribute('transform', `translate(${x}, ${y})${scale ? ' scale(' + scale + ')' : ''}`);
  }

  function _repositionControls() {
    if (!workspace) return;
    const svg = workspace.getParentSvg && workspace.getParentSvg();
    if (!svg) return;
    const W = svg.clientWidth;
    if (!W) return;
    const tb = workspace.getToolbox && workspace.getToolbox();
    const tbW = tb ? tb.getWidth() : 0;
    const { zoom, trash } = _ctrlEls(svg);
    if (_ctrlObserver) _ctrlObserver.disconnect();   // nezachytávaj vlastné zápisy
    _flipRight(zoom,  W, tbW, null);
    _flipRight(trash, W, tbW, 0.6);
    if (_ctrlObserver) _reobserveControls(svg);
  }

  function _reobserveControls(svg) {
    const { zoom, trash } = _ctrlEls(svg);
    [zoom, trash].forEach(el => {
      if (el) _ctrlObserver.observe(el, { attributes: true, attributeFilter: ['transform'] });
    });
  }

  function _setupControlReposition() {
    const svg = workspace.getParentSvg && workspace.getParentSvg();
    if (!svg) return;
    _ctrlObserver = new MutationObserver(() => _repositionControls());
    _reobserveControls(svg);
    // počiatočná reposícia (po vykreslení)
    requestAnimationFrame(() => _repositionControls());
    setTimeout(() => _repositionControls(), 200);
  }

  function generateCode() {
    if (!workspace || !gen) return null;
    try {
      // Procedúry musia byť pred hlavným programom
      const blocks = workspace.getTopBlocks(true);
      const procs = blocks.filter(b => b.type === 'karel_procedure');
      const main  = blocks.filter(b => b.type === 'karel_program');
      const rest  = blocks.filter(b => b.type !== 'karel_procedure' && b.type !== 'karel_program');
      const allOrdered = [...procs, ...main, ...rest];
      return allOrdered.map(b => gen.blockToCode(b)).join('');
    } catch (e) {
      return null;
    }
  }

  // ── Verejné API ────────────────────────────────────────────────────────────

  function init(divId, onCodeChange, kw, labels) {
    _onCodeChange = onCodeChange;
    if (kw) Object.assign(KW, kw);
    if (labels) Object.assign(_labels, labels);
    defineBlocks();
    createGenerator();   // generátor číta KW za behu (closure) → netreba prebudovať
    initWorkspace(divId);
  }

  // Zmena jazyka: prog kľúčové slová (kw, TOKEN→slovo) a/alebo GUI texty (labels).
  // Bloky majú slová „zapečené" pri inštancii → prebudujeme: uložíme XML,
  // predefinujeme bloky s novými slovami, načítame XML späť (zachová mená procedúr
  // a počty opakovaní), aktualizujeme toolbox.
  function setLang(kw, labels) {
    if (kw) Object.assign(KW, kw);
    if (labels) Object.assign(_labels, labels);
    if (!workspace) return;
    const xml = Blockly.Xml.workspaceToDom(workspace);
    defineBlocks();
    _suppressChange = true;
    workspace.clear();
    Blockly.Xml.domToWorkspace(xml, workspace);
    _suppressChange = false;
    if (workspace.updateToolbox) workspace.updateToolbox(buildToolbox());
    requestAnimationFrame(() => _repositionControls());
  }

  function clearWorkspace() {
    if (!workspace) return;
    _suppressChange = true;
    workspace.clear();
    const dom = Blockly.utils.xml.textToDom(
      '<xml><block type="karel_program" x="30" y="30" deletable="false" movable="false"></block></xml>'
    );
    Blockly.Xml.domToWorkspace(dom, workspace);
    _suppressChange = false;
  }

  function resize() {
    if (workspace) Blockly.svgResize(workspace);
    requestAnimationFrame(() => _repositionControls());
  }

  return { init, setLang, clearWorkspace, resize, generateCode };

})();
