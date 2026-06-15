# -*- coding: utf-8 -*-
"""Karel core – dátový model sveta (World, WorldSettings) + .karxml I/O."""
import os, re, json, math
import xml.etree.ElementTree as ET          # stavba XML (to_xml)
try:
    # bezpečné parsovanie neoverených karxml — blokuje DTD/entity (billion-laughs, XXE)
    from defusedxml.ElementTree import fromstring as _safe_fromstring, parse as _safe_parse
except ImportError:                          # fallback ak defusedxml nie je k dispozícii
    _safe_fromstring, _safe_parse = ET.fromstring, ET.parse
from xml.dom import minidom

# Horný limit rozmerov sveta — bráni alokácii obrích mriežok (DoS cez from_xml)
MAX_WORLD_DIM = 200
from copy import deepcopy
import html as _html_mod
from .base import Direction, KarelError, KarelStop, KarelBudget, KarelLimit
from .missions import GoalCondition
from .lang import _INTERP_LANG_DIR

class WorldSettings:
    """Nastavenia obmedzení a reštrikcií sveta — ukladajú sa do .karxml."""
    def __init__(self):
        self.brick_limit      = -1    # max malých tehál pre Karela (-1 = ∞)
        self.big_brick_limit  = -1    # max veľkých tehál (-1 = ∞)
        self.mark_limit       = -1    # max značiek (-1 = ∞)
        # Zakázané príkazy: množina tokenov z CMD_T (napr. {'FORWARD','DROP'})
        self.disabled_cmds    = set()
        # Zakázať definovanie vlastných príkazov ('prikaz … koniec')
        self.disable_procedure = False
        # Max. výška výstupu — o koľko tehiel môže Karel vyskočiť naraz (default 1)
        self.max_climb        = 1
        # Max. zoskok nadol — o koľko tehiel môže Karel zoskočiť naraz (-1 = ∞)
        self.max_drop         = -1
        # Rozpočet pohybu — počítané od posledného resetu (-1 = ∞)
        self.max_steps        = -1    # max počet krokov (dopredu/dozadu)
        self.max_turns        = -1    # max počet otočení (vlavo/vpravo)
        # Max. výška stohu tehiel, do ktorej môže Karel klásť tehly (-1 = ∞)
        # Počíta sa v jednotkách malých tehiel; kvader = 5 jednotiek
        self.max_brick_height = -1
        # Jazyk programovania pre tento svet ('sk' alebo 'en')
        self.prog_lang        = 'sk'
        # Zakázať grafické ovládanie Karla (D-pad + akčné tlačidlá)
        self.disable_graphic  = False
        # Zakázať príkazové ovládanie Karla (textový riadok priamych príkazov)
        self.disable_command  = False
        # Zamknúť pohľad kamery
        self.camera_locked    = False
        self.camera_az        = math.radians(225)
        self.camera_el        = math.radians(28)
        self.camera_dist      = 16.0


class World:
    """Karelova mriežková mapa.  x=0 vľavo, y=0 dole."""
    BIG_BRICK_UNITS = 5   # veľká tehla = 5 malých

    def __init__(self, width=12, height=10):
        self.width=width; self.height=height
        self.walls      = [[set() for _ in range(width)] for _ in range(height)]
        self.bricks     = [[0     for _ in range(width)] for _ in range(height)]
        self.big_bricks = [[0     for _ in range(width)] for _ in range(height)]
        self.marks      = [[False  for _ in range(width)] for _ in range(height)]
        self.karel_x=0; self.karel_y=0; self.karel_dir=Direction.EAST
        self.settings = WorldSettings()
        # Runtime inventár — resetuje sa pri každom reštarte hry
        self._bricks_left     = -1
        self._big_bricks_left = -1
        self._marks_left      = -1
        # Rozpočet pohybu — počítadlá od posledného resetu
        self._steps_used      = 0
        self._turns_used      = 0
        # Metadáta sveta
        self.title        = ''
        self.intro_html   = ''
        self.success_html = ''
        self.failure_html = ''
        self.program_text = ''
        self.next_level   = ''
        self.prev_level   = ''
        # Misia — podmienky a režim vyhodnocovania
        self.goal_conditions: list    = []   # list[GoalCondition]
        self.mission_reset_on_failure: bool = False
        self._add_border_walls()

    def _add_border_walls(self):
        for x in range(self.width):
            self.walls[0][x].add('S'); self.walls[self.height-1][x].add('N')
        for y in range(self.height):
            self.walls[y][0].add('W'); self.walls[y][self.width-1].add('E')

    def reset_inventory(self):
        """Resetuje inventár podľa nastavení — volať po každom reštarte sveta."""
        self._bricks_left     = self.settings.brick_limit
        self._big_bricks_left = self.settings.big_brick_limit
        self._marks_left      = self.settings.mark_limit
        self._steps_used      = 0
        self._turns_used      = 0

    def inventory_str(self):
        """Vráti (malé, veľké, značky) ako zobraziteľné reťazce."""
        def _s(v): return '∞' if v < 0 else str(v)
        return _s(self._bricks_left), _s(self._big_bricks_left), _s(self._marks_left)

    def resize(self, new_w, new_h):
        """Zmení rozmery sveta; zachová tehly a značky v rámci nových rozmerov."""
        new_walls      = [[set()  for _ in range(new_w)] for _ in range(new_h)]
        new_bricks     = [[0      for _ in range(new_w)] for _ in range(new_h)]
        new_big_bricks = [[0      for _ in range(new_w)] for _ in range(new_h)]
        new_marks      = [[False  for _ in range(new_w)] for _ in range(new_h)]
        for y in range(min(self.height, new_h)):
            for x in range(min(self.width, new_w)):
                # Interné steny (nie na okraji starého sveta)
                if not (x==0 or x==self.width-1 or y==0 or y==self.height-1):
                    new_walls[y][x] = set(self.walls[y][x])
                new_bricks[y][x]     = self.bricks[y][x]
                new_big_bricks[y][x] = self.big_bricks[y][x]
                new_marks[y][x]      = self.marks[y][x]
        self.width=new_w; self.height=new_h
        self.walls=new_walls; self.bricks=new_bricks
        self.big_bricks=new_big_bricks; self.marks=new_marks
        self.karel_x = min(self.karel_x, new_w-1)
        self.karel_y = min(self.karel_y, new_h-1)
        self._add_border_walls()

    def _step(self,x,y,d):
        return (x+1,y) if d==Direction.EAST  else \
               (x-1,y) if d==Direction.WEST  else \
               (x,y+1) if d==Direction.NORTH else (x,y-1)

    def _front(self): return self._step(self.karel_x,self.karel_y,self.karel_dir)

    def add_wall(self,x,y,s):
        self.walls[y][x].add(s)
        opp={'N':'S','S':'N','E':'W','W':'E'}[s]
        nx,ny={'N':(x,y+1),'S':(x,y-1),'E':(x+1,y),'W':(x-1,y)}[s]
        if 0<=nx<self.width and 0<=ny<self.height: self.walls[ny][nx].add(opp)

    def remove_wall(self,x,y,s):
        self.walls[y][x].discard(s)
        opp={'N':'S','S':'N','E':'W','W':'E'}[s]
        nx,ny={'N':(x,y+1),'S':(x,y-1),'E':(x+1,y),'W':(x-1,y)}[s]
        if 0<=nx<self.width and 0<=ny<self.height: self.walls[ny][nx].discard(opp)

    def is_wall_ahead(self):
        return self.karel_dir.to_str() in self.walls[self.karel_y][self.karel_x]

    def _height(self, x, y):
        """Celková výška bunky v jednotkách malých tehál."""
        return self.bricks[y][x] + self.big_bricks[y][x] * self.BIG_BRICK_UNITS

    def _can_step_height(self, dh):
        """True ak Karel zvládne výškový rozdiel dh (výstup/zoskok)."""
        if dh > self.settings.max_climb: return False          # príliš vysoký výstup
        md = self.settings.max_drop
        if md >= 0 and -dh > md: return False                  # príliš hlboký zoskok
        return True

    def _consume_step(self):
        """Skontroluje rozpočet krokov; vyhodí KarelBudget ak je vyčerpaný."""
        ms = self.settings.max_steps
        if ms >= 0 and self._steps_used >= ms: raise KarelBudget('steps')
        self._steps_used += 1

    def move_forward(self):
        if self.is_wall_ahead(): return
        nx,ny = self._front()
        dh = self._height(nx,ny) - self._height(self.karel_x,self.karel_y)
        if not self._can_step_height(dh): return
        self._consume_step()
        self.karel_x,self.karel_y = nx,ny

    def move_back(self):
        back=self.karel_dir.opposite()
        if back.to_str() in self.walls[self.karel_y][self.karel_x]: return
        bx,by = self._step(self.karel_x,self.karel_y,back)
        dh = self._height(bx,by) - self._height(self.karel_x,self.karel_y)
        if not self._can_step_height(dh): return
        self._consume_step()
        self.karel_x,self.karel_y = bx,by

    def _consume_turn(self):
        """Skontroluje rozpočet otočení; vyhodí KarelBudget ak je vyčerpaný."""
        mt = self.settings.max_turns
        if mt >= 0 and self._turns_used >= mt: raise KarelBudget('turns')
        self._turns_used += 1

    def turn_left(self):  self._consume_turn(); self.karel_dir=self.karel_dir.left()
    def turn_right(self): self._consume_turn(); self.karel_dir=self.karel_dir.right()

    # Tehly/bricks: kladú/dvíhajú sa PRED Karelom; znacka je POD nim
    def _height_limit_ok(self, nx, ny, added_units):
        """True ak po pridaní added_units jednotiek neprekročíme max_brick_height.
        Kvader = BIG_BRICK_UNITS (5) jednotiek; _height to už zohľadňuje."""
        mh = self.settings.max_brick_height
        if mh < 0: return True
        return self._height(nx, ny) + added_units <= mh

    def drop_brick(self):
        if self.is_wall_ahead(): return
        if self._bricks_left == 0: return
        nx,ny=self._front()
        if not self._height_limit_ok(nx, ny, 1): return
        self.bricks[ny][nx]+=1
        if self._bricks_left > 0: self._bricks_left -= 1
    def drop_big_brick(self):
        """Kvader (veľká tehla) — na políčku môže byť max 1 kvader."""
        if self.is_wall_ahead(): return
        if self._big_bricks_left == 0: return
        nx,ny=self._front()
        if self.big_bricks[ny][nx] >= 1: return
        if not self._height_limit_ok(nx, ny, self.BIG_BRICK_UNITS): return
        self.big_bricks[ny][nx] = 1
        if self._big_bricks_left > 0: self._big_bricks_left -= 1
    def pick_brick(self):
        if self.is_wall_ahead(): return
        nx,ny=self._front()
        if self.bricks[ny][nx]<=0: return
        self.bricks[ny][nx]-=1
        if self._bricks_left >= 0: self._bricks_left += 1

    def pick_big_brick(self):
        """Zdvihne kvader spred Karela — len cez GUI, nie programovo."""
        if self.is_wall_ahead(): return
        nx,ny=self._front()
        if self.big_bricks[ny][nx]<=0: return
        self.big_bricks[ny][nx]-=1
        if self._big_bricks_left >= 0: self._big_bricks_left += 1

    def pick_any_brick(self):
        """Zdvihne malú tehlu ak je; ak nie, zdvihne kvader. Používa sa len z GUI."""
        nx,ny=self._front()
        if self.bricks[ny][nx] > 0:
            self.pick_brick()
        elif self.big_bricks[ny][nx] > 0:
            self.pick_big_brick()
    def mark(self):
        if not self.marks[self.karel_y][self.karel_x]:
            if self._marks_left == 0: return
            if self._marks_left > 0: self._marks_left -= 1
        self.marks[self.karel_y][self.karel_x]=True
    def clear(self):
        if self.marks[self.karel_y][self.karel_x]:
            if self._marks_left >= 0: self._marks_left += 1
        self.marks[self.karel_y][self.karel_x]=False

    def check_wall(self):
        if self.is_wall_ahead(): return True
        # Kvader pred Karelom — tiež sa správa ako stena
        nx,ny = self._front()
        return (0 <= nx < self.width and 0 <= ny < self.height and
                self.big_bricks[ny][nx] > 0)
    def check_brick(self):
        nx,ny=self._front()
        return (0<=nx<self.width and 0<=ny<self.height and
                (self.bricks[ny][nx]>0 or self.big_bricks[ny][nx]>0))
    def check_free(self):
        nx,ny=self._front()
        return not (0<=nx<self.width and 0<=ny<self.height and
                    (self.bricks[ny][nx]>0 or self.big_bricks[ny][nx]>0))
    def check_sign(self):  return self.marks[self.karel_y][self.karel_x]

    def to_json(self):
        return dict(width=self.width,height=self.height,
                    karel_x=self.karel_x,karel_y=self.karel_y,
                    karel_dir=self.karel_dir.to_str(),
                    walls=[[x,y,s] for y in range(self.height) for x in range(self.width) for s in self.walls[y][x]],
                    bricks=[[x,y,self.bricks[y][x]] for y in range(self.height) for x in range(self.width) if self.bricks[y][x]>0],
                    big_bricks=[[x,y,self.big_bricks[y][x]] for y in range(self.height) for x in range(self.width) if self.big_bricks[y][x]>0],
                    marks=[[x,y] for y in range(self.height) for x in range(self.width) if self.marks[y][x]])
    @staticmethod
    def from_json(d):
        w=World(d['width'],d['height'])
        w.karel_x=d['karel_x']; w.karel_y=d['karel_y']
        w.karel_dir=Direction.from_str(d['karel_dir'])
        for x,y,s in d.get('walls',[]): w.walls[y][x].add(s)
        for x,y,c in d.get('bricks',[]): w.bricks[y][x]=c
        for x,y,c in d.get('big_bricks',[]): w.big_bricks[y][x]=c
        for x,y   in d.get('marks',[]): w.marks[y][x]=True
        return w

    # ---- XML  ---------------------------------------------------------------
    def to_xml(self):
        """Vráti XML reťazec (.karxml formát)."""
        root = ET.Element('world', width=str(self.width), height=str(self.height))
        ET.SubElement(root, 'karel',
                      x=str(self.karel_x), y=str(self.karel_y),
                      dir=self.karel_dir.to_str())
        # steny
        ws = ET.SubElement(root, 'walls')
        for y in range(self.height):
            for x in range(self.width):
                for s in sorted(self.walls[y][x]):
                    ET.SubElement(ws, 'wall', x=str(x), y=str(y), side=s)
        # malé tehly
        br = ET.SubElement(root, 'bricks')
        for y in range(self.height):
            for x in range(self.width):
                if self.bricks[y][x] > 0:
                    ET.SubElement(br, 'brick', x=str(x), y=str(y), count=str(self.bricks[y][x]))
        # veľké tehly
        bb = ET.SubElement(root, 'bigbricks')
        for y in range(self.height):
            for x in range(self.width):
                if self.big_bricks[y][x] > 0:
                    ET.SubElement(bb, 'bigbrick', x=str(x), y=str(y), count=str(self.big_bricks[y][x]))
        # značky
        mk = ET.SubElement(root, 'marks')
        for y in range(self.height):
            for x in range(self.width):
                if self.marks[y][x]:
                    ET.SubElement(mk, 'mark', x=str(x), y=str(y))
        # metadáta
        def _txt(tag, val):
            if val:
                el = ET.SubElement(root, tag)
                el.text = val
        _txt('title',        self.title)
        _txt('intro',        self.intro_html)
        _txt('success',      self.success_html)
        _txt('failure',      self.failure_html)
        _txt('program',      self.program_text)
        _txt('next_level',   self.next_level)
        _txt('prev_level',   self.prev_level)
        # nastavenia sveta
        s = self.settings
        cam_custom = (abs(s.camera_az - math.radians(225)) > 1e-6
                      or abs(s.camera_el - math.radians(28)) > 1e-6
                      or abs(s.camera_dist - 16.0) > 1e-6)
        has_settings = (s.brick_limit!=-1 or s.big_brick_limit!=-1 or s.mark_limit!=-1
                        or s.disabled_cmds or s.disable_procedure or s.camera_locked
                        or s.disable_graphic or s.disable_command or cam_custom
                        or s.max_climb != 1 or s.prog_lang != 'sk'
                        or s.max_drop != -1 or s.max_steps != -1 or s.max_turns != -1
                        or s.max_brick_height != -1)
        if has_settings:
            st = ET.SubElement(root, 'settings')
            ET.SubElement(st,'max_climb').text        = str(s.max_climb)
            if s.max_drop != -1:
                ET.SubElement(st,'max_drop').text         = str(s.max_drop)
            if s.max_steps != -1:
                ET.SubElement(st,'max_steps').text        = str(s.max_steps)
            if s.max_turns != -1:
                ET.SubElement(st,'max_turns').text        = str(s.max_turns)
            if s.max_brick_height != -1:
                ET.SubElement(st,'max_brick_height').text = str(s.max_brick_height)
            if s.prog_lang != 'sk':
                ET.SubElement(st,'prog_lang').text    = s.prog_lang
            ET.SubElement(st,'brick_limit').text     = str(s.brick_limit)
            ET.SubElement(st,'big_brick_limit').text = str(s.big_brick_limit)
            ET.SubElement(st,'mark_limit').text      = str(s.mark_limit)
            if s.disabled_cmds:
                ET.SubElement(st,'disabled_cmds').text = ','.join(sorted(s.disabled_cmds))
            if s.disable_procedure:
                ET.SubElement(st,'disable_procedure').text = 'true'
            if s.disable_graphic:
                ET.SubElement(st,'disable_graphic').text = 'true'
            if s.disable_command:
                ET.SubElement(st,'disable_command').text = 'true'
            if s.camera_locked:
                ET.SubElement(st,'camera_locked').text = 'true'
            # uložený pohľad kamery (vždy — aby sa zapamätal aktuálny pohľad,
            # nielen pri zamknutej kamere)
            ET.SubElement(st,'camera_az').text    = str(s.camera_az)
            ET.SubElement(st,'camera_el').text    = str(s.camera_el)
            ET.SubElement(st,'camera_dist').text  = str(s.camera_dist)
        # misia — podmienky splnenia
        if self.goal_conditions or self.mission_reset_on_failure:
            miss = ET.SubElement(root, 'mission')
            if self.mission_reset_on_failure:
                miss.set('reset_on_failure', 'true')
            for cond in self.goal_conditions:
                miss.append(cond.to_xml_el())
        # pekné formátovanie
        raw = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(raw)
        return dom.toprettyxml(indent='  ', encoding=None)

    @staticmethod
    def from_xml(xml_str):
        """Načíta svet z XML reťazca alebo cesty k súboru."""
        # os.path.isfile len pre krátke reťazce — dlhý karxml nie je cesta a
        # vyhol by sa zbytočnej syscall/chybe pri vstupe s NUL bajtmi
        if len(xml_str) < 260 and os.path.isfile(xml_str):
            tree = _safe_parse(xml_str)
            root = tree.getroot()
        else:
            root = _safe_fromstring(xml_str)
        try:
            width, height = int(root.get('width')), int(root.get('height'))
        except (TypeError, ValueError):
            raise ValueError('svet: chýba/neplatné width alebo height')
        if not (1 <= width <= MAX_WORLD_DIM and 1 <= height <= MAX_WORLD_DIM):
            raise ValueError(f'svet: rozmer mimo 1..{MAX_WORLD_DIM}')
        w = World(width, height)
        k = root.find('karel')
        if k is not None:
            w.karel_x = int(k.get('x', 0))
            w.karel_y = int(k.get('y', 0))
            w.karel_dir = Direction.from_str(k.get('dir', 'E'))
        for el in root.findall('walls/wall'):
            x, y, s = int(el.get('x')), int(el.get('y')), el.get('side')
            if 0 <= x < w.width and 0 <= y < w.height:
                w.walls[y][x].add(s)
        for el in root.findall('bricks/brick'):
            x, y = int(el.get('x')), int(el.get('y'))
            if 0 <= x < w.width and 0 <= y < w.height:
                w.bricks[y][x] = int(el.get('count', 1))
        for el in root.findall('bigbricks/bigbrick'):
            x, y = int(el.get('x')), int(el.get('y'))
            if 0 <= x < w.width and 0 <= y < w.height:
                w.big_bricks[y][x] = int(el.get('count', 1))
        for el in root.findall('marks/mark'):
            x, y = int(el.get('x')), int(el.get('y'))
            if 0 <= x < w.width and 0 <= y < w.height:
                w.marks[y][x] = True
        def _gtxt(tag): el = root.find(tag); return el.text.strip() if el is not None and el.text else ''
        w.title        = _gtxt('title')
        w.intro_html   = _gtxt('intro')
        w.success_html = _gtxt('success')
        w.failure_html = _gtxt('failure')
        w.program_text = _gtxt('program')
        w.next_level   = _gtxt('next_level')
        w.prev_level   = _gtxt('prev_level')
        # nastavenia
        st = root.find('settings')
        if st is not None:
            def _gi(tag,d):
                el=st.find(tag); return int(el.text) if el is not None and el.text else d
            def _gb(tag):
                el=st.find(tag); return el is not None and (el.text or '').strip().lower()=='true'
            def _gf(tag,d):
                el=st.find(tag); return float(el.text) if el is not None and el.text else d
            w.settings.max_climb        = _gi('max_climb', 1)
            w.settings.max_drop         = _gi('max_drop', -1)
            w.settings.max_steps        = _gi('max_steps', -1)
            w.settings.max_turns        = _gi('max_turns', -1)
            w.settings.max_brick_height = _gi('max_brick_height', -1)
            pl_el = st.find('prog_lang')
            w.settings.prog_lang = (pl_el.text.strip().lower()
                                    if pl_el is not None and pl_el.text else 'sk')
            # fallback: ak .lng pre daný jazyk neexistuje, použi sk
            if not os.path.exists(os.path.join(_INTERP_LANG_DIR, f'{w.settings.prog_lang}.lng')):
                w.settings.prog_lang = 'sk'
            w.settings.brick_limit     = _gi('brick_limit',-1)
            w.settings.big_brick_limit = _gi('big_brick_limit',-1)
            w.settings.mark_limit      = _gi('mark_limit',-1)
            dc = st.find('disabled_cmds')
            if dc is not None and dc.text:
                w.settings.disabled_cmds = set(dc.text.strip().split(','))
            w.settings.disable_procedure = _gb('disable_procedure')
            w.settings.disable_graphic   = _gb('disable_graphic')
            w.settings.disable_command   = _gb('disable_command')
            w.settings.camera_locked     = _gb('camera_locked')
            # uložený pohľad kamery sa načíta vždy (ak je v súbore), nielen pri zámku
            w.settings.camera_az   = _gf('camera_az',  math.radians(225))
            w.settings.camera_el   = _gf('camera_el',  math.radians(28))
            w.settings.camera_dist = _gf('camera_dist', 16.0)
        # misia
        miss_el = root.find('mission')
        if miss_el is not None:
            w.mission_reset_on_failure = (miss_el.get('reset_on_failure','') == 'true')
            for cel in miss_el.findall('condition'):
                w.goal_conditions.append(GoalCondition.from_xml_el(cel))
        return w

    def copy(self): return deepcopy(self)



BUILTIN_WORLD={
    "width":10,"height":8,"karel_x":1,"karel_y":1,"karel_dir":"E",
    "walls":[],
    "bricks":[],
    "marks":[]
}

