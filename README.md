# Karel 2030

> 🇸🇰 [Slovenská verzia / Slovak version](README.sk.md)

A **web-based** educational programming simulator built around Karel the Robot.
Students program a robot on a grid in a browser; teachers prepare worlds and
share them with students via links. Karel 2030 is the web evolution of the
**Karel 2010** desktop app (tkinter) — both share the same `karel_core` engine.

- **Backend:** Python + FastAPI (REST + WebSocket)
- **Frontend:** browser (Three.js 3D scene + CodeMirror editor)
- **Deployment:** Docker (Linux image)

## Overview

Karel is a robot that moves around a grid world. Students program it using a
simple language, learning the fundamentals of algorithmic thinking. The teacher
prepares a world (layout + task + success conditions), shares a link, and reviews
each student's progress live.

## Running

### With Docker (recommended)

```bash
# Create .env with the admin password (leave empty to disable admin)
echo "KarelAdminPWD=yourSecretPassword" > .env

docker compose up -d
```

Then open **http://localhost:8000/**.

After code changes: `docker compose build --no-cache && docker compose up -d`

### Without Docker (local dev)

```bash
pip install fastapi "uvicorn[standard]" pillow numpy
mkdir -p data/worlds
python -m uvicorn server.app:app --reload --port 8000
```

See **[docs/admin-guide.md](docs/admin-guide.md)** for full details: admin password, data persistence, offline vendor JS, Docker volume backup.

> The original **desktop** app still lives in this repo and runs standalone:
> `python karel2010.py`. The web version is the actively developed one.

## Roles

| Role | Access | Can do |
|------|--------|--------|
| **Teacher** (default) | main URL `/` | Create/edit worlds, run programs, share with students, review progress |
| **Student** | a shared link `…/s/{code}` | Sees only the task + solving environment; program autosaves |
| **Admin** | teacher + password (🔒 Admin) | Additionally publish (📤) / delete (🗑) shared worlds |

## Sharing with students (in short)

1. **👥 Share** opens one window bound to the current world.
2. Set the **🌐 student address** (public IP/hostname:port) so links work outside localhost.
3. **➕ Add student** → copy their permanent link → send it.
4. Watch each student's status: **— not started / ✏️ working / ✅ solved**, view
   their program (👁), or remove them (🗑).

Full instructions: **[docs/teacher-guide.md](docs/teacher-guide.md)** (EN) ·
**[docs/sk/navod-pre-ucitelov.md](docs/sk/navod-pre-ucitelov.md)** (SK).

## The Karel language

The teacher sets the programming language per world; the interpreter accepts all
keyword variants simultaneously.

```
zaciatok          ← Slovak     |  begin          ← English
  opakuj 4 krat  ← Slovak      |    repeat 4 times
    dopredu                     |      forward
    vlavo                       |      left
  koniec                        |    end
koniec                          |  end
```

**Supported keyword languages:** Slovak (`sk`) · English (`en`) · German (`de`) ·
French (`fr`) · Italian (`it`) · Spanish (`es`) · English/Pattis (`en_pattis`).
GUI languages: the six above (Pattis is keywords-only). Both dropdowns
auto-populate from the language files present — adding a language needs only the
corresponding files. See **[docs/language-reference.md](docs/language-reference.md)**
for the full keyword table.

## World file format (.karxml)

Worlds are stored as `.karxml` (XML): grid size, Karel position, bricks, big
bricks, marks, walls, description/intro HTML, settings (limits, disabled commands,
camera, programming language) and the mission (goal conditions). Full
specification: **[docs/karxml-format.md](docs/karxml-format.md)**.

Built-in worlds live in `worlds/`; worlds published from the app are stored on the
server's data volume (`data/worlds/`). To capture in-app edits back into the repo,
use `scripts/sync_worlds.ps1` (see [CLAUDE.md](CLAUDE.md)).

## Features

- **3D view** (Three.js) with mouse rotate/pan/zoom
- **Program editor** with syntax highlighting and a command filter
- **Direct control** of Karel via buttons or a typed-command line
- **Full interpreter** (procedures, loops, conditionals with `not`/`and`/`or` +
  parentheses; infinite-loop and recursion guards)
- **World settings editor** — restrict commands, disable graphic/command control,
  limit supplies, lock camera, set per-world language
- **Mission system** — goal conditions, success/failure, reset-on-failure
- **Student sharing** — per-student links, autosaved programs, progress &
  completion tracking
- **Admin mode** — password-gated publishing with brute-force lockout

## Documentation

### English

| Document | Audience | Description |
|----------|----------|-------------|
| [docs/teacher-guide.md](docs/teacher-guide.md) | Teachers | World design, World Settings, sharing with students, pedagogy |
| [docs/student-guide.md](docs/student-guide.md) | Students | Interface walkthrough, language quick reference |
| [docs/admin-guide.md](docs/admin-guide.md) | Admins / IT | Docker setup, admin password, publishing worlds, local dev |
| [docs/language-reference.md](docs/language-reference.md) | Everyone | Complete language reference — all commands, all languages, examples |
| [docs/karxml-format.md](docs/karxml-format.md) | World authors | `.karxml` file format specification |
| [docs/architecture.md](docs/architecture.md) | Developers | Code architecture, data model, renderer |
| [docs/api.md](docs/api.md) | Developers | REST + WebSocket API contract |
| [CHANGELOG.md](CHANGELOG.md) | Everyone | Version history (web) |

### Slovenčina

| Dokument | Komu | Popis |
|----------|------|-------|
| [docs/sk/navod-pre-ucitelov.md](docs/sk/navod-pre-ucitelov.md) | Učitelia | Tvorba svetov, Nastavenia sveta, zdieľanie so žiakmi, pedagogika |
| [docs/sk/navod-pre-ziakov.md](docs/sk/navod-pre-ziakov.md) | Žiaci | Popis rozhrania, rýchla referencia jazyka |
| [docs/sk/navod-admin.md](docs/sk/navod-admin.md) | Admini / IT | Docker, admin heslo, publikovanie svetov, lokálny vývoj |
| [docs/sk/jazyk-karla.md](docs/sk/jazyk-karla.md) | Všetci | Kompletná referencia jazyka — všetky príkazy, všetky jazyky, príklady |

## Background

Karel 2030 grows out of **Karel 2010**, a Python port of the educational
environment designed as a master's project at the Faculty of Mathematics, Physics
and Informatics, Comenius University Bratislava (Mgr. Michal Zeman, 2004). The
Karel robot concept originated with Richard Pattis (*Karel the Robot*, 1981) and
was adapted for Slovak schools in the late 1980s by Marián Vittek, Andrej Blaho
and colleagues.

## Author

Original: Mgr. Zimo, 2005 · Web version: 2026
https://github.com/ZimoSka/Karel2030
