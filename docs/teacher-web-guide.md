# Karel 2030 (web) — Teacher Guide

This guide covers the **web version of Karel**: how to sign in as admin, how to
create and save your own worlds, and how to share assignments with students and
review their work.

> For pedagogy and the teaching progression (what to teach and in what order),
> see [teacher-guide.md](teacher-guide.md). This document is about **operating
> the web app**.

---

## 1. Three modes (roles)

| Role | How to get there | What it can do |
|------|------------------|----------------|
| **Teacher** (default) | Open the main address, e.g. `http://localhost:8000/` | Create/edit worlds, run programs, share with students, review progress |
| **Student** | Opens a **link** you send (`…/s/{code}`) | Sees only the task, scene, editor and controls. Their program autosaves. Cannot see world settings or sharing |
| **Admin** | Teacher + password login (**🔒 Admin** button) | Additionally: **publish** (📤) and **delete** (🗑) shared worlds on the server |

Students install nothing and create no account — a browser link is enough.

---

## 2. Admin mode (password login)

Publishing and deleting shared worlds is password-protected so that a student or
random visitor cannot change server content.

### Setting the password (one-time, technical)

The password is provided as the container environment variable
**`KarelAdminPWD`**. It is already wired in `docker-compose.yml`:

```yaml
environment:
  - KarelAdminPWD=${KarelAdminPWD:-}
```

Start with your own password:

```bash
KarelAdminPWD=yourSecret docker compose up -d
```

or create an `.env` file next to `docker-compose.yml`:

```
KarelAdminPWD=yourSecret
```

If the password is empty, admin login is **disabled** (the server returns 403).

### Logging in

1. Click **🔒 Admin** in the top bar.
2. Enter the password → **Log in**.
3. On success the button becomes **🔓 Admin** and admin tools appear
   (📤 Publish, 🗑 Delete world).
4. The session lasts ~8 hours and **survives a page refresh** (stored in a cookie).
5. Clicking **🔓 Admin** again logs you out.

### Brute-force protection

After **3 wrong attempts** admin is **locked for 30 minutes** for that device —
during the lockout even the correct password is rejected. This is intentional.

---

## 3. Creating your own world

A world is a grid where Karel stands, with bricks, marks, a start position, a
task description, and success/failure conditions (the *mission*).

### Where to start

- **From an existing world:** pick one in the **Worlds** dropdown.
- **From a file:** **📂** → load a `.karxml` file from disk.
- **From scratch:** start with the current world and edit it in Settings.

### Editing via "⚙ World settings" (6 tabs)

| Tab | What you set |
|-----|--------------|
| **Description** | World title, **task** (HTML), success/failure messages |
| **Room** | Grid width × height, **Karel's start position and direction**, the programming language for this world |
| **Supplies** | Limits for bricks, big bricks and marks (∞ = unlimited) |
| **Commands** | Which commands are **allowed/disabled** for the student, allow/disable custom procedures, and **disable graphic / command control** |
| **View** | Camera lock and saved viewing angle |
| **Mission** | Success/failure conditions + "reset world on failure" |

> **Commands tab — checkbox logic:** *checked = the command is visible and
> allowed for the student*. Unchecking hides/disables it. You can also fully
> disable **graphic control** (arrows and action buttons) or **command control**
> (the text input line) — e.g. when you want students to solve only by program.

### Placing bricks and marks

You build the world's geometry by **driving Karel** (the "Karel control" panel,
*Graphic* tab):

- Move Karel with the arrows onto the target cell.
- **Drop brick / Drop big** — places a brick in front of Karel.
- **Mark ★ / Unmark ★** — toggles a mark on the cell under Karel.
- **Pick brick** — removes a brick.

Karel's start position is set in **Room** (X, Y, direction). Grid size is there too.

> **Interior walls** cannot be drawn directly in the web UI — only the border
> walls are added automatically. For a maze with inner walls, prepare a `.karxml`
> file (or start from an existing world that has walls) and load it via **📂**.

### Mission (success/failure conditions)

In the **Mission** tab you add conditions. Each one has:

- **Type:** Karel's position, a cell's state, mark under Karel, brick/wall ahead,
  or a *snapshot* of the whole room.
- **Result:** *success* or *failure*.
- **When:** *each step* (after every move) or *at the end* of the program.
- **Operator and negation:** combine several conditions (AND/OR, NOT).

Example (the "walk the wall" world): *failure each step if Karel's height ≠ 1*
(fell off the wall) **and** *success at the end if Karel is on the mark*
(walked the whole loop to the end).

The **"Reset world on failure"** option returns Karel to the start after every
failure — it works for both programs and manual steps.

---

## 4. Saving a world

There are two ways — they differ in where the world is stored:

| Action | Button | Where it saves | Who needs it |
|--------|--------|----------------|--------------|
| **Save to file** | 💾 | Downloads a `.karxml` to your disk (backup, transfer) | anyone |
| **Publish** | 📤 | To the **server** — appears in the **Worlds** list for everyone | admin |
| **Delete** | 🗑 | Removes a published world from the server | admin |

When publishing you enter a **name (id)**. The same name overwrites the existing
world (this is how you edit an already-shared world).

> **Persistence of published worlds:** published worlds live in the server's data
> storage (a Docker volume) and survive a restart. If you need them to be a
> permanent part of the project (and survive a full rebuild / deployment to a
> fresh server), they must be saved into the source code — ask the project
> maintainer (there is a `scripts/sync_worlds.ps1` helper for this).

---

## 5. Sharing with students

All sharing for the current world is in **one window**: the **👥 Share** button.

### Assigning a task

1. Prepare/open the world you want to assign.
2. Click **👥 Share**.
3. At the top set the **🌐 Student address** — the IP/hostname and port where
   Karel is reachable for students (e.g. `karel.school.org:8000` or
   `192.168.1.10:8000`). The default `localhost:8000` only works on your own
   computer! The address is remembered.
4. Type a **student name** → **➕ Add student**. They get their own permanent link.
5. For each student click **📋** (copy link) and send it to them (mail, chat,
   class board…).

The window is bound to the world — when you **open it next time you see the same
students** and their progress. If you edit the world and reopen sharing, students
receive the **updated** version.

### What the student sees

The student opens their link → a **student-mode page**: the task, the scene, the
editor and the controls. Their program **autosaves** — they can close the browser
and continue later where they left off.

### Reviewing progress

In the same window (**👥 Share**), each student shows a status:

| Status | Meaning |
|--------|---------|
| **— not started** | The student has written/solved nothing yet |
| **✏️ + date** | The student worked on it (has a program in progress) |
| **✅ solved + date** | The student completed the mission (even if solved graphically, without a program) |

- **👁** — shows the student's program. In the preview you can click
  **↧ Load into editor** to run/check their program on your side.
- **🗑** — deletes the student and their work (after confirmation).

### A typical lesson

1. (Admin) prepare and **publish** the world.
2. **👥 Share** → set the public address → add students → hand out the links.
3. During the lesson watch the share window for who is **✏️ working** and who
   has **✅ solved** it.
4. For those who struggle, open **👁** their program, **↧ load** it on your side
   and help.

---

## 6. FAQ

**A student's link doesn't work from home / another computer.**
Check the **🌐 Student address** in the share window — it must not be `localhost`
but the server's public IP/hostname, and the port must be reachable from outside.

**Will I lose my world edits after a rebuild?**
Published worlds survive a restart. For full safety (and versioning) have them
saved into the project source — see section 4, "Persistence".

**I forgot the admin password / locked myself out.**
The lockout lasts 30 minutes. The password is set by the administrator via
`KarelAdminPWD` (section 2).

**Can a student see the solution or the settings?**
No. Student mode hides world settings and sharing. They only see the task and the
solving environment.
