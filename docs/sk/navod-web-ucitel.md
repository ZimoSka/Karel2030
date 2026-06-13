# Karel 2030 (web) — Návod pre učiteľa

Tento návod pokrýva **webovú verziu Karla**: ako sa prihlásiť ako admin, ako
vytvárať a ukladať vlastné svety a ako zdieľať úlohy so žiakmi a kontrolovať
ich prácu.

> Pedagogické pozadie a postupnosť výučby (čo učiť a v akom poradí) nájdeš v
> [navod-pre-ucitelov.md](navod-pre-ucitelov.md). Tento dokument je o **ovládaní
> webovej appky**.

---

## 1. Tri režimy (role)

| Rola | Ako sa do nej dostaneš | Čo môže |
|------|------------------------|---------|
| **Učiteľ** (predvolené) | Otvor hlavnú adresu, napr. `http://localhost:8000/` | Tvoriť/upravovať svety, spúšťať programy, zdieľať žiakom, kontrolovať pokrok |
| **Žiak** | Otvorí **link**, ktorý mu pošleš (`…/s/{kód}`) | Vidí len zadanie, scénu, editor a ovládanie. Program sa mu automaticky ukladá. Nevidí nastavenia sveta ani zdieľanie |
| **Admin** | Učiteľ + prihlásenie heslom (tlačidlo **🔒 Admin**) | Navyše: **publikovať** (📤) a **mazať** (🗑) zdieľané svety na serveri |

Žiak nepotrebuje nič inštalovať ani sa registrovať — stačí mu link v prehliadači.

---

## 2. Admin režim (prihlásenie heslom)

Publikovanie a mazanie spoločných svetov je chránené heslom, aby žiak alebo
náhodný návštevník nemohol meniť obsah na serveri.

### Nastavenie hesla (jednorazovo, technické)

Heslo sa zadáva ako premenná prostredia kontajnera **`KarelAdminPWD`**.
V `docker-compose.yml` je už pripravené:

```yaml
environment:
  - KarelAdminPWD=${KarelAdminPWD:-}
```

Spustenie s vlastným heslom:

```bash
KarelAdminPWD=tvojeTajneHeslo docker compose up -d
```

alebo vytvor súbor `.env` vedľa `docker-compose.yml`:

```
KarelAdminPWD=tvojeTajneHeslo
```

Ak je heslo prázdne, admin prihlásenie je **vypnuté** (server odmietne s 403).

### Prihlásenie

1. Klikni na **🔒 Admin** v hornej lište.
2. Zadaj heslo → **Prihlásiť**.
3. Po úspechu sa tlačidlo zmení na **🔓 Admin** a objavia sa admin nástroje
   (📤 Publikovať, 🗑 Zmazať svet).
4. Prihlásenie platí ~8 hodín a **prežije obnovenie stránky** (drží sa v cookie).
5. Opätovný klik na **🔓 Admin** = odhlásenie.

### Ochrana proti hádaniu hesla

Po **3 nesprávnych pokusoch** sa admin pre dané zariadenie **zablokuje na 30 minút**
— počas blokovania neprejde ani správne heslo. Toto je zámerná ochrana.

---

## 3. Tvorba vlastného sveta

Svet = mriežka, na ktorej stojí Karel, s tehlami, značkami, štartovou pozíciou,
zadaním a podmienkami splnenia (misiou).

### Odkiaľ začať

- **Z existujúceho sveta:** vyber svet v rozbaľovacom zozname **Svety**.
- **Zo súboru:** **📂** → načítaj `.karxml` súbor z disku.
- **Od nuly:** začni s aktuálnym svetom a uprav ho v Nastaveniach.

### Úprava cez „⚙ Nastavenia sveta" (6 záložiek)

| Záložka | Čo nastavíš |
|---------|-------------|
| **Popis** | Názov sveta, **zadanie** (HTML), správy pri úspechu/neúspechu |
| **Miestnosť** | Šírka × výška mriežky, **štartová pozícia a smer Karla**, jazyk programovania pre tento svet |
| **Zásoby** | Limity tehál, veľkých tehál a značiek (∞ = neobmedzené) |
| **Príkazy** | Ktoré príkazy sú pre žiaka **povolené/zakázané**, povoliť/zakázať vlastné príkazy, a **zakázať grafické / príkazové ovládanie** |
| **Pohľad** | Uzamknutie kamery a uložený uhol pohľadu |
| **Misia** | Podmienky úspechu/neúspechu + „pri neúspechu resetovať svet" |

> **Záložka Príkazy — logika zaškrtnutia:** *zaškrtnuté = príkaz je pre žiaka
> viditeľný a povolený*. Odškrtnutím príkaz skryješ/zakážeš. Takisto vieš úplne
> vypnúť **grafické ovládanie** (šípky a akčné tlačidlá) alebo **príkazové
> ovládanie** (textový riadok) — napr. keď chceš, aby žiak riešil len programom.

### Rozmiestnenie tehál a značiek

Geometriu sveta staviaš **ovládaním Karla** (panel „Ovládanie Karla", záložka
*Graficky*):

- Pohni Karla šípkami na požadované políčko.
- **Polož tehlu / Polož veľkú** — položí tehlu pred Karla.
- **Označ ★ / Odznač ★** — značka na políčku pod Karlom.
- **Zdvihni tehlu** — odoberie tehlu.

Štartovú pozíciu Karla nastavíš v **Miestnosť** (X, Y, smer). Rozmery mriežky
tiež tam.

> **Steny vnútri mriežky** sa vo webe priamo nekreslia — obvodové steny vzniknú
> automaticky. Ak potrebuješ zložitejšie bludisko so stenami, priprav `.karxml`
> súbor (alebo vyjdi z existujúceho sveta so stenami) a načítaj ho cez **📂**.

### Misia (podmienky splnenia)

V záložke **Misia** pridávaš podmienky. Každá má:

- **Typ:** poloha Karla, stav políčka, značka pod Karlom, tehla/stena pred
  Karlom, alebo *snímka* celej miestnosti.
- **Výsledok:** *úspech* alebo *neúspech*.
- **Kedy:** *priebežne* (po každom kroku) alebo *na konci* programu.
- **Operátor a negácia:** kombinovanie viacerých podmienok (A/ALEBO, NIE).

Príklad (svet „prejdi murik"): *neúspech priebežne, ak výška Karla ≠ 1*
(spadol z muriku) **a** *úspech na konci, ak je Karel na značke* (prešiel celý
okruh až na koniec).

Voľba **„Pri neúspechu resetovať svet"** vráti Karla na štart po každom
neúspechu — funguje pri programe aj pri ručnom kroku.

---

## 4. Uloženie sveta

Sú dva spôsoby — líšia sa tým, kam svet uložia:

| Akcia | Tlačidlo | Kam uloží | Komu treba |
|-------|----------|-----------|-----------|
| **Uložiť do súboru** | 💾 | Stiahne `.karxml` na tvoj disk (záloha, prenos) | komukoľvek |
| **Publikovať** | 📤 | Na **server** — objaví sa v zozname **Svety** pre všetkých | adminovi |
| **Zmazať** | 🗑 | Odstráni publikovaný svet zo servera | adminovi |

Pri publikovaní zadáš **meno (id)**. Rovnaké meno = prepíše existujúci svet
(takto upravuješ už zdieľaný svet).

> **Trvalosť publikovaných svetov:** publikované svety žijú na dátovom úložisku
> servera (Docker volume) a prežijú reštart. Ak potrebuješ, aby boli natrvalo
> súčasťou projektu (a prežili aj kompletnú prestavbu / nasadenie na čistý
> server), treba ich uložiť do zdrojového kódu — o to požiadaj správcu projektu
> (existuje na to skript `scripts/sync_worlds.ps1`).

---

## 5. Zdieľanie so žiakmi

Celé zdieľanie je v **jednom okne** pre aktuálny svet: tlačidlo **👥 Zdieľaj**.

### Ako zadať úlohu

1. Priprav/otvor svet, ktorý chceš zadať.
2. Klikni **👥 Zdieľaj**.
3. Hore nastav **🌐 Adresa pre žiakov** — IP/hostname a port, na ktorom je Karel
   pre žiakov dostupný (napr. `karel.skola.sk:8000` alebo `192.168.1.10:8000`).
   Predvolené je `localhost:8000` (funguje len na tvojom počítači!). Adresa sa
   zapamätá.
4. Napíš **meno žiaka** → **➕ Pridať žiaka**. Vznikne mu vlastný trvalý link.
5. Pri každom žiakovi klikni **📋** (kopíruj link) a pošli mu ho (mail, chat,
   nástenka…).

Okno je naviazané na svet — keď ho **otvoríš nabudúce, uvidíš tých istých
žiakov** aj ich pokrok. Keď svet upravíš a znova otvoríš zdieľanie, žiaci
dostanú **aktualizovanú** verziu.

### Čo vidí žiak

Žiak otvorí svoj link → dostane sa do **žiackeho režimu**: vidí zadanie, scénu,
editor a ovládanie. Jeho program sa **automaticky ukladá** — môže zavrieť
prehliadač a nabudúce pokračovať tam, kde skončil.

### Kontrola pokroku

V tom istom okne (**👥 Zdieľaj**) pri každom žiakovi vidíš stav:

| Stav | Význam |
|------|--------|
| **— nezačal** | Žiak ešte nič nenapísal ani nevyriešil |
| **✏️ + dátum** | Žiak na úlohe pracoval (má rozpísaný program) |
| **✅ vyriešil + dátum** | Žiak splnil misiu (aj keď ju vyriešil graficky, bez programu) |

- **👁** — zobrazí žiakov program. V náhľade môžeš kliknúť **↧ Načítať do
  editora** a jeho program si u seba spustiť/skontrolovať.
- **🗑** — zmaže žiaka aj jeho prácu (po potvrdení).

### Typický priebeh hodiny

1. (Admin) priprav a **publikuj** svet.
2. **👥 Zdieľaj** → nastav verejnú adresu → pridaj žiakov → rozošli linky.
3. Počas hodiny sleduj v okne zdieľania, kto **✏️ pracuje** a kto už **✅ vyriešil**.
4. Komu to nejde, otvor **👁** jeho program, **↧ načítaj** ho k sebe a poraď.

---

## 6. Časté otázky

**Žiakovi link nefunguje z domu / z iného počítača.**
Skontroluj **🌐 Adresu pre žiakov** v okne zdieľania — nesmie byť `localhost`,
ale verejná IP/hostname servera, a port musí byť dostupný zvonku.

**Stratím svoje úpravy svetov po prestavbe?**
Publikované svety prežijú reštart. Pre úplnú istotu (a verziovanie) ich nechaj
uložiť do zdrojového kódu projektu — pozri sekciu 4, „Trvalosť".

**Zabudol som admin heslo / zablokoval som sa.**
Blokovanie trvá 30 minút. Heslo nastavuje správca cez `KarelAdminPWD` (sekcia 2).

**Môže žiak vidieť riešenie alebo nastavenia?**
Nie. Žiacky režim skrýva nastavenia sveta aj zdieľanie. Vidí len zadanie a
prostredie na riešenie.
