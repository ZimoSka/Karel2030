# Changelog — Karel 2030 (web)

Verzia žije v súbore `VERSION` a zobrazuje sa na webe (badge) aj cez
`GET /api/version`. Formát: `MAJOR.MINOR.PATCH`.

Dokumentácia pre učiteľa: [docs/teacher-web-guide.md](docs/teacher-web-guide.md)
(EN), [docs/sk/navod-web-ucitel.md](docs/sk/navod-web-ucitel.md) (SK).

---

## 2.0.0 — GUI parita s desktopom kompletná; prvý stabilný release pre školy

Milestone: webová verzia Karla 2030 dosiahla plnú paritu funkcií s desktop Karel 2010.
Nasadená na Linux server (`http://10.0.1.22:8090/`) pre žiakov a učiteľov.

**Nové od v1.4.0:**
- Globálne vizuálne nastavenia (farby/textúry) sa ukladajú na server a platia pre
  všetkých používateľov naraz; prežijú reštart kontajnera (`data/visual.json`).
- Grogu GLB modely pridané priamo do Docker image (nie gitignored).
- Oprava: výber „—" v dropdowne Svety načíta prázdny builtin svet (predtým chyba).
- Oprava: `_DATA_DIR` NameError pri štarte kontajnera s globálnymi vizuálnymi nastaveniami.

**Kompletné od v1.0.0 (T3.2 GUI parita):**
- Tlačidlá pohľadu kamery (Def/Pred/Vrch/Bok)
- Príkazový režim (taby Graficky/Príkazovo + log)
- Filter príkazov so skupinami + „Tvoje príkazy" z editora
- Nastavenia sveta (6 záložiek): resize, title, limity, zakázané príkazy, kamera
- Editor misií (6 typov podmienok, eval/when/op/negate, snapshot)
- Otvoriť/Uložiť svet a program (lokálny disk + admin publish do volume)
- Prepínač jazyka (UI jazyk + prog jazyk per-svet)
- Admin režim chránený heslom (env `KarelAdminPWD`, lockout po 3 pokusoch)
- Zdieľanie pre žiakov (persistentné linky, autosave, sledovanie vyriešenia)
- Rich text editor pre zadanie/úspech/neúspech misie
- Docker image na `ghcr.io/zimoska/karel2030`, GitHub Actions CI

**Ďalší krok: T5 Blockly editor (v2.x.x)**

## 1.4.0 — Vizuálne nastavenia uložené na serveri (pre všetkých používateľov)

- Vizuálne nastavenia (farby, textúry, viditeľnosť) sa ukladajú na server ako
  sidecar `{world_id}_visual.json` — platia pre učiteľa aj všetkých žiakov.
- Nové endpointy: `GET /api/worlds/{id}/visual`, `PUT /api/worlds/{id}/visual` (admin).
- Visual settings sú súčasťou WS state (`reason: load/connect`) — žiaci ich
  dostanú automaticky pri načítaní sveta.
- Admin dialóg auto-ukladá zmeny na server (debounce 800 ms) ak je otvorený svet.
- Posledný otvorený svet sa pamätá cez refresh (localStorage `karel_last_world`).
- Admin-only nastavenia: skin, vizuálne nastavenia a vlastný GLB model skryté
  pre žiakov (vidí len výber jazyka).
- Tlačidlo v nastaveniach zmenené z „Zavrieť" na „OK".

## 1.3.0 — Vizuálne nastavenia sveta + Grogu malý + oprava orientácie

- **Vizuálne nastavenia sveta** v ⚙ Nastavenia: farba/textúra + viditeľnosť pre
  Murik, Podlahu, Grid, Okolie; len farba/textúra pre Tehlu, Kvader, Značku.
  Aplikujú sa naživo, ukladajú do localStorage. Textúry z lokálneho súboru (PNG/JPG…);
  textúry > 1 MB sa neukladajú (session-only) s upozornením.
- **Grogu malý** (`grogu_small.glb`, ~4.8 MB) — nový default skin (bola 21 MB verzia).
  Grogu HD (`grogu.glb`) ostáva ako voliteľný skin v menu. Oba gitignored (Disney IP).
- **Oprava orientácie GLB modelu**: `yaw = -π/2` (GLB štandard: +Z dopredu → Karel: +X
  dopredu). Komentár v `KAREL_SKINS` vysvetľuje ako nastaviť `yaw` pre ďalšie modely.
- `KarelRenderer.skinList()` — statická metóda pre dynamický zoznam skinov v dialógu.
- `renderer.getVisualSettings()` / `applyVisualSettings(vs)` — verejné API renderera.

## 1.2.0 — Okno nastavení + výber skinu (Grogu default)

- Nové **⚙ Nastavenia** (ikona v lište, pre všetkých): jazyk rozhrania +
  vzhľad Karla. Výber jazyka **presunutý** z lišty do tohto okna.
- **Skiny Karla** vymeniteľné za behu cez `KAREL_SKINS` (Grogu / Robot).
  Default **Grogu** (`models/grogu.glb`); voľba sa pamätá v localStorage,
  prepnutie naživo prekreslí Karla. Robota (kvádre) možno kedykoľvek zvoliť.
- `renderer.setSkin(id)` + reposícia na aktuálny stav po načítaní modelu.
- `grogu.glb` (~20 MB, Disney IP) je v `.gitignore` — v repe/CI nie je;
  do lokálneho image sa zabalí (`.dockerignore` ho nevylučuje).

## 1.1.0 — Vymeniteľný 3D model Karla (skin)

- Ak existuje `static/models/karel.glb`, renderer ho použije namiesto kvádrovej
  postavičky; inak ostáva default robot (404 → tichý fallback). GLTFLoader
  vendorovaný (offline) + CDN fallback.
- Model sa automaticky vycentruje, postaví na podlahu a zmenší na políčko;
  ladenie cez `KAREL_MODEL_YAW` / `KAREL_MODEL_HEIGHT` v `render3d.js`.
- `.glb`/`.gltf` v `static/models/` sú v `.gitignore` (IP — napr. Grogu/Disney
  sa nedistribuuje). Návod na export z Blenderu: `static/models/README.md`.

## 1.0.0 — Save kamery, oprava príkladov, učiteľom upravené svety

- Uloženie sveta zapamätá aktuálny pohľad kamery (az/el/dist).
- Príklady: medzery okolo „/"; prázdny príklad = len zaciatok/koniec, komentár 2030.
- Pullnuté učiteľom upravené svety (01, 1a1, Bludisko) do repa.

## 0.9.0 — Layout zdieľania, verejná adresa, trvalosť svetov

- **Zdieľanie — rozloženie:** karta žiaka prerobená na dve línie
  (meno + stav + akcie / link + kopíruj), `min-width:0` na inputoch a širší
  dialóg → žiadny horizontálny scrollbar pri dlhých menách/linkoch.
- **Verejná adresa pre žiakov:** pole „🌐 Adresa pre žiakov" (IP/hostname:port,
  default `localhost:8000`, uložené v `localStorage`). Linky sa generujú z nej
  (nie z `location.origin`) a prepočítavajú sa naživo → fungujú aj mimo localhostu.
- **Trvalosť svetov:** zdroj pravdy = repo `worlds/`. `scripts/sync_worlds.ps1`
  (`pull`/`push`/`list`) na zachytenie in-app úprav (volume `data/worlds`) späť
  do gitu; pravidlo workflow v `CLAUDE.md`. Svet 01 reconcilovaný (zlúčená oprava
  misie + `disabled_cmds` z in-app verzie).

## 0.8.0 — Admin režim chránený heslom

- Env **`KarelAdminPWD`** definuje admin heslo (`docker-compose.yml`).
  Prázdne → admin prihlásenie vypnuté (403).
- Tlačidlo **🔒 Admin**: dialóg na heslo → admin režim (zobrazia sa 📤/🗑).
  Opätovný klik = odhlásenie. Stav prežije refresh (httponly cookie, 8 h).
- Server: `POST /api/admin/login` (`secrets.compare_digest`),
  `GET /api/admin/status`, `POST /api/admin/logout`.
- **Lockout:** po 3 nesprávnych pokusoch blok na 30 min (podľa X-Forwarded-For/IP),
  429 aj pre správne heslo počas blokovania.
- `POST`/`DELETE /api/worlds` teraz vyžadujú admin cookie (401 inak).
- Stará `?role=admin` URL brána zrušená — admin len cez heslo.

## 0.7.2 — Oprava misie sveta 01

- Úspech sveta 01 bol „skončiť kdekoľvek na muriku vo výške 1" → falošný úspech
  aj keď žiak neprešiel celý murik. Opravené: úspech = `check=sign` na konci
  (Karel musí skončiť na značke = obísť celý okruh).

## 0.7.1 — Reset pri neúspechu aj pri priamom ovládaní

- „Pri neúspechu resetovať svet" fungoval len po behu programu. Opravené:
  `session.direct()` resetuje svet aj po neúspechu pri grafickom/príkazovom kroku.

## 0.7.0 — Jedno okno zdieľania + sledovanie vyriešenia + zákaz ovládania

- **Zdieľanie zlúčené do jedného okna** (👥 Zdieľaj), naviazané na svet:
  pridaj žiaka (meno → link), kopíruj, sleduj pokrok, zmaž. Endpointy
  `assignments/ensure`, `assignments/{id}/links` (POST), `links/{token}` (DELETE).
- **Sledovanie vyriešenia:** žiak, ktorý splní misiu (aj graficky, bez programu),
  sa zaznamená (`mark_completed`); pokrok ukazuje „✅ vyriešil".
- **Zákaz manuálneho ovládania:** `disable_graphic` / `disable_command` vo
  WorldSettings, `.karxml`, state JSON, apply_settings; frontend skryje
  príslušný ovládací tab.

## 0.6.0 — (medzistupeň) zoznam úloh + pokrok žiakov

- Predchodca jedného okna: zoznam úloh a per-žiak pokrok (neskôr zlúčené do 0.7.0).

## 0.5.0 — Zdieľanie pre žiakov (základ)

- Assignmenty + linky + žiacky režim (`/s/{token}`), autosave programu do
  workspace na volume, žiacka stránka cez `<base href="/">`.
- Verziovanie (VERSION, `/api/version`, badge, no-cache statika, git SHA/build
  time cez build-args).

---

## Architektúra (kde čo je)

- **`karel_core/`** — GUI-free jadro (model sveta, jazyk, interpreter, misie),
  zdieľané s desktopom.
- **`server/`** — FastAPI: `app.py` (REST + WS + admin + statika),
  `sessions.py` (interpreter na vlákne → WS), `state.py` (World↔JSON),
  `storage.py` (assignments/links/workspaces/worlds na volume).
- **`static/`** — frontend (Three.js scéna, CodeMirror editor, dialógy).
- **`worlds/`** — baked svety (zdroj pravdy); `data/worlds/` na volume = publikované.
- **`scripts/sync_worlds.ps1`** — synchronizácia svetov volume ↔ repo.
- **`tests/`** — `test_core.py` (jadro), `test_server.py` (REST/WS/admin).
