# -*- coding: utf-8 -*-
"""Karel core – jazykový systém (.lng kľúčové slová + .ini GUI preklady)."""
import os, configparser

_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LANG_ROOT  = os.environ.get('KAREL_LANG_DIR', os.path.join(_PKG_PARENT, 'lang'))

KW: dict = {}            # word.lower() → TOKEN  (všetky jazyky naraz)
_LANG_PRIMARY: dict = {} # lang_code → {TOKEN: primary_word}
_LANG_DISABLED: dict = {} # lang_code → set of TOKEN names disabled by default
_LANG_NAME:     dict = {} # lang_code → display name (z NAME direktívy v .lng)
_INTERP_LANG_DIR = os.path.join(_LANG_ROOT, 'interpreter')

def _load_all_interpreter_langs() -> None:
    """Načíta všetky lang/interpreter/*.lng súbory.
    KW sa naplní všetkými kľúčovými slovami zo všetkých jazykov —
    interpreter tak akceptuje ľubovoľný jazyk súčasne.
    _LANG_PRIMARY uloží primárne slovo (prvé) pre každý jazyk a token.
    _LANG_DISABLED uloží set tokenov, ktoré sú v danom jazyku štandardne zakázané."""
    global KW, _LANG_PRIMARY, _LANG_DISABLED, _LANG_NAME
    KW.clear(); _LANG_PRIMARY.clear(); _LANG_DISABLED.clear(); _LANG_NAME.clear()
    if not os.path.isdir(_INTERP_LANG_DIR):
        _fallback_bkw(); return
    for fname in sorted(os.listdir(_INTERP_LANG_DIR)):
        if not fname.endswith('.lng'): continue
        lang = fname[:-4].lower()   # 'sk', 'en', 'de', 'en_pattis', …
        _LANG_PRIMARY[lang] = {}
        path = os.path.join(_INTERP_LANG_DIR, fname)
        try:
            with open(path, encoding='utf-8') as f:
                lines = f.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' not in line: continue
            token, _, rest = line.partition('=')
            token = token.strip().upper()
            words = rest.split()
            if not words: continue
            if token == 'NAME':
                # Direktíva NAME — zobrazený názov jazyka v dropdowne
                _LANG_NAME[lang] = rest.strip()
                continue
            if token == 'DISABLED':
                # Direktíva DISABLED — tieto tokeny sa pri výbere jazyka automaticky zakážu
                _LANG_DISABLED[lang] = set(w.upper() for w in words)
                continue
            _LANG_PRIMARY[lang][token] = words[0].lower()
            for w in words:
                KW[w.lower()] = token
    # Ak žiadne súbory nenašiel, použi hardcoded zálohu
    if not KW:
        _fallback_bkw()

def _fallback_bkw() -> None:
    """Núdzový fallback — hardcoded SK+EN kľúčové slová ak chýbajú .lng súbory."""
    for t,vs in [
        ('BEGIN',['begin','zaciatok','začiatok']),('END',['end','koniec']),
        ('PROCEDURE',['procedure','prikaz','príkaz']),
        ('REPEAT',['repeat','opakuj']),('TIMES',['times','krat','krát']),
        ('END_REPEAT',['*repeat','*opakuj']),
        ('WHILE',['while','kym','kým']),('NOT',['not','nie']),('DO',['do','rob']),
        ('END_WHILE',['*while','*kym','*kým']),
        ('IF',['if','ak']),('THEN',['then','tak','potom']),
        ('ELSE',['else','inak']),('END_IF',['*if','*ak']),
        ('FORWARD',['forward','dopredu']),('BACK',['back','dozadu','vzad']),
        ('LEFT',['left','vlavo','dolava','vľavo','doľava']),
        ('RIGHT',['right','vpravo','doprava']),
        ('DROP',['drop','poloz','polož']),('PICK',['pick','zdvihni','zodvihni']),
        ('DROP_BIG',['drop_big','drop_b','dropb','poloz_velku','poloz_v','polozv']),
        ('MARK',['mark','oznac','označ']),
        ('CLEAR',['clear','unmark','odznac','ocisti','cisti','odznač','očisti','čisti']),
        ('WALL',['wall','stena','je_stena','is_wall']),
        ('BRICK',['brick','tehla','je_tehla','is_brick']),
        ('FREE',['free','volno','voľno','is_free']),
        ('SIGN',['sign','znacka','značka','je_znacka','is_sign']),
        ('FALSE',['false','nepravda']),('TRUE',['true','pravda']),
        ('SLOWLY',['slowly','slow','pomaly','spomal']),
        ('QUICKLY',['quickly','quick','rychlo','rýchlo','pridaj']),
    ]:
        for v in vs: KW[v] = t
    _LANG_PRIMARY['sk'] = {
        'BEGIN':'zaciatok','END':'koniec','PROCEDURE':'prikaz','REPEAT':'opakuj',
        'TIMES':'krat','END_REPEAT':'*opakuj','WHILE':'kym','NOT':'nie',
        'AND':'a','OR':'alebo','DO':'rob',
        'END_WHILE':'*kym','IF':'ak','THEN':'potom','ELSE':'inak','END_IF':'*ak',
        'FORWARD':'dopredu','BACK':'dozadu','LEFT':'vlavo','RIGHT':'vpravo',
        'DROP':'poloz','PICK':'zdvihni','DROP_BIG':'poloz_velku',
        'MARK':'oznac','CLEAR':'odznac','WALL':'stena','BRICK':'tehla',
        'FREE':'volno','SIGN':'znacka','FALSE':'nepravda','TRUE':'pravda',
        'SLOWLY':'pomaly','QUICKLY':'rychlo',
    }
    _LANG_PRIMARY['en'] = {
        'BEGIN':'begin','END':'end','PROCEDURE':'procedure','REPEAT':'repeat',
        'TIMES':'times','END_REPEAT':'*repeat','WHILE':'while','NOT':'not',
        'AND':'and','OR':'or','DO':'do',
        'END_WHILE':'*while','IF':'if','THEN':'then','ELSE':'else','END_IF':'*if',
        'FORWARD':'forward','BACK':'back','LEFT':'left','RIGHT':'right',
        'DROP':'drop','PICK':'pick','DROP_BIG':'drop_big',
        'MARK':'mark','CLEAR':'clear','WALL':'wall','BRICK':'brick',
        'FREE':'free','SIGN':'sign','FALSE':'false','TRUE':'true',
        'SLOWLY':'slowly','QUICKLY':'quickly',
    }

_load_all_interpreter_langs()

def _primary_kw(token: str, lang: str) -> str:
    """Vráti primárne kľúčové slovo pre daný token v danom jazyku.
    Fallback: EN, potom lowercase token."""
    return (_LANG_PRIMARY.get(lang, {}).get(token)
            or _LANG_PRIMARY.get('en', {}).get(token)
            or token.lower())

# Spätné mapovanie: token → [varianty slov]  (pre highlighting zakázaných príkazov)
_KW_REVERSE: dict = {}
for _kw, _kt in KW.items():
    _KW_REVERSE.setdefault(_kt, []).append(_kw)

def _cmds_list(disabled=None) -> list:
    """Zoznam základných príkazov v aktuálnom prog_lang (pre filter panel).
    Tokeny v množine disabled sú vynechané."""
    p = _primary_kw; L = _current_prog_lang
    toks = ['FORWARD','BACK','LEFT','RIGHT','DROP','DROP_BIG','PICK',
            'MARK','CLEAR','SLOWLY','QUICKLY']
    return [p(t,L) for t in toks if not (disabled and t in disabled)]

def _cmds_structs() -> list:
    """Zoznam riadiacich štruktúr v aktuálnom prog_lang."""
    p = _primary_kw; L = _current_prog_lang
    rep = p('REPEAT',L); tim = p('TIMES',L); end = p('END',L)
    whl = p('WHILE',L);  cnd = '…';         rob = p('DO',L)
    ifs = p('IF',L);     thn = p('THEN',L); els = p('ELSE',L)
    prc = p('PROCEDURE',L); bgn = p('BEGIN',L)
    return [
        f'{rep} N {tim} ... {end}',
        f'{whl} {cnd} {rob} ... {end}',
        f'{ifs} {cnd} {thn} ... {end}',
        f'{ifs} ... {thn} ... {els} ... {end}',
        f'{prc} Meno\n{bgn}\n\n{end}',
    ]

def _cmds_conds(disabled=None) -> list:
    """Zoznam podmienok v aktuálnom prog_lang. Tokeny v množine disabled sú vynechané."""
    p = _primary_kw; L = _current_prog_lang
    n = p('NOT',L); a = p('AND',L); o = p('OR',L)
    d = disabled or set()
    conds = [p(t,L) for t in ['WALL','BRICK','FREE','SIGN','TRUE','FALSE'] if t not in d]
    conds += [f'{n} {p(t,L)}' for t in ['WALL','BRICK'] if t not in d]
    # Príklady logických spojok
    if 'WALL' not in d and 'SIGN' not in d:
        conds.append(f'{p("WALL",L)} {o} {p("SIGN",L)}')
    if 'FREE' not in d and 'BRICK' not in d:
        conds.append(f'{p("FREE",L)} {a} {n} {p("BRICK",L)}')
    return conds


_LANG_DIR   = _LANG_ROOT

def _available_ui_langs() -> list:
    """Vráti [(kód, zobrazené_meno), …] pre všetky dostupné jazyky GUI (lang/*.ini).
    Zoradené podľa kódu.  Fallback: [('sk','Slovenčina'),('en','English')]."""
    langs = []
    if os.path.isdir(_LANG_DIR):
        for fname in sorted(os.listdir(_LANG_DIR)):
            if fname.endswith('.ini') and not fname.startswith('_'):
                code = fname[:-4]
                cfg  = configparser.ConfigParser(interpolation=None)
                try:
                    cfg.read(os.path.join(_LANG_DIR, fname), encoding='utf-8')
                    name = cfg.get('meta', 'name', fallback=code)
                except Exception:
                    name = code
                langs.append((code, name))
    return langs or [('sk', 'Slovenčina'), ('en', 'English')]

def _available_prog_langs() -> list:
    """Vráti [(kód, zobrazené_meno), …] pre všetky dostupné programovacie jazyky
    (lang/interpreter/*.lng).  Meno načíta prednostne z _LANG_NAME (direktíva NAME
    v .lng súbore), potom z lang/{kód}.ini [meta] name, inak kód."""
    langs = []
    if os.path.isdir(_INTERP_LANG_DIR):
        for fname in sorted(os.listdir(_INTERP_LANG_DIR)):
            if fname.endswith('.lng'):
                code = fname[:-4]
                # 1) NAME direktíva priamo v .lng súbore
                if code in _LANG_NAME:
                    name = _LANG_NAME[code]
                else:
                    # 2) lang/{kód}.ini [meta] name  (iba ak súbor existuje)
                    ini_path = os.path.join(_LANG_DIR, f'{code}.ini')
                    cfg      = configparser.ConfigParser(interpolation=None)
                    try:
                        cfg.read(ini_path, encoding='utf-8')
                        name = cfg.get('meta', 'name', fallback=code)
                    except Exception:
                        name = code
                langs.append((code, name))
    return langs or [('sk', 'Slovenčina'), ('en', 'English')]

# Aktuálny prekladový slovník — naplní sa pri štarte cez _load_ui_lang()
_ui_strings:        dict = {}
_current_prog_lang: str  = 'sk'

def _load_ui_lang(lang: str = 'sk') -> None:
    """Načíta lang/{lang}.ini do _ui_strings (všetky sekcie okrem action_labels)."""
    global _ui_strings
    path = os.path.join(_LANG_DIR, f'{lang}.ini')
    if not os.path.exists(path):
        path = os.path.join(_LANG_DIR, 'sk.ini')
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path, encoding='utf-8')
    flat: dict = {}
    for sec in cfg.sections():
        for key, val in cfg.items(sec):
            flat[f'{sec}.{key}'] = val.strip()
    _ui_strings = flat

def _T(key: str, **fmt) -> str:
    """Vráti preložený reťazec pre daný kľúč (sekcia.kľúč).
    Ak kľúč neexistuje, vráti samotný kľúč ako fallback."""
    val = _ui_strings.get(key, key)
    if fmt:
        try:
            val = val.format(**fmt)
        except (KeyError, ValueError):
            pass
    return val

# Mapovanie: kľúč akcie (v ControlPanel) → token interpretera
_ACTION_TOKEN = {
    'drop':     'DROP',
    'drop_big': 'DROP_BIG',
    'pick':     'PICK',
    'mark':     'MARK',
    'clear':    'CLEAR',
}

def _switch_prog_lang(lang: str) -> None:
    """Prepne aktuálny programovací jazyk (nastaví _current_prog_lang).
    Labely akčných tlačidiel sledujú GUI jazyk (_ui_strings), nie prog_lang."""
    global _current_prog_lang
    _current_prog_lang = lang

def _prog_btn(action: str) -> tuple:
    """Vráti (display_label, karel_command) pre danú akciu.
    Label pochádza z [action_labels] GUI jazykového súboru (sleduje GUI lang).
    Príkaz je primárne kľúčové slovo z interpreter/*.lng pre aktuálny prog_lang."""
    token = _ACTION_TOKEN.get(action, action.upper())
    # Label = GUI jazyk (action_labels sekcia z _ui_strings)
    label = (_ui_strings.get('action_labels.' + token.lower())
             or _primary_kw(token, _current_prog_lang))
    label = label.replace('\\n', '\n')   # ini ukladá \n ako literal backslash-n
    # Command = programovací jazyk
    cmd   = _primary_kw(token, _current_prog_lang)
    return label, cmd


def current_prog_lang() -> str:
    """Getter pre aktuálny prog_lang (mutable modulový stav)."""
    return _current_prog_lang
