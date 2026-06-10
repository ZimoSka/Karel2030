# Karel 2030 – Plán vývoja (webová verzia)

> Projekt vznikol ako klon `karel2010` (desktop tkinter verzia) — git história je
> zachovaná. Desktop verzia žije ďalej v pôvodnom repe; zmeny do nej len on-demand.

---

## Cieľový stav

Karel beží ako **Docker image (Linux)** na serveri. Backend = Python (core z karel2010
+ FastAPI). Frontend = webový prehliadač (Three.js 3D, CodeMirror editor, neskôr Blockly).

**Model používania:**
- Default rola po otvorení = **učiteľ** — pripraví svet, zadanie, nastavenia
- Tlačidlo **„Zdieľaj žiakom"** → unikátne **persistentné linky** pre žiakov
- Link otvorí **žiacky mód** s automaticky natiahnutým svetom; žiak sa vie kedykoľvek vrátiť
- Persistencia: súborové úložisko na Docker volume (`assignments/`, `workspaces/`),
  za rozhraním `Storage` — DB výmena možná neskôr bez zmeny API

**Deployment:** GitHub Actions → `ghcr.io/zimoska/karel2030` → linux server pulluje.
Prístup na server: SSH kľúčom (treba nastaviť — užívateľ je root, kľúč doplníme).

---

## Tasky (možné robiť čiastočne paralelne)

### T1 — Core extrakcia  🔴 prerekvizita pre T2
Z `karel2010.py` vytiahnuť **`karel_core/`** bez tkinter závislostí:
- `world.py` — World, WorldSettings, Direction, KarelError/Stop/Budget/Limit
- `missions.py` — GoalCondition, evaluate_goals
- `lang.py` — KW, _LANG_PRIMARY/_DISABLED/_NAME, .lng/.ini loadery
- `interpreter.py` — tokenize, Parser, AST, KarelInterpreter (MAX_OPS, MAX_D)
- `karxml.py` — to_xml/from_xml (+ .karjson spätná kompatibilita)
- Testy: identické správanie (parser, interpreter, limity, XML roundtrip)

### T2 — Integračná vrstva (API)  ⏳ po T1 (potrebuje core)
- FastAPI + uvicorn
- **WS** `/session/{token}`: run/stop/reset/direct-cmd → server po každom kroku
  posiela delta stavu (on_step ekvivalent); delay rieši server
- **REST**: `/worlds`, `/assignment` (create/share), `/workspace/{token}` (load/save),
  `/langs` (preklady pre frontend)
- `Storage` rozhranie (file-based: JSON/karxml na volume)
- Session model: token → World + interpreter inštancia

### T3 — Web frontend  🟢 čiastočne paralelne s T2 (po dohode API kontraktu)
- Three.js 3D scéna (mriežka, steny, tehly, kvadre, značky, Karel, kamera)
- CodeMirror editor + Karel highlighting (z .lng kľúčových slov)
- Panely: navigátor (inventár), ovládanie (šípky+akcie), príkazy, filter
- Dialógy: intro, misia výsledok, budget, limit
- i18n z lang/*.ini cez API
- Učiteľský mód: nastavenia sveta, misie editor, „Zdieľaj žiakom"
- Žiacky mód: zamknuté nastavenia, natiahnutý svet

### T4 — Docker + deploy  🟢 paralelne (kostra hneď, finalizácia po T2)
- Dockerfile (python slim, uvicorn), docker-compose (volume pre data/)
- GitHub Actions workflow → build → push ghcr.io
- SSH kľúč na linux server + docker context / pull skript
- Lokálne testovanie: Docker Desktop na Windows (engine treba zapnúť)

### T5 — Blockly editor  ⏸ po T3
- Custom bloky pre Karel jazyk + generátor → Karel text → existujúci interpreter
- Prepínač Text ↔ Bloky; prieskum hotový (vzor Otto Blockly/BlocklyDuino)

---

## Paralelizácia — odporúčaný postup

```
T1 core ──────► T2 API ──────► integrácia ◄────── T3 frontend
                   ▲                                   ▲
                   └── API kontrakt (dohodnúť hneď) ───┘
T4 docker kostra ──────────────────────────► T4 finalizácia + deploy
```

1. **Najprv:** T1 + návrh API kontraktu (správy WS, REST endpointy) — dokument `docs/api.md`
2. **Potom paralelne:** T2 (server) a T3 (frontend proti mock dátam podľa kontraktu)
3. **T4 kostra** (Dockerfile, Actions) hocikedy popri tom

---

## ✅ Hotové

- Repo `ZimoSka/Karel2030` založené, klon s históriou karel2010, pushnuté
- Rozhodnutia: share-link model, file storage, stack (FastAPI/Three.js/CodeMirror),
  deploy cez ghcr.io

## Zdedené z karel2010 (funkčný základ core)

- Kompletný interpreter: logické spojky (a/alebo/nie + zátvorky), MAX_OPS=100k,
  MAX_D=1000, KarelBudget (max_steps/max_turns), max_climb/max_drop/max_brick_height
- GoalCondition misie (6 typov, and/or, on_step/on_finish)
- 7 prog jazykov (.lng), 6 GUI jazykov (.ini, 196 kľúčov)
- .karxml formát
