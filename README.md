<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/GUI-PySide6-green?logo=qt" alt="PySide6">
  <img src="https://img.shields.io/badge/SSH-Paramiko-orange?logo=ssh" alt="SSH">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT">
</p>

<h1 align="center">🖥️ VPS Manager</h1>

<p align="center">
  <strong>A cross-platform SSH server manager with an interactive console, script store, and one-click execution — built with Python &amp; Qt.</strong>
</p>

<p align="center">
  <em>Think MobaXterm + PuTTY, minus the bloat, plus open-source DNA.</em>
</p>

---

## ✨ Features

| Feature | Status |
|---------|--------|
| ✅ **Server registry** — save SSH servers (name, IP, port, PEM key, description) | Done |
| ✅ **Interactive SSH console** — real-time shell, send commands line by line | Done |
| ✅ **Script library** — associate scripts with servers, edit inline | Done |
| ✅ **One-click remote execution** — uploads script content + runs on target | Done |
| ✅ **Persistent SQLite storage** — survives restarts | Done |
| ✅ **Thread-safe SSH** — non-blocking via `QThread` + `paramiko` | Done |
| 🔄 **SFTP integration** — drag & drop file transfer | Planned |
| 🔄 **Multiple concurrent sessions** — tabbed terminals | Planned |
| 🔄 **Command history** — searchable, replayable | Planned |
| 🔄 **Docker / VPS monitoring** — live stats dashboard | Planned |

---

## 📸 Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/vps-manager.git
cd vps-manager

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

> **Linux / macOS:** `./run_vps_manager.sh`  
> **Windows:** double-click `run_vps_manager.bat`

---

## 🧰 Usage Guide

### Add a server

1. Click **Add Server** → fill in:
   - **Name** – human-friendly label (e.g. *Production*, *Dev-VPS*)
   - **IP / Hostname** – reachable address
   - **Port** – default `22`
   - **Username** – SSH login user
   - **PEM File** – path to your private key (`.pem`)
2. Click **OK** — your server appears in the list.

### Connect & run commands

1. Select a server → click **Connect**.
2. Type commands in the input bar and press **Enter**.
3. Output streams live in the console pane.

### Scripts

1. Select a server → open the **Scripts** tab.
2. **Add Script** — pick a local `.sh` file.
3. Select the script → **Execute** — content is uploaded to `/tmp/` on the remote host and run.

The built-in script editor lets you write or tweak scripts before saving/executing.

---

## 🏗️ Architecture

```
vps-manager/
├── src/                    # Application source
│   ├── __init__.py         # Package marker + version
│   ├── __main__.py         # python -m src entry
│   ├── main.py             # CLI/desktop entry point
│   ├── app.py              # Main window (VPSManagerApp)
│   ├── database.py         # SQLite CRUD (DatabaseManager)
│   ├── ssh_worker.py       # SSH QThread (SSHWorker)
│   └── dialogs.py          # Add/Edit server dialog
├── scripts/                # Sample scripts
├── tests/                  # (future) test suite
├── main.py                 # Legacy entry → delegates to src/
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

### Design decisions

| Decision | Rationale |
|----------|-----------|
| **Single SSH worker** per session | Simplicity; multi-session support is a planned feature |
| **Script upload via heredoc** | Avoids SFTP dependency for basic use; SFTP will replace this later |
| **SQLite over flat files** | Atomic writes, schema enforcement, easy queries |
| **QThread over asyncio** | Qt integration is cleaner with signals/slots |
| **Path resolution from `__file__`** | CWD-independent — run from anywhere |

---

## 🔐 Security

- **PEM keys are never stored in the repository.**  
  The `.gitignore` explicitly excludes `*.pem`, `*.key`, and `*.p12`.
- **Connection details are stored locally** in an SQLite database.  
  Future: add optional encryption with a master password.
- **SSH host keys** are accepted automatically (`AutoAddPolicy`).  
  For production, switch to `RejectPolicy` + manual verification.
- **Script uploads** go to `/tmp/` and are cleaned up on exit.

---

## 🐳 Docker (roadmap)

```yaml
services:
  vps-manager:
    build: .
    ports:
      - "5901:5901"    # VNC (headless mode)
    volumes:
      - ./data:/data   # persistence
    environment:
      - DISPLAY=:99
```

A headless `Dockerfile` + VNC/Xvfb is planned for x86 cloud VPS deployments.

---

## 🧪 Running tests

```bash
python -m pytest tests/
```

*(Test suite is a work-in-progress.)*

---

## 🚀 Roadmap

### Phase 1 — Stabilise (current)
- [x] Refactor monolithic `main.py` into modular `src/` package
- [x] Fix fake console → real interactive SSH channel
- [x] Fix script execution (local path → upload + remote run)
- [x] Proper `.gitignore` + project-level Git repo
- [x] CWD-independent database path

### Phase 2 — Rich UX
- [ ] Multi-tab terminals (one per server)
- [ ] Command history with ↑/↓ arrows
- [ ] ANSI colour parsing in console
- [ ] Terminal emulation (QTerminalWidget / pyte)

### Phase 3 — Power features
- [ ] SFTP file browser (drag & drop)
- [ ] Docker / VPS metrics dashboard (live CPU, RAM, disk)
- [ ] SSH config (`~/.ssh/config`) parser
- [ ] Export / import server lists (JSON)

### Phase 4 — Operations
- [ ] Docker image with VNC
- [ ] OpenClaw integration (automation gateway)
- [ ] Multi-cloud inventory (OCI, AWS, Azure)
- [ ] Encrypted credential storage

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/amazing-thing`)
3. Commit your changes (`git commit -m 'feat: add amazing thing'`)
4. Push (`git push origin feat/amazing-thing`)
5. Open a Pull Request

We use [Conventional Commits](https://www.conventionalcommits.org/).

---

## 📄 License

MIT — use it, ship it, make it better.

---

<p align="center">
  <sub>Built with ❤️ for the <a href="https://openclaw.ai">OpenClaw</a> ecosystem.</sub>
</p>
