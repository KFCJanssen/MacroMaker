"""
app_support.py — Plumbing that isn't part of any one page:

  * settings  : load/save settings.json (atomic write, never crashes the app)
  * logging   : error.log in the app-data folder, catching crashes from the
                main thread, background threads and Tk callbacks
  * single instance : a second launch tells the running copy to show itself
                and then exits, so two copies never fight over the hotkeys
"""

import json
import logging
import logging.handlers
import os
import sys
import threading

log = logging.getLogger("MacroMaker")


# ── Settings ────────────────────────────────────────────────────────────────
def load_settings(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        log.exception("Could not read settings from %s", path)
        return {}


def save_settings(path: str, data: dict):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)   # atomic: never leaves a half-written file
    except Exception:
        log.exception("Could not save settings to %s", path)


# ── Error log ───────────────────────────────────────────────────────────────
def setup_logging(log_path: str, version: str):
    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=256_000, backupCount=1, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-7s %(threadName)s: %(message)s"))
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    log.info("Macro Maker v%s started", version)

    def excepthook(exc_type, exc, tb):
        log.critical("Unhandled error", exc_info=(exc_type, exc, tb))
    sys.excepthook = excepthook

    def thread_excepthook(args):
        log.error("Unhandled error in thread %s", args.thread.name if args.thread else "?",
                  exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = thread_excepthook


# ── Single instance ─────────────────────────────────────────────────────────
_EVENT_NAME = "Local\\KFCJanssen.MacroMaker.Show"


class SingleInstance:
    """
    Uses a named Windows event. The first copy creates it and waits on it in a
    background thread; a second copy finds it already exists, signals it (which
    makes the first copy show its window) and should then exit.
    """

    def __init__(self):
        self.is_primary = True
        self._handle = None
        self._stop = threading.Event()
        if sys.platform != "win32":
            return
        import ctypes
        self._k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._k32.CreateEventW.restype = ctypes.c_void_p
        self._k32.CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_bool,
                                           ctypes.c_bool, ctypes.c_wchar_p]
        self._k32.SetEvent.argtypes = [ctypes.c_void_p]
        self._k32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self._k32.CloseHandle.argtypes = [ctypes.c_void_p]
        # auto-reset event, initially not signalled
        self._handle = self._k32.CreateEventW(None, False, False, _EVENT_NAME)
        ERROR_ALREADY_EXISTS = 183
        if self._handle and ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            self.is_primary = False

    def notify_primary(self):
        """Second copy: ask the running copy to show its window."""
        if self._handle:
            self._k32.SetEvent(self._handle)

    def listen(self, on_show):
        """First copy: call on_show() (from a background thread) on every signal."""
        if not self._handle:
            return

        def run():
            WAIT_OBJECT_0 = 0
            while not self._stop.is_set():
                if self._k32.WaitForSingleObject(self._handle, 500) == WAIT_OBJECT_0:
                    if not self._stop.is_set():
                        on_show()
        threading.Thread(target=run, name="single-instance", daemon=True).start()

    def close(self):
        self._stop.set()
