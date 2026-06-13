# Karel 2030 — Návod pre admina

> 🇬🇧 [English version](../admin-guide.md)

Tento návod pokrýva spustenie servera Karel 2030, nastavenie admin hesla a správu publikovaných svetov.

---

## Prehľad admin režimu

Existujú tri roly:

| Rola | Prístup | Čo môže robiť |
|------|---------|---------------|
| **Učiteľ** | Hlavná URL `/` | Tvorba/úprava svetov, zdieľanie so žiakmi, sledovanie pokroku |
| **Žiak** | Zdieľaný link `/s/{token}` | Riešenie zadania; program sa automaticky ukladá |
| **Admin** | Učiteľ + prihlásenie heslom | Navyše: publikovanie (📤) a mazanie (🗑) zdieľaných svetov |

Admin režim sa odomkne kliknutím na **🔒 Admin** v toolbare a zadaním hesla. Je to **upgrade na úrovni relácie** — zatvorenie prehliadača vráti späť do učiteľského módu.

---

## Spustenie cez Docker (odporúčané)

Docker je primárny spôsob nasadenia. Obraz beží na Linuxe a zahŕňa všetky závislosti.

### Predpoklady
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) alebo Docker Engine (Linux)
- `docker compose` (súčasť Docker Desktop)

### Rýchly štart

```bash
# 1. Klonovanie repozitára
git clone https://github.com/ZimoSka/Karel2030.git
cd Karel2030

# 2. Vytvor súbor .env s admin heslom
echo "KarelAdminPWD=tvojeHeslo" > .env

# 3. Zostavenie a spustenie
docker compose up -d

# 4. Otvoriť v prehliadači
# http://localhost:8000/
```

### Zastavenie a reštart

```bash
docker compose down          # zastaviť
docker compose up -d         # spustiť znova (použije existujúci obraz)
docker compose up -d --build # prestaviť obraz (po zmenách kódu)
```

### Po zmenách kódu (JS, Python, šablóny)

```bash
docker compose build --no-cache && docker compose up -d
```

---

## Admin heslo (`KarelAdminPWD`)

Admin heslo sa nastavuje cez premennú prostredia `KarelAdminPWD`.

**Ak je prázdna alebo nenastavená → admin prihlásenie je vypnuté (všetci sú len učitelia).**

### Nastavenie hesla

**Možnosť 1 — súbor `.env`** (odporúčané):
```
# Karel2030/.env
KarelAdminPWD=tvojeHeslo
```
Súbor `.env` je v gitignore — nebude commitnutý do repozitára.

**Možnosť 2 — inline s docker compose:**
```bash
KarelAdminPWD=tvojeHeslo docker compose up -d
```

**Možnosť 3 — exportovanie v shelli (PowerShell):**
```powershell
$env:KarelAdminPWD = "tvojeHeslo"
docker compose up -d
```

### Bezpečnostné poznámky
- Porovnanie hesla používa `secrets.compare_digest` (odolné voči časovacím útokom).
- Po **3 neúspešných pokusoch** sa IP adresa zablokuje na **30 minút**.
- Blokovanie je na základe `X-Forwarded-For` alebo priamej IP klienta.
- Admin relácia je uložená v **httponly cookie** (nedostupná pre JavaScript).
- Zmeňte heslo aktualizáciou `.env` a reštartom: `docker compose up -d`.

---

## Perzistencia dát

Publikované svety a dáta žiakov sú uložené v Docker **volume** `karel_data`, pripojenom na `/data` v kontajneri.

```yaml
# docker-compose.yml (výňatok)
volumes:
  - karel_data:/data
```

Tieto dáta pretrvávajú naprieč reštartami a prestavbami kontajnera. Záloha:

```bash
docker run --rm -v karel_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/zaloha_karel_data.tar.gz /data
```

Vstavané svety sú v priečinku `worlds/` repozitára. Svety publikované z aplikácie sa ukladajú do `data/worlds/` na volume.

Synchronizácia publikovaných svetov späť do repozitára: `scripts/sync_worlds.ps1`.

---

## Lokálny vývoj bez Dockera (len pre vývojárov)

> Táto sekcia je pre prispievateľov, ktorí menia zdrojový kód. **Učitelia vždy používajú Docker.**

Karel 2030 možno spustiť aj priamo bez Dockera:

```bash
# Inštalácia Python závislostí
pip install fastapi "uvicorn[standard]" pillow numpy

# Vytvor dátový priečinok
mkdir -p data/worlds

# Spustenie dev servera (auto-reload pri zmenách súborov)
python -m uvicorn server.app:app --reload --port 8000
```

Potom otvorte `http://localhost:8000/`.

> **Poznámka:** Vstavané svety sa načítajú z `worlds/`. Publikované svety idú do `data/worlds/`. `KarelAdminPWD` nastavte ako bežnú premennú prostredia (`$env:KarelAdminPWD = "heslo"` v PowerShell).

Vendor JS súbory (Three.js, CodeMirror) pri chýbaní fallbackujú na CDN. Na stiahnutie pre offline použitie: `python vendor/get_vendor.py`.

---

## Publikovanie a mazanie svetov

Po prihlásení ako admin (tlačidlo 🔒 Admin → zadanie hesla):

- **📤 Publikovať** — uloží aktuálny svet na server do `data/worlds/`. Okamžite sa objaví v dropdowne Svetov pre všetkých používateľov.
- **🗑 Zmazať** — odstráni aktuálne vybraný publikovaný svet. Nedá sa vrátiť späť.

Vstavané svety (z priečinka `worlds/` repozitára) nemožno mazať cez UI — odstráňte ich z priečinka `worlds/` a prestavte obraz.

---

## Vlastný 3D model (GLB)

Admin používatelia môžu nahradiť predvolený model Karela vlastným `.glb` súborom:

1. Kliknite **⚙** (nastavenia aplikácie) → sekcia Vlastný 3D model.
2. Kliknite **📁 Vybrať…** a vyberte `.glb` súbor z počítača.
3. Nastavte **yaw** (rotáciu) a **výšku** podľa modelu.
4. Model je uložený v relácii prehliadača (nie na serveri).

> **Dôležité:** Vlastný model sa načítava z vášho počítača pri každej relácii. Uchovajte `.glb` súbor na rovnakom mieste.

> **Bezpečnostná poznámka:** Pribalený `grogu.glb` (ak je prítomný) je Disney IP — je v gitignore a nesmie byť nikdy commitnutý do verejného repozitára ani zahrnutý v Docker obrazoch distribuovaných cez GHCR/CI.

---

## Vendor JS súbory (offline použitie)

Karel 2030 načítava Three.js, CodeMirror, atď. z `vendor/` s CDN fallbackom. Pre plne offline nasadenie (napr. trieda bez internetu):

```bash
python vendor/get_vendor.py
docker compose build --no-cache && docker compose up -d
```

---

## Prehľad premenných prostredia

| Premenná | Predvolená | Popis |
|----------|-----------|-------|
| `KarelAdminPWD` | *(prázdna)* | Admin heslo. Prázdna = admin vypnutý. |
| `PORT` | `8000` | Port (nastavený v docker-compose.yml) |

---

## Aktualizácia Karel 2030

```bash
git pull
docker compose build --no-cache && docker compose up -d
```

Dáta žiakov a publikované svety na volume nie sú aktualizáciou dotknuté.
