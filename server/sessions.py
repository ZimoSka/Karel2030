# -*- coding: utf-8 -*-
"""Session manager — token → World + KarelInterpreter.

Beh programu vo vlákne (ako desktop verzia); interpreter callbacky
(on_step/on_finish/on_error/on_budget/on_limit) pchajú JSON správy do
asyncio fronty cez loop.call_soon_threadsafe — WS coroutine ich odosiela."""
import asyncio, threading
from karel_core import (World, KarelInterpreter, KarelBudget, parse, ParseErr,
                        evaluate_goals, KW, CMD_T)
from .state import world_to_state, MAX_PROGRAM_BYTES

DELAY_MIN, DELAY_MAX = 0.02, 3.0


def _v1(msg: dict) -> dict:
    msg['v'] = 1
    return msg


class Session:
    """Jedna živá WS session: vlastný World (+ _base) a interpreter."""

    def __init__(self, world: World, teacher: bool = False):
        self.teacher = teacher
        self.queue: asyncio.Queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self._thread: threading.Thread | None = None
        self.delay = 0.25
        self.load(world)

    # --- svet ---------------------------------------------------------------
    def load(self, world: World):
        """Natiahne nový svet — base = štartovací stav (vzor pre reset)."""
        self.base = world.copy()
        self.world = world
        self.world.reset_inventory()
        self.itp = self._new_itp()

    def _new_itp(self) -> KarelInterpreter:
        itp = KarelInterpreter(self.world)
        itp.delay = self.delay
        itp.on_step   = self._on_step
        itp.on_finish = self._on_finish
        itp.on_error  = lambda m: self._emit({'type': 'error', 'message': str(m)})
        itp.on_budget = lambda k: self._emit({'type': 'budget', 'kind': k})
        itp.on_limit  = lambda k: self._emit({'type': 'limit', 'kind': k})
        return itp

    def reset(self):
        """_reset_world() — svet späť na štart, počítadlá vynulované."""
        self.stop()
        self.world = self.base.copy()
        self.world.reset_inventory()
        self.itp = self._new_itp()

    # --- emit (volané aj z interpreter vlákna) ----------------------------
    def _emit(self, msg: dict):
        self.loop.call_soon_threadsafe(self.queue.put_nowait, _v1(msg))

    def state_msg(self, reason: str) -> dict:
        # settings + mission len pre učiteľa a pri connect/load (kontrakt §4)
        full = self.teacher or reason in ('connect', 'load')
        return _v1({'type': 'state', 'reason': reason,
                    'state': world_to_state(self.world, full=full)})

    # --- interpreter callbacky (bežia v run vlákne) ------------------------
    def _on_step(self):
        self._emit({'type': 'step', 'state': world_to_state(self.world, full=False)})
        result = evaluate_goals(self.world, on_step=True)
        if result:
            self._mission(result)
            self.itp.stop()

    def _on_finish(self, msg):
        status = 'stopped' if msg else 'done'
        self._emit({'type': 'finished', 'status': status})
        if status == 'done':
            result = evaluate_goals(self.world, on_step=False)
            if result:
                self._mission(result)

    def _mission(self, result: str):
        html = (self.world.success_html if result == 'success'
                else self.world.failure_html)
        self._emit({'type': 'mission', 'result': result, 'message_html': html})

    # --- beh programu --------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def run_program(self, program: str):
        """Parsuj a spusti program v novom vlákne. Chyby → správy do fronty."""
        if self.running:
            self._emit({'type': 'error', 'message': 'Program už beží.'})
            return
        if len(program.encode('utf-8', errors='replace')) > MAX_PROGRAM_BYTES:
            self._emit({'type': 'error', 'message': 'Program je príliš veľký.'})
            return
        try:
            prog = parse(program)
        except ParseErr as e:
            self._emit({'type': 'parse_error', 'message': str(e), 'line': e.line})
            return
        if self.world.settings.disable_procedure and prog.procedures:
            self._emit({'type': 'parse_error', 'line': 0,
                        'message': 'Vlastné príkazy sú v tomto svete zakázané.'})
            return
        self.itp.delay = self.delay
        self._emit({'type': 'started'})
        self._thread = threading.Thread(target=self.itp.run, args=(prog,), daemon=True)
        self._thread.start()

    def stop(self):
        self.itp.stop()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def set_speed(self, delay):
        try:
            delay = float(delay)
        except (TypeError, ValueError):
            return
        self.delay = max(DELAY_MIN, min(DELAY_MAX, delay))
        self.itp.delay = self.delay

    # --- priamy príkaz (tlačidlo) ---------------------------------------------
    def direct(self, word: str) -> list:
        """Vykoná priamy príkaz; vráti zoznam správ na odoslanie."""
        if self.running:
            return [_v1({'type': 'direct_result', 'ok': False,
                         'error': 'running'})]
        token = KW.get((word or '').strip().lower())
        if token not in CMD_T:
            return [_v1({'type': 'direct_result', 'ok': False,
                         'error': 'unknown_cmd'})]
        if token in self.world.settings.disabled_cmds:
            return [_v1({'type': 'direct_result', 'ok': False,
                         'error': 'disabled'})]
        w = self.world
        actions = {'FORWARD': w.move_forward, 'BACK': w.move_back,
                   'LEFT': w.turn_left, 'RIGHT': w.turn_right,
                   'DROP': w.drop_brick, 'PICK': w.pick_brick,
                   'DROP_BIG': w.drop_big_brick, 'MARK': w.mark, 'CLEAR': w.clear}
        out = []
        try:
            fn = actions.get(token)
            if fn:
                fn()   # SLOWLY/QUICKLY nemajú priamy efekt na svet
            out.append(_v1({'type': 'direct_result', 'ok': True}))
        except KarelBudget as e:
            # rozpočet vyčerpaný — príkaz sa nevykonal, frontend zobrazí dialóg
            out.append(_v1({'type': 'direct_result', 'ok': False, 'error': 'budget'}))
            out.append(_v1({'type': 'budget', 'kind': e.kind}))
            return out
        out.append(_v1({'type': 'step', 'state': world_to_state(w, full=False)}))
        result = evaluate_goals(w, on_step=True)
        if result:
            html = w.success_html if result == 'success' else w.failure_html
            out.append(_v1({'type': 'mission', 'result': result,
                            'message_html': html}))
        return out
