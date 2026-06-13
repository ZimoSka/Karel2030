# Karel 2030 — Návod pre žiakov

> 🇬🇧 [English version](../student-guide.md)

---

## Čo je Karel?

Karel je robot, ktorý žije v 3D svete — mriežke. Tvojou úlohou je Karela naprogramovať — napísať príkazy, ktoré mu povedia čo má robiť — aby vyriešil zadanie, ktoré ti dal tvoj učiteľ.

Nemusíš nič inštalovať. Učiteľ ti dal link, ktorý sa otvorí priamo v prehliadači.

---

## Otvorenie zadania

Otvor link, ktorý ti poslal učiteľ. Uvidíš:

1. **Popis zadania** (vyskakovacie okno na začiatku) — prečítaj ho pozorne.
2. 3D svet Karela — mriežka kde Karel stojí.
3. **Editor** dole — tu píšeš program.

---

## Rozhranie

### 3D pohľad
Zobrazuje Karela a svet. Ťahaním myšou otáčaš pohľad, kolieskom priblížiš/vzdialíš. Karel vždy hľadí jedným zo štyroch smerov (Východ, Sever, Západ, Juh).

### Navigátor (vpravo hore)
Zobrazuje koľko tehál, značiek a krokov ti zostalo (ak učiteľ nastavil limity).

### Ovládanie Karla (vpravo dole)
Umožňuje pohybovať Karelom ručne pomocou šípkových tlačidiel alebo písaním príkazov. Hodí sa na preskúmanie sveta pred písaním programu.

### Editor (dole uprostred)
Tu píšeš Karlov program. Klikni **▶ Spustiť** na spustenie.

### Zoznam príkazov (vpravo dole)
Zobrazuje dostupné príkazy v tomto svete. Klik na príkaz ho vloží do editora.

---

## Spustenie programu

1. Napíš program do editora.
2. Klikni **▶ Spustiť** (alebo Ctrl+Enter) na spustenie.
3. Klikni **⏹ Stop** na zastavenie.
4. Klikni **↺ Reset** na návrat Karela na štart.

Posuvníkom **Rýchlosť** spomaľ alebo zrýchľ vykonávanie — vidíš čo Karel robí krok po kroku.

---

## Priame ovládanie

Ak sú viditeľné šípkové tlačidlá v Ovládaní Karla, môžeš ho pohybovať ručne:

- **▲** — dopredu
- **◀** — vlavo
- **▶** — vpravo
- **▼** — dozadu (ak je povolené)
- Akčné tlačidlá: kladenie/zdvíhanie tehál, kladenie/odstraňovanie značiek

---

## Písanie programu

Každý Karlov program má hlavný blok:

```
zaciatok
  dopredu
  vlavo
  dopredu
koniec
```

### Príkazy

| Príkaz | Čo robí |
|--------|---------|
| `dopredu` | Krok dopredu |
| `dozadu` | Krok dozadu |
| `vlavo` | Otočenie o 90° doľava |
| `vpravo` | Otočenie o 90° doprava |
| `poloz` | Polož tehlu pred Karela |
| `zdvihni` | Zdvihni tehlu pred Karelom |
| `oznac` | Polož značku na políčko kde Karel stojí |
| `odznac` | Odstráni značku z Karlovho políčka |

> Učiteľ mohol niektoré príkazy zakázať pre toto zadanie.

### Opakuj (repeat)

Použi `opakuj` keď vieš koľkokrát opakovať:

```
opakuj 4 krat
  dopredu
  vlavo
koniec
```

### Kým (while)

Použi `kym` keď nevieš koľkokrát opakovať:

```
kym nie stena rob
  dopredu
koniec
```

### Ak (if)

Použi `ak` na rozhodovanie:

```
ak tehla potom
  zdvihni
inak
  dopredu
koniec
```

### Podmienky

| Podmienka | Pravdivá keď… |
|-----------|--------------|
| `stena` | Pred Karelom je stena alebo okraj |
| `tehla` | Pred Karelom je tehla |
| `volno` | Pred Karelom nič nestojí |
| `znacka` | Karel stojí na značke |

Podmienky možno kombinovať:
```
ak nie stena a nie tehla potom dopredu koniec
kym stena alebo tehla rob vlavo koniec
```

### Procedúry (vlastné príkazy)

Môžeš Karelovi naučiť nové príkazy:

```
prikaz OtocVpravo
zaciatok
  vlavo
  vlavo
  vlavo
koniec

zaciatok
  OtocVpravo
  dopredu
koniec
```

---

## Keď Karel uviazne alebo program nefunguje

- Karel **nikdy nespadne**. Ak nemôže vykonať príkaz (napr. ísť do steny), ticho ho preskočí a pokračuje.
- Použi **↺ Reset** na reštart od začiatku.
- Sleduj vykonávanie so spomalenou rýchlosťou — uvidíš čo Karel robí krok po kroku.
- Skontroluj zoznam príkazov — ukáže aké príkazy sú v tomto svete povolené.

---

## Úspech a neúspech misie

Keď splníš úlohu, zobrazí sa **správa o úspechu**. Ak porušíš pravidlo, zobrazí sa **správa o neúspechu**.

Tvoj pokrok sa automaticky ukladá. Môžeš zavrieť prehliadač a vrátiť sa neskôr — program aj pozícia Karela budú tam kde si skončil.

---

## Klávesové skratky

| Skratka | Akcia |
|---------|-------|
| `Ctrl+Enter` | Spustiť program |
| `Ctrl+S` | Uložiť program do súboru |

---

## Varianty jazyka

Učiteľ mohol nastaviť svet na iný jazyk príkazov. Fungujú rovnako — menia sa len slová:

| Slovenčina | Angličtina | Nemčina | Francúzština |
|------------|-----------|---------|--------------|
| `dopredu` | `forward` | `vorwärts` | `avance` |
| `vlavo` | `left` | `links` | `gauche` |
| `kym nie stena rob` | `while not wall do` | `solange nicht wand tue` | `tantque pas mur faire` |
| `zaciatok` / `koniec` | `begin` / `end` | `anfang` / `ende` | `début` / `fin` |

Kompletná tabuľka kľúčových slov: **[jazyk-karla.md](jazyk-karla.md)**
