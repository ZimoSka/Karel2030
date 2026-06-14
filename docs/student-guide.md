# Karel 2030 — Student Guide

> 🇸🇰 [Slovenská verzia](sk/navod-pre-ziakov.md)

---

## What is Karel?

Karel is a robot that lives in a 3D grid world. Your goal is to program Karel — write instructions that tell it what to do — so that it solves the task your teacher set for you.

You do not need to install anything. Your teacher gave you a link that opens directly in the browser.

---

## Opening your task

Open the link your teacher sent you. You will see:

1. The **task description** (pop-up at the start) — read it carefully.
2. Karel's 3D world — the grid where Karel stands.
3. The **editor** at the bottom — this is where you write your program.

---

## The interface

### 3D view
Shows Karel and the world. You can rotate the view by dragging with the mouse, zoom with the scroll wheel. Karel always faces one of four directions (East, North, West, South).

### Navigator (top-right)
Shows how many bricks, marks, and steps you have left (if your teacher set limits).

### Control panel (bottom-right)
Lets you move Karel manually using arrow buttons or by typing commands. Useful for exploring the world before writing a program.

### Editor (bottom-center)
Where you write your Karel program. Click **▶ Spustiť** to run it.

### Command list (bottom-right)
Lists the commands available in this world. Click any command to insert it into the editor.

---

## Running a program

1. Write your program in the editor.
2. Click **▶ Spustiť** (or press Ctrl+Enter) to run it.
3. Click **⏹ Stop** to stop a running program.
4. Click **↺ Reset** to put Karel back at the start.

Use the **Speed** slider to slow down or speed up the execution so you can watch what happens.

---

## Direct control

If the d-pad arrows are visible in the Control panel, you can move Karel manually:

- **▲** — move forward
- **◀** — turn left
- **▶** — turn right
- **▼** — move backward (if enabled)
- Action buttons: place/pick bricks, place/remove marks

---

## Two ways to build a program: Code or Blocks

Above the editor there are two tabs:

- **Kód (Code)** — type your program as text.
- **Blokovo (Blocks)** — build your program by snapping colored blocks together, like a puzzle.

You can switch between them any time. The blocks always **generate the text code automatically** — so when you switch from Blocks to Code, you see the same program written out.

### Using the block editor

1. Click the **Blokovo** tab.
2. On the right are block **categories** (Movement, Actions, Structures, Conditions, Procedures). Click one to open it.
3. **Drag** a block into the work area and snap it inside the `begin … end` block.
4. Blocks that fit together click into place like puzzle pieces.
5. To delete a block, drag it to the **trash can** (bottom-right) or drag it back to the categories.

The three buttons (`▁ ▄ █`) above the editor make the editor area **small, medium, or full screen** — full screen hides the 3D world so you see only the blocks.

> The words on the blocks are in the same language your teacher set for the world. The category names follow the interface language.

When you are happy with your blocks, switch to the **Kód** tab to see the generated program, or just press **▶ Spustiť** to run it.

---

## Writing a Karel program

Every Karel program has a main block:

```
begin
  forward
  left
  forward
end
```

### Commands

| Command | What it does |
|---------|-------------|
| `forward` | Move one step forward |
| `back` | Move one step backward |
| `left` | Turn 90° to the left |
| `right` | Turn 90° to the right |
| `drop` | Place a brick on the tile in front of Karel |
| `pick` | Pick up a brick from the tile in front |
| `mark` | Place a mark on the tile Karel stands on |
| `clear` | Remove the mark from Karel's tile |

> Your teacher may have disabled some of these commands for this task.

### Repeat loop

Use `repeat` when you know how many times to repeat:

```
repeat 4 times
  forward
  left
end
```

### While loop

Use `while` when you don't know how many times to repeat:

```
while not wall do
  forward
end
```

### If statement

Use `if` to make a decision:

```
if brick then
  pick
else
  forward
end
```

### Conditions

| Condition | True when… |
|-----------|-----------|
| `wall` | There is a wall (or border) in front of Karel |
| `brick` | There is a brick in front of Karel |
| `free` | There is nothing blocking Karel's path |
| `sign` | Karel is standing on a mark |

You can combine conditions:
```
if not wall and not brick then forward end
while wall or brick do left end
```

### Procedures (custom commands)

You can teach Karel new commands:

```
procedure TurnRight
begin
  left
  left
  left
end

begin
  TurnRight
  forward
end
```

---

## When Karel is stuck or the program doesn't work

- Karel **never crashes**. If it cannot execute a command (e.g., walk into a wall), it silently skips it and continues.
- Use `↺ Reset` to restart from the beginning.
- Watch the execution with the Speed slider turned down — you can see what Karel does step by step.
- Use the **👁 view** in the command list to check which commands are available in this world.

---

## Mission success and failure

When you solve a task, a **success message** appears. If you break a rule (e.g., Karel stepped on a tile it shouldn't have), a **failure message** appears.

Your progress is automatically saved. You can close the browser and come back later — your program and Karel's position will be there.

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Run program |
| `Ctrl+S` | Save program to file |

---

## Language variants

Your teacher may set the world to use a different keyword language. The commands work the same way — only the words change:

| English | Slovak | German | French |
|---------|--------|--------|--------|
| `forward` | `dopredu` | `vorwärts` | `avance` |
| `left` | `vlavo` | `links` | `gauche` |
| `while not wall do` | `kym nie stena rob` | `solange nicht wand tue` | `tantque pas mur faire` |
| `begin` / `end` | `zaciatok` / `koniec` | `anfang` / `ende` | `début` / `fin` |

See the full keyword table: **[language-reference.md](language-reference.md)**
