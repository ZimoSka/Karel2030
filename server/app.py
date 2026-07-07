# -*- coding: utf-8 -*-
"""Karel 2030 — FastAPI server podľa docs/api.md (REST §2, WS §3)."""
import os, json, asyncio, configparser, time, secrets, shutil
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
_EXAMPLES_BAKED = os.environ.get('KAREL_EXAMPLES_DIR', os.path.join(_ROOT, 'examples'))
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
    # bezpečnostné hlavičky (clickjacking, MIME sniffing, referrer leak)
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.setdefault('Referrer-Policy', 'same-origin')
    resp.headers.setdefault('Content-Security-Policy', _CSP)
    return resp


# CSP — obmedzí odkiaľ sa načítajú zdroje (obrana proti injektovaným externým
# skriptom/exfiltrácii). 'unsafe-inline' pre skripty je nutné (inline bootstrap
# v index.html); CDN hosty kvôli fallbacku vendorovaných knižníc. XSS samotné
# rieši sanitizácia HTML zadania, CSP je defense-in-depth.
_CSP = ("default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com "
        "https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob: https:; "
        "media-src 'self' data: blob:; font-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'self'")


# Globálny limit veľkosti tela požiadavky — bráni načítaniu obrieho tela do
# pamäte ešte pred kontrolami v endpointoch (DoS). 2 MB pokryje aj zmenšené textúry.
MAX_BODY_BYTES = 2 * 1024 * 1024


@app.middleware('http')
async def _limit_body(request, call_next):
    if request.method in ('POST', 'PUT', 'PATCH'):
        cl = request.headers.get('content-length')
        if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
            return _err(413, 'too_large', 'telo požiadavky je príliš veľké')
    return await call_next(request)
# Publikované svety (admin) — perzistentné na volume, popri baked worlds/
_DATA_DIR      = os.environ.get('KAREL_DATA_DIR', './data')
_PUBLISHED_DIR = os.path.join(_DATA_DIR, 'worlds')
_EXAMPLES_DIR  = os.path.join(_DATA_DIR, 'examples')   # volume = jediný zdroj príkladov
os.makedirs(_PUBLISHED_DIR, exist_ok=True)
os.makedirs(_EXAMPLES_DIR, exist_ok=True)


def _seed_dir_if_empty(dst, src, suffix):
    """Skopíruj baked súbory (src) do volume (dst) iba ak je dst prázdny.
    Volume je odvtedy autoritatívny — zmazané položky sa neobnovia."""
    try:
        has_any = any(f.lower().endswith(suffix) for f in os.listdir(dst))
    except FileNotFoundError:
        has_any = False
    if has_any or not os.path.isdir(src):
        return
    for fname in os.listdir(src):
        if fname.lower().endswith(suffix):
            shutil.copy(os.path.join(src, fname), os.path.join(dst, fname))


# Volume je JEDINÝ zdroj svetov aj príkladov. Baked obsah (v image) slúži len
# ako počiatočná výplň pri prvom spustení (prázdny volume). Odvtedy je volume
# autoritatívny — zmazané položky sa neobnovia.
_seed_dir_if_empty(_PUBLISHED_DIR, _WORLDS_DIR, '.karxml')
_seed_dir_if_empty(_EXAMPLES_DIR, _EXAMPLES_BAKED, '.prg')

import re as _re
_SAFE_WID = _re.compile(r'^[A-Za-z0-9 _-]{1,64}$')
_SAFE_TID = _re.compile(r'^[A-Za-z0-9_-]{1,64}$')   # učiteľský/token id


def _err(status: int, code: str, detail: str = '') -> JSONResponse:
    return JSONResponse({'error': code, 'detail': detail}, status_code=status)


# --- Rate limiting (in-memory, per IP + akcia) --------------------------------
# Bráni spamu neautentizovaných endpointov (tvorba úloh/linkov, parse-karxml).
_rate_hits: dict = {}


def _rate_ok(request: 'Request', bucket: str, limit: int, window: float = 60.0) -> bool:
    now = time.time()
    key = f'{bucket}:{_client_key(request)}'
    hits = _rate_hits.setdefault(key, [])
    cutoff = now - window
    hits[:] = [t for t in hits if t > cutoff]
    if len(hits) >= limit:
        return False
    hits.append(now)
    if len(_rate_hits) > 5000:            # soft cap proti rastu pamäte
        for k in [k for k, v in _rate_hits.items() if not v or v[-1] < cutoff]:
            _rate_hits.pop(k, None)
    return True


def _rate_err():
    return _err(429, 'rate_limited', 'Príliš veľa požiadaviek. Skús neskôr.')


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


# Dôvera k X-Forwarded-For: štandardne NIE (priame spojenie). Za reverznou
# proxy nastav KAREL_TRUSTED_PROXY=1 — vtedy berieme POSLEDNÚ položku XFF
# (tú pridala naša proxy = reálny klient), nie prvú (klientom podvrhnuteľnú).
_TRUSTED_PROXY = os.environ.get('KAREL_TRUSTED_PROXY', '').lower() in ('1', 'true', 'yes')


def _client_key(request: Request) -> str:
    """Identita klienta pre per-IP lockout. Per reálnu IP → útočník z inej IP
    nezamkne admina; XFF sa neberie ak nie sme za dôveryhodnou proxy (inak by
    sa lockout dal obísť podvrhnutím hlavičky)."""
    if _TRUSTED_PROXY:
        xff = request.headers.get('x-forwarded-for')
        if xff:
            return xff.split(',')[-1].strip()
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
        # Heslo nie je nastavené → otvorený admin režim (lokálne použitie jedným
        # učiteľom). Klik na Admin aktivuje režim bez výzvy na heslo.
        token = secrets.token_urlsafe(24)
        _admin_sessions[token] = time.time() + ADMIN_TTL
        resp = JSONResponse({'ok': True})
        resp.set_cookie(ADMIN_COOKIE, token, httponly=True,
                        samesite='lax', max_age=ADMIN_TTL)
        return resp
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
# Učiteľská identita — anonymná cookie. Assignmenty (a tým žiacke linky) sú
# viazané na učiteľa, ktorý ich vytvoril. Iný učiteľ vidí čistý zoznam.
# =========================================================================
TEACHER_COOKIE = 'karel_teacher'
TEACHER_TTL    = 90 * 24 * 3600     # 90 dní


def _teacher_id(request: Request) -> str | None:
    tid = request.cookies.get(TEACHER_COOKIE)
    return tid if tid and _SAFE_TID.match(tid) else None


def _set_teacher_cookie(resp: JSONResponse, tid: str) -> None:
    resp.set_cookie(TEACHER_COOKIE, tid, httponly=True, samesite='lax',
                    max_age=TEACHER_TTL)


def _owns_assignment(request: Request, aid: str) -> bool:
    """Vlastní volajúci učiteľ daný assignment? (admin má prístup ku všetkému)."""
    if _is_admin(request):
        return storage.load_assignment(aid) is not None
    a = storage.load_assignment(aid)
    tid = _teacher_id(request)
    return a is not None and tid is not None and a.get('owner') == tid


@app.get('/api/teacher/session')
def teacher_session(request: Request):
    """Zabezpečí učiteľskú cookie (vytvorí ak chýba) a vráti id. Frontend ju
    zavolá pri štarte (učiteľ) pred otvorením WS."""
    tid = _teacher_id(request)
    resp = JSONResponse({'teacher_id': tid or '(new)'})
    if not tid:
        tid = secrets.token_urlsafe(12)
        _set_teacher_cookie(resp, tid)
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
    """Príklady = .prg súbory na volume (_EXAMPLES_DIR). Názov = filename bez
    prípony. Baked príklady sa naseedujú pri prvom spustení."""
    out = []
    if os.path.isdir(_EXAMPLES_DIR):
        for fname in sorted(os.listdir(_EXAMPLES_DIR)):
            if not fname.lower().endswith('.prg'):
                continue
            try:
                with open(os.path.join(_EXAMPLES_DIR, fname), encoding='utf-8') as f:
                    out.append({'name': fname[:-4], 'program': f.read()})
            except Exception:
                pass
    return out


_GLOBAL_VISUAL_PATH = os.path.join(_DATA_DIR, 'visual.json')


def _load_global_visual() -> dict:
    if os.path.exists(_GLOBAL_VISUAL_PATH):
        try:
            with open(_GLOBAL_VISUAL_PATH, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _visual_path(world_id: str) -> str:
    """Cesta k sidecar vizuálnych nastavení (vždy v _PUBLISHED_DIR)."""
    return os.path.join(_PUBLISHED_DIR, f'{world_id}_visual.json')


def _load_visual(world_id: str) -> dict:
    """Globálne nastavenia ako základ, per-svet ich môžu prepísať."""
    vis = _load_global_visual()
    p = _visual_path(world_id)
    if os.path.exists(p):
        try:
            with open(p, encoding='utf-8') as f:
                vis.update(json.load(f))
        except Exception:
            pass
    return vis


def _world_files() -> dict:
    """id (stem súboru) → cesta k .karxml. Jediný zdroj = volume
    (_PUBLISHED_DIR). Baked svety sa do volume naseedujú pri prvom spustení
    (_seed_worlds_if_empty) — žiadne miešanie dvoch úložísk."""
    out = {}
    if os.path.isdir(_PUBLISHED_DIR):
        for fname in sorted(os.listdir(_PUBLISHED_DIR)):
            if fname.lower().endswith('.karxml'):
                out[fname[:-7]] = os.path.join(_PUBLISHED_DIR, fname)
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
    state['visual'] = _load_visual(world_id)
    return state


@app.get('/api/worlds/{world_id}/visual')
def get_world_visual(world_id: str):
    if not _SAFE_WID.match(world_id):
        return _err(400, 'bad_id', 'neplatné id')
    return _load_visual(world_id)


@app.put('/api/worlds/{world_id}/visual')
async def put_world_visual(world_id: str, request: Request):
    if not _is_admin(request):
        return _err(401, 'unauthorized', 'len admin')
    if not _SAFE_WID.match(world_id):
        return _err(400, 'bad_id', 'neplatné id')
    data = await request.json()
    os.makedirs(_PUBLISHED_DIR, exist_ok=True)
    with open(_visual_path(world_id), 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return {'ok': True}


@app.get('/api/settings/visual')
def get_global_visual():
    return _load_global_visual()


@app.put('/api/settings/visual')
async def put_global_visual(request: Request):
    if not _is_admin(request):
        return _err(401, 'unauthorized', 'len admin')
    data = await request.json()
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_GLOBAL_VISUAL_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return {'ok': True}


@app.post('/api/worlds/parse-karxml')
async def parse_karxml(request: Request):
    if not _rate_ok(request, 'parse', 60):
        return _rate_err()
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
    if not _rate_ok(request, 'assign', 20):
        return _rate_err()
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
    tid = _teacher_id(request) or secrets.token_urlsafe(12)
    aid = storage.save_assignment({'karxml': karxml, 'title': title, 'owner': tid})
    resp = JSONResponse({'assignment_id': aid})
    if not _teacher_id(request):
        _set_teacher_cookie(resp, tid)
    return resp


@app.post('/api/assignments/ensure')
async def ensure_assignment(request: Request):
    """Get-or-create assignment naviazaný na svet (world_key).
    Vždy aktualizuje karxml/title → žiaci dostanú najnovšiu verziu sveta.
    Jedno okno zdieľania na svet: opätovné otvorenie nájde ten istý assignment."""
    if not _rate_ok(request, 'assign', 30):
        return _rate_err()
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
    tid = _teacher_id(request) or secrets.token_urlsafe(12)
    aid = storage.assignment_for_world(world_key, owner=tid) if world_key else None
    if aid:
        storage.update_assignment(aid, {'karxml': karxml, 'title': title})
    else:
        aid = storage.save_assignment({'karxml': karxml, 'title': title,
                                       'world_key': world_key, 'owner': tid})
    resp = JSONResponse({'assignment_id': aid})
    if not _teacher_id(request):
        _set_teacher_cookie(resp, tid)
    return resp


@app.post('/api/assignments/{aid}/links')
async def add_link(aid: str, request: Request):
    """Pridá jedného žiaka (meno) → vráti jeho link."""
    if not _rate_ok(request, 'link', 30):
        return _rate_err()
    if not _owns_assignment(request, aid):
        return _err(403, 'forbidden', 'nie je tvoj assignment')
    try:
        body = await request.json()
    except Exception:
        return _err(400, 'bad_json', 'expected JSON body')
    name = (body.get('name') or '').strip()
    links = storage.create_links(aid, [name])
    return {'link': links[0]}


@app.delete('/api/links/{token}')
def delete_link(token: str, request: Request):
    """Zmaže žiakov link aj jeho prácu — len vlastník assignmentu."""
    link = storage.resolve_token(token)
    if link is None:
        return _err(404, 'not_found', f'token {token!r}')
    if not _owns_assignment(request, link['assignment_id']):
        return _err(403, 'forbidden', 'nie je tvoj link')
    storage.delete_link(token)
    return {'ok': True}


@app.get('/api/assignments/{aid}')
def get_assignment(aid: str, request: Request):
    if not _owns_assignment(request, aid):
        return _err(403, 'forbidden', 'nie je tvoj assignment')
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
    if not _rate_ok(request, 'share', 10):
        return _rate_err()
    if not _owns_assignment(request, aid):
        return _err(403, 'forbidden', 'nie je tvoj assignment')
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
def list_assignments(request: Request):
    """Zoznam úloh DANÉHO učiteľa (podľa cookie); admin vidí všetky."""
    owner = None if _is_admin(request) else _teacher_id(request)
    if owner is None and not _is_admin(request):
        return []        # bez učiteľskej cookie → prázdny zoznam
    return storage.list_assignments(owner)


@app.get('/api/assignments/{aid}/links')
def assignment_links(aid: str, request: Request):
    if not _owns_assignment(request, aid):
        return _err(403, 'forbidden', 'nie je tvoj assignment')
    return {'links': storage.list_links(aid)}


@app.get('/api/assignments/{aid}/progress')
def assignment_progress(aid: str, request: Request):
    """Pre každý link: meno žiaka + jeho uložený program (čo žiak spravil)."""
    if not _owns_assignment(request, aid):
        return _err(403, 'forbidden', 'nie je tvoj assignment')
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
        cam = msg.get('camera') or {}      # zapamätaj aktuálny pohľad kamery
        for key, attr in (('az', 'camera_az'), ('el', 'camera_el'), ('dist', 'camera_dist')):
            if key in cam:
                try:
                    setattr(w.settings, attr, float(cam[key]))
                except (TypeError, ValueError):
                    pass
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
            wid = msg['world_id']
            path = _world_files().get(wid)
            if not path:
                raise ValueError(f"world {wid!r} not found")
            w = kc.World.from_xml(path)
            session.visual = _load_visual(wid)
        else:
            w = kc.World.from_json(kc.BUILTIN_WORLD)
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


# Limit súbežných WS sessions per IP — každá session drží World + spúšťa
# vlákna interpretera (64 MB stack) → bez limitu DoS cez množstvo spojení.
_ws_count: dict = {}
MAX_WS_PER_IP = 12


def _ws_ip(ws: WebSocket) -> str:
    if _TRUSTED_PROXY:
        xff = ws.headers.get('x-forwarded-for')
        if xff:
            return xff.split(',')[-1].strip()
    return ws.client.host if ws.client else 'unknown'


@app.websocket('/ws/{token}')
async def ws_student(ws: WebSocket, token: str):
    link = storage.resolve_token(token)
    assignment = link and storage.load_assignment(link['assignment_id'])
    if not assignment:
        await ws.close(code=4404)
        return
    ip = _ws_ip(ws)
    if _ws_count.get(ip, 0) >= MAX_WS_PER_IP:
        await ws.close(code=4429)
        return
    _ws_count[ip] = _ws_count.get(ip, 0) + 1
    try:
        await ws.accept()
        world_key = assignment.get('world_key', '')
        visual = _load_visual(world_key) if world_key else {}
        session = Session(kc.World.from_xml(assignment['karxml']), teacher=False, visual=visual)
        await _ws_loop(ws, session, token=token)
    finally:
        _ws_count[ip] = max(0, _ws_count.get(ip, 0) - 1)


@app.websocket('/ws/teacher/{session_id}')
async def ws_teacher(ws: WebSocket, session_id: str):
    # učiteľská session vyžaduje učiteľskú cookie (nastaví ju /api/teacher/session
    # pri štarte) → bráni neobmedzenému otváraniu sessions cudzími skriptami
    tid = ws.cookies.get(TEACHER_COOKIE)
    if not (tid and _SAFE_TID.match(tid)):
        await ws.close(code=4401)
        return
    ip = _ws_ip(ws)
    if _ws_count.get(ip, 0) >= MAX_WS_PER_IP:
        await ws.close(code=4429)
        return
    _ws_count[ip] = _ws_count.get(ip, 0) + 1
    try:
        await ws.accept()
        # učiteľ začína s prázdnym builtin svetom; svet si natiahne cez load_world
        session = Session(kc.World.from_json(kc.BUILTIN_WORLD), teacher=True)
        await _ws_loop(ws, session)
    finally:
        _ws_count[ip] = max(0, _ws_count.get(ip, 0) - 1)


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
