# Windows guest recipes (`prlctl` & `pdfm-mcp`)

## 1. Execution identity and quoting

- **Interactive session vs Session 0:**
  - `prlctl exec "$VM" --current-user ...` (or default MCP `parallels_vm_exec`) runs inside the logged-in user's desktop session. Always use `--current-user` when opening visible windows or capturing the screen.
  - Plain `prlctl exec "$VM" ...` (or MCP `elevated=true`) runs in Session 0 (`SYSTEM`). Nothing started there is visible on desktop, and scheduled tasks created as `SYSTEM` may return `ERROR: Access is denied` when queried by `--current-user`.
- **Do not pass nested quotes through inline `-Command '...'`:** `prlctl exec` strips inner double quotes (turning `"Ethernet"` into bareword `Ethernet`).
- **Do not double-base64 large scripts inside `-EncodedCommand`:** Embedding a base64 payload inside a UTF-16LE base64 launcher expands size ~3.55x and silently exceeds Parallels `PrlVmGuest_RunProgram` limits.

## 2. Single-call `.ps1` streaming + clean visible terminal capture

Stream arbitrarily large `.ps1` scripts over stdin into a tiny ~244-char `-EncodedCommand` writer, launch PowerShell visibly with `-WindowStyle Hidden` on the outer caller (so `prl_tools_service.exe` does not flash a second window), then capture with `scripts/vm_capture.py` (which invokes `scripts/win_capture.py` using DPI-aware in-guest GDI `CopyFromScreen`):

```bash
W_ENC=$(python3 -c 'import base64; print(base64.b64encode("[IO.File]::WriteAllText((Join-Path $env:USERPROFILE \"run_win.ps1\"), [Console]::In.ReadToEnd())".encode("utf-16le")).decode())')
cat << 'PS1' | perl -e 'alarm 15; exec @ARGV' prlctl exec "$VM" --current-user powershell -NoProfile -WindowStyle Hidden -EncodedCommand "$W_ENC"
Clear-Host
Write-Output "PS C:\> hostname"
hostname
Write-Output "PS C:\> whoami"
whoami
PS1

L_ENC=$(python3 -c 'import base64; print(base64.b64encode("Remove-Item -Path \"HKCU:\\Console\\%SystemRoot%_System32_WindowsPowerShell_v1.0_powershell.exe\" -Force -ErrorAction SilentlyContinue; Start-Process powershell -ArgumentList \"-NoLogo\",\"-NoExit\",\"-ExecutionPolicy\",\"Bypass\",\"-File\",(Join-Path $env:USERPROFILE \"run_win.ps1\")".encode("utf-16le")).decode())')
perl -e 'alarm 15; exec @ARGV' prlctl exec "$VM" --current-user powershell -NoProfile -WindowStyle Hidden -EncodedCommand "$L_ENC"
sleep 3 && python3 scripts/vm_capture.py "$VM" tmp/raw_win.png tmp/win.png
prlctl exec "$VM" cmd /c "taskkill /IM powershell.exe /F 2>nul & exit /b 0"
```

## 3. Windows capture and admin pitfalls

- **Use `scripts/win_capture.py` / `scripts/vm_capture.py` for saved PNGs:** On Apple Silicon Macs, `prlctl capture` on an unfocused or idle-dimmed Windows VM frequently returns all-black frames or partial black bottom scanlines from Metal/DWM compositing. In-guest `CopyFromScreen` captures crisp HiDPI output regardless of host window focus.
- **Close windows cleanly without killing yourself:** Avoid unfiltered `Stop-Process -Name powershell`; run `prlctl exec "$VM" cmd /c "taskkill /IM powershell.exe /F 2>nul & exit /b 0"` (without `--current-user` so elevated PowerShell windows terminate cleanly without `Access is denied`).
- **Keep native command ordering intact:** Piping native executables (`ping`, `nslookup`) into `Select-String` alongside PowerShell cmdlets can reorder console output due to stream buffering; use bounded native calls (`ping -n 1 -w 1500`) directly and pass `-ErrorAction SilentlyContinue` to `Get-DnsClientCache` (which throws an error after `ipconfig /flushdns` when the cache is empty).
- **Elevation:** Modifying `C:\Windows\System32\drivers\etc\hosts`, IP settings, or firewall rules requires Administrator privileges (Session 0 `prlctl exec` without `--current-user` runs as `SYSTEM`; for desktop UAC prompts, use `parallels_vm_send_key` or scheduled tasks with `/RL HIGHEST` and matching `/RU`).
