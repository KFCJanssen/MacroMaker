"""
updater.py — Checks GitHub Releases for a newer Macro Maker and installs it.

How an update is installed (only possible when running as the .exe):
  1. download the new MacroMaker.exe next to the current one as *.new
  2. rename the running exe to *.old (Windows allows renaming a running exe)
  3. move *.new into place and start it with --after-update
  4. this copy quits; the new copy deletes *.old on its next start
If anything fails before step 3 the original exe is put back untouched.
"""

import json
import os
import subprocess
import sys
import urllib.request

REPO = "KFCJanssen/MacroMaker"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
ASSET_NAME = "MacroMaker.exe"


def parse_version(v: str) -> tuple:
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def can_self_update() -> bool:
    """Only the packaged .exe can replace itself; running from source can't."""
    return getattr(sys, "frozen", False) and sys.platform == "win32"


def check_latest(timeout: float = 10) -> dict:
    """Return {'version': '1.9', 'url': <exe download url or None>, 'notes': str}."""
    req = urllib.request.Request(API_LATEST, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "MacroMaker-updater"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    url = next((a["browser_download_url"] for a in data.get("assets", [])
                if a.get("name") == ASSET_NAME), None)
    return {"version": data.get("tag_name", "").lstrip("vV"),
            "url": url,
            "notes": (data.get("body") or "").strip()}


def cleanup_old_exe():
    """Delete the previous version left behind by an update (if any)."""
    if not can_self_update():
        return
    old = sys.executable + ".old"
    try:
        if os.path.exists(old):
            os.remove(old)
    except OSError:
        pass   # still locked; we'll try again next start


def download_and_install(url: str, progress=None):
    """
    Download the new exe and swap it in. Calls progress(fraction) while
    downloading. Returns the path of the new exe; the caller must then call
    launch_new() and quit. Raises on failure (with the original restored).
    """
    exe = sys.executable
    new = exe + ".new"
    old = exe + ".old"

    req = urllib.request.Request(url, headers={"User-Agent": "MacroMaker-updater"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(new, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done / total)
    if os.path.getsize(new) < 1_000_000:
        os.remove(new)
        raise RuntimeError("Downloaded file is too small — update aborted.")

    if os.path.exists(old):
        os.remove(old)
    os.replace(exe, old)          # rename the running exe out of the way
    try:
        os.replace(new, exe)
    except Exception:
        os.replace(old, exe)      # put the original back
        raise
    return exe


def launch_new(exe: str):
    env = os.environ.copy()
    # Tell PyInstaller the child is a separate app, not part of this one.
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    return subprocess.Popen([exe, "--after-update"], env=env, close_fds=True,
                            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
