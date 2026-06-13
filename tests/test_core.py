# -*- coding: utf-8 -*-
"""Regresné testy karel_core — overujú identické správanie s karel2010.py
pred extrakciou. Spustenie:  python -m pytest tests/ -q   (alebo priamo python tests/test_core.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import karel_core as k


def _itp(world, **cb):
    itp = k.KarelInterpreter(world); itp.delay = 0
    for name, fn in cb.items():
        setattr(itp, name, fn)
    return itp


def _world(w=10, h=8):
    wd = k.World.from_json(k.BUILTIN_WORLD)
    return wd


# ---------------- parser + logické spojky ----------------

def test_parse_basic():
    for src in [
        'zaciatok dopredu vlavo koniec',
        'zaciatok opakuj 3 krat dopredu koniec koniec',
        'zaciatok kym nie stena rob dopredu koniec koniec',
        'zaciatok ak tehla potom zdvihni inak dopredu koniec koniec',
    ]:
        assert k.parse(src) is not None


def test_parse_logic_connectives():
    for src in [
        'zaciatok ak stena alebo znacka potom vlavo koniec koniec',
        'zaciatok kym volno a nie tehla rob dopredu koniec koniec',
        'zaciatok ak (stena alebo tehla) a nie znacka potom dozadu koniec koniec',
        'zaciatok ak nie (stena alebo znacka) potom dopredu koniec koniec',
    ]:
        assert k.parse(src) is not None


def test_parse_errors():
    for bad in [
        'zaciatok ak stena alebo potom dopredu koniec koniec',
        'zaciatok ak (stena alebo tehla potom dopredu koniec koniec',
        'zaciatok ak a stena potom dopredu koniec koniec',
    ]:
        try:
            k.parse(bad)
            assert False, f'mal vyhodit ParseErr: {bad}'
        except k.ParseErr:
            pass


def test_logic_evaluation():
    wd = _world()
    itp = _itp(wd)
    def ev(cond):
        prog = k.parse(f'zaciatok ak {cond} potom dopredu koniec koniec')
        return itp._ev(prog.main_stmts[0].cond)
    # Karel (1,1) smer E, prázdny svet
    assert ev('volno') is True
    assert ev('stena') is False
    assert ev('stena alebo volno') is True
    assert ev('stena a volno') is False
    assert ev('nie stena') is True
    # priorita: a > alebo
    assert ev('stena alebo volno a nie tehla') is True     # F or (T and T)
    assert ev('volno a stena alebo pravda') is True        # (T and F) or T
    assert ev('volno a stena alebo nepravda') is False     # (T and F) or F
    assert ev('(stena alebo tehla) a volno') is False
    assert ev('nie (stena a tehla)') is True


# ---------------- beh interpretera ----------------

def test_run_to_wall():
    wd = _world()
    itp = _itp(wd)
    itp.run(k.parse('zaciatok kym nie stena a nie tehla rob dopredu koniec koniec'))
    assert wd.karel_x == 9   # pri východnej stene


def test_world01_success_requires_mark():
    """Svet 01: úspech = dôjsť na značku (3,1), nie len skončiť na muriku.
    Strážca proti regresii falošného úspechu pri prejdení len časti muriku."""
    def run(src):
        wd = k.World.from_xml('worlds/01.karxml'); wd.reset_inventory()
        itp = k.KarelInterpreter(wd); itp.delay = 0; res = {'r': None}
        def on_step():
            r = k.evaluate_goals(wd, on_step=True)
            if r: res['r'] = r; itp.stop()
        def fin(_):
            if res['r'] is None: res['r'] = k.evaluate_goals(wd, on_step=False)
        itp.on_step = on_step; itp.on_finish = fin
        itp.run(k.parse(src)); return res['r']
    # len časť muriku → NIE úspech (predtým to falošne prešlo)
    partial = 'zaciatok opakuj 3 krat kym tehla rob dopredu koniec vlavo koniec koniec'
    assert run(partial) != 'success'
    # celý okruh + dôjdi na značku → úspech
    full = ('zaciatok opakuj 4 krat kym tehla rob dopredu koniec vlavo koniec '
            'kym tehla rob dopredu koniec koniec')
    assert run(full) == 'success'


# ---------------- pohybové rozpočty ----------------

def test_step_budget():
    wd = _world(); wd.settings.max_steps = 3
    hit = []
    itp = _itp(wd, on_budget=lambda kind: hit.append(kind))
    itp.run(k.parse('zaciatok dopredu dopredu dopredu dopredu dopredu koniec'))
    assert wd._steps_used == 3 and wd.karel_x == 4 and hit == ['steps']


def test_turn_budget():
    wd = _world(); wd.settings.max_turns = 2
    hit = []
    itp = _itp(wd, on_budget=lambda kind: hit.append(kind))
    itp.run(k.parse('zaciatok vlavo vlavo vlavo koniec'))
    assert wd._turns_used == 2 and hit == ['turns']


def test_budget_reset():
    wd = _world(); wd._steps_used = 5; wd._turns_used = 3
    wd.reset_inventory()
    assert wd._steps_used == 0 and wd._turns_used == 0


# ---------------- fyzické limity ----------------

def test_max_brick_height_with_kvader():
    wd = _world(); wd.settings.max_brick_height = 6
    nx, ny = wd._front()
    wd.big_bricks[ny][nx] = 1          # kvader = výška 5
    wd.drop_brick(); assert wd.bricks[ny][nx] == 1    # 5+1 <= 6 OK
    wd.drop_brick(); assert wd.bricks[ny][nx] == 1    # 5+2 > 6 blokované


def test_max_drop():
    wd = k.World(10, 8); wd.karel_x = 2; wd.karel_y = 2
    wd.karel_dir = k.Direction.EAST
    wd.big_bricks[2][2] = 1            # Karel na kvadri (výška 5)
    wd.settings.max_drop = 2
    wd.move_forward(); assert wd.karel_x == 2          # zoskok 5 > 2 blokovaný
    wd.settings.max_drop = -1
    wd.move_forward(); assert wd.karel_x == 3          # neobmedzené OK


# ---------------- bezpečnostné stropy ----------------

def test_infinite_loop_guard():
    wd = _world()
    hit = []
    itp = _itp(wd, on_limit=lambda kind: hit.append(kind))
    itp.run(k.parse('zaciatok kym pravda rob vlavo koniec koniec'))
    assert hit == ['loop']


def test_infinite_loop_empty_body():
    wd = _world()
    hit = []
    itp = _itp(wd, on_limit=lambda kind: hit.append(kind))
    itp.run(k.parse('zaciatok kym pravda rob koniec koniec'))
    assert hit == ['loop']


def test_infinite_recursion():
    wd = _world()
    hit = []
    itp = _itp(wd, on_limit=lambda kind: hit.append(kind))
    itp.run(k.parse('prikaz Tik zaciatok Tik koniec zaciatok Tik koniec'))
    assert hit == ['recursion']


def test_deep_finite_recursion_ok():
    wd = k.World(200, 4); wd.karel_x = 0; wd.karel_y = 0
    wd.karel_dir = k.Direction.EAST
    hit, err, fin = [], [], []
    itp = _itp(wd, on_limit=lambda kk: hit.append(kk),
               on_error=lambda m: err.append(m), on_finish=lambda m: fin.append(m))
    itp.run(k.parse('prikaz Tik zaciatok ak nie stena potom dopredu Tik koniec koniec zaciatok Tik koniec'))
    assert hit == [] and err == [] and wd.karel_x == 199


def test_no_false_positive_limits():
    wd = _world()
    hit, fin = [], []
    itp = _itp(wd, on_limit=lambda kk: hit.append(kk), on_finish=lambda m: fin.append(m))
    itp.run(k.parse('zaciatok opakuj 5 krat dopredu koniec koniec'))
    assert hit == [] and fin == [None] and itp._ops < 50


# ---------------- XML roundtrip ----------------

def test_xml_roundtrip_settings():
    wd = _world()
    s = wd.settings
    s.max_steps = 10; s.max_turns = 4; s.max_drop = 2; s.max_brick_height = 6
    s.brick_limit = 7; s.disabled_cmds = {'BACK', 'RIGHT'}
    wd.goal_conditions.append(k.GoalCondition('karel_pos', x=3, y=1, z=1,
                                              eval_='failure', when='on_step'))
    wd2 = k.World.from_xml(wd.to_xml())
    s2 = wd2.settings
    assert (s2.max_steps, s2.max_turns, s2.max_drop, s2.max_brick_height) == (10, 4, 2, 6)
    assert s2.brick_limit == 7 and s2.disabled_cmds == {'BACK', 'RIGHT'}
    assert len(wd2.goal_conditions) == 1
    c = wd2.goal_conditions[0]
    assert (c.check, c.x, c.y, c.z, c.eval, c.when) == ('karel_pos', 3, 1, 1, 'failure', 'on_step')


# ---------------- misie ----------------

def test_goal_evaluation():
    wd = _world()
    wd.goal_conditions.append(k.GoalCondition('karel_pos', x=wd.karel_x, y=wd.karel_y,
                                              eval_='success', when='on_step'))
    assert k.evaluate_goals(wd, on_step=True) == 'success'


# ---------------- jazykový systém ----------------

def test_lang_system():
    assert k.KW.get('dopredu') == 'FORWARD'
    assert k.KW.get('forward') == 'FORWARD'
    assert k.KW.get('a') == 'AND' and k.KW.get('alebo') == 'OR'
    assert k._primary_kw('FORWARD', 'sk') == 'dopredu'
    assert k._primary_kw('FORWARD', 'en') == 'forward'
    k._switch_prog_lang('en')
    assert k.current_prog_lang() == 'en'
    assert 'forward' in k._cmds_list()
    k._switch_prog_lang('sk')
    assert 'dopredu' in k._cmds_list()
    langs = dict(k._available_prog_langs())
    assert 'sk' in langs and 'en_pattis' in langs


def test_ui_strings():
    k._load_ui_lang('sk')
    assert k._T('menu.open_world') != 'menu.open_world'   # kľúč existuje
    assert k._T('neexistujuci.kluc') == 'neexistujuci.kluc'  # fallback


if __name__ == '__main__':
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn(); print(f'OK   {name}')
            except Exception as e:
                fails += 1; print(f'FAIL {name}: {e}')
    sys.exit(1 if fails else 0)
