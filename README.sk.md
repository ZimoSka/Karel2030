# Karel 2030

> 🇬🇧 [English version / Anglická verzia](README.md)

**Webový** výukový programovací simulátor postavený na koncepte robota Karla.
Žiaci programujú robota na mriežke priamo v prehliadači; učiteľ pripraví svety a
zdieľa ich žiakom cez linky. Karel 2030 je webové pokračovanie desktopovej
aplikácie **Karel 2010** (tkinter) — obe používajú rovnaké jadro `karel_core`.

- **Backend:** Python + FastAPI (REST + WebSocket)
- **Frontend:** prehliadač (Three.js 3D scéna + CodeMirror editor)
- **Nasadenie:** Docker (Linux image)

## Prehľad

Karel je robot, ktorý sa pohybuje v mriežkovom svete. Žiaci ho programujú
jednoduchým jazykom a učia sa základy algoritmického myslenia. Učiteľ pripraví
svet (rozloženie + zadanie + podmienky splnenia), pošle link a naživo sleduje
pokrok každého žiaka.

## Spustenie (web)

Cez Docker:

```bash
KarelAdminPWD=tvojeTajneHeslo docker compose up -d
```

Potom otvor **http://localhost:8000/**. Admin heslo (`KarelAdminPWD`) chráni
publikovanie/mazanie zdieľaných svetov — pozri návod pre učiteľa nižšie. Prázdne
heslo = admin prihlásenie vypnuté.

Lokálny vývoj bez Dockeru:

```bash
pip install fastapi "uvicorn[standard]" pillow numpy
python -m uvicorn server.app:app --reload --port 8000
```

> Pôvodná **desktopová** appka je stále v repozitári a beží samostatne:
> `python karel2010.py`. Aktívne vyvíjaná je webová verzia.

## Role

| Rola | Prístup | Čo môže |
|------|---------|---------|
| **Učiteľ** (predvolené) | hlavná adresa `/` | Tvoriť/upravovať svety, spúšťať programy, zdieľať žiakom, kontrolovať pokrok |
| **Žiak** | zdieľaný link `…/s/{kód}` | Vidí len zadanie + prostredie na riešenie; program sa automaticky ukladá |
| **Admin** | učiteľ + heslo (🔒 Admin) | Navyše publikovať (📤) / mazať (🗑) zdieľané svety |

## Zdieľanie so žiakmi (v skratke)

1. **👥 Zdieľaj** otvorí jedno okno naviazané na aktuálny svet.
2. Nastav **🌐 adresu pre žiakov** (verejná IP/hostname:port), aby linky fungovali aj mimo localhostu.
3. **➕ Pridať žiaka** → skopíruj jeho trvalý link → pošli mu ho.
4. Sleduj stav každého žiaka: **— nezačal / ✏️ pracuje / ✅ vyriešil**, zobraz
   jeho program (👁) alebo ho zmaž (🗑).

Celý návod: **[docs/sk/navod-web-ucitel.md](docs/sk/navod-web-ucitel.md)** (SK) ·
**[docs/teacher-web-guide.md](docs/teacher-web-guide.md)** (EN).

## Jazyk Karla

Učiteľ nastaví programovací jazyk pre každý svet; interpreter akceptuje všetky
varianty kľúčových slov súčasne.

```
zaciatok          ← slovenčina  |  begin          ← angličtina
  opakuj 4 krat  ← slovenčina   |    repeat 4 times
    dopredu                      |      forward
    vlavo                        |      left
  koniec                         |    end
koniec                           |  end
```

**Podporované jazyky kľúčových slov:** slovenčina (`sk`) · angličtina (`en`) ·
nemčina (`de`) · francúzština (`fr`) · taliančina (`it`) · španielčina (`es`) ·
angličtina/Pattis (`en_pattis`). Oba rozbaľovacie zoznamy sa dopĺňajú automaticky
zo súborov — pridanie jazyka si vyžaduje len príslušné súbory. Kompletná tabuľka:
**[docs/language-reference.md](docs/language-reference.md)**.

## Formát súboru sveta (.karxml)

Svety sú uložené ako `.karxml` (XML): rozmer mriežky, pozícia Karla, tehly, veľké
tehly, značky, steny, zadanie (HTML), nastavenia (limity, zakázané príkazy,
kamera, jazyk) a misia (podmienky splnenia). Špecifikácia:
**[docs/karxml-format.md](docs/karxml-format.md)**.

Zabudované svety sú v `worlds/`; svety publikované z appky sú na dátovom úložisku
servera (`data/worlds/`). Na prenesenie in-app úprav späť do repozitára slúži
`scripts/sync_worlds.ps1` (pozri [CLAUDE.md](CLAUDE.md)).

## Vlastnosti

- **3D pohľad** (Three.js) s ovládaním myšou (otáčanie/posun/zoom)
- **Editor programov** so zvýrazňovaním syntaxe a filtrom príkazov
- **Priame ovládanie** Karla tlačidlami aj písaným príkazom
- **Plnohodnotný interpreter** (procedúry, cykly, podmienky s `nie`/`a`/`alebo`
  + zátvorky; ochrana proti nekonečnému cyklu a rekurzii)
- **Editor nastavení sveta** — obmedziť príkazy, zakázať grafické/príkazové
  ovládanie, limity zásob, zámok kamery, jazyk per svet
- **Systém misií** — podmienky splnenia, úspech/neúspech, reset pri neúspechu
- **Zdieľanie žiakom** — linky per žiak, autosave programov, sledovanie pokroku
  a vyriešenia
- **Admin režim** — publikovanie chránené heslom s blokovaním proti hádaniu

## Dokumentácia

| Dokument | Komu | Popis |
|----------|------|-------|
| [docs/sk/navod-web-ucitel.md](docs/sk/navod-web-ucitel.md) | Učitelia (web) | **Admin, tvorba/ukladanie svetov, zdieľanie a kontrola žiakov** |
| [docs/sk/navod-pre-ucitelov.md](docs/sk/navod-pre-ucitelov.md) | Učitelia | Tvorba svetov + pedagogická postupnosť |
| [docs/sk/navod-pre-ziakov.md](docs/sk/navod-pre-ziakov.md) | Žiaci | Popis rozhrania, rýchla referencia jazyka |
| [docs/sk/jazyk-karla.md](docs/sk/jazyk-karla.md) | Všetci | Kompletná referencia jazyka Karel |
| [CHANGELOG.md](CHANGELOG.md) | Všetci | História verzií (web) |

Technická dokumentácia (architektúra, API) je v angličtine: [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md).

## Pozadie

Karel 2030 vychádza z **Karla 2010**, Python portu výukového prostredia
navrhnutého ako diplomová práca na FMFI Univerzity Komenského v Bratislave
(Mgr. Michal Zeman, 2004). Koncept robota Karla pochádza od Richarda Pattisa
(*Karel the Robot*, 1981) a pre slovenské školy ho v 80. rokoch prispôsobili
Marián Vittek, Andrej Blaho a kolegovia.

## Autor

Originál: Mgr. Zimo, 2005 · Webová verzia: 2026
https://github.com/ZimoSka/Karel2030
