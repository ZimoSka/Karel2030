# Karel 2030 — Language Reference

> 🇸🇰 [Slovenská verzia](sk/jazyk-karla.md)

This document covers the Karel programming language — its syntax, all commands, all keyword variants in all supported languages, and example programs.

**How it works:** The interpreter accepts *all* keyword variants from *all* languages simultaneously. A student can mix `forward`, `dopredu`, `adelante` in the same program and Karel will understand all of them. The teacher selects the *primary* language per world (World Settings → Commands) — this determines which words appear on the buttons and in code templates.

---

## Supported languages

| Code | Language | Sample keywords |
|------|----------|----------------|
| `sk` | Slovak / Slovenčina | `dopredu`, `vlavo`, `opakuj` |
| `en` | English | `forward`, `left`, `repeat` |
| `de` | German / Deutsch | `vorwärts`, `links`, `wiederhole` |
| `fr` | French / Français | `avance`, `gauche`, `répète` |
| `it` | Italian / Italiano | `avanza`, `sinistra`, `ripeti` |
| `es` | Spanish / Español | `adelante`, `izquierda`, `repite` |
| `en_pattis` | English (Pattis 1981) | `move`, `turnleft`, `iterate` |

---

## Program structure

Every Karel program that runs autonomously must have a main block:

```
begin
  forward
  forward
  left
end
```

Custom commands (procedures) are defined before the main block:

```
procedure Side
begin
  repeat 3 times forward end
  left
end

begin
  repeat 4 times Side end
end
```

---

## Commands

### Movement

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| FORWARD | `dopredu` | `forward` | `vorwärts` | `avance` | `avanza` | `adelante` | `move` |
| BACK | `dozadu` | `back` | `zurück` | `recule` | `arretra` | `atras` | *(disabled)* |
| LEFT | `vlavo` | `left` | `links` | `gauche` | `sinistra` | `izquierda` | `turnleft` |
| RIGHT | `vpravo` | `right` | `rechts` | `droite` | `destra` | `derecha` | *(disabled)* |

Notable aliases: `move`, `moveforward` (EN); `vorwaerts` (DE); `avancer` (FR); `avanza`, `avanzar` (ES); `turnleft`, `turnright` (EN); `dolava`, `doľava` (SK)

---

### Bricks — placed and picked up **in front of** Karel

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| DROP | `poloz` | `drop` | `lege` | `pose` | `posa` | `pon` | *(disabled)* |
| PICK | `zdvihni` | `pick` | `hebe` | `prends` | `prendi` | `toma` | *(disabled)* |
| DROP_BIG | `kvader` | `drop_big` | `quader` | `bloc` | `blocco` | `bloque` | *(disabled)* |

Aliases: `polož`, `zodvihni` (SK); `block`, `dropb` (EN); `lege_quader` (DE); `pose_bloc` (FR); `posa_blocco` (IT); `pon_bloque` (ES)

**Small bricks** (`drop` / `poloz`):
- Placed and picked up in front of Karel, not on Karel's tile.
- Multiple bricks stack on top of each other.
- Karel can climb at most 1 brick higher per step (configurable).
- Rendered in **green**.

**Kvader / block** (`drop_big` / `kvader`):
- Equivalent in height to **5 small bricks**.
- Maximum **one kvader per tile**.
- Small bricks on the same tile stack on top of the kvader.
- `wall` condition returns **true** when a kvader is directly ahead.
- Karel **cannot climb** over a kvader (too tall).
- Picking up a kvader is **GUI-only** — not available in Karel programs.
- Rendered in **brown**.

---

### Marks — placed and picked up **under** Karel (Karel's current tile)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| MARK | `oznac` | `mark` | `markiere` | `marque` | `marca` | `marca` | `putbeeper` |
| CLEAR | `odznac` | `clear` | `lösche` | `efface` | `cancella` | `borra` | `pickbeeper` |

Aliases: `označ`, `odznač`, `čisti` (SK); `unmark` (EN); `loesche` (DE); `marcar`, `borrar` (ES)

> **Pattis note:** `putbeeper` and `pickbeeper` place/remove a mark on Karel's current tile — matching the original Pattis semantics where Karel interacts with "beepers" at the current corner.

---

### Speed

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| SLOWLY | `pomaly` | `slowly` | `langsam` | `lentement` | `lentamente` | `despacio` | *(disabled)* |
| QUICKLY | `rychlo` | `quickly` | `schnell` | `vite` | `presto` | `rapido` | *(disabled)* |

Aliases: `rýchlo`, `spomal`, `pridaj` (SK); `slow`, `quick` (EN); `lento`, `rápido` (ES)

---

## Conditions

Used inside `while` and `if`. Atomic conditions can be negated with `not` and combined with `and` / `or` and parentheses `( )`.

| Token | SK | EN | DE | FR | IT | ES | Pattis | True when… |
|-------|----|----|----|----|----|----|--------|-----------|
| WALL | `stena` | `wall` | `wand` | `mur` | `muro` | `pared` | `front_is_blocked` | Wall, border, or kvader in front of Karel |
| BRICK | `tehla` | `brick` | `stein` | `brique` | `mattone` | `ladrillo` | *(disabled)* | At least one brick in front |
| FREE | `volno` | `free` | `frei` | `libre` | `libero` | `libre` | `front_is_clear` | No brick in front |
| SIGN | `znacka` | `sign` | `markierung` | `marqueur` | `segno` | `senal` | `next_to_a_beeper` | Mark on Karel's current tile |
| TRUE | `pravda` | `true` | `wahr` | `vrai` | `vero` | `verdadero` | `true` | Always true |
| FALSE | `nepravda` | `false` | `falsch` | `faux` | `falso` | `falso` | `false` | Always false |

> **Note:** `free` and `wall` are **not** exact opposites at the grid border — `free` ignores the border while `wall` detects it. To walk up to a wall, use `while not wall`, not `while free`.

### Logical connectives

| Token | SK | EN | DE | FR | IT | ES |
|-------|----|----|----|----|----|----|
| NOT | `nie` | `not` | `nicht` | `pas` | `non` | `no` |
| AND | `a` (`aj`) | `and` | `und` | `et` | `e` | `y` |
| OR | `alebo` | `or` | `oder` | `ou` | `o` | `o` |

**Precedence:** `NOT` > `AND` > `OR`. Use parentheses `( )` to override.

```
if  wall or sign  then  left  end
while  not wall and not brick  do  forward  end
if  (wall or brick) and not sign  then  back  end
```

---

## Control structures

### Program block

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| BEGIN | `zaciatok` | `begin` | `anfang` | `début` | `inizio` | `inicio` | `begin` |
| END | `koniec` | `end` | `ende` | `fin` | `fine` | `fin` | `end` |

Aliases: `začiatok` (SK); `debut` (FR)

---

### Procedure definition

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| PROCEDURE | `prikaz` | `procedure` | `prozedur` | `procedure` | `procedura` | `instruccion` | `define` |

Aliases: `príkaz` (SK); `instrucción`, `procedimiento` (ES); `define_new_instruction` (Pattis)

```
procedure Name
begin
  ...
end
```

- Procedures can call each other and call themselves (recursion).
- Maximum recursion depth: **1000 levels**.
- No variables exist in the language — recursion depth and brick stacks serve as "memory".

---

### Repeat loop

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| REPEAT | `opakuj` | `repeat` | `wiederhole` | `répète` | `ripeti` | `repite` | `iterate` |
| TIMES | `krat` | `times` | `mal` | `fois` | `volte` | `veces` | `times` |

Aliases: `krát` (SK); `repete` (FR); `repetir` (ES); `repeat` (Pattis alias)

```
repeat 5 times
  forward
end
```

`N` must be a literal integer.

---

### While loop

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| WHILE | `kym` | `while` | `solange` | `tantque` | `mentre` | `mientras` | `while` |
| DO | `rob` | `do` | `tue` | `faire` | `fai` | `haz` | `do` |

Aliases: `kým` (SK); `hacer` (ES)

```
while not wall do
  forward
end
```

The condition may be a logical expression: `while not wall and not brick do …`

---

### If statement

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| IF | `ak` | `if` | `wenn` | `si` | `se` | `si` | `if` |
| THEN | `potom` | `then` | `dann` | `alors` | `allora` | `entonces` | `then` |
| ELSE | `inak` | `else` | `sonst` | `sinon` | `altrimenti` | `sino` | `else` |

Aliases: `tak` (SK); `si_no` (ES)

```
if brick then
  pick
else
  forward
end
```

The `else` branch is optional.

---

## Command behavior at obstacles

Karel **never crashes**. If a command cannot be executed, it is silently skipped:

| Situation | Behavior |
|-----------|----------|
| `forward` / `back` into a wall, border, or kvader | Karel stays, program continues |
| `forward` / `back` onto a tile too high to climb | Karel stays, program continues |
| `drop` with no bricks in inventory | Skipped |
| `drop_big` with no kvaders or tile already has one | Skipped |
| `pick` with no brick in front | Skipped |
| `mark` with no marks in inventory | Skipped |

---

## English (Pattis) mode

The Pattis variant reproduces Richard Pattis's original 1981 Karel language. It is more restricted:

**Disabled:** `BACK`, `RIGHT`, `DROP`, `DROP_BIG`, `PICK`, `BRICK`, `SLOWLY`, `QUICKLY`

| Concept | Pattis keyword | Standard EN equivalent |
|---------|---------------|----------------------|
| Move forward | `move` | `forward` |
| Turn left | `turnleft` | `left` |
| Place mark | `putbeeper` | `mark` |
| Remove mark | `pickbeeper` | `clear` |
| Wall ahead? | `front_is_blocked` | `wall` |
| Path clear? | `front_is_clear` | `free` |
| Mark at tile? | `next_to_a_beeper` | `sign` |
| Repeat | `iterate N times` | `repeat N times` |
| Define procedure | `define Name` | `procedure Name` |

---

## Comments

```
// Single-line comment
# Also single-line
{ Block comment }
```

---

## Full example — same program in all languages

**Task:** Walk Karel forward until a wall, marking each tile.

### Slovak
```
zaciatok
  kym nie stena rob
    oznac
    dopredu
  koniec
  oznac
koniec
```

### English
```
begin
  while not wall do
    mark
    forward
  end
  mark
end
```

### German
```
anfang
  solange nicht wand tue
    markiere
    vorwärts
  ende
  markiere
ende
```

### French
```
début
  tantque pas mur faire
    marque
    avance
  fin
  marque
fin
```

### Italian
```
inizio
  mentre non muro fai
    marca
    avanza
  fine
  marca
fine
```

### Spanish
```
inicio
  mientras no pared haz
    marca
    adelante
  fin
  marca
fin
```

### English (Pattis)
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

## More example programs

### Walk in a square
```
procedure Side
begin
  repeat 3 times forward end
  left
end

begin
  repeat 4 times Side end
end
```

### Collect all bricks in a row
```
procedure PickAll
begin
  while brick do pick end
end

begin
  while not wall do
    PickAll
    forward
  end
end
```

### Solve a maze (right-hand rule)
```
procedure Step
begin
  if wall then left else forward end
end

begin
  repeat 80 times Step end
end
```

### Move a stack of bricks forward
```
procedure MoveStack
begin
  while brick do
    pick
    forward
    drop
    back
  end
end

begin MoveStack end
```

---

## Formal grammar

```
program      = { procedure } main_block
procedure    = PROCEDURE NAME main_block
main_block   = BEGIN { statement } END
statement    = command
             | REPEAT NUMBER TIMES { statement } END
             | WHILE condition DO { statement } END
             | IF condition THEN { statement } [ ELSE { statement } ] END
             | NAME
command      = FORWARD | BACK | LEFT | RIGHT
             | DROP | PICK | DROP_BIG
             | MARK | CLEAR
             | SLOWLY | QUICKLY
condition    = or_expr
or_expr      = and_expr { OR and_expr }
and_expr     = not_expr { AND not_expr }
not_expr     = [ NOT ] atom
atom         = WALL | BRICK | FREE | SIGN | TRUE | FALSE | '(' or_expr ')'
```

The actual keyword used for each token depends on the configured `prog_lang`. All language variants are accepted simultaneously.

---

## Pedagogical progression

| Stage | Concept | Notes |
|-------|---------|-------|
| 1 | Direct control — buttons, typed commands | Learn relative orientation |
| 2 | Simple sequences — `begin … end` | Short deterministic programs |
| 3 | Procedures — `procedure … end` | Decompose problems; teach abstraction |
| 4 | Repeat loop — `repeat N times` | When repetition count is known |
| 5 | While loop — `while condition do` | When count is unknown; use sensors |
| 6 | If/else — `if condition then … else` | Branching, decision-making |
| 7 | Recursion — procedures calling themselves | Counting with bricks as memory |

Recommended age group: grades 3–7 of primary school. Karel bridges to Logo, Pascal, and Java.

---

## Adding a new language

1. Create `lang/interpreter/xx.lng` — see format below.
2. Create `lang/xx.ini` — GUI strings (menu, toolbar, dialogs); see any existing `.ini` as a template.
3. Both dropdowns populate automatically — no code changes needed.

**`.lng` file format:**
```
# Comment
NAME       = Display Name           ← shown in dropdown
DISABLED   = BACK RIGHT             ← tokens disabled when this language is selected
FORWARD    = primary_word  alias1   ← TOKEN = primary alias1 alias2 ...
LEFT       = primary_word  alias1
BEGIN      = begin
END        = end
...
```

The first word after `=` is the primary keyword (shown on buttons). All words in all `.lng` files are merged into one global keyword map — the interpreter accepts every variant from every language simultaneously.
