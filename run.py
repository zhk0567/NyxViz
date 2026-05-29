#!/usr/bin/env python3
"""
NyxViz single entry point: free ports, start Vite dev server, open browser.

Usage:
    python run.py
"""
from __future__ import annotations

import atexit
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NYX_DATA = ROOT / "Nyx"
STATS_FILE = ROOT / "public" / "stats" / "timeline.json"
FIGURES_DIR = ROOT / "docs" / "figures"
REPORT_DIR = ROOT / "docs" / "report"
NODE_MODULES = ROOT / "node_modules"

HOST = "127.0.0.1"
PORT = int(os.environ.get("NYXVIZ_PORT", "5173"))
URL = f"http://{HOST}:{PORT}/"

# Ports that may be left from previous Vite / capture runs
PORTS_TO_CLEAR = [PORT, 5173, 5174, 4173]

_vite_process: subprocess.Popen | None = None


def log(msg: str) -> None:
    print(f"[NyxViz] {msg}", flush=True)


def kill_ports(ports: list[int]) -> None:
    """Release TCP ports on Windows (netstat + taskkill)."""
    if sys.platform != "win32":
        for port in ports:
            try:
                subprocess.run(
                    ["fuser", "-k", f"{port}/tcp"],
                    cwd=ROOT,
                    capture_output=True,
                    check=False,
                )
            except FileNotFoundError:
                pass
        return

    try:
        out = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        ).stdout
    except OSError as e:
        log(f"Could not list ports: {e}")
        return

    pids: set[int] = set()
    for line in out.splitlines():
        if "LISTENING" not in line.upper():
            continue
        for port in ports:
            if re.search(rf":{port}\s", line):
                parts = line.split()
                if parts:
                    try:
                        pids.add(int(parts[-1]))
                    except ValueError:
                        pass
                break

    for pid in pids:
        if pid <= 0:
            continue
        log(f"Stopping process PID {pid} (port in use)")
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            check=False,
        )


def ensure_dependencies() -> bool:
    if not shutil.which("node") or not shutil.which("npm"):
        log("ERROR: Node.js / npm not found. Install Node 18+ first.")
        return False

    if not NODE_MODULES.is_dir():
        log("Installing npm dependencies (first run)…")
        r = subprocess.run(
            ["npm", "install"],
            cwd=ROOT,
            shell=sys.platform == "win32",
        )
        if r.returncode != 0:
            log("ERROR: npm install failed")
            return False
    return True


def ensure_data() -> bool:
    if not NYX_DATA.is_dir():
        log(f"ERROR: Missing data folder: {NYX_DATA}")
        log("Place contest files Nyx/0000.dat … 0099.dat under this directory.")
        return False

    sample = NYX_DATA / "0000.dat"
    if not sample.is_file():
        log(f"ERROR: Missing {sample}")
        return False
    return True


def ensure_stats() -> None:
    if STATS_FILE.is_file():
        return
    log("Precomputing timeline stats (first run)…")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "precompute.py")], cwd=ROOT, check=True)


def ensure_deliverables() -> None:
    """Generate report markdown and static figures if missing."""
    if not (REPORT_DIR / "task1_volume.md").is_file():
        log("Generating report sections…")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "export_report.py")],
            cwd=ROOT,
            check=True,
        )
    if not any(FIGURES_DIR.glob("*.png")):
        log("Generating static figures (slice / charts; vtk capture optional)…")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_figures.py")],
            cwd=ROOT,
            check=True,
        )


def wait_for_server(host: str, port: int, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.4)
    return False


def start_vite() -> subprocess.Popen:
    log(f"Starting dev server on {URL}")
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    proc = subprocess.Popen(
        [
            "npx",
            "vite",
            "--host",
            HOST,
            "--port",
            str(PORT),
            "--strictPort",
        ],
        cwd=ROOT,
        shell=sys.platform == "win32",
        creationflags=creationflags,
    )
    return proc


def stop_vite() -> None:
    global _vite_process
    if _vite_process is None or _vite_process.poll() is not None:
        return
    log("Shutting down dev server…")
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(_vite_process.pid)],
            capture_output=True,
            check=False,
        )
    else:
        _vite_process.terminate()
        try:
            _vite_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _vite_process.kill()
    _vite_process = None


def main() -> int:
    global _vite_process

    os.chdir(ROOT)
    log("Nyx cosmology density visualization")
    log(f"Project root: {ROOT}")

    kill_ports(PORTS_TO_CLEAR)
    time.sleep(0.5)

    if not ensure_dependencies():
        return 1
    if not ensure_data():
        return 1

    try:
        ensure_stats()
        ensure_deliverables()
    except subprocess.CalledProcessError:
        log("ERROR: precompute or figure generation failed")
        return 1

    atexit.register(stop_vite)

    if sys.platform == "win32":
        signal.signal(signal.SIGINT, lambda *_: (stop_vite(), sys.exit(0)))
        signal.signal(signal.SIGBREAK, lambda *_: (stop_vite(), sys.exit(0)))  # type: ignore[attr-defined]

    _vite_process = start_vite()

    if not wait_for_server(HOST, PORT):
        log("ERROR: Server did not become ready in time")
        stop_vite()
        return 1

    log("Opening browser…")
    webbrowser.open(URL)

    log(f"Ready — press Ctrl+C to stop. App URL: {URL}")
    try:
        return _vite_process.wait()
    except KeyboardInterrupt:
        stop_vite()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
