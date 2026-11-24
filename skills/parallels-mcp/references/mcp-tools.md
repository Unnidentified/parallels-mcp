# `pdfm-mcp` tool reference

All tools come from the bundled `pdfm-mcp` binary (`github.com/Parallels/pdfm-mcp`). Pass either the VM's UUID or exact `Name` as `vm_id` (spaces do not need extra quotes inside MCP arguments).

## Discovery and inspection

| Tool | Purpose | Key arguments |
| --- | --- | --- |
| `parallels_search_vms` | Fast compact lookup (`id`, `name`, `state`, `os`, `ip`) | `query`, `state`, `limit`, `refresh` |
| `parallels_list_vms` | Full `prlctl list -a -i` JSON (cached; large output) | `refresh` |
| `parallels_vm_info` | Full `prlctl` JSON config for one VM | `vm_id`, `refresh` |

Prefer `parallels_search_vms` over `parallels_list_vms` when locating a VM.

## Power and lifecycle

| Tool | Behavior | Key arguments |
| --- | --- | --- |
| `parallels_vm_start` | Start stopped VM or resume paused VM | `vm_id` |
| `parallels_vm_stop` | Graceful stop (Parallels Tools -> ACPI) unless `kill=true` | `vm_id`, `kill`, `drop_state` |
| `parallels_vm_restart` | Graceful shutdown + start | `vm_id` |
| `parallels_vm_reset` | Hard reset | `vm_id` |
| `parallels_vm_pause` / `resume` | Pause / resume execution | `vm_id` |
| `parallels_vm_suspend` | Suspend VM state to disk | `vm_id` |
| `parallels_vm_reset_uptime` | Reset VM uptime counter | `vm_id` |

## Guest command execution

| Tool | When to use | Limits and notes |
| --- | --- | --- |
| `parallels_vm_exec` | Quick synchronous guest command | Max `command` 4096 chars, 5 min timeout. Splits argv (no shell started; use `sh -c "..."`, `cmd /c "..."`, or `powershell -NoProfile -Command "..."`). Defaults to logged-in user; `elevated=true` runs as root/`SYSTEM`. |
| `parallels_vm_exec_start` | Builds, package installs, long tasks | `timeout_seconds` default 1800, max 14400. Max 4 concurrent jobs per VM. |
| `parallels_vm_exec_result` | Poll async job output | `stdout_offset` / `stderr_offset` (256 KB slice per call; retains up to 4 MB stdout / 1 MB stderr); `wait_ms` up to 30000. |
| `parallels_vm_exec_cancel` | Kill background `prlctl` process | `job_id` |

Important: setting `user` explicitly prompts Parallels for a terminal password unless passwordless (fails with `exit_code: 255` over non-interactive exec). Leave `user` unset (logged-in user) or use `elevated=true`.

## Screen, OCR, keyboard, and sequences

| Tool | Purpose | Notes |
| --- | --- | --- |
| `parallels_vm_capture` | Screenshot PNG in context | Downscaled to `max_dimension` (256–4096, default 1568) unless `full_resolution=true`. |
| `parallels_vm_observe` | Local Apple Vision OCR (`text`, `changes`, `find`) | Zero image payload returned; returns recognized text/lines or `[x, y]` centers for `find` (`min_confidence` 0–1, `region: [x0,y0,x1,y1]`). Multiply by `original_width/width` for native pixels. |
| `parallels_vm_type` | ASCII keystrokes (`\n`, `\t`, `\\`) | Max 4096 chars; `delay_ms` default 200 (0–5000). |
| `parallels_vm_send_key` | Single key, scancode, or modifier combo sequence | `key` / `scancode`, `event: press|release`, or `events` array. |
| `parallels_vm_sequence` | Run 1–50 steps in one call | Supports `{"tool": ..., "args": ...}`, `{"wait": {"seconds": N}}`, `{"wait": {"until": "settled"\|"changed", ...}}`, `{"gate": [...]}`, `expect`, `retry`, `validate_only`, `max_images` (0–16), `timeout_seconds` (1–900, default 120). |

## Snapshots, hardware, disks, cloning, encryption

- **Snapshots:** `parallels_vm_snapshot_list` (`tree`, `snapshot_id`), `parallels_vm_snapshot_create` (`name`, `description`), `parallels_vm_snapshot_switch` (`skip_resume`), `parallels_vm_snapshot_delete` (`children`).
- **Config & devices:** `parallels_vm_set` (cpus, memory, `high_resolution`, `shared_clipboard`, shared folders, `smart_guard`, `startup_view`, etc.), `parallels_vm_device_add`, `parallels_vm_device_set`, `parallels_vm_device_del` (requires VM stopped; disk delete preserves image by default unless `destroy_image`).
- **Disk & lifecycle:** `parallels_vm_reclaim_disk` (`estimate=true` is read-only), `parallels_vm_clone` (`linked`, `template`, `snapshot_id`), `parallels_vm_encrypt` / `parallels_vm_decrypt` / `parallels_vm_change_encryption_password`, `parallels_vm_delete` (`confirm` must match `vm_id` or exact VM name).
