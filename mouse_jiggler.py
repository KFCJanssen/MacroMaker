"""
mouse_jiggler.py — Keeps the PC (and games like Roblox) from seeing you as idle.

Every few seconds it nudges the mouse a few pixels and straight back, so the
cursor ends up where it started. On Windows it uses the legacy mouse_event()
relative-move path (the same one macro_runner uses), which games pick up as
real input, and it asks Windows not to sleep or turn off the display while on.
"""

import sys
import threading
import time

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import ctypes
    import ctypes.wintypes

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    MOUSEEVENTF_MOVE = 0x0001

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.wintypes.UINT),
                    ("dwTime", ctypes.wintypes.DWORD)]

    def _nudge(dx: int, dy: int):
        _user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)

    def _idle_seconds() -> float:
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if not _user32.GetLastInputInfo(ctypes.byref(info)):
            return float("inf")
        return ((_kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0

    def _keep_awake(on: bool):
        flags = ES_CONTINUOUS
        if on:
            flags |= ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        _kernel32.SetThreadExecutionState(flags)

else:
    from pynput.mouse import Controller as _MouseController
    _mc = _MouseController()

    def _nudge(dx: int, dy: int):
        _mc.move(dx, dy)

    def _idle_seconds() -> float:
        return float("inf")   # no idle detection off Windows: always jiggle

    def _keep_awake(on: bool):
        pass


class MouseJiggler:
    def __init__(self, on_status_change=None, on_jiggle=None):
        self.running = False
        self.interval_s = 30        # how often to jiggle
        self.distance_px = 2        # how far to move before coming back
        self.only_when_idle = True  # skip while the user is using the PC
        self.jiggle_count = 0
        self.on_status_change = on_status_change
        self.on_jiggle = on_jiggle
        self._stop_evt = threading.Event()
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.jiggle_count = 0
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if self.on_status_change:
            self.on_status_change(True)

    def stop(self):
        if not self.running:
            return
        self.running = False
        self._stop_evt.set()
        if self.on_status_change:
            self.on_status_change(False)

    def toggle(self):
        self.stop() if self.running else self.start()

    def _jiggle(self):
        d = max(1, int(self.distance_px))
        _nudge(d, d)
        time.sleep(0.05)
        _nudge(-d, -d)
        self.jiggle_count += 1
        if self.on_jiggle:
            self.on_jiggle(self.jiggle_count)

    def _run(self):
        # The thread that calls SetThreadExecutionState must stay alive for the
        # request to hold, so we set it here and clear it before exiting.
        _keep_awake(True)
        last = time.monotonic()
        try:
            while not self._stop_evt.wait(0.5):
                interval = max(1, int(self.interval_s))
                if time.monotonic() - last < interval:
                    continue
                # With "only when idle", wait until the user has also been
                # inactive for a full interval, so we never fight their mouse.
                if self.only_when_idle and _idle_seconds() < interval:
                    continue
                self._jiggle()
                last = time.monotonic()
        finally:
            _keep_awake(False)
