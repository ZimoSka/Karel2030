# -*- coding: utf-8 -*-
"""Testy serverovej vrstvy (REST + WS) cez fastapi.testclient.
Spustenie:  python -m pytest tests/test_server.py -q"""
import os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Dátový adresár do tempu — PRED importom server.app (storage vzniká pri importe)
os.environ['KAREL_DATA_DIR'] = tempfile.mkdtemp(prefix='karel_data_')

from fastapi.testclient import TestClient   # noqa: E402
import karel_core as kc                     # noqa: E402
from server.app import app                  # noqa: E402

client = TestClient(app)


def _karxml(max_steps=-1):
    w = kc.World.from_json(kc.BUILTIN_WORLD)
    w.title = 'Testovací svet'
    w.settings.max_steps = max_steps
    return w.to_xml()


def _make_link(max_steps=-1):
    aid = client.post('/api/assignments',
                      json={'karxml': _karxml(max_steps), 'title': 'T'}
                      ).json()['assignment_id']
    links = client.post(f'/api/assignments/{aid}/share',
                        json={'count': 1}).json()['links']
    return aid, links[0]['token']


def _collect(ws, terminal=('finished', 'budget', 'limit', 'parse_error', 'error')):
    """Číta správy kým nepríde terminálny typ; vráti všetky."""
    msgs = []
    for _ in range(500):
        m = ws.receive_json()
        msgs.append(m)
        if m['type'] in terminal:
            break
    return msgs


# ---------------- REST: jazyky ----------------

def test_langs_ui():
    langs = client.get('/api/langs/ui').json()
    codes = {l['code'] for l in langs}
    assert 'sk' in codes and 'en' in codes
    tr = client.get('/api/langs/ui/sk').json()
    assert tr and any(k.startswith('menu.') for k in tr)
    assert client.get('/api/langs/ui/zz').status_code == 404


def test_langs_prog():
    codes = {l['code'] for l in client.get('/api/langs/prog').json()}
    assert 'sk' in codes and 'en_pattis' in codes
    sk = client.get('/api/langs/prog/sk').json()
    assert sk['primary']['FORWARD'] == 'dopredu'
    assert sk['all_words']['forward'] == 'FORWARD'
    pat = client.get('/api/langs/prog/en_pattis').json()
    assert 'BACK' in pat['disabled']


# ---------------- REST: príklady a svety ----------------

def test_examples():
    ex = client.get('/api/examples').json()
    assert ex and {'name', 'program'} <= set(ex[0])


def test_worlds():
    ws = client.get('/api/worlds').json()
    assert ws and {'id', 'title'} <= set(ws[0])
    st = client.get(f"/api/worlds/{ws[0]['id']}").json()
    assert st['width'] > 0 and 'karel' in st and 'program_text' in st
    assert client.get('/api/worlds/neexistuje').status_code == 404


def test_parse_karxml():
    r = client.post('/api/worlds/parse-karxml', content=_karxml())
    assert r.status_code == 200
    st = r.json()
    assert st['meta']['title'] == 'Testovací svet'
    assert client.post('/api/worlds/parse-karxml',
                       content='<nezmysel>').status_code == 400


# ---------------- REST: assignmenty + workspace ----------------

def test_assignment_share_resolve_workspace():
    aid, token = _make_link()
    # metadáta assignmentu
    a = client.get(f'/api/assignments/{aid}').json()
    assert a['title'] == 'T' and a['state']['width'] == 10
    # share s menami
    named = client.post(f'/api/assignments/{aid}/share',
                        json={'names': ['Janko', 'Eva']}).json()['links']
    assert [l['name'] for l in named] == ['Janko', 'Eva']
    assert all(l['url'] == f"/s/{l['token']}" for l in named)
    # prehľad linkov
    links = client.get(f'/api/assignments/{aid}/links').json()['links']
    assert len(links) == 3
    # workspace load (default) + save + reload
    w0 = client.get(f'/api/workspace/{token}').json()
    assert w0['assignment_id'] == aid and 'state' in w0
    assert client.put(f'/api/workspace/{token}',
                      json={'program_text': 'zaciatok dopredu koniec'}
                      ).status_code == 200
    w1 = client.get(f'/api/workspace/{token}').json()
    assert w1['program_text'] == 'zaciatok dopredu koniec'
    # neznámy token
    assert client.get('/api/workspace/xxxxxx').status_code == 404


def test_assignment_errors():
    assert client.post('/api/assignments', json={}).status_code == 400
    assert client.get('/api/assignments/neexistuje').status_code == 404
    aid, _ = _make_link()
    assert client.post(f'/api/assignments/{aid}/share',
                       json={}).status_code == 400


# ---------------- WS: žiacka session ----------------

def test_ws_connect_and_run():
    _, token = _make_link()
    with client.websocket_connect(f'/ws/{token}') as ws:
        first = ws.receive_json()
        assert first['type'] == 'state' and first['reason'] == 'connect'
        assert 'settings' in first['state']         # plný stav pri connect
        assert first['v'] == 1
        ws.send_json({'v': 1, 'type': 'speed', 'delay': 0.0})   # clamp na 0.02
        ws.send_json({'v': 1, 'type': 'run',
                      'program': 'zaciatok dopredu dopredu koniec'})
        msgs = _collect(ws)
        types = [m['type'] for m in msgs]
        assert types[0] == 'started'
        assert types.count('step') == 2
        assert msgs[-1] == {'v': 1, 'type': 'finished', 'status': 'done'}
        # step správy neobsahujú settings (sparse beh)
        step = next(m for m in msgs if m['type'] == 'step')
        assert 'settings' not in step['state']
        assert step['state']['karel']['x'] == 2     # 1 → 2 po prvom kroku


def test_ws_reset():
    _, token = _make_link()
    with client.websocket_connect(f'/ws/{token}') as ws:
        ws.receive_json()
        ws.send_json({'v': 1, 'type': 'speed', 'delay': 0.02})
        ws.send_json({'v': 1, 'type': 'run', 'program': 'zaciatok dopredu koniec'})
        _collect(ws)
        ws.send_json({'v': 1, 'type': 'reset'})
        st = ws.receive_json()
        assert st['type'] == 'state' and st['reason'] == 'reset'
        assert st['state']['karel']['x'] == 1       # späť na štart
        assert st['state']['counters']['steps_used'] == 0


def test_ws_budget():
    _, token = _make_link(max_steps=2)
    with client.websocket_connect(f'/ws/{token}') as ws:
        ws.receive_json()
        ws.send_json({'v': 1, 'type': 'speed', 'delay': 0.02})
        ws.send_json({'v': 1, 'type': 'run',
                      'program': 'zaciatok dopredu dopredu dopredu koniec'})
        msgs = _collect(ws, terminal=('budget',))
        assert msgs[-1] == {'v': 1, 'type': 'budget', 'kind': 'steps'}
        assert [m['type'] for m in msgs].count('step') == 2


def test_ws_parse_error():
    _, token = _make_link()
    with client.websocket_connect(f'/ws/{token}') as ws:
        ws.receive_json()
        ws.send_json({'v': 1, 'type': 'run',
                      'program': 'zaciatok ak alebo potom dopredu koniec koniec'})
        m = ws.receive_json()
        assert m['type'] == 'parse_error' and m['line'] >= 1 and m['message']


def test_ws_direct_and_get_state():
    _, token = _make_link()
    with client.websocket_connect(f'/ws/{token}') as ws:
        ws.receive_json()
        ws.send_json({'v': 1, 'type': 'direct', 'cmd': 'dopredu'})
        r = ws.receive_json()
        assert r == {'v': 1, 'type': 'direct_result', 'ok': True}
        step = ws.receive_json()
        assert step['type'] == 'step' and step['state']['karel']['x'] == 2
        ws.send_json({'v': 1, 'type': 'direct', 'cmd': 'blabla'})
        r = ws.receive_json()
        assert r['type'] == 'direct_result' and r['ok'] is False
        ws.send_json({'v': 1, 'type': 'get_state'})
        st = ws.receive_json()
        assert st['type'] == 'state' and st['reason'] == 'requested'


# ---------------- WS: učiteľská session ----------------

def test_ws_teacher_load_and_settings():
    with client.websocket_connect('/ws/teacher/abc') as ws:
        first = ws.receive_json()
        assert first['type'] == 'state' and 'settings' in first['state']
        ws.send_json({'v': 1, 'type': 'load_world', 'karxml': _karxml()})
        st = ws.receive_json()
        assert st['type'] == 'state' and st['reason'] == 'load'
        assert st['state']['meta']['title'] == 'Testovací svet'
        ws.send_json({'v': 1, 'type': 'apply_settings',
                      'settings': {'max_steps': 7, 'disabled_cmds': ['BACK']},
                      'title': 'Nový titul'})
        st = ws.receive_json()
        assert st['state']['settings']['max_steps'] == 7
        assert st['state']['settings']['disabled_cmds'] == ['BACK']
        assert st['state']['meta']['title'] == 'Nový titul'
