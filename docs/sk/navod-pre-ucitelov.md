# Karel 2030 — Príručka pre učiteľov

> 🇬🇧 [English version](../teacher-guide.md)

---

## Čo je Karel 2030?

Karel 2030 je webové vzdelávacie programovacie prostredie. Žiaci ovládajú robota (Karela) na 3D mriežke písaním programov. Učiteľ pripravuje **svety** — rozloženie mriežky s úlohami a podmienkami úspechu — a zdieľa ich so žiakmi cez linky. Všetko beží v prehliadači.

**Žiaci nepotrebujú inštaláciu.** Otvoria link a začnú programovať.

---

## Rola učiteľa

Keď otvoríte hlavnú URL (`http://…:8000/`), ste v **učiteľskom móde** automaticky:

- Tvorba, úprava a ukladanie svetov.
- Spúšťanie programov a priame ovládanie Karela.
- Zdieľanie svetov so žiakmi a sledovanie ich pokroku.
- Na publikovanie alebo mazanie zdieľaných svetov treba admin prístup (pozri [Návod pre admina](navod-admin.md)).

---

## Prehľad rozhrania

| Oblasť | Funkcia |
|--------|---------|
| **Toolbar** (hore) | Prepínanie svetov, spustenie/zastavenie/reset, nastavenia sveta, zdieľanie |
| **3D scéna** (stred-vľavo) | Zobrazuje aktuálny svet; otáčanie/pohyb/zoom myšou |
| **Navigátor** (vpravo hore) | Zásoby (tehly, značky) a rozpočet krokov/otočení |
| **Ovládanie Karla** (vpravo dole) | Priame ovládanie (smerové tlačidlá alebo príkazový riadok) |
| **Editor** (dole uprostred) | Písanie a spúšťanie Karel programov |
| **Zoznam príkazov** (vpravo dole) | Dostupné príkazy a podmienky; klik = vloží do editora |

---

## Tvorba sveta

1. Otvorte Nastavenia sveta tlačidlom **⚙ Nastavenia**.
2. Dialóg má šesť záložiek: **Popis, Miestnosť, Zásoby, Príkazy, Pohľad, Misia**.
3. Nastavte svet a kliknite **Použiť a zavrieť**.

### Záložka: Popis
- **Názov** — zobrazuje sa nad 3D scénou.
- **Intro HTML** — popis úlohy, ktorý žiak vidí pri otvorení sveta (podporuje `<b>`, `<ul>`, `<img>`, atď.).
- **Úspech / Neúspech HTML** — správa zobrazená po skončení misie.

### Záložka: Miestnosť
- Nastavte **šírku** a **výšku** mriežky.
- Nastavte **štartovaciu pozíciu** Karela (x, y) a smer.
- Umiestnite tehly, kvadery, značky a steny priamo v 3D pohľade.

> **Tip:** Presuňte Karela na požadovanú štartovaciu pozíciu cez ovládací panel, potom otvorte Nastavenia sveta — zobrazí sa aktuálna pozícia.

### Záložka: Zásoby
- **Limit tehál** — počet malých tehál pre Karela. `-1` = neobmedzene.
- **Limit kvaderov** — počet kvaderov. `-1` = neobmedzene.
- **Limit značiek** — počet značiek. `-1` = neobmedzene.
- **Max kroky / Max otočenia** — rozpočet pohybu. Po vyčerpaní sa program zastaví a zobrazí dialóg.
- **Max výstup** — maximálna výška o ktorú Karel môže vystúpiť v jednom kroku (predvolene 1).
- **Max zoskok** — maximálna výška zostupu. `-1` = neobmedzene.
- **Max výška tehál** — maximálna výška stohu, na ktorý môže Karel klásť tehly.

### Záložka: Príkazy
- Vyberte **programovací jazyk** (slovenčina, angličtina, nemčina, francúzština, taliančina, španielčina, angličtina/Pattis).
- Zaškrtnite/odškrtnite jednotlivé príkazy na **zakázanie** pre tento svet.
- **Zakázať procedúry** — žiaci nemôžu definovať vlastné príkazy.
- **Zakázať grafické ovládanie** — skryje smerové tlačidlá; nutnosť písať program.
- **Zakázať príkazový riadok** — skryje riadok pre písaný príkaz.

### Záložka: Pohľad (Kamera)
- Nastavte a **zamknite** uhol kamery pre tento svet. Keď je zamknutá, žiaci nemôžu otáčať pohľad.

### Záložka: Misia
- Pridajte **podmienky cieľa** — pravidlá, ktoré spustia úspech alebo neúspech.
- Každá podmienka má: typ, kedy sa vyhodnocuje (po každom kroku / po skončení), operátor (AND/OR), negáciu a výsledok (úspech/neúspech).

**Typy podmienok cieľa:**

| Typ | Splnená keď… |
|-----|-------------|
| `karel_pos` | Karel je na konkrétnom (x, y, výška) — pole môže byť prázdne pre „ľubovoľné" |
| `cell_state` | Konkrétna bunka má správny počet tehál/značiek |
| `sign` | Karel stojí na značke |
| `brick_ahead` | Pred Karelom je tehla |
| `wall_ahead` | Pred Karelom je stena |
| `snapshot` | Celá miestnosť zodpovedá zachytenému snímku |

> **Reset pri neúspechu:** Keď je zapnutý, Karel sa po neúspešnej podmienke automaticky resetuje.

---

## Umiestňovanie objektov v miestnosti

Pomocou ovládacieho panelu pohybujte Karelom a akčnými tlačidlami kladzte/zdvíhajte tehly a značky:

- **Polož tehlu** — malá tehla pred Karela.
- **Polož veľkú** — kvader (= 5 výšok tehly) pred Karela.
- **Zdvihni tehlu** — zdvihni tehlu z políčka pred Karelom.
- **Označ** — značka pod Karelom (na políčku kde stojí).
- **Odznač** — odstráni značku z Karlovho políčka.

Steny umiestnite cez záložku **Miestnosť** alebo kliknutím na hranu políčka v 3D pohľade.

---

## Ukladanie sveta

**Uloženie lokálne (vlastné súbory učiteľa):**
Kliknite **💾** v toolbare → stiahne súbor `.karxml` do počítača.
Na opätovné načítanie kliknite **📂** a vyberte súbor.

**Publikovanie pre žiakov (vyžaduje admin prístup):**
Admin používatelia kliknú **📤** a publikujú aktuálny svet. Publikované svety sa objavia v dropdowne Svetov. Pozri [Návod pre admina](navod-admin.md).

---

## Zdieľanie so žiakmi

Kliknite **👥 Zdieľaj** — otvorí sa okno zdieľania pre aktuálny svet.

1. **Nastavte adresu pre žiakov** (🌐 políčko) — verejná IP/hostname:port. Príklad: `192.168.1.10:8000` alebo `karel.skola.sk`.
2. **Pridajte žiaka** (➕ Pridať žiaka) — zadajte meno a kliknite Pridať. Vytvorí sa trvalý link.
3. **Skopírujte link** (📋 ikona pri každom žiakovi) a pošlite ho žiakovi (e-mail, chat, tabuľa…).
4. **Sledujte pokrok** — každý žiak má jeden z troch stavov:
   - `— nezačal` — link ešte neotvoril
   - `✏️ pracuje` — program rozpracovaný
   - `✅ vyriešil` — misia splnená
5. **Zobrazte program žiaka** — kliknite 👁.
6. **Zmažte žiaka** — kliknite 🗑 (odstráni link aj uloženú prácu).

> **Linky žiakov sú trvalé.** Ten istý link funguje naprieč reláciami — žiaci môžu zavrieť prehliadač a pokračovať.

---

## Pedagogická postupnosť

| Stupeň | Koncept | Odporúčané nastavenia |
|--------|---------|----------------------|
| 1 | Priame ovládanie — tlačidlá a písané príkazy | Zakázať editor |
| 2 | Jednoduché sekvencie — `zaciatok … koniec` | Obmedzené zásoby |
| 3 | Procedúry — definovanie vlastných príkazov | Zakázať rekurziu ak potrebné |
| 4 | Opakuj — `opakuj N krat` | Úlohy so známym počtom |
| 5 | Kým — `kym podmienka rob` | Podmienky stena/tehla |
| 6 | Ak/inak — `ak podmienka potom … inak` | Svety s vetvením |
| 7 | Rekurzia — procedúra volajúca seba | Počítanie s tehlami |

**Tip:** V prvých stupňoch zakážte `BACK` a `RIGHT` aby sa žiaci sústredili na relatívnu orientáciu. Použite `max_steps` na motiváciu k efektívnym riešeniam.

---

## Práca s viacerými svetmi

Dropdown **Svety** (toolbar) zobrazuje všetky publikované svety. Prepnutím svetu sa načíta celý stav (mriežka, program, nastavenia).

Na prípravu nového sveta: upravte Nastavenia sveta, uložte lokálne cez **💾**, potom publikujte cez **📤** (admin).

---

## Tipy na dobrý dizajn sveta

- Pište **Intro** jasne a konkrétne — žiaci ho vidia ako prvé.
- Použite `max_steps` alebo `max_turns` na odrádzanie od hrubej sily.
- Zamknite kameru pre svety, kde záleží na orientácii.
- Použite podmienku `snapshot` keď musí byť správny celkový stav miestnosti.
- Podmienky neúspechu s `on_step` okamžite zachytia chyby.
- Otestujte svet ako žiak — otvorte žiacky link v súkromnom okne prehliadača.

---

## Jazyk Karla (rýchla referencia)

Kompletná referencia: **[jazyk-karla.md](jazyk-karla.md)**

```
zaciatok                        prikaz OtocVpravo
  dopredu                       zaciatok
  vlavo                           vlavo
  dopredu                         vlavo
koniec                            vlavo
                                koniec

opakuj 4 krat                   kym nie stena rob
  dopredu                         dopredu
  vlavo                         koniec
koniec
                                ak tehla potom
                                  zdvihni
                                inak
                                  dopredu
                                koniec
```

**Podmienky:** `stena`, `tehla`, `volno`, `znacka`, `pravda`, `nepravda`  
**Operátory:** `nie`, `a`, `alebo` — závorky podporované  
**Komentáre:** `// text` alebo `{ text }`
