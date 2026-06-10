# -*- coding: utf-8 -*-
"""Karel 2030 — FastAPI server podľa docs/api.md (REST §2, WS §3)."""
import os, asyncio, configparser
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import karel_core as kc
from .state import (world_to_state, cond_from_dict, karxml_to_world,
                    MAX_KARXML_BYTES, MAX_PROGRAM_BYTES)
from .storage import FileStorage
from .sessions import Session

app = FastAPI(title='Karel 2030')
storage = FileStorage()

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORLDS_DIR = os.environ.get('KAREL_WORLDS_DIR', os.path.join(_ROOT, 'worlds'))
_STATIC_DIR = os.path.join(_ROOT, 'static')


def _err(status: int, code: str, detail: str = '') -> JSONResponse:
    return JSONResponse({'error': code, 'detail': detail}, status_code=status)


# =========================================================================
# REST — jazyky a preklady
# =========================================================================

@app.get('/api/langs/ui')
def langs_ui():
    return [{'code': c, 'name': n} for c, n in kc._available_ui_langs()]


@app.get('/api/langs/ui/{code}')
def langs_ui_one(code: str):
    path = os.path.join(kc._LANG_DIR, f'{code}.ini')
    if '/' in code or '\\' in code or not os.path.exists(path):
        return _err(404, 'not_found', f'ui lang {code!r}')
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path, encoding='utf-8')
    return {f'{sec}.{key}': val.strip()
            for sec in cfg.sections() for key, val in cfg.items(sec)}


@app.get('/api/langs/prog')
def langs_prog():
    return [{'code': c, 'name': n} for c, n in kc._available_prog_langs()]


@app.get('/api/langs/prog/{code}')
def langs_prog_one(code: str):
    if code not in kc._LANG_PRIMARY:
        return _err(404, 'not_found', f'prog lang {code!r}')
    # all_words = celé KW (interpreter akceptuje všetky jazyky súčasne)
    return {'primary': kc._LANG_PRIMARY[code],
            'disabled': sorted(kc._LANG_DISABLED.get(code, set())),
            'all_words': kc.KW}


# =========================================================================
# REST — svety a príklady
# =========================================================================

@app.get('/api/examples')
def examples():
    return [{'name': n, 'program': p} for n, p in kc.EXAMPLES.items()]


def _world_files() -> dict:
    """id (stem súboru) → cesta k .karxml v worlds/."""
    out = {}
    if os.path.isdir(_WORLDS_DIR):
        for fname in sorted(os.listdir(_WORLDS_DIR)):
            if fname.lower().endswith('.karxml'):
                out[fname[:-7]] = os.path.join(_WORLDS_DIR, fname)
    return out


@app.get('/api/worlds')
def worlds():
    out = []
    for wid, path in _world_files().items():
        try:
            w = kc.World.from_xml(path)
            out.append({'id': wid, 'title': w.title or wid})
        except Exception:
            continue   # poškodený súbor preskočíme
    return out


@app.get('/api/worlds/{world_id}')
def world_one(world_id: str):
    path = _world_files().get(world_id)
    if not path:
        return _err(404, 'not_found', f'world {world_id!r}')
    w = kc.World.from_xml(path)
    w.reset_inventory()
    state = world_to_state(w, full=True)
    state['program_text'] = w.program_text
    return state


@app.post('/api/worlds/parse-karxml')
async def parse_karxml(request: Request):
    # body = surové .karxml (kontrakt §2)
    raw = await request.body()
    if len(raw) > MAX_KARXML_BYTES:
        return _err(400, 'too_large', 'karxml > 256 kB')
    try:
        w = karxml_to_world(raw.decode('utf-8', errors='replace'))
    except Exception as e:
        return _err(400, 'bad_karxml', str(e))
    w.reset_inventory()
    state = world_to_state(w, full=True)
    state['program_text'] = w.program_text
    return state


# =========================================================================
# REST — assignmenty a zdieľanie (učiteľ)
# =========================================================================

@app.post('/api/assignments')
async def create_assignment(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _err(400, 'bad_json', 'expected JSON body')
    karxml = body.get('karxml', '')
    if not karxml:
        return _err(400, 'missing_karxml', 'field "karxml" required')
    try:
        w = karxml_to_world(karxml)
    except Exception as e:
        return _err(400, 'bad_karxml', str(e))
    title = body.get('title') or w.title
    aid = storage.save_assignment({'karxml': karxml, 'title': title})
    return {'assignment_id': aid}


@app.get('/api/assignments/{aid}')
def get_assignment(aid: str):
    data = storage.load_assignment(aid)
    if data is None:
        return _err(404, 'not_found', f'assignment {aid!r}')
    w = kc.World.from_xml(data['karxml'])
    w.reset_inventory()
    return {'assignment_id': aid, 'title': data.get('title', ''),
            'created': data.get('created'),
            'state': world_to_state(w, full=True),
            'program_text': w.program_text}


@app.post('/api/assignments/{aid}/share')
async def share_assignment(aid: str, request: Request):
    if storage.load_assignment(aid) is None:
        return _err(404, 'not_found', f'assignment {aid!r}')
    try:
        body = await request.json()
    except Exception:
        return _err(400, 'bad_json', 'expected JSON body')
    names = body.get('names')
    count = body.get('count')
    if names is not None:
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            return _err(400, 'bad_names', '"names" must be list of strings')
        links = storage.create_links(aid, names)
    elif isinstance(count, int) and 0 < count <= 1000:
        links = storage.create_links(aid, count)
    else:
        return _err(400, 'bad_count', 'expected {"count": N} or {"names": [...]}')
    return {'links': links}


@app.get('/api/assignments/{aid}/links')
def assignment_links(aid: str):
    if storage.load_assignment(aid) is None:
        return _err(404, 'not_found', f'assignment {aid!r}')
    return {'links': storage.list_links(aid)}


# =========================================================================
# REST — workspace (žiak)
# =========================================================================

@app.get('/api/workspace/{token}')
def get_workspace(token: str):
    link = storage.resolve_token(token)
    if link is None:
        return _err(404, 'not_found', f'token {token!r}')
    assignment = storage.load_assignment(link['assignment_id'])
    if assignment is None:
        return _err(404, 'not_found', 'assignment missing')
    ws = storage.load_workspace(token) or {}
    w = kc.World.from_xml(assignment['karxml'])
    w.reset_inventory()
    return {'assignment_id': link['assignment_id'],
            'name': link.get('name', ''),
            'program_text': ws.get('program_text', w.program_text),
            'state': world_to_state(w, full=True)}


@app.put('/api/workspace/{token}')
async def put_workspace(token: str, request: Request):
    if storage.resolve_token(token) is None:
        return _err(404, 'not_found', f'token {token!r}')
    try:
        body = await request.json()
    except Exception:
        return _err(400, 'bad_json', 'expected JSON body')
    program = body.get('program_text', '')
    if not isinstance(program, str):
        return _err(400, 'bad_program', '"program_text" must be string')
    if len(program.encode('utf-8', errors='replace')) > MAX_PROGRAM_BYTES:
        return _err(400, 'too_large', 'program > 64 kB')
    storage.save_workspace(token, {'program_text': program})
    return {'ok': True}


# =========================================================================
# WebSocket — spoločná slučka pre žiaka aj učiteľa
# =========================================================================

async def _ws_loop(ws: WebSocket, session: Session):
    """Dve úlohy: sender vyprázdňuje frontu, receiver spracúva klienta."""
    await ws.send_json(session.state_msg('connect'))

    async def sender():
        while True:
            msg = await session.queue.get()
            await ws.send_json(msg)

    send_task = asyncio.create_task(sender())
    try:
        while True:
            msg = await ws.receive_json()
            await _handle_client_msg(ws, session, msg)
    except WebSocketDisconnect:
        pass
    finally:
        send_task.cancel()
        session.stop()


async def _handle_client_msg(ws: WebSocket, session: Session, msg: dict):
    t = msg.get('type')
    if t == 'run':
        session.run_program(msg.get('program', ''))
    elif t == 'stop':
        # stop v exekútore — join behu nesmie blokovať event loop
        await asyncio.get_event_loop().run_in_executor(None, session.stop)
    elif t == 'reset':
        await asyncio.get_event_loop().run_in_executor(None, session.reset)
        await ws.send_json(session.state_msg('reset'))
    elif t == 'direct':
        for m in session.direct(msg.get('cmd', '')):
            await ws.send_json(m)
    elif t == 'speed':
        session.set_speed(msg.get('delay'))
    elif t == 'get_state':
        await ws.send_json(session.state_msg('requested'))
    elif t == 'load_world' and session.teacher:
        await _teacher_load_world(ws, session, msg)
    elif t == 'apply_settings' and session.teacher:
        _teacher_apply_settings(session, msg)
        await ws.send_json(session.state_msg('requested'))
    else:
        await ws.send_json({'v': 1, 'type': 'error',
                            'message': f'Neznámy typ správy: {t!r}'})


async def _teacher_load_world(ws: WebSocket, session: Session, msg: dict):
    try:
        if msg.get('karxml'):
            w = karxml_to_world(msg['karxml'])
        elif msg.get('world_id'):
            path = _world_files().get(msg['world_id'])
            if not path:
                raise ValueError(f"world {msg['world_id']!r} not found")
            w = kc.World.from_xml(path)
        else:
            raise ValueError('expected "karxml" or "world_id"')
    except Exception as e:
        await ws.send_json({'v': 1, 'type': 'error', 'message': str(e)})
        return
    await asyncio.get_event_loop().run_in_executor(None, session.stop)
    session.load(w)
    await ws.send_json(session.state_msg('load'))


def _teacher_apply_settings(session: Session, msg: dict):
    """Ekvivalent WorldSettings Apply — patchuje svet bez resetu Karela.
    Zmeny sa premietajú do world aj base (base = vzor pre reset)."""
    for w in (session.world, session.base):
        st = msg.get('settings') or {}
        s = w.settings
        for key in ('prog_lang', 'disable_procedure', 'max_climb', 'max_drop',
                    'max_steps', 'max_turns', 'max_brick_height',
                    'camera_locked', 'brick_limit', 'big_brick_limit',
                    'mark_limit'):
            if key in st:
                setattr(s, key, st[key])
        if 'disabled_cmds' in st:
            s.disabled_cmds = set(st['disabled_cmds'])
        cam = st.get('camera') or {}
        for key, attr in (('az', 'camera_az'), ('el', 'camera_el'),
                          ('dist', 'camera_dist')):
            if key in cam:
                setattr(s, attr, float(cam[key]))
        if 'goal_conditions' in msg:
            w.goal_conditions = [cond_from_dict(d) for d in msg['goal_conditions']]
        for key in ('title', 'intro_html', 'success_html', 'failure_html'):
            if key in msg:
                setattr(w, key, msg[key])


@app.websocket('/ws/{token}')
async def ws_student(ws: WebSocket, token: str):
    link = storage.resolve_token(token)
    assignment = link and storage.load_assignment(link['assignment_id'])
    if not assignment:
        await ws.close(code=4404)
        return
    await ws.accept()
    session = Session(kc.World.from_xml(assignment['karxml']), teacher=False)
    await _ws_loop(ws, session)


@app.websocket('/ws/teacher/{session_id}')
async def ws_teacher(ws: WebSocket, session_id: str):
    await ws.accept()
    # učiteľ začína s prázdnym builtin svetom; svet si natiahne cez load_world
    session = Session(kc.World.from_json(kc.BUILTIN_WORLD), teacher=True)
    await _ws_loop(ws, session)


# =========================================================================
# Static frontend
# =========================================================================

@app.get('/s/{token}')
def student_page(token: str):
    index = os.path.join(_STATIC_DIR, 'index.html')
    if os.path.exists(index):
        return FileResponse(index)
    return _err(404, 'not_found', 'static/index.html missing')


if os.path.isdir(_STATIC_DIR):
    app.mount('/', StaticFiles(directory=_STATIC_DIR, html=True), name='static')
