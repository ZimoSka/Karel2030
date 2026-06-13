# Karel 2030 — Teacher's Guide

> 🇸🇰 [Slovenská verzia](sk/navod-pre-ucitelov.md)

---

## What is Karel 2030?

Karel 2030 is a web-based educational programming environment. Students control a robot (Karel) on a 3D grid by writing programs. The teacher prepares **worlds** — grid layouts with tasks and success conditions — and shares them with students via links. Everything runs in the browser.

**No installation is needed for students.** They open a link and start programming.

---

## Teacher role

When you open the main URL (`http://…:8000/`), you are in **teacher mode** by default:

- Create, edit, and save worlds.
- Run programs and control Karel directly.
- Share worlds with students and monitor their progress.
- Publishing or deleting shared worlds requires admin access (see [Admin Guide](admin-guide.md)).

---

## Interface overview

| Area | What it does |
|------|-------------|
| **Toolbar** (top) | Switch worlds, run/stop/reset, open world settings, access sharing |
| **3D scene** (center-left) | Displays the current world; rotate/pan/zoom with mouse |
| **Navigator** (top-right) | Shows inventory (bricks, marks) and steps/turns budget if set |
| **Control panel** (bottom-right) | Control Karel manually (d-pad or typed commands) |
| **Editor** (bottom-center) | Write and run Karel programs |
| **Command list** (bottom-right) | Available commands and conditions; click to insert |

---

## Creating a world

1. Open World Settings via the **⚙ Nastavenia** button.
2. The dialog has six tabs: **Popis, Miestnosť, Zásoby, Príkazy, Pohľad, Misia**.
3. Configure the world and click **Použiť a zavrieť**.

### Tab: Popis (Description)
- **Title** — displayed above the 3D view.
- **Intro HTML** — task description shown to the student when they open the world (supports `<b>`, `<ul>`, `<img>`, etc.).
- **Success / Failure HTML** — message shown at mission end.

### Tab: Miestnosť (Room)
- Set grid **width** and **height**.
- Set Karel's **starting position** (x, y) and facing direction.
- Place bricks, big bricks (kvaders), marks, and walls directly in the 3D view.

> **Tip:** Move Karel to the desired start position using the control panel, then open World Settings — it shows the current position.

### Tab: Zásoby (Inventory)
- **Brick limit** — how many small bricks Karel has. `-1` = unlimited.
- **Big brick limit** — how many kvaders Karel has. `-1` = unlimited.
- **Mark limit** — how many marks Karel has. `-1` = unlimited.
- **Max steps / Max turns** — movement budget. When exhausted → program stops, dialog appears.
- **Max climb** — maximum brick-height difference Karel can step up in one move (default 1).
- **Max drop** — maximum height Karel can step down. `-1` = unlimited.
- **Max brick height** — maximum stack height Karel can place bricks on.

### Tab: Príkazy (Commands)
- Choose the **programming language** (Slovak, English, German, French, Italian, Spanish, English/Pattis).
- Check/uncheck individual commands to **disable** them for this world.
- **Disable procedures** — prevents students from defining their own commands.
- **Disable graphic control** — hides the d-pad; forces program-only mode.
- **Disable command-line** — hides the typed-command input.

### Tab: Pohľad (Camera)
- Adjust and **lock** the camera angle for this world. When locked, students cannot rotate the view.

### Tab: Misia (Mission)
- Add **goal conditions** — rules that trigger success or failure.
- Each condition has: type, when to evaluate (on each step / on finish), operator (AND/OR), negation flag, and result (success/failure).

**Goal condition types:**

| Type | Triggers when… |
|------|---------------|
| `karel_pos` | Karel is at a specific (x, y, height) — any field can be blank for "any value" |
| `cell_state` | A specific cell has the required bricks/marks |
| `sign` | Karel is standing on a mark |
| `brick_ahead` | There is a brick in front of Karel |
| `wall_ahead` | There is a wall in front of Karel |
| `snapshot` | The entire room matches a previously captured snapshot |

> **Reset on failure:** When enabled, Karel resets automatically when a failure condition triggers.

---

## Placing objects in the world

Use the **Control panel** to move Karel, and the action buttons to place/pick bricks and marks:

- **Drop brick** — place a small brick on the tile in front of Karel.
- **Drop big brick (kvader)** — place a kvader (= 5 brick-heights) in front of Karel.
- **Pick brick** — pick up a small brick from the tile in front of Karel.
- **Mark** — place a mark under Karel (on Karel's current tile).
- **Clear** — remove the mark from Karel's current tile.

Walls can be placed via **World Settings → Miestnosť** or by clicking a cell edge in the 3D view.

---

## Saving a world

**Save locally (teacher's own files):**
Click **💾** in the toolbar → downloads a `.karxml` file to your computer.
To reload it later, click **📂** and choose the file.

**Publish for students (admin required):**
Admin users click **📤** to publish the current world. Published worlds appear in the Worlds dropdown for all users. See the [Admin Guide](admin-guide.md).

---

## Sharing with students

Click **👥 Zdieľaj** to open the Share dialog for the current world.

1. **Set the student address** (🌐 field) — the public IP/hostname:port where students can reach your server. Example: `192.168.1.10:8000` or `karel.school.sk`.
2. **Add a student** (➕ Pridať žiaka) — enter a name and click Add. A permanent student link is created.
3. **Copy the link** (📋 icon next to each student) and send it to them (email, chat, whiteboard…).
4. **Monitor progress** — each student shows one of three states:
   - `— nezačal` — link not yet opened
   - `✏️ pracuje` — program in progress
   - `✅ vyriešil` — mission completed
5. **View a student's program** — click 👁 to see what they wrote.
6. **Delete a student** — click 🗑 (removes their link and saved work).

> **Student links are permanent.** The same link works across sessions. Students can close the browser and continue where they left off.

---

## Pedagogical progression

The Karel language is designed so that teachers can reveal complexity gradually:

| Stage | Concept | Suggested world settings |
|-------|---------|-------------------------|
| 1 | Direct control — buttons and typed commands | Disable program editor |
| 2 | Simple sequences — `begin … end` | Limited inventory |
| 3 | Procedures — define and call custom commands | Disable recursion if needed |
| 4 | Repeat loop — `repeat N times` | Known-count problems |
| 5 | While loop — `while condition do` | Wall/brick conditions |
| 6 | If/else — `if condition then … else` | Branching worlds |
| 7 | Recursion — procedures calling themselves | Counting with bricks |

**Tip:** Disable `BACK` and `RIGHT` in early stages to focus attention on relative orientation. Use `max_steps` to motivate efficient solutions.

---

## Working with multiple worlds

The **Worlds** dropdown (toolbar) lists all published worlds. Switching worlds reloads the full state (grid, program, settings).

To prepare a new world from scratch: make edits in World Settings, save locally with **💾**, then publish with **📤** (admin).

---

## Tips for good world design

- Write the **Intro** with clear, concrete instructions. Students see it first.
- Use `max_steps` or `max_turns` to discourage brute-force solutions.
- Lock the camera for worlds where orientation matters.
- Use `snapshot` conditions when the final state of the entire room must be correct.
- Use `on_step` failure conditions (e.g., "Karel must not step on a mark") to catch mistakes immediately.
- Test your world as a student: open the student link in a private browser window.

---

## The Karel language (quick reference)

Full reference: **[language-reference.md](language-reference.md)**

```
begin                           procedure TurnRight
  forward                       begin
  left                            left
  forward                         left
end                               left
                                end

repeat 4 times                  while not wall do
  forward                         forward
  left                          end
end
                                if brick then
                                  pick
                                else
                                  forward
                                end
```

**Conditions:** `wall`, `brick`, `free`, `sign`, `true`, `false`  
**Operators:** `not`, `and`, `or` — parentheses supported  
**Comments:** `// text` or `{ text }`
