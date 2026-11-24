# parallels-mcp

Universal Antigravity / T3 Code plugin bundling the **Parallels Desktop MCP server (`pdfm-mcp`)** with cross-OS (Linux & Windows) guest scripting, screenshot capture, window auto-cropping, Apple Vision OCR, and VM lifecycle workflows.

## Prerequisites

- macOS with **Parallels Desktop** (`prlctl` CLI) and **Parallels Tools** installed in guests.
- **`pdfm-mcp`** binary installed on your Mac:
  ```bash
  brew install --cask parallels/tap/pdfm-mcp
  ```
- Python 3 + `Pillow` (`pip install pillow`) for `scripts/vm_capture.py` and `scripts/crop_capture.py`.

## Contents

- `plugin.json`: Antigravity plugin manifest.
- `mcp_config.json`: Registers `pdfm-mcp` cleanly across Homebrew (`/opt/homebrew/bin/pdfm-mcp`), `/usr/local/bin/pdfm-mcp`, `~/.local/bin/pdfm-mcp`, or `PATH`.
- `skills/parallels-mcp/`:
  - `SKILL.md`: Tool selection (`pdfm-mcp` vs `prlctl`), execution rules, guest pitfalls, and capture pipeline.
  - `references/mcp-tools.md`: Complete reference for `pdfm-mcp` tools (`parallels_*`).
  - `references/linux-recipes.md`: Linux Wayland/X11 terminal scripting, `systemd-run`, Netplan/`systemd-resolved`, and `ssh.socket` recipes.
  - `references/windows-recipes.md`: Windows `--current-user` vs Session 0, stdin `.ps1` streaming over short `-EncodedCommand`, HiDPI `CopyFromScreen` captures, and UAC/taskkill notes.
  - `scripts/`:
    - `detect_vm_env.py`: Checks `prlctl`, `pdfm-mcp`, Pillow, and lists VMs.
    - `vm_capture.py`: Captures Linux & Windows VMs with black-frame/wallpaper retry validation.
    - `win_capture.py`: In-guest HiDPI GDI `CopyFromScreen` capture (no Metal/DWM partial-black scanlines).
    - `crop_capture.py`: Auto-detects foreground terminal window (ignoring dark wallpaper corners) and trims empty rows.

## Install

```bash
agy plugin install https://github.com/Unnidentified/parallels-mcp
```

Or validate locally:

```bash
agy plugin validate --strict .
```
