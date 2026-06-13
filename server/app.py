# -*- coding: utf-8 -*-
"""Karel 2030 — FastAPI server podľa docs/api.md (REST §2, WS §3)."""
import os, asyncio, configparser, time, secrets
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


def _read_version() -> str:
    try:
        with open(os.path.join(_ROOT, 'VERSION'), encoding='utf-8') as f:
            return f.read().strip()
    except OSError:
        return '0.0.0'

VERSION    = _read_version()
GIT_SHA    = os.environ.get('KAREL_GIT_SHA', 'dev')
BUILD_TIME = os.environ.get('KAREL_BUILD_TIME', '')


@app.get('/api/version')
def version():
    return {'version': VERSION, 'git_sha': GIT_SHA, 'build_time': BUILD_TIME}


@app.middleware('http')
async def _no_cache_static(request, call_next):
    """Statika (index.html, JS, CSS) sa nesmie cachovať — inak učiteľ vidí
    staré súbory po rebuilde. ETag/Last-Modified zostávajú (304 ak nezmenené)."""
    resp = await call_next(request)
    if request.method == 'GET' and not request.url.path.startswith('/api'):
        resp.headers['Cache-Control'] = 'no-cache'
    return resp
# Publikované svety (admin) — perzistentné na volume, popri baked worlds/
_PUBLISHED_DIR = os.path.join(os.environ.get('KAREL_DATA_DIR', './data'), 'worlds')
os.makedirs(_PUBLISHED_DIR, exist_ok=True)

import re as _re
_SAFE_WID = _re.compile(r'^[A-Za-z0-9 _-]{1,64}$')


def _err(status: int, code: str, detail: str = '') -> JSONResponse:
    return JSONResponse({'error': code, 'detail': detail}, status_code=status)


# =========================================================================
# Admin autentifikácia — heslo z env KarelAdminPWD, session cookie, lockout
# =========================================================================
ADMIN_PWD   = os.environ.get('KarelAdminPWD', '')
ADMIN_TTL   = 8 * 3600          # platnosť admin session (s)
MAX_FAILS   = 3                 # počet pokusov pred zablokovaním
BLOCK_SECS  = 30 * 60           # dĺžka blokovania (s)
ADMIN_COOKIE = 'karel_admin'

_admin_sessions: dict = {}      # token -> expiry (epoch)
_admin_fails: dict = {}         # client_key -> {'count': int, 'blocked_until': epoch}


def _client_key(request: Request) -> str:
    """Identita klienta pre lockout: prvý X-Forwarded-For, inak IP."""
    xff = request.headers.get('x-forwarded-for')
    if xff:
        return xff.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


def _block_minutes(key: str) -> int:
    """Koľko minút zostáva do odblokovania (0 = neblokovaný)."""
    rec = _admin_fails.get(key)
    if rec and rec['blocked_until'] > time.time():
        return int((rec['blocked_until'] - time.time()) // 60) + 1
    return 0


def _is_admin(request: Request) -> bool:
    tok = request.cookies.get(ADMIN_COOKIE)
    if not tok:
        return False
    exp = _admin_sessions.get(tok)
    if not exp:
        return False
    if exp < time.time():
        _admin_sessions.pop(tok, None)
        return False
    return True


@app.post('/api/admin/login')
async def admin_login(request: Request):
    key = _client_key(request)
    mins = _block_minutes(key)
    if mins:
        return _err(429, 'locked', f'Príliš veľa pokusov. Skús znova o {mins} min.')
    if not ADMIN_PWD:
        return _err(403, 'admin_disabled', 'Admin heslo nie je na serveri nastavené.')
    try:
        body = await request.json()
    except Exception:
        body = {}
    pwd = str((body or {}).get('password', ''))
    if secrets.compare_digest(pwd, ADMIN_PWD):
        _admin_fails.pop(key, None)               # vynuluj pokusy
        token = secrets.token_urlsafe(24)
        _admin_sessions[token] = time.time() + ADMIN_TTL
        resp = JSONResponse({'ok': True})
        resp.set_cookie(ADMIN_COOKIE, token, httponly=True,
                        samesite='lax', max_age=ADMIN_TTL)
        return resp
    # neúspešný pokus
    rec = _admin_fails.setdefault(key, {'count': 0, 'blocked_until': 0})
    rec['count'] += 1
    if rec['count'] >= MAX_FAILS:
        rec['blocked_until'] = time.time() + BLOCK_SECS
        rec['count'] = 0
        return _err(429, 'locked',
                    f'Príliš veľa pokusov. Admin zablokovaný na {BLOCK_SECS // 60} min.')
    left = MAX_FAILS - rec['count']
    return _err(401, 'bad_password', f'Nesprávne heslo. Zostáva pokusov: {left}.')


@app.get('/api/admin/status')
def admin_status(request: Request):
    return {'admin': _is_admin(request), 'configured': bool(ADMIN_PWD)}


@app.post('/api/admin/logout')
def admin_logout(request: Request):
    tok = request.cookies.get(ADMIN_COOKIE)
    if tok:
        _admin_sessions.pop(tok, None)
    resp = JSONResponse({'ok': True})
    resp.delete_cookie(ADMIN_COOKIE)
    return resp


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
    """id (stem súboru) → cesta k .karxml. Spája baked worlds/ + publikované
    (data/worlds/); publikované pri zhode id prepíšu baked."""
    out = {}
    for d in (_WORLDS_DIR, _PUBLISHED_DIR):
        if os.path.isdir(d):
            for fname in sorted(os.listdir(d)):
                if fname.lower().endswith('.karxml'):
                    out[fname[:-7]] = os.path.join(d, fname)
    return out


@app.post('/api/worlds')
async def publish_world(request: Request):
    """Publikuj svet do volume (admin). Body: {id, karxml}."""
    if not _is_admin(request):
        return _err(401, 'unauthorized', 'len admin')
    data = await request.json()
    wid = (data or {}).get('id', '').strip()
    karxml = (data or {}).get('karxml', '')
    if not _SAFE_WID.match(wid):
        return _err(400, 'bad_id', 'id: 1-64 znakov [A-Za-z0-9 _-]')
    if len(karxml.encode('utf-8', 'replace')) > MAX_KARXML_BYTES:
        return _err(400, 'too_large', 'karxml > 256 kB')
    try:
        kc.World.from_xml(karxml)        # validácia
    except Exception as e:
        return _err(400, 'invalid', str(e))
    with open(os.path.join(_PUBLISHED_DIR, f'{wid}.karxml'), 'w', encoding='utf-8') as f:
        f.write(karxml)
    return {'id': wid, 'published': True}


@app.delete('/api/worlds/{world_id}')
def delete_world(world_id: str, request: Request):
    """Zmaž publikovaný svet z volume (admin). Baked worlds/ sa nedajú mazať."""
    if not _is_admin(request):
        return _err(401, 'unauthorized', 'len admin')
    if not _SAFE_WID.match(world_id):
        return _err(400, 'bad_id', 'neplatné id')
    path = os.path.join(_PUBLISHED_DIR, f'{world_id}.karxml')
    if not os.path.exists(path):
        return _err(404, 'not_found', 'nie je publikovaný (baked svety sa nemažú)')
    os.remove(path)
    return {'id': world_id, 'deleted': True}


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


@app.post('/api/assignments/ensure')
async def ensure_assignment(request: Request):
    """Get-or-create assignment naviazaný na svet (world_key).
    Vždy aktualizuje karxml/title → žiaci dostanú najnovšiu verziu sveta.
    Jedno okno zdieľania na svet: opätovné otvorenie nájde ten istý assignment."""
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
    world_key = (body.get('world_key') or '').strip()
    aid = storage.assignment_for_world(world_key) if world_key else None
    if aid:
        storage.update_assignment(aid, {'karxml': karxml, 'title': title})
    else:
        aid = storage.save_assignment({'karxml': karxml, 'title': title,
                                       'world_key': world_key})
    return {'assignment_id': aid}


@app.post('/api/assignments/{aid}/links')
async def add_link(aid: str, request: Request):
    """Pridá jedného žiaka (meno) → vráti jeho link."""
    if storage.load_assignment(aid) is None:
        return _err(404, 'not_found', f'assignment {aid!r}')
    try:
        body = await request.json()
    except Exception:
        return _err(400, 'bad_json', 'expected JSON body')
    name = (body.get('name') or '').strip()
    links = storage.create_links(aid, [name])
    return {'link': links[0]}


@app.delete('/api/links/{token}')
def delete_link(token: str):
    """Zmaže žiakov link aj jeho prácu."""
    if not storage.delete_link(token):
        return _err(404, 'not_found', f'token {token!r}')
    return {'ok': True}


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


@app.get('/api/assignments')
def list_assignments():
    """Zoznam úloh — učiteľ sa vie vrátiť k linkom. (Bez auth: vidno všetky.)"""
    return storage.list_assignments()


@app.get('/api/assignments/{aid}/links')
def assignment_links(aid: str):
    if storage.load_assignment(aid) is None:
        return _err(404, 'not_found', f'assignment {aid!r}')
    return {'links': storage.list_links(aid)}


@app.get('/api/assignments/{aid}/progress')
def assignment_progress(aid: str):
    """Pre každý link: meno žiaka + jeho uložený program (čo žiak spravil)."""
    if storage.load_assignment(aid) is None:
        return _err(404, 'not_found', f'assignment {aid!r}')
    out = []
    for link in storage.list_links(aid):
        wsp = storage.load_workspace(link['token']) or {}
        prog = wsp.get('program_text', '')
        solved = bool(wsp.get('completed'))
        out.append({'token': link['token'], 'name': link['name'], 'url': link['url'],
                    'has_work': bool(prog.strip()) or solved, 'program_text': prog,
                    'solved': solved, 'completed_at': wsp.get('completed_at'),
                    'updated': wsp.get('updated') or wsp.get('completed_at')})
    return out


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

async def _ws_loop(ws: WebSocket, session: Session, token: str | None = None):
    """Dve úlohy: sender vyprázdňuje frontu, receiver spracúva klienta.
    Pri žiakovi (token) zaznamená vyriešenie misie aj keď ju vyriešil graficky."""
    await ws.send_json(session.state_msg('connect'))

    async def sender():
        while True:
            msg = await session.queue.get()
            if token and msg.get('type') == 'mission' and msg.get('result') == 'success':
                storage.mark_completed(token)   # žiak vyriešil svet → ulož pokrok
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
    elif t == 'export_world' and session.teacher:
        w = session.world
        if 'program' in msg:
            w.program_text = msg['program']
        await ws.send_json({'v': 1, 'type': 'world_export',
                            'karxml': w.to_xml(), 'title': w.title})
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
        for key in ('prog_lang', 'disable_procedure', 'disable_graphic',
                    'disable_command', 'max_climb', 'max_drop',
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
        # rozmery miestnosti (resize zachová obsah v rámci nových rozmerov)
        nw = int(st.get('width', w.width)); nh = int(st.get('height', w.height))
        if (nw, nh) != (w.width, w.height) and 3 <= nw <= 50 and 3 <= nh <= 50:
            w.resize(nw, nh)
        # štartová pozícia + smer Karela
        k = msg.get('karel') or {}
        if 'x' in k: w.karel_x = max(0, min(w.width - 1, int(k['x'])))
        if 'y' in k: w.karel_y = max(0, min(w.height - 1, int(k['y'])))
        if 'dir' in k: w.karel_dir = kc.Direction.from_str(k['dir'])
        if 'reset_on_failure' in msg:
            w.mission_reset_on_failure = bool(msg['reset_on_failure'])
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
    await _ws_loop(ws, session, token=token)


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
