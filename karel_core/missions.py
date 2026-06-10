# -*- coding: utf-8 -*-
"""Karel core – systém misií (GoalCondition, evaluate_goals)."""
import xml.etree.ElementTree as ET
from .base import Direction

# =========================================================================
# PODMIENKY  MISIE  (goal conditions)
# =========================================================================

class GoalCondition:
    """Jedna podmienka misie v plochom zozname s AND/OR operátorom.

    Atribúty:
        check   – 'karel_pos' | 'sign' | 'brick_ahead' | 'wall_ahead' |
                  'cell_state' | 'snapshot'
        eval    – 'success' | 'failure'
        when    – 'on_step' | 'on_finish'
        op      – 'or' | 'and'   (operátor s predchádzajúcou podmienkou rovnakého eval)
        negate  – True → výsledok check() sa neguje
        x, y    – súradnice (pre karel_pos, cell_state)
        z       – výška dlaždice kde Karel stojí (pre karel_pos; None = ignorovať)
        cell_marks, cell_bricks, cell_big_bricks – pre cell_state
        snap    – dict so snapshot dátami (pre snapshot)
    """
    def __init__(self, check, eval_='success', when='on_finish', op='or', negate=False,
                 x=None, y=None, z=None,
                 cell_marks=None, cell_bricks=None, cell_big_bricks=None,
                 snap=None):
        self.check  = check
        self.eval   = eval_
        self.when   = when
        self.op     = op
        self.negate = negate
        self.x = x; self.y = y; self.z = z
        self.cell_marks      = cell_marks
        self.cell_bricks     = cell_bricks
        self.cell_big_bricks = cell_big_bricks
        self.snap = snap   # dict: bricks, big_bricks, marks, karel_x, karel_y, karel_dir

    # --- snapshot helper ---------------------------------------------------
    @staticmethod
    def snapshot_from_world(world, include_karel=False):
        from copy import deepcopy
        s = dict(bricks=deepcopy(world.bricks),
                 big_bricks=deepcopy(world.big_bricks),
                 marks=deepcopy(world.marks))
        if include_karel:
            s['karel_x'] = world.karel_x
            s['karel_y'] = world.karel_y
            s['karel_dir'] = world.karel_dir
        return s

    # --- raw check (bez negate) -------------------------------------------
    def _check_raw(self, world):
        if self.check == 'karel_pos':
            if self.x is not None and world.karel_x != self.x: return False
            if self.y is not None and world.karel_y != self.y: return False
            if self.z is not None and world._height(world.karel_x, world.karel_y) != self.z:
                return False
            return True
        if self.check == 'sign':
            return bool(world.marks[world.karel_y][world.karel_x])
        if self.check == 'brick_ahead':
            nx, ny = world._front()
            if not (0 <= nx < world.width and 0 <= ny < world.height): return False
            return world.bricks[ny][nx] > 0 or world.big_bricks[ny][nx] > 0
        if self.check == 'wall_ahead':
            return world.check_wall()
        if self.check == 'cell_state':
            x, y = self.x, self.y
            if not (0 <= x < world.width and 0 <= y < world.height): return False
            if self.cell_marks is not None and world.marks[y][x] != self.cell_marks: return False
            if self.cell_bricks is not None and world.bricks[y][x] != self.cell_bricks: return False
            if self.cell_big_bricks is not None and world.big_bricks[y][x] != self.cell_big_bricks: return False
            return True
        if self.check == 'snapshot' and self.snap:
            s = self.snap
            if world.bricks != s.get('bricks'): return False
            if world.big_bricks != s.get('big_bricks'): return False
            if world.marks != s.get('marks'): return False
            if s.get('karel_x') is not None and world.karel_x != s['karel_x']: return False
            if s.get('karel_y') is not None and world.karel_y != s['karel_y']: return False
            if s.get('karel_dir') is not None and world.karel_dir != s['karel_dir']: return False
            return True
        return False

    def check_val(self, world):
        val = self._check_raw(world)
        return (not val) if self.negate else val

    # --- popis pre GUI ----------------------------------------------------
    def describe(self):
        neg = '¬' if self.negate else ''
        ev  = '✓' if self.eval == 'success' else '✗'
        wh  = '⚡' if self.when == 'on_step' else '🏁'
        if self.check == 'karel_pos':
            parts = []
            if self.x is not None: parts.append(f"x={self.x}")
            if self.y is not None: parts.append(f"y={self.y}")
            if self.z is not None: parts.append(f"z={self.z}")
            loc = ','.join(parts) if parts else '*'
            return f"{ev}{wh} {neg}Karel@({loc})"
        if self.check == 'sign':        return f"{ev}{wh} {neg}značka pod Karelom"
        if self.check == 'brick_ahead': return f"{ev}{wh} {neg}tehla pred Karelom"
        if self.check == 'wall_ahead':  return f"{ev}{wh} {neg}stena pred Karelom"
        if self.check == 'cell_state':
            p = []
            if self.cell_marks is not None:      p.append('značka' if self.cell_marks else 'bez značky')
            if self.cell_bricks is not None:     p.append(f"{self.cell_bricks}× tehla")
            if self.cell_big_bricks is not None: p.append(f"{self.cell_big_bricks}× kvader")
            return f"{ev}{wh} {neg}políčko({self.x},{self.y}): {', '.join(p)}"
        if self.check == 'snapshot':    return f"{ev}{wh} {neg}snímok miestnosti"
        return f"{ev}{wh} {neg}{self.check}"

    # --- XML --------------------------------------------------------------
    def to_xml_el(self):
        attrs = dict(check=self.check, eval=self.eval, when=self.when, op=self.op)
        if self.negate: attrs['negate'] = 'true'
        if self.x is not None: attrs['x'] = str(self.x)
        if self.y is not None: attrs['y'] = str(self.y)
        if self.z is not None: attrs['z'] = str(self.z)
        if self.cell_marks is not None:      attrs['cell_marks']      = 'true' if self.cell_marks else 'false'
        if self.cell_bricks is not None:     attrs['cell_bricks']     = str(self.cell_bricks)
        if self.cell_big_bricks is not None: attrs['cell_big_bricks'] = str(self.cell_big_bricks)
        el = ET.Element('condition', **attrs)
        if self.check == 'snapshot' and self.snap:
            s = self.snap
            br = ET.SubElement(el, 'bricks')
            for row in s['bricks']:
                ET.SubElement(br, 'row').text = ','.join(map(str, row))
            bb = ET.SubElement(el, 'bigbricks')
            for row in s['big_bricks']:
                ET.SubElement(bb, 'row').text = ','.join(map(str, row))
            mk = ET.SubElement(el, 'marks')
            for row in s['marks']:
                ET.SubElement(mk, 'row').text = ','.join('1' if v else '0' for v in row)
            if s.get('karel_x') is not None:
                el.set('karel_x', str(s['karel_x']))
                el.set('karel_y', str(s['karel_y']))
                el.set('karel_dir', s['karel_dir'].to_str())
        return el

    @staticmethod
    def from_xml_el(el):
        def _gi(a): return int(el.get(a)) if el.get(a) is not None else None
        def _gb(a): v = el.get(a); return (v.lower() == 'true') if v is not None else None
        check  = el.get('check', el.get('type', 'karel_pos'))  # 'type' = starý formát
        eval_  = el.get('eval', 'success')
        when   = el.get('when', 'on_finish')
        op     = el.get('op',   'or')
        negate = el.get('negate', 'false').lower() == 'true'
        c = GoalCondition(check=check, eval_=eval_, when=when, op=op, negate=negate,
                          x=_gi('x'), y=_gi('y'), z=_gi('z'),
                          cell_marks=_gb('cell_marks'),
                          cell_bricks=_gi('cell_bricks'),
                          cell_big_bricks=_gi('cell_big_bricks'))
        # Starý formát kompatibilita
        if check == 'karel_pos' and el.get('height') is not None:
            c.z = int(el.get('height'))
        if check == 'cell_state':
            c.cell_marks      = _gb('marks') if c.cell_marks is None else c.cell_marks
            c.cell_bricks     = _gi('bricks') if c.cell_bricks is None else c.cell_bricks
            c.cell_big_bricks = _gi('big_bricks') if c.cell_big_bricks is None else c.cell_big_bricks
        if check == 'snapshot':
            def _rows(tag):
                return [[int(v) for v in r.text.split(',')] for r in el.findall(f'{tag}/row')]
            def _brows(tag):
                return [[v == '1' for v in r.text.split(',')] for r in el.findall(f'{tag}/row')]
            kx = _gi('karel_x'); ky = _gi('karel_y')
            kd = Direction.from_str(el.get('karel_dir')) if el.get('karel_dir') else None
            br = _rows('bricks'); bb = _rows('bigbricks'); mk = _brows('marks')
            if br and bb and mk:
                c.snap = dict(bricks=br, big_bricks=bb, marks=mk,
                              karel_x=kx, karel_y=ky, karel_dir=kd)
        return c


def evaluate_goals(world, on_step=False):
    """Vyhodnotí podmienky misie. Vracia 'success', 'failure' alebo None.

    Podmienky rovnakého eval sa kombinujú sekvenciálne (zľava doprava)
    operátorom op každej podmienky (okrem prvej).
    Failure sa vyhodnocuje pred success.
    """
    when = 'on_step' if on_step else 'on_finish'
    for eval_type in ('failure', 'success'):
        group = [c for c in world.goal_conditions
                 if c.eval == eval_type and c.when == when]
        if not group:
            continue
        result = None
        for c in group:
            val = c.check_val(world)
            if result is None:
                result = val
            elif c.op == 'and':
                result = result and val
            else:
                result = result or val
        if result:
            return eval_type
    return None


