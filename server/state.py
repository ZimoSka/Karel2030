# -*- coding: utf-8 -*-
"""Serializácia World → state JSON podľa docs/api.md §4 (+ opačný smer)."""
from karel_core import World, GoalCondition, Direction

# Limity veľkosti vstupov (docs/api.md §6)
MAX_PROGRAM_BYTES = 64 * 1024
MAX_KARXML_BYTES  = 256 * 1024


def world_to_state(w: World, full: bool = True) -> dict:
    """World → sparse state JSON. full=True pridá settings + mission
    (posiela sa učiteľovi a pri connect; bežné step správy ich nemajú)."""
    s = w.settings
    state = {
        'width': w.width, 'height': w.height,
        'karel': {'x': w.karel_x, 'y': w.karel_y, 'dir': w.karel_dir.to_str()},
        'bricks':     [[x, y, w.bricks[y][x]] for y in range(w.height)
                       for x in range(w.width) if w.bricks[y][x] > 0],
        'big_bricks': [[x, y] for y in range(w.height)
                       for x in range(w.width) if w.big_bricks[y][x] > 0],
        'marks':      [[x, y] for y in range(w.height)
                       for x in range(w.width) if w.marks[y][x]],
        'walls':      [[x, y, side] for y in range(w.height)
                       for x in range(w.width) for side in sorted(w.walls[y][x])],
        'inventory':  {'bricks': w._bricks_left, 'big_bricks': w._big_bricks_left,
                       'marks': w._marks_left},
        'counters':   {'steps_used': w._steps_used, 'turns_used': w._turns_used},
        'meta': {'title': w.title, 'intro_html': w.intro_html,
                 'success_html': w.success_html, 'failure_html': w.failure_html},
    }
    if full:
        state['settings'] = {
            'prog_lang': s.prog_lang,
            'disabled_cmds': sorted(s.disabled_cmds),
            'disable_procedure': s.disable_procedure,
            'disable_graphic': s.disable_graphic,
            'disable_command': s.disable_command,
            'max_climb': s.max_climb, 'max_drop': s.max_drop,
            'max_steps': s.max_steps, 'max_turns': s.max_turns,
            'max_brick_height': s.max_brick_height,
            'brick_limit': s.brick_limit, 'big_brick_limit': s.big_brick_limit,
            'mark_limit': s.mark_limit,
            'camera_locked': s.camera_locked,
            'camera': {'az': s.camera_az, 'el': s.camera_el, 'dist': s.camera_dist},
            'reset_on_failure': w.mission_reset_on_failure,
        }
        state['mission'] = [cond_to_dict(c) for c in w.goal_conditions]
    return state


def cond_to_dict(c: GoalCondition) -> dict:
    """GoalCondition → plochý dict (rovnaké polia ako XML atribúty)."""
    d = {'check': c.check, 'eval': c.eval, 'when': c.when,
         'op': c.op, 'negate': c.negate}
    for k in ('x', 'y', 'z', 'cell_marks', 'cell_bricks', 'cell_big_bricks'):
        v = getattr(c, k)
        if v is not None:
            d[k] = v
    if c.check == 'snapshot' and c.snap:
        snap = dict(c.snap)
        kd = snap.get('karel_dir')
        if isinstance(kd, Direction):
            snap['karel_dir'] = kd.to_str()
        d['snap'] = snap
    return d


def cond_from_dict(d: dict) -> GoalCondition:
    """Dict → GoalCondition (pre apply_settings z učiteľského frontendu)."""
    c = GoalCondition(
        check=d.get('check', 'karel_pos'),
        eval_=d.get('eval', 'success'),
        when=d.get('when', 'on_finish'),
        op=d.get('op', 'or'),
        negate=bool(d.get('negate', False)),
        x=d.get('x'), y=d.get('y'), z=d.get('z'),
        cell_marks=d.get('cell_marks'),
        cell_bricks=d.get('cell_bricks'),
        cell_big_bricks=d.get('cell_big_bricks'))
    snap = d.get('snap')
    if snap:
        snap = dict(snap)
        if isinstance(snap.get('karel_dir'), str):
            snap['karel_dir'] = Direction.from_str(snap['karel_dir'])
        c.snap = snap
    return c


def karxml_to_world(karxml: str) -> World:
    """.karxml reťazec → World; kontroluje limit veľkosti."""
    if len(karxml.encode('utf-8', errors='replace')) > MAX_KARXML_BYTES:
        raise ValueError('karxml too large')
    return World.from_xml(karxml)
