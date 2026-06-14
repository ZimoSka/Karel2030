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

  // ── Primárne kľúčové slová (default SK, aktualizuje setLang) ───────────────
  let KW = {
    BEGIN:'zaciatok', END:'koniec',
    FORWARD:'dopredu', BACK:'dozadu', LEFT:'vlavo', RIGHT:'vpravo',
    DROP:'poloz', PICK:'zdvihni', DROP_BIG:'poloz-velku', PICK_BIG:'zdvihni-velku',
    MARK:'oznac', CLEAR:'odznac',
    SLOWLY:'pomaly', QUICKLY:'rychlo',
    REPEAT:'opakuj', TIMES:'krat',
    WHILE:'kym', DO:'rob',
    IF:'ak', THEN:'potom', ELSE:'inak',
    WALL:'stena', FREE:'volno', BRICK:'tehla', SIGN:'znacka',
    TRUE:'pravda', FALSE:'nepravda', NOT:'nie',
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
        this.setTooltip('Hlavný program');
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
    const actionDefs = [
      ['karel_drop',      () => KW.DROP],
      ['karel_pick',      () => KW.PICK],
      ['karel_drop_big',  () => KW.DROP_BIG],
      ['karel_pick_big',  () => KW.PICK_BIG],
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
  }

  // ── Generátor kódu ─────────────────────────────────────────────────────────

  let gen = null;

  function createGenerator() {
    gen = new Blockly.Generator('Karel');
    gen.ORDER_ATOMIC = 0;
    const fb = gen.forBlock;

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
    fb['karel_pick_big'] = () => KW.PICK_BIG + '\n';
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
  }

  // ── Toolbox (JSON) ─────────────────────────────────────────────────────────

  function buildToolbox() {
    return {
      kind: 'categoryToolbox',
      contents: [
        {
          kind: 'category', name: 'Pohyb', colour: C_MOTION,
          contents: [
            { kind: 'block', type: 'karel_forward' },
            { kind: 'block', type: 'karel_back' },
            { kind: 'block', type: 'karel_left' },
            { kind: 'block', type: 'karel_right' },
          ]
        },
        {
          kind: 'category', name: 'Akcie', colour: C_ACTION,
          contents: [
            { kind: 'block', type: 'karel_drop' },
            { kind: 'block', type: 'karel_pick' },
            { kind: 'block', type: 'karel_drop_big' },
            { kind: 'block', type: 'karel_pick_big' },
            { kind: 'block', type: 'karel_mark' },
            { kind: 'block', type: 'karel_clear' },
            { kind: 'block', type: 'karel_slowly' },
            { kind: 'block', type: 'karel_quickly' },
          ]
        },
        {
          kind: 'category', name: 'Štruktúry', colour: C_CONTROL,
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
          kind: 'category', name: 'Podmienky', colour: C_COND,
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
      grid: { spacing: 20, length: 3, colour: '#2a2a2a', snap: true },
      zoom: { controls: true, wheel: true, startScale: 0.9 },
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
  }

  function generateCode() {
    if (!workspace || !gen) return null;
    try {
      return gen.workspaceToCode(workspace);
    } catch (e) {
      return null;
    }
  }

  // ── Verejné API ────────────────────────────────────────────────────────────

  function init(divId, onCodeChange) {
    _onCodeChange = onCodeChange;
    defineBlocks();
    createGenerator();
    initWorkspace(divId);
  }

  function setLang(primaryKwMap) {
    // Aktualizuje KW slovník a prebuduje etikety existujúcich blokov
    if (!primaryKwMap) return;
    Object.assign(KW, primaryKwMap);
    // Bloky sa prebudujú až pri ďalšom použití (redefineBlocks nie je potrebné
    // pre existujúci workspace — label zmeny treba riešiť inak; odložené na neskor)
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
  }

  return { init, setLang, clearWorkspace, resize, generateCode };

})();
