# -*- coding: utf-8 -*-
"""Persistencia podľa docs/api.md §5 — Storage protokol + súborová implementácia.

data/
├── assignments/{id}.json    {"karxml": ..., "title": ..., "created": ...}
├── links/{token}.json       {"assignment_id": ..., "name": ...}
└── workspaces/{token}.json  {"program_text": ..., "updated": ...}
"""
import os, json, time, secrets, re
from typing import Protocol

_SAFE_ID = re.compile(r'^[A-Za-z0-9_-]+$')   # ochrana proti path traversal


class Storage(Protocol):
    def save_assignment(self, data: dict) -> str: ...
    def load_assignment(self, id: str) -> dict | None: ...
    def create_links(self, assignment_id, names_or_count) -> list: ...
    def list_links(self, assignment_id: str) -> list: ...
    def resolve_token(self, token: str) -> dict | None: ...
    def save_workspace(self, token: str, data: dict) -> None: ...
    def load_workspace(self, token: str) -> dict | None: ...


class FileStorage:
    """Súborová implementácia — JSON súbory v KAREL_DATA_DIR (default ./data)."""

    def __init__(self, root: str | None = None):
        self.root = root or os.environ.get('KAREL_DATA_DIR', './data')
        for sub in ('assignments', 'links', 'workspaces'):
            os.makedirs(os.path.join(self.root, sub), exist_ok=True)

    # --- interné ---------------------------------------------------------
    def _path(self, sub: str, id_: str) -> str | None:
        if not _SAFE_ID.match(id_ or ''):
            return None
        return os.path.join(self.root, sub, f'{id_}.json')

    def _read(self, sub: str, id_: str) -> dict | None:
        p = self._path(sub, id_)
        if not p or not os.path.exists(p):
            return None
        with open(p, encoding='utf-8') as f:
            return json.load(f)

    def _write(self, sub: str, id_: str, data: dict) -> None:
        p = self._path(sub, id_)
        if not p:
            raise ValueError(f'invalid id: {id_!r}')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    # --- assignments -------------------------------------------------------
    def save_assignment(self, data: dict) -> str:
        aid = secrets.token_urlsafe(12)
        data = dict(data); data.setdefault('created', time.time())
        self._write('assignments', aid, data)
        return aid

    def load_assignment(self, id: str) -> dict | None:
        return self._read('assignments', id)

    def update_assignment(self, id: str, patch: dict) -> bool:
        """Zlúči patch do existujúceho assignmentu (napr. nový karxml/title)."""
        data = self._read('assignments', id)
        if data is None:
            return False
        data.update(patch)
        self._write('assignments', id, data)
        return True

    def assignment_for_world(self, world_key: str) -> str | None:
        """Nájde assignment naviazaný na svet (world_key) — najnovší ak je viac."""
        if not world_key:
            return None
        d = os.path.join(self.root, 'assignments')
        best, best_t = None, -1
        for fname in os.listdir(d):
            if not fname.endswith('.json'):
                continue
            aid = fname[:-5]
            data = self._read('assignments', aid)
            if data and data.get('world_key') == world_key:
                t = data.get('created') or 0
                if t > best_t:
                    best, best_t = aid, t
        return best

    def list_assignments(self) -> list:
        """Zoznam všetkých úloh (najnovšie prvé). Bez auth — vidno všetky."""
        out = []
        d = os.path.join(self.root, 'assignments')
        for fname in os.listdir(d):
            if not fname.endswith('.json'):
                continue
            aid = fname[:-5]
            data = self._read('assignments', aid)
            if data:
                out.append({'id': aid, 'title': data.get('title', ''),
                            'created': data.get('created')})
        out.sort(key=lambda a: a.get('created') or 0, reverse=True)
        return out

    # --- links ---------------------------------------------------------------
    def create_links(self, assignment_id, names_or_count) -> list:
        if isinstance(names_or_count, int):
            names = [''] * names_or_count
        else:
            names = list(names_or_count)
        links = []
        for name in names:
            token = secrets.token_urlsafe(12)
            self._write('links', token, {'assignment_id': assignment_id, 'name': name})
            links.append({'token': token, 'name': name, 'url': f'/s/{token}'})
        return links

    def list_links(self, assignment_id: str) -> list:
        """Prehľad existujúcich linkov assignmentu (lineárny scan — v1 stačí)."""
        out = []
        d = os.path.join(self.root, 'links')
        for fname in sorted(os.listdir(d)):
            if not fname.endswith('.json'):
                continue
            token = fname[:-5]
            data = self._read('links', token)
            if data and data.get('assignment_id') == assignment_id:
                out.append({'token': token, 'name': data.get('name', ''),
                            'url': f'/s/{token}'})
        return out

    def resolve_token(self, token: str) -> dict | None:
        return self._read('links', token)

    def delete_link(self, token: str) -> bool:
        """Zmaže link aj jeho workspace (žiakovu prácu)."""
        p = self._path('links', token)
        if not p or not os.path.exists(p):
            return False
        os.remove(p)
        wp = self._path('workspaces', token)
        if wp and os.path.exists(wp):
            os.remove(wp)
        return True

    # --- workspaces ----------------------------------------------------------
    def save_workspace(self, token: str, data: dict) -> None:
        data = dict(data); data['updated'] = time.time()
        self._write('workspaces', token, data)

    def load_workspace(self, token: str) -> dict | None:
        return self._read('workspaces', token)

    def mark_completed(self, token: str) -> None:
        """Zaznamená že žiak vyriešil svet (aj graficky, bez programu).
        Zlúči do existujúceho workspace — nezmaže uložený program."""
        data = self._read('workspaces', token) or {}
        data['completed'] = True
        data['completed_at'] = time.time()
        self._write('workspaces', token, data)
