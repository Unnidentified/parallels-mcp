#!/usr/bin/env python3
"""Inspect Parallels Desktop CLI, pdfm-mcp binary, Pillow, and available VMs.

Usage: python3 detect_vm_env.py
"""
import json
import os
import shutil
import subprocess
import sys


def find_pdfm_mcp():
    candidates = [
        "/opt/homebrew/bin/pdfm-mcp",
        "/usr/local/bin/pdfm-mcp",
        os.path.expanduser("~/.local/bin/pdfm-mcp"),
        shutil.which("pdfm-mcp"),
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def main():
    report = {
        "python": sys.version.split()[0],
        "pillow": False,
        "prlctl": shutil.which("prlctl"),
        "pdfm_mcp": find_pdfm_mcp(),
        "vms": [],
    }
    try:
        __import__("PIL")
        report["pillow"] = True
    except Exception:
        pass

    if report["prlctl"]:
        try:
            r = subprocess.run(["prlctl", "list", "-a"], capture_output=True, text=True, timeout=15)
            report["vms"] = [line.strip() for line in r.stdout.splitlines() if "{" in line]
        except Exception as exc:
            report["prlctl_error"] = repr(exc)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
