---
name: parallels-mcp
description: Control, script, snapshot, inspect via OCR, and cleanly capture Parallels Desktop VMs (Linux, Windows, macOS guests) using the bundled pdfm-mcp MCP server and hardened prlctl helpers. Use whenever automating VMs on Parallels Desktop, running guest commands reliably, taking clean terminal/GUI screenshots, debugging Parallels networking/snapshots/devices, or driving GUI apps inside a VM.
---

# Parallels Desktop & `pdfm-mcp`

This skill drives Parallels Desktop VMs cleanly via the bundled **`pdfm-mcp`** MCP server and `prlctl` scripts. Load only the reference file you need:

| Need | File |
| --- | --- |
| Full `pdfm-mcp` tool catalog, limits, OCR & sequences | `references/mcp-tools.md` |
| Linux guest scripting, Wayland/X11 terminals, Netplan & services | `references/linux-recipes.md` |
| Windows guest `--current-user`, stdin `.ps1` streaming, HiDPI captures | `references/windows-recipes.md` |
| Environment check + VM capture helpers | `scripts/*.py` |

## 1. Check tooling first

1. Check if `pdfm-mcp` MCP tools (`parallels_search_vms`, `parallels_vm_exec`, `parallels_vm_capture`, `parallels_vm_observe`, etc.) are available in your toolset.
   - If they are marked **Lazy**, read their JSON schema under `<appDataDir>/mcp/.../parallels_*.json` and invoke via `call_mcp_tool`.
2. Check host binaries and VMs quickly if running shell commands:
   `python3 scripts/detect_vm_env.py`

## 2. Choose `pdfm-mcp` vs `prlctl`

| Task | Best path | Why |
| --- | --- | --- |
| Find VM name/UUID/state/IP | `parallels_search_vms` | Compact JSON; avoids `parallels_list_vms` truncation |
| Inspect full hardware/net config | `parallels_vm_info` | Structured JSON for a single VM |
| Short guest commands (<= 4096 chars, <= 5 min) | `parallels_vm_exec` | Clean argv parsing, exit code, stdout/stderr |
| Long installs/builds in guest | `parallels_vm_exec_start` + `parallels_vm_exec_result` | Async job with incremental stdout/stderr polling |
| Multi-line scripts / heredocs / large payloads | `prlctl exec "$VM" bash << 'EOF'` (Linux) or stdin `-EncodedCommand` writer (Windows) | Avoids argv splitting and 4096-char cap |
| Read screen text / find UI element coordinates | `parallels_vm_observe` | Built-in local Apple Vision OCR (`text`, `changes`, `find`) |
| Multi-step UI/wait automation | `parallels_vm_sequence` | Runs up to 50 steps with `settled`/`changed` image waits |
| Save clean cropped terminal PNG on disk | `scripts/vm_capture.py` | Handles Windows HiDPI `CopyFromScreen` + dark-wallpaper cropping + retries |
| Power, snapshots, devices, cloning, reclaim | `parallels_vm_*` tools (or `prlctl`) | Snapshot safety checks & clean argument validation |

## 3. Non-negotiable operational rules

1. **Snapshot before invasive edits.** Before changing users, permissions, firewalls, Netplan/IPs, or services in a VM you want to keep clean, inspect `parallels_vm_snapshot_list` (or `prlctl snapshot-list`) and take a snapshot if missing.
2. **Guard `prlctl exec` against hangs and collisions:**
   - macOS does not ship `timeout(1)`. Wrap uncertain/initial `prlctl exec` probes with `perl -e 'alarm 10; exec @ARGV' prlctl exec ...`.
   - Serialize `prlctl exec` calls per VM; overlapping calls fail with `PrlJob_GetRetCode: Invalid argument`.
3. **Linux command framing:**
   - Never run multi-statement commands as `prlctl exec "$VM" bash -c "cmd1; cmd2"`: Parallels can split on `;` and execute truncated commands (e.g., running bare `id` as `root` instead of `id <user>`). Always stream scripts via `prlctl exec "$VM" bash << 'EOF'`.
   - Plain `prlctl exec "$VM"` runs as **root**; `--current-user` runs as the desktop user (needed for GUI/Wayland with `DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/<uid> WAYLAND_DISPLAY=wayland-0`).
4. **Windows command & capture rules:**
   - Plain `prlctl exec` (or `elevated=true` in MCP) runs in **Session 0 (`SYSTEM`)**; `--current-user` (or default MCP `parallels_vm_exec`) lands in the interactive desktop session.
   - Never pass nested double quotes through inline `powershell -Command '...'` over `prlctl exec` (inner `"` are stripped).
   - Never double-base64 large `.ps1` payloads inside `-EncodedCommand` (~3.55x bloat hits Parallels `PrlVmGuest_RunProgram` limits). Stream the `.ps1` file over stdin into a ~244-char `-EncodedCommand` writer (see `references/windows-recipes.md`).
5. **Reliable screenshots:**
   - For direct model vision inspection or UI waiting, `parallels_vm_capture` and `parallels_vm_observe` work directly via MCP.
   - When saving cropped terminal screenshots to files on disk, always use `scripts/vm_capture.py "<VM>" raw.png out.png`. On ARM64 Macs, `prlctl capture` on unfocused Windows VMs often yields black/partial-scanline frames; `vm_capture.py` uses in-guest HiDPI `CopyFromScreen` (`win_capture.py`) on Windows and auto-detects terminal bounds ignoring dark wallpapers (`crop_capture.py --window`).
6. **Secret hygiene with `parallels_vm_observe`:** OCR runs locally via Apple Vision, but its output enters model context; do not run it while secrets or credentials are visible on screen unless intended.

## 4. Bundled scripts

- `scripts/detect_vm_env.py`: JSON capability report (`prlctl`, `pdfm-mcp`, `Pillow`, VM list).
- `scripts/vm_capture.py`: Capture + validate + auto-crop Linux/Windows terminal windows with retries.
- `scripts/win_capture.py`: In-guest Windows HiDPI `CopyFromScreen` desktop PNG dumper.
- `scripts/crop_capture.py`: Auto-detects foreground terminal window (`--window`) or trims empty rows (`--box`, `--pad`).
