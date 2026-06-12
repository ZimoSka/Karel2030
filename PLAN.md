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

### T1 — Core extrakcia  ✅ HOTOVÉ
`karel_core/` balík bez tkinter závislostí: `base.py` (Direction+výnimky),
`missions.py`, `lang.py` (.lng+.ini, KAREL_LANG_DIR env), `world.py`
(vrátane .karxml I/O — karxml.py netreba, XML žije pri World), `interpreter.py`,
`samples.py`. Desktop `karel2010.py` importuje core a funguje ďalej (2642 r.).
**19 regresných testov** v `tests/test_core.py` — parser, logické spojky,
rozpočty, fyzické limity, loop-guard, rekurzia, XML roundtrip, misie, jazyky.

### 🐞 Spätná väzba z testovania (jún 2026) — vyriešiť neskôr

**Bugy:**
- [x] **B1. Default pohľad kamery zlý** — opravené: render3d mapoval worldY→−Z
      (zrkadlilo voči pythonu); zmenené na worldY→+Z (zhodné s Python desktopom),
      vrátane podlahy/mriežky/stien/cieľa kamery a smeru Karela. az/el sedí 1:1.
- [x] **B2. Nastavenia sveta sa nedali otvoriť po pohybe** — opravené: `step` aj
      `state` sa teraz zlučujú do `state` (Object.assign), takže settings/mission
      prežijú step správy (full=False). Overené: dialóg sa otvorí po pohybe.
- [x] **B3. Dialóg nastavení menil veľkosť podľa záložky** — opravené: `#set-body`
      pevná výška 380px → dialóg konštantný (523px na všetkých 6 záložkách).

**UX / texty:**
- [x] **U1. Editor „Môj program" default** — nechať štruktúru `zaciatok … koniec`
      + pôvodný úvodný komentár (ako desktop EXAMPLES).
- [x] **U2. Zoznam príkazov — celé šablóny štruktúr** — `opakuj N krat … koniec`,
      `kym podm rob … koniec`, `ak podm potom … inak … koniec` (nie len kľúčové slovo);
      dieťa čo nepozná syntax inak nemá šancu. (Desktop má `_cmds_structs`.)
- [x] **U3. Zadanie úlohy — rich text editor** namiesto HTML, s náhľadom výsledku;
      + prejsť všetky svety a upraviť `intro_html` nech vyzerajú pekne.
- [x] **U4. Misia úspech/neúspech — rich text** + skonvertovať nečitateľné HTML texty.
- [x] **U5. Záložka Miestnosť** — „Pozícia Karla štartovacia" + „výška" je mätúce;
      premenovať na **X** a **Y** (výška = Z).
- [x] **U6. Pohybové obmedzenia** — dopísať že **-1 = neobmedzené**; a spraviť to
      checkboxom „neobmedzené" ako pri Zásobách (krajšie).
- [x] **U7. Záložka Príkazy — otočiť logiku**: zaškrtnuté = príkaz **viditeľný**
      (logickejšie). *(rovnaká zmena aj v Python Karlovi — viď jeho PLAN)*
- [x] **U8. Texty podmienok — skloňovanie**: „Poloha Karla" → „Poloha **Karela**";
      prejsť VŠETKY texty (Karel sa skloňuje: Karela/Karelovi…).
- [x] **U9. Ikona/brand** — robotia hlava vľavo hore je strašidelná; dať krajšiu;
      text zmeniť na **„Karel 2030"**.

**Funkcie:**
- [x] **F-prog. Programovací jazyk presunúť do Nastavení sveta** (ako Python verzia),
      nie do toolbaru.
- [x] **F-admin. Úroveň admin — editovať publikované svety** v kontajneri
      (načítať publikovaný svet, upraviť, znova publikovať/zmazať).

---

### T2 — Integračná vrstva (API)  ✅ HOTOVÉ
`server/` balík podľa docs/api.md: `state.py` (World↔sparse JSON), `storage.py`
(FileStorage, KAREL_DATA_DIR), `sessions.py` (interpreter na daemon vlákne →
asyncio fronta → WS), `app.py` (všetky REST endpointy + WS /ws/{token} +
/ws/teacher/{id} + static mount + /s/{token}). 13 server testov, spolu 32
zelených. Diery kontraktu zdokumentované v server/NOTES.md.

### T3 — Web frontend  ✅ HOTOVÉ (v1)
`static/`: Three.js 3D scéna (mriežka/steny/tehly/kvadre/značky/Karel,
OrbitControls), CodeMirror s dynamickým Karel módom, panely podľa desktopu,
dialógy, i18n cez data-i18n, mock mód (?mock=1), vendor knižnice lokálne.
**Overené v prehliadači:** mock mód (beh s opakuj, parse error dialóg) AJ
reálny server end-to-end (`kym nie stena` cez WS, Karel došiel k stene,
0 chýb v konzole). Diery kontraktu v static/NOTES.md.
**Zostáva → rozpísané v T3.2 nižšie (GUI parita s desktopom).**

### T3.2 — Dorovnanie GUI funkcií voči desktop Karel 2010  ✅ HOTOVÉ (A–G)
Vývoj a testovanie na **lokálnom Dockeri** (deploy odložený, viď „Odložené").
Gap-analýza (web GUI má: beh/stop/reset, speed, príklady, 3D, inventár+počítadlá,
dpad+5 akčných tlačidiel, CodeMirror editor + plochý zoznam príkazov, dialógy
intro/mission/budget/limit/parse_error, i18n, disabled_cmds, direct ovládanie):

Chýba oproti desktopu:
- [x] **A. Tlačidlá pohľadu kamery** (Def/Pred/Vrch/Bok) — hotové, overené
- [x] **B. Príkazový režim** — taby Graficky/Príkazovo + log, písaný príkaz cez
      ws.direct — hotové, overené
- [x] **C. Filter príkazov** — filter input + skupiny (pohyb/štruktúry/podmienky)
      + „Tvoje príkazy" z editora — hotové, overené
- [x] **D. Nastavenia sveta (učiteľ)** — dialóg so 6 záložkami (settings.js),
      end-to-end overené (resize, title, limity, zakázané príkazy, kamera)
- [x] **E. Editor misií (GoalCondition)** — add/edit/remove podmienok (6 typov,
      eval/when/op/negate, snapshot z aktuálneho stavu) — overené
- [x] **F. Otvoriť/Uložiť svet a program** — F1 lokálny disk (.karxml), F2 admin
      publish do volume, F3 dropdown predvyrobených svetov, F4 program ↔ súbor.
      Backend: merge worlds/+data/worlds/, POST /api/worlds, WS export_world,
      rola admin (?role=admin). Overené (publish AdminTest, load Bludisko).
- [x] **G. Prepínač jazyka** — UI jazyk (localStorage) + prog jazyk (per-svet
      cez applySettings) dropdowny; overené (EN UI + EN príkazy).

✅ **T3.2 GUI parita HOTOVÁ** (A–G). Web GUI dorovnané s desktop Karel 2010.

> **Pozn.:** editácia miestnosti myšou v 3D NIE je v pláne — nebola ani
> v pôvodnom Karlovi. Učiteľ skladá svet priamym ovládaním (B) + uloží (F).

### T4 — Docker + deploy  🟡 build overený, nasadenie zostáva
✅ Dockerfile, docker-compose.yml, .dockerignore, GitHub Actions → ghcr.io,
worlds/ so vzorovými svetmi.
✅ **Lokálny build + beh overený** (Docker Desktop, image 181 MB, python:3.12-slim):
kontajner naštartoval uvicorn, frontend na `/`, všetky REST endpointy OK,
share-link tok (assignment→linky→workspace) zapísal do `/data`, WebSocket
beh end-to-end (state→started→step→finished, Karel došiel k stene).
✅ **GitHub Actions overené** — beh 27295518843 zelený: testy → buildx →
push do `ghcr.io/zimoska/karel2030:latest` (+ :SHA), manifest potvrdený.
(Staršie zlyhania boli prechodný Docker Hub timeout, nie chyba.)
**Nasadenie → ODLOŽENÉ** (viď „Odložené na neskôr").

---

## ⏸ Odložené na neskôr (po dorovnaní GUI)

- **Nasadenie na linux server** — SSH kľúč (root) + `docker context`/`compose pull`;
  package v ghcr.io spraviť public alebo login tokenom; Node 20 → bump verzií actions.
  CI/CD (build+push do ghcr.io) je hotové a overené, chýba len krok na serveri.
- ✅ **Perzistentné zdieľanie žiackych liniek — HOTOVÉ (v0.5.0)**. Učiteľ „👥 Zdieľaj"
  (mená/počet → linky s kopírovaním), žiak `/s/{token}` → žiacky mód, program auto-save
  na volume, prežíva reload. Fix `<base href="/">` pre assety na /s/{token}.
  Overené end-to-end v kontajneri (assignment→link→workspace→reload).

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
