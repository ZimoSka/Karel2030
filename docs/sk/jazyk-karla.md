# Karel 2030 — Referencia jazyka

> 🇬🇧 [English version](../language-reference.md)

Tento dokument pokrýva programovací jazyk Karla — jeho syntax, všetky príkazy, kľúčové slová vo všetkých podporovaných jazykoch a príklady programov.

**Ako to funguje:** Interpreter akceptuje *všetky* varianty kľúčových slov zo *všetkých* jazykov súčasne. Žiak môže v jednom programe kombinovať `dopredu`, `forward`, `adelante` a Karel im porozumie. Učiteľ nastavuje *primárny* jazyk per svet (Nastavenia sveta → Príkazy) — to určuje, aké slová sa zobrazujú na tlačidlách a v šablónach kódu.

---

## Podporované jazyky

| Kód | Jazyk | Ukážkové kľúčové slová |
|-----|-------|------------------------|
| `sk` | Slovenčina | `dopredu`, `vlavo`, `opakuj` |
| `en` | English | `forward`, `left`, `repeat` |
| `de` | Deutsch / Nemčina | `vorwärts`, `links`, `wiederhole` |
| `fr` | Français / Francúzština | `avance`, `gauche`, `répète` |
| `it` | Italiano / Taliančina | `avanza`, `sinistra`, `ripeti` |
| `es` | Español / Španielčina | `adelante`, `izquierda`, `repite` |
| `en_pattis` | Angličtina (Pattis 1981) | `move`, `turnleft`, `iterate` |

---

## Štruktúra programu

Každý Karlov program má hlavný blok:

```
zaciatok
  dopredu
  dopredu
  vlavo
koniec
```

Vlastné príkazy (procedúry) sa definujú pred hlavným blokom:

```
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
```

---

## Príkazy

### Pohyb

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| FORWARD | `dopredu` | `forward` | `vorwärts` | `avance` | `avanza` | `adelante` | `move` |
| BACK | `dozadu` | `back` | `zurück` | `recule` | `arretra` | `atras` | *(zakázané)* |
| LEFT | `vlavo` | `left` | `links` | `gauche` | `sinistra` | `izquierda` | `turnleft` |
| RIGHT | `vpravo` | `right` | `rechts` | `droite` | `destra` | `derecha` | *(zakázané)* |

Aliasy: `vzad`, `vľavo`, `doľava`, `dolava` (SK); `move`, `moveforward`, `turnleft`, `turnright` (EN); `vorwaerts` (DE); `avancer` (FR); `avanza`, `avanzar` (ES)

---

### Tehly — kladú sa a zdvíhajú **pred** Karelom

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| DROP | `poloz` | `drop` | `lege` | `pose` | `posa` | `pon` | *(zakázané)* |
| PICK | `zdvihni` | `pick` | `hebe` | `prends` | `prendi` | `toma` | *(zakázané)* |
| DROP_BIG | `kvader` | `drop_big` | `quader` | `bloc` | `blocco` | `bloque` | *(zakázané)* |

Aliasy: `polož`, `zodvihni` (SK); `block`, `dropb` (EN); `lege_quader` (DE); `pose_bloc` (FR)

**Malé tehly** (`poloz` / `drop`):
- Kladú sa a zdvíhajú pred Karelom, nie na jeho políčku.
- Viac tehál sa vrství na seba.
- Karel vie vystúpiť max. o 1 tehlu vyššie v jednom kroku (nastaviteľné).
- Zobrazujú sa **zelenou** farbou.

**Kvader / block** (`kvader` / `drop_big`):
- Výška = **5 malých tehál**.
- Max. **jeden kvader na políčko**.
- Malé tehly na tom istom políčku sa vrstva na vrch kvadera.
- Podmienka `stena` vracia **pravda** keď je kvader priamo pred Karelom.
- Karel **nemôže preskočiť** kvader (príliš vysoký).
- Zdvíhanie kvadera je **len cez GUI** — nie v Karel programe.
- Zobrazuje sa **hnedou** farbou.

---

### Značky — kladú sa a odstraňujú **pod** Karelom (políčko kde stojí)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| MARK | `oznac` | `mark` | `markiere` | `marque` | `marca` | `marca` | `putbeeper` |
| CLEAR | `odznac` | `clear` | `lösche` | `efface` | `cancella` | `borra` | `pickbeeper` |

Aliasy: `označ`, `odznač`, `čisti` (SK); `unmark` (EN); `loesche` (DE); `marcar`, `borrar` (ES)

> **Poznámka Pattis:** `putbeeper` a `pickbeeper` kladú/odstraňujú značku na políčku kde Karel stojí — podľa pôvodnej Pattis sémantiky kde Karel interaguje s "bzučiakmi" na aktuálnom rohu.

---

### Rýchlosť

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| SLOWLY | `pomaly` | `slowly` | `langsam` | `lentement` | `lentamente` | `despacio` | *(zakázané)* |
| QUICKLY | `rychlo` | `quickly` | `schnell` | `vite` | `presto` | `rapido` | *(zakázané)* |

Aliasy: `rýchlo`, `spomal`, `pridaj` (SK); `slow`, `quick` (EN)

---

## Podmienky

Používajú sa vo `kym` a `ak`. Atómové podmienky možno negovať pomocou `nie` a kombinovať pomocou `a` / `alebo` a závoriek `( )`.

| Token | SK | EN | DE | FR | IT | ES | Pattis | Pravdivá keď… |
|-------|----|----|----|----|----|----|--------|--------------|
| WALL | `stena` | `wall` | `wand` | `mur` | `muro` | `pared` | `front_is_blocked` | Stena, okraj alebo kvader pred Karelom |
| BRICK | `tehla` | `brick` | `stein` | `brique` | `mattone` | `ladrillo` | *(zakázané)* | Aspoň jedna tehla pred Karelom |
| FREE | `volno` | `free` | `frei` | `libre` | `libero` | `libre` | `front_is_clear` | Žiadna tehla pred Karelom |
| SIGN | `znacka` | `sign` | `markierung` | `marqueur` | `segno` | `senal` | `next_to_a_beeper` | Značka na políčku kde Karel stojí |
| TRUE | `pravda` | `true` | `wahr` | `vrai` | `vero` | `verdadero` | `true` | Vždy pravda |
| FALSE | `nepravda` | `false` | `falsch` | `faux` | `falso` | `falso` | `false` | Vždy nepravda |

> **Pozor:** `volno` a `stena` **nie sú** presnými opakmi pri okraji mriežky — `volno` okraj ignoruje, `stena` ho deteguje. Na chôdzu k stene používaj `kym nie stena`, nie `kym volno`.

### Logické spojky

| Token | SK | EN | DE | FR | IT | ES |
|-------|----|----|----|----|----|----|
| NOT | `nie` | `not` | `nicht` | `pas` | `non` | `no` |
| AND | `a` (`aj`) | `and` | `und` | `et` | `e` | `y` |
| OR | `alebo` | `or` | `oder` | `ou` | `o` | `o` |

**Priorita:** `NIE` > `A` > `ALEBO`. Závorky `( )` menia prioritu.

```
ak stena alebo znacka potom vlavo koniec
kym nie stena a nie tehla rob dopredu koniec
ak (stena alebo tehla) a nie znacka potom dozadu koniec
```

---

## Riadiace štruktúry

### Hlavný blok programu

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| BEGIN | `zaciatok` | `begin` | `anfang` | `début` | `inizio` | `inicio` | `begin` |
| END | `koniec` | `end` | `ende` | `fin` | `fine` | `fin` | `end` |

Aliasy: `začiatok` (SK); `debut` (FR)

---

### Procedúra (vlastný príkaz)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| PROCEDURE | `prikaz` | `procedure` | `prozedur` | `procedure` | `procedura` | `instruccion` | `define` |

Aliasy: `príkaz` (SK); `instrucción`, `procedimiento` (ES); `define_new_instruction` (Pattis)

```
prikaz Nazov
zaciatok
  ...
koniec
```

- Procedúry môžu volať seba navzájom a samy seba (rekurzia).
- Maximálna hĺbka rekurzie: **1000 úrovní**.
- V jazyku neexistujú premenné — rekurzia a zásoby tehál slúžia ako "pamäť".

---

### Opakuj (repeat)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| REPEAT | `opakuj` | `repeat` | `wiederhole` | `répète` | `ripeti` | `repite` | `iterate` |
| TIMES | `krat` | `times` | `mal` | `fois` | `volte` | `veces` | `times` |

Aliasy: `krát` (SK); `repete` (FR); `repetir` (ES); `repeat` (Pattis alias)

```
opakuj 5 krat
  dopredu
koniec
```

`N` musí byť celé číslo.

---

### Kým (while)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| WHILE | `kym` | `while` | `solange` | `tantque` | `mentre` | `mientras` | `while` |
| DO | `rob` | `do` | `tue` | `faire` | `fai` | `haz` | `do` |

Aliasy: `kým` (SK); `hacer` (ES)

```
kym nie stena rob
  dopredu
koniec
```

Podmienka môže byť logický výraz: `kym nie stena a nie tehla rob …`

---

### Ak (if)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| IF | `ak` | `if` | `wenn` | `si` | `se` | `si` | `if` |
| THEN | `potom` | `then` | `dann` | `alors` | `allora` | `entonces` | `then` |
| ELSE | `inak` | `else` | `sonst` | `sinon` | `altrimenti` | `sino` | `else` |

Aliasy: `tak` (SK); `si_no` (ES)

```
ak tehla potom
  zdvihni
inak
  dopredu
koniec
```

Vetva `inak` je nepovinná.

---

## Správanie príkazov pri prekážkach

Karel **nikdy nespadne**. Ak príkaz nemôže byť vykonaný, ticho sa preskočí:

| Situácia | Správanie |
|----------|-----------|
| `dopredu` / `dozadu` do steny, okraja alebo kvadera | Karel zostane, program pokračuje |
| `dopredu` / `dozadu` na príliš vysoké políčko | Karel zostane, program pokračuje |
| `poloz` bez tehál v zásobách | Preskočí sa |
| `kvader` bez kvadera alebo políčko má kvader | Preskočí sa |
| `zdvihni` bez tehly pred Karelom | Preskočí sa |
| `oznac` bez značiek v zásobách | Preskočí sa |

---

## Mód Pattis (angličtina, 1981)

Pattis variant reprodukuje pôvodný jazyk Richarda Pattisa z roku 1981. Je obmedzenjší:

**Zakázané:** `BACK`, `RIGHT`, `DROP`, `DROP_BIG`, `PICK`, `BRICK`, `SLOWLY`, `QUICKLY`

| Koncept | Pattis | Štandardný ekvivalent |
|---------|--------|-----------------------|
| Krok dopredu | `move` | `forward` |
| Otočenie vľavo | `turnleft` | `left` |
| Polož značku | `putbeeper` | `mark` |
| Odstráň značku | `pickbeeper` | `clear` |
| Je stena pred? | `front_is_blocked` | `wall` |
| Je cesta voľná? | `front_is_clear` | `free` |
| Je značka pod? | `next_to_a_beeper` | `sign` |
| Opakuj | `iterate N times` | `repeat N times` |
| Definuj procedúru | `define Nazov` | `procedure Nazov` |

---

## Komentáre

```
// Jednoriadkový komentár
# Tiež jednoriadkový
{ Blokový komentár }
```

---

## Kompletný príklad — rovnaký program vo všetkých jazykoch

**Úloha:** Choď Karelom dopredu až k stene a na každom políčku polož značku.

### Slovenčina
```
zaciatok
  kym nie stena rob
    oznac
    dopredu
  koniec
  oznac
koniec
```

### Angličtina
```
begin
  while not wall do
    mark
    forward
  end
  mark
end
```

### Nemčina
```
anfang
  solange nicht wand tue
    markiere
    vorwärts
  ende
  markiere
ende
```

### Francúzština
```
début
  tantque pas mur faire
    marque
    avance
  fin
  marque
fin
```

### Taliančina
```
inizio
  mentre non muro fai
    marca
    avanza
  fine
  marca
fine
```

### Španielčina
```
inicio
  mientras no pared haz
    marca
    adelante
  fin
  marca
fin
```

### Angličtina (Pattis)
```
begin
  while not front_is_blocked do
    putbeeper
    move
  end
  putbeeper
end
```

---

## Ďalšie príklady programov

### Chôdza po štvorcovej dráhe
```
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
```

### Pozbieranie všetkých tehál v rade
```
prikaz ZbierVsetky
zaciatok
  kym tehla rob zdvihni koniec
koniec

zaciatok
  kym nie stena rob
    ZbierVsetky
    dopredu
  koniec
koniec
```

### Bludisko (pravidlo pravej ruky)
```
prikaz Krok
zaciatok
  ak stena potom vlavo inak dopredu koniec
koniec

zaciatok
  opakuj 80 krat Krok koniec
koniec
```

### Presunutie stohu tehál dopredu
```
prikaz PriesunutieStohu
zaciatok
  kym tehla rob
    zdvihni
    dopredu
    poloz
    dozadu
  koniec
koniec

zaciatok PriesunutieStohu koniec
```

---

## Formálna gramatika

```
program      = { procedúra } hlavný_blok
procedúra    = PRIKAZ MENO hlavný_blok
hlavný_blok  = ZACIATOK { príkaz } KONIEC
príkaz       = príkaz_pohybu
             | OPAKUJ ČÍSLO KRAT { príkaz } KONIEC
             | KYM podmienka ROB { príkaz } KONIEC
             | AK podmienka POTOM { príkaz } [ INAK { príkaz } ] KONIEC
             | MENO
podmienka    = alebo_výraz
alebo_výraz  = a_výraz { ALEBO a_výraz }
a_výraz      = nie_výraz { A nie_výraz }
nie_výraz    = [ NIE ] atom
atom         = STENA | TEHLA | VOLNO | ZNACKA | PRAVDA | NEPRAVDA | '(' alebo_výraz ')'
```

---

## Pedagogická postupnosť

| Stupeň | Koncept | Poznámky |
|--------|---------|----------|
| 1 | Priame ovládanie — tlačidlá, písané príkazy | Naučiť sa relatívnu orientáciu |
| 2 | Jednoduché sekvencie — `zaciatok … koniec` | Krátke deterministické programy |
| 3 | Procedúry — `prikaz … koniec` | Rozkladanie problémov; abstrakcia |
| 4 | Opakuj — `opakuj N krat` | Keď je počet opakovaní známy |
| 5 | Kým — `kym podmienka rob` | Keď počet nie je známy; použitie senzorov |
| 6 | Ak/inak — `ak podmienka potom … inak` | Vetvenie, rozhodovanie |
| 7 | Rekurzia — procedúra volajúca seba | Počítanie s tehlami ako pamäťou |

Odporúčaná veková skupina: 3.–7. ročník základnej školy. Karel je mostíkom k Logo, Pascalu a Jave.

---

## Pridanie nového jazyka

1. Vytvorte `lang/interpreter/xx.lng` — formát nižšie.
2. Vytvorte `lang/xx.ini` — GUI texty (menu, toolbar, dialógy); pozrite akékoľvek existujúce `.ini` ako šablónu.
3. Oba dropdowny sa automaticky doplnia — **žiadna zmena kódu nie je potrebná**.

**Formát súboru `.lng`:**
```
# Komentár
NAME       = Zobrazený názov         ← zobrazí sa v dropdowne
DISABLED   = BACK RIGHT              ← tokeny zakázané pri výbere tohto jazyka
FORWARD    = primárne_slovo  alias1  ← TOKEN = primárne alias1 alias2 ...
LEFT       = primárne_slovo  alias1
BEGIN      = zaciatok
END        = koniec
...
```

Prvé slovo za `=` je primárne kľúčové slovo (zobrazuje sa na tlačidlách). Všetky slová zo všetkých `.lng` súborov sa zlúčia do jednej globálnej mapy — interpreter akceptuje každý variant z každého jazyka súčasne.
