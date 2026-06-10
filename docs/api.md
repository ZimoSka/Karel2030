# Karel 2030 — API kontrakt (backend ↔ frontend)

Verzia kontraktu: **1** (pole `"v": 1` v každej WS správe).
Tento dokument je záväzný pre T2 (server) aj T3 (frontend) — zmeny len po dohode
a so zápisom sem.

---

## 1. Pojmy

| Pojem | Význam |
|---|---|
| **Assignment** | Učiteľom pripravený svet + nastavenia + zadanie (snapshot .karxml). Nemenný po zdieľaní. |
| **Workspace** | Žiakov priestor k assignmentu: jeho program (text) + metadáta. Kľúčovaný **tokenom** zo žiackeho linku. |
| **Session** | Živé WebSocket pripojenie: server drží `World` + `KarelInterpreter` inštanciu v pamäti. Po odpojení zaniká (workspace ostáva na disku). |

Žiacky link: `https://server/s/{token}` — frontend z neho otvorí žiacky mód
a pripojí sa na WS `/ws/{token}`.
Učiteľský režim: default na `https://server/` (bez tokenu) — pracuje s vlastnou
session, svety si otvára/ukladá priamo.

---

## 2. REST endpointy

Všetko pod `/api`, JSON. Chybové odpovede: `{"error": "kód", "detail": "text"}`
+ HTTP status (400/404/409/500).

### Jazyky a preklady
| Metóda | Cesta | Odpoveď |
|---|---|---|
| GET | `/api/langs/ui` | `[{"code":"sk","name":"Slovenčina"}, …]` |
| GET | `/api/langs/ui/{code}` | flat dict prekladov `{"menu.open_world": "...", …}` |
| GET | `/api/langs/prog` | `[{"code":"sk","name":"Slovenčina"}, …]` |
| GET | `/api/langs/prog/{code}` | `{"primary": {"FORWARD":"dopredu",…}, "disabled": ["BACK",…], "all_words": {"dopredu":"FORWARD",…}}` — pre editor highlighting a tlačidlá |

### Svety a príklady
| Metóda | Cesta | Popis |
|---|---|---|
| GET | `/api/examples` | `[{"name":"Prázdny/Empty","program":"…"}, …]` |
| GET | `/api/worlds` | zoznam serverových .karxml svetov `[{"id","title"}]` |
| GET | `/api/worlds/{id}` | svet ako **state JSON** (viď §4) + `program_text`, `intro_html`, … |
| POST | `/api/worlds/parse-karxml` | body = surové .karxml → state JSON (import súboru z klienta) |

### Assignmenty a zdieľanie (učiteľ)
| Metóda | Cesta | Popis |
|---|---|---|
| POST | `/api/assignments` | body = `{"karxml": "<world …>", "title": "…"}` → `{"assignment_id": "a1b2…"}` |
| GET | `/api/assignments/{id}` | metadáta + state JSON |
| POST | `/api/assignments/{id}/share` | body = `{"count": 25}` alebo `{"names": ["Janko","Eva"]}` → `{"links": [{"token":"x7…","name":"Janko","url":"/s/x7…"}, …]}` |
| GET | `/api/assignments/{id}/links` | existujúce linky (idempotentný prehľad pre učiteľa) |

### Workspace (žiak)
| Metóda | Cesta | Popis |
|---|---|---|
| GET | `/api/workspace/{token}` | `{"assignment_id", "name", "program_text", "state": …}` — state = svet assignmentu (žiakov beh sa neperzistuje, len program) |
| PUT | `/api/workspace/{token}` | body = `{"program_text": "…"}` → uloží žiakov program (auto-save z editora) |

---

## 3. WebSocket protokol — `/ws/{token}` (žiak) a `/ws/teacher/{session_id}` (učiteľ)

Všetky správy JSON, vždy s `"v": 1` a `"type"`.

### Klient → server

| type | Polia | Význam |
|---|---|---|
| `run` | `program: str` | parsuj a spusti program (z aktuálnej pozície Karela) |
| `stop` | — | zastav beh |
| `reset` | — | `_reset_world()` — svet späť na štart assignmentu, počítadlá vynulované |
| `direct` | `cmd: str` | priamy príkaz (slovo aliasu, napr. `"dopredu"`) — ekvivalent tlačidla |
| `speed` | `delay: float` | nastav delay interpretera (sekundy/krok, 0.02–3.0) |
| `get_state` | — | vyžiadaj plný stav (napr. po reconnect-e) |

Učiteľská session navyše:
| type | Polia | Význam |
|---|---|---|
| `load_world` | `karxml: str` \| `world_id: str` | natiahni svet do session |
| `apply_settings` | `settings: {…}`, `goal_conditions: […]`, `title`, `intro_html`, … | ekvivalent WorldSettings Apply (bez resetu Karela) |

### Server → klient

| type | Polia | Význam |
|---|---|---|
| `state` | `state: State` (§4), `reason: "connect"\|"reset"\|"load"\|"requested"` | plný stav sveta |
| `step` | `state: State` | stav po jednom kroku interpretera (on_step) |
| `parse_error` | `message: str`, `line: int` | syntaktická chyba — beh nezačal |
| `started` | — | program začal bežať |
| `finished` | `status: "done"\|"stopped"` | beh skončil |
| `error` | `message: str` | KarelError (neznáma procedúra, zakázaný príkaz…) |
| `budget` | `kind: "steps"\|"turns"` | vyčerpaný rozpočet → frontend zobrazí dialóg OK/Reset |
| `limit` | `kind: "loop"\|"recursion"` | bezpečnostný strop → dialóg OK |
| `mission` | `result: "success"\|"failure"`, `message_html: str` | výsledok misie (on_step aj on_finish) |
| `direct_result` | `ok: bool`, `error: str?` | výsledok priameho príkazu |

Poradie pri behu: `started` → `step`* → (`finished` | `error` | `budget` | `limit` | `mission`).
`step` správy server **throttluje** podľa `delay` (posiela po každom kroku, ako desktop `on_step`).

---

## 4. State JSON (stav sveta)

Riedky (sparse) formát — posiela sa celý pri každom kroku (svety sú max 50×50;
optimalizácia na delty je možná neskôr bez zmeny kontraktu — pribudol by typ `delta`).

```json
{
  "width": 10, "height": 8,
  "karel": {"x": 1, "y": 1, "dir": "E"},
  "bricks":     [[3,1,2], [4,1,1]],          // [x, y, count]
  "big_bricks": [[2,3]],                      // [x, y]  (max 1/tile)
  "marks":      [[1,1]],                      // [x, y]
  "walls":      [[0,0,"S"], [0,0,"W"]],      // [x, y, side] — vrátane okrajov
  "inventory":  {"bricks": -1, "big_bricks": -1, "marks": -1},   // -1 = ∞
  "counters":   {"steps_used": 0, "turns_used": 0},
  "settings": {
    "prog_lang": "sk", "disabled_cmds": ["BACK"], "disable_procedure": false,
    "max_climb": 1, "max_drop": -1, "max_steps": -1, "max_turns": -1,
    "max_brick_height": -1,
    "camera_locked": false, "camera": {"az": 3.93, "el": 0.49, "dist": 16.0}
  },
  "meta": {"title": "…", "intro_html": "…", "success_html": "…", "failure_html": "…"},
  "mission": [ {"check":"karel_pos","eval":"failure","when":"on_step",
                "op":"or","negate":false,"x":3,"y":1,"z":1}, … ]
}
```

Súradnice ako v core: x=0 vľavo, y=0 dole. `mission` a `settings` posiela server
len učiteľskej session a pri `connect` (žiak ich potrebuje na zobrazenie obmedzení,
ale nemôže ich meniť — vynucuje server).

---

## 5. Persistencia (Storage rozhranie)

```
data/                              ← Docker volume
├── assignments/{id}.json          {"karxml": "...", "title": "...", "created": ...}
├── links/{token}.json             {"assignment_id": "...", "name": "Janko"}
└── workspaces/{token}.json        {"program_text": "...", "updated": ...}
```

Python rozhranie (implementácia v1 = súbory; neskôr vymeniteľné za DB):
```python
class Storage(Protocol):
    def save_assignment(self, data: dict) -> str            # → id
    def load_assignment(self, id: str) -> dict | None
    def create_links(self, assignment_id, names_or_count) -> list[dict]
    def resolve_token(self, token: str) -> dict | None       # → {assignment_id, name}
    def save_workspace(self, token: str, data: dict) -> None
    def load_workspace(self, token: str) -> dict | None
```

Tokeny: `secrets.token_urlsafe(12)` (16 znakov URL-safe).

---

## 6. Bezpečnostné poznámky

- Interpreter beží na serveri — **MAX_OPS=100k a MAX_D=1000 sú kritické** (už v core)
- Jeden beh = jedno vlákno; server limituje **1 bežiaci program na session**
- `delay` clamp 0.02–3.0 (žiak si nezníži na 0 a nezahltí WS)
- Veľkosť programu limit 64 kB; veľkosť .karxml 256 kB
- Tokeny neuhádnuteľné; assignment po zdieľaní immutable (nový = nová verzia)
