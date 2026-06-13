# Karel 2030 — Admin Guide

> 🇸🇰 [Slovenská verzia](sk/navod-admin.md)

This guide covers running the Karel 2030 server, setting the admin password, and managing published worlds.

---

## Admin mode overview

There are three roles:

| Role | Access | What they can do |
|------|--------|-----------------|
| **Teacher** | Main URL `/` | Create/edit worlds, share with students, monitor progress |
| **Student** | Shared link `/s/{token}` | Solve the task; program autosaves |
| **Admin** | Teacher + password login | Additionally: publish (📤) and delete (🗑) shared worlds |

Admin mode is unlocked by clicking **🔒 Admin** in the toolbar and entering the password. It is a **session-level** upgrade — closing the browser returns to teacher mode.

---

## Running with Docker (recommended)

Docker is the primary deployment method. The image runs on Linux and handles all dependencies.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)
- `docker compose` (included with Docker Desktop)

### Quick start

```bash
# 1. Clone the repository
git clone https://github.com/ZimoSka/Karel2030.git
cd Karel2030

# 2. Create the .env file with the admin password
echo "KarelAdminPWD=yourSecretPassword" > .env

# 3. Build and start
docker compose up -d

# 4. Open in browser
# http://localhost:8000/
```

### Stopping and restarting

```bash
docker compose down          # stop
docker compose up -d         # start again (uses existing image)
docker compose up -d --build # rebuild image (after code changes)
```

### After code changes (JS, Python, templates)

```bash
docker compose build --no-cache && docker compose up -d
```

---

## Admin password (`KarelAdminPWD`)

The admin password is set via the `KarelAdminPWD` environment variable.

**If empty or not set → admin login is disabled (everyone is teacher-only).**

### Setting the password

**Option 1 — `.env` file** (recommended):
```
# Karel2030/.env
KarelAdminPWD=yourSecretPassword
```
The `.env` file is gitignored — it will not be committed to the repository.

**Option 2 — inline with docker compose:**
```bash
KarelAdminPWD=yourSecret docker compose up -d
```

**Option 3 — export in shell:**
```bash
export KarelAdminPWD=yourSecret
docker compose up -d
```

### Security notes
- The password comparison uses `secrets.compare_digest` (timing-safe).
- After **3 failed login attempts**, the IP address is locked out for **30 minutes**.
- The lockout is based on `X-Forwarded-For` or the direct client IP.
- The admin session is stored in an **httponly cookie** (not accessible to JavaScript).
- Change the password by updating `.env` and restarting: `docker compose up -d`.

---

## Data persistence

Published worlds and student data are stored in the Docker **volume** `karel_data`, mounted at `/data` inside the container.

```yaml
# docker-compose.yml (excerpt)
volumes:
  - karel_data:/data
```

This data persists across container restarts and rebuilds. To back it up:

```bash
# Export the volume contents
docker run --rm -v karel_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/karel_data_backup.tar.gz /data
```

Built-in worlds live in `worlds/` in the repository. Worlds published from the app are stored in the `data/worlds/` directory on the volume.

To sync published worlds back to the repository: `scripts/sync_worlds.ps1`.

---

## Local development without Docker (developers only)

> This section is for contributors modifying the source code. **Teachers should always use Docker.**

You can run Karel 2030 directly without Docker for development:

```bash
# Install Python dependencies
pip install fastapi "uvicorn[standard]" pillow numpy

# Create the data directory
mkdir -p data/worlds

# Start the dev server (auto-reloads on file changes)
python -m uvicorn server.app:app --reload --port 8000
```

Then open `http://localhost:8000/`.

> **Note:** Built-in worlds are loaded from `worlds/`. Published worlds go to `data/worlds/`. Set `KarelAdminPWD` as a regular environment variable (`$env:KarelAdminPWD = "secret"` on PowerShell).

Vendor JS files (Three.js, CodeMirror) fall back to CDN when not present in `vendor/`. To download them for offline use: `python vendor/get_vendor.py`.

---

## Publishing and deleting worlds

Once logged in as admin (🔒 Admin button → enter password):

- **📤 Publish** — saves the current world to the server's `data/worlds/`. It appears immediately in the Worlds dropdown for all users.
- **🗑 Delete** — removes the currently selected published world. Cannot be undone.

Built-in worlds (from the repository's `worlds/` folder) cannot be deleted from the UI — remove them from the `worlds/` directory and rebuild the image.

---

## Custom 3D model (GLB)

Admin users can replace the default Karel model with a custom `.glb` file:

1. Click **⚙** (app settings) → Custom 3D model section.
2. Click **📁 Vybrať…** and select a `.glb` file from your computer.
3. Set the **yaw** (rotation) and **height** to fit the model.
4. The model is stored in the browser session (not on the server).

> **Important:** The custom model is loaded from your local machine each session. Keep the `.glb` file in the same location.

> **Security note:** The bundled `grogu.glb` (if present) is Disney IP — it is gitignored and must never be committed to the public repository or included in Docker images distributed via GHCR/CI.

---

## Vendor JS files (offline use)

Karel 2030 loads Three.js, CodeMirror, etc. from `vendor/` with CDN fallback. For fully offline deployments (e.g., classroom without internet):

```bash
python vendor/get_vendor.py
docker compose build --no-cache && docker compose up -d
```

---

## Environment variables summary

| Variable | Default | Description |
|----------|---------|-------------|
| `KarelAdminPWD` | *(empty)* | Admin password. Empty = admin disabled. |
| `PORT` | `8000` | Port to listen on (set in docker-compose.yml) |

---

## Updating Karel 2030

```bash
git pull
docker compose build --no-cache && docker compose up -d
```

Student data and published worlds on the volume are not affected by an update.
