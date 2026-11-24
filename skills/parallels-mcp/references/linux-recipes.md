# Linux guest recipes (`prlctl` & `pdfm-mcp`)

## 1. Execution fundamentals

- **Check VM power state first:** run `prlctl list -a` (or `parallels_search_vms`) before `prlctl exec` (`PRL_ERR_IO_STOPPED` means the VM is suspended).
- **Avoid full `apt-get upgrade` mid-GUI-session unless needed:** upgrading `systemd`, `dbus`, or `gnome-terminal` mid-session breaks `gnome-terminal` window spawning until reboot (`prlctl restart "$VM"`, then wait for auto-login; or fall back to `xfce4-terminal`).
- **Root vs desktop session:** `prlctl exec "$VM" ...` (or MCP `elevated=true`) runs as **root**. `prlctl exec "$VM" --current-user ...` (or default MCP `parallels_vm_exec`) runs as the active GUI user.
- **Always use `bash << 'EOF'` for multi-command probes:** Never run `prlctl exec "$VM" bash -c "cmd1; cmd2"`; Parallels argv splitting can cut at `;` and run truncated commands (for instance running bare `id` as `root` instead of `id <user>`).
- **Guard probes with Perl alarm on macOS:** macOS has no native `timeout(1)`. Wrap potentially hanging probes with `perl -e 'alarm 10; exec @ARGV' prlctl exec ...` and avoid firing overlapping `prlctl exec` calls at the same VM (`PrlJob_GetRetCode: Invalid argument`).
- **Wait after boot or reboot:** Poll until both Parallels Tools and desktop login are ready before touching GUI apps or `gsettings`:
  ```bash
  until perl -e 'alarm 5; exec @ARGV' prlctl exec "$VM" --current-user whoami >/dev/null 2>&1; do sleep 2; done
  ```

## 2. Opening a clean GUI terminal window and capturing it

1. Configure idle blanking and centered windows once per session (`USER_UID=$(prlctl exec "$VM" --current-user id -u)`):
   ```bash
   prlctl exec "$VM" --current-user env XDG_RUNTIME_DIR="/run/user/$USER_UID" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$USER_UID/bus" \
     gsettings set org.gnome.desktop.session idle-delay 0
   prlctl exec "$VM" --current-user env XDG_RUNTIME_DIR="/run/user/$USER_UID" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$USER_UID/bus" \
     gsettings set org.gnome.desktop.screensaver lock-enabled false
   prlctl exec "$VM" --current-user env XDG_RUNTIME_DIR="/run/user/$USER_UID" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$USER_UID/bus" \
     gsettings set org.gnome.mutter center-new-windows true
   ```
2. Write the script inside `$HOME` (never `/tmp`, which wipes on reboot), use `sudo` inside the script for root-only commands (`cat /etc/netplan/*.yaml`, `resolvectl flush-caches`, `resolvectl statistics`) so GNOME never opens an interactive Polkit password modal, bind slow network calls (`ping -c 1 -W 2`, `dig +time=2 +tries=1`, `curl --max-time 3`), and write a `.cap_done` sentinel before `sleep 900`:
   ```bash
   prlctl exec "$VM" bash << 'EOF'
   rm -f /home/parallels/.cap_done
   cat > /home/parallels/run_cmd.sh << 'SCRIPT'
   export PS4="$ "
   set -x
   ip -4 -o a
   ip route
   ping -c 1 -W 2 10.211.55.1
   { set +x; } 2>/dev/null
   touch /home/parallels/.cap_done
   sleep 900
   SCRIPT
   chown parallels:parallels /home/parallels/run_cmd.sh && chmod 644 /home/parallels/run_cmd.sh
   EOF
   ```
3. Launch `gnome-terminal` **without trailing `&`** (it communicates over D-Bus and returns right away; `&` overlaps `prlctl exec` calls), wait for `.cap_done`, and capture with `vm_capture.py`:
   ```bash
   prlctl exec "$VM" pkill -u parallels -f '/home/parallels/run_[c]md.sh' || true
   prlctl exec "$VM" --current-user env DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
     gnome-terminal --geometry=100x26 -- bash /home/parallels/run_cmd.sh
   for i in $(seq 1 15); do
     if perl -e 'alarm 5; exec @ARGV' prlctl exec "$VM" test -f /home/parallels/.cap_done 2>/dev/null; then break; fi
     sleep 1
   done
   sleep 1
   python3 scripts/vm_capture.py "$VM" tmp/raw_linux.png tmp/linux.png
   prlctl exec "$VM" pkill -u parallels -f '/home/parallels/run_[c]md.sh' || true
   ```
   Never kill `gnome-terminal-server` or run `pkill -f` without the `[c]` bracket trick and `-u <user>`.

## 3. Background daemons and OS-specific gotchas

- **Persistent background jobs:** `prlctl exec` kills `nohup` and `setsid` children when exiting. Launch background jobs as transient systemd units:
  ```bash
  prlctl exec "$VM" systemd-run --unit=my-worker bash -c 'exec yes >/dev/null 2>&1'
  # stop later:
  prlctl exec "$VM" systemctl stop my-worker
  ```
- **Ubuntu Netplan + `systemd-networkd` vs `NetworkManager` DNS:** Check `ls -la /etc/netplan/` because Netplan merges every `.yaml` file (a leftover `00-installer-config.yaml` with `enp0s5` or `dhcp4: true` overrides or warns). If `resolvectl status eth0` stays on DHCP DNS (`10.211.55.1`) after updating `01-netcfg.yaml`, stop conflicting renderers and clear leases inside `bash << 'EOF'` before `netplan apply`.
- **Ubuntu 24.04/26.04 SSH (`ssh.socket`):** OpenSSH uses socket activation; disabling `ssh.service` alone leaves port 22 listening. Run `systemctl disable --now ssh.socket ssh.service`.
- **Config key overrides (`/etc/security/pwquality.conf`, `/etc/login.defs`):** Edit or comment out pre-existing keys in place rather than appending duplicate lines at EOF.
