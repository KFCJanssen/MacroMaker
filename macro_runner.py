import threading
import time
import sys
import ctypes
import ctypes.wintypes
import pyautogui
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button as MouseButton, Controller as MouseController

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

_kb = KeyboardController()
_mc = MouseController()

# ── Win32 legacy input (same APIs TinyTask uses) ──────────────────────────────
# mouse_event() and SetCursorPos() are the oldest injection path and are picked
# up by DirectInput / Roblox where SendInput (used by pyautogui & pynput) is not.
_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    _user32 = ctypes.windll.user32

    MOUSEEVENTF_MOVE       = 0x0001
    MOUSEEVENTF_LEFTDOWN   = 0x0002
    MOUSEEVENTF_LEFTUP     = 0x0004
    MOUSEEVENTF_RIGHTDOWN  = 0x0008
    MOUSEEVENTF_RIGHTUP    = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP   = 0x0040
    MOUSEEVENTF_ABSOLUTE   = 0x8000   # coords are normalized 0-65535

    _BTN_DOWN = {
        "left":   MOUSEEVENTF_LEFTDOWN,
        "right":  MOUSEEVENTF_RIGHTDOWN,
        "middle": MOUSEEVENTF_MIDDLEDOWN,
    }
    _BTN_UP = {
        "left":   MOUSEEVENTF_LEFTUP,
        "right":  MOUSEEVENTF_RIGHTUP,
        "middle": MOUSEEVENTF_MIDDLEUP,
    }

    # Cache screen dimensions once at startup for coordinate normalisation.
    # GetSystemMetrics(SM_CXVIRTUALSCREEN/SM_CYVIRTUALSCREEN) covers multi-monitor setups.
    _SCREEN_W = _user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
    _SCREEN_H = _user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
    if _SCREEN_W <= 0:
        _SCREEN_W = _user32.GetSystemMetrics(0)   # SM_CXSCREEN fallback
    if _SCREEN_H <= 0:
        _SCREEN_H = _user32.GetSystemMetrics(1)   # SM_CYSCREEN fallback

    def _win_move(x: int, y: int):
        """
        Move cursor the same way TinyTask does:
          1. mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, norm_x, norm_y)
             This injects a real WM_MOUSEMOVE through the input pipeline so every
             application — including those that do hover/hit-testing on WM_MOUSEMOVE —
             updates its button hot states before the click arrives.
          2. SetCursorPos(x, y)  — snap the hardware cursor to the exact pixel
             (TinyTask does both; mouse_event with ABSOLUTE can land off-by-one on
             some DPI configurations, so SetCursorPos is the authoritative position).

        Using SetCursorPos ALONE (the previous approach) only repositions the cursor
        visually; it does NOT generate a WM_MOUSEMOVE through the injection path, so
        buttons never see the hover event and ignore the subsequent click.
        """
        norm_x = (x * 65535) // _SCREEN_W
        norm_y = (y * 65535) // _SCREEN_H
        _user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, norm_x, norm_y, 0, 0)
        _user32.SetCursorPos(x, y)

    def _win_click(x: int, y: int, button: str = "left"):
        """
        Fire a click exactly as TinyTask does:
          mouse_event(LEFTDOWN, 0, 0, 0, 0)
          mouse_event(LEFTUP,   0, 0, 0, 0)
        No coordinates — the cursor is already at (x, y) from the preceding _win_move.
        TinyTask never passes coordinates to the click mouse_event calls.
        """
        _user32.mouse_event(_BTN_DOWN.get(button, MOUSEEVENTF_LEFTDOWN), 0, 0, 0, 0)
        time.sleep(0.04)   # 40ms hold between down and up
        _user32.mouse_event(_BTN_UP.get(button, MOUSEEVENTF_LEFTUP),   0, 0, 0, 0)

else:
    # macOS / Linux fallback — pynput is the best option there
    _MOUSE_BUTTON_MAP = {
        "left":   MouseButton.left,
        "right":  MouseButton.right,
        "middle": MouseButton.middle,
    }

    def _win_move(x: int, y: int):
        _mc.position = (x, y)

    def _win_click(x: int, y: int, button: str = "left"):
        _mc.position = (x, y)
        time.sleep(0.08)
        btn = _MOUSE_BUTTON_MAP.get(button, MouseButton.left)
        _mc.press(btn)
        time.sleep(0.05)
        _mc.release(btn)


def _get_cursor_pos() -> tuple[int, int]:
    """Return current cursor position."""
    if _IS_WINDOWS:
        pt = ctypes.wintypes.POINT()
        _user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    else:
        pos = _mc.position
        return int(pos[0]), int(pos[1])


def _smooth_move(sx: int, sy: int, tx: int, ty: int, steps: int = 20, total_ms: int = 160):
    """
    Glide from (sx,sy) to (tx,ty) via interpolated SetCursorPos calls.
    Produces a stream of mousemove events the game engine registers as
    real physical movement, enabling hover detection before a click.
    Uses smoothstep easing (same curve as a real mouse deceleration).
    """
    sleep_s = (total_ms / 1000.0) / steps
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)   # smoothstep
        ix = int(sx + (tx - sx) * ease)
        iy = int(sy + (ty - sy) * ease)
        _win_move(ix, iy)
        time.sleep(sleep_s)


_KEY_MAP = {
    "ctrl":         Key.ctrl,
    "control":      Key.ctrl,
    "ctrl_l":       Key.ctrl_l,
    "ctrl_r":       Key.ctrl_r,
    "alt":          Key.alt,
    "alt_l":        Key.alt_l,
    "alt_r":        Key.alt_r,
    "shift":        Key.shift,
    "shift_l":      Key.shift_l,
    "shift_r":      Key.shift_r,
    "win":          Key.cmd,
    "cmd":          Key.cmd,
    "super":        Key.cmd,
    "enter":        Key.enter,
    "return":       Key.enter,
    "space":        Key.space,
    "tab":          Key.tab,
    "esc":          Key.esc,
    "escape":       Key.esc,
    "backspace":    Key.backspace,
    "delete":       Key.delete,
    "del":          Key.delete,
    "insert":       Key.insert,
    "home":         Key.home,
    "end":          Key.end,
    "pageup":       Key.page_up,
    "page_up":      Key.page_up,
    "pgup":         Key.page_up,
    "pagedown":     Key.page_down,
    "page_down":    Key.page_down,
    "pgdn":         Key.page_down,
    "up":           Key.up,
    "down":         Key.down,
    "left":         Key.left,
    "right":        Key.right,
    "caps_lock":    Key.caps_lock,
    "capslock":     Key.caps_lock,
    "num_lock":     Key.num_lock,
    "numlock":      Key.num_lock,
    "scroll_lock":  Key.scroll_lock,
    "print_screen": Key.print_screen,
    "pause":        Key.pause,
    "f1":  Key.f1,  "f2":  Key.f2,  "f3":  Key.f3,  "f4":  Key.f4,
    "f5":  Key.f5,  "f6":  Key.f6,  "f7":  Key.f7,  "f8":  Key.f8,
    "f9":  Key.f9,  "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
}


def _resolve_key(name: str):
    """Return a pynput Key or single character for a given key name string."""
    n = name.strip().lower()
    if n in _KEY_MAP:
        return _KEY_MAP[n]
    if len(name.strip()) == 1:
        return name.strip()
    return name.strip()


def _press_keys(keys_str: str, duration_ms: int = 50):
    """
    Press key(s) using pynput — works globally across all windows.
    Supports combos like ctrl+c, alt+f4.
    Holds each key for duration_ms milliseconds.
    """
    parts = [k.strip() for k in keys_str.split("+") if k.strip()]
    if not parts:
        return
    resolved = [_resolve_key(p) for p in parts]
    try:
        for k in resolved:
            _kb.press(k)
        hold = max(0, duration_ms) / 1000.0
        if hold > 0:
            time.sleep(hold)
        for k in reversed(resolved):
            _kb.release(k)
    except Exception:
        try:
            for k in reversed(resolved):
                _kb.release(k)
        except Exception:
            pass


class MacroStep:
    def __init__(self, step_type, **kwargs):
        self.type = step_type
        self.data = kwargs

    def to_dict(self):
        return {"type": self.type, **self.data}

    @staticmethod
    def from_dict(d):
        t = d.pop("type")
        return MacroStep(t, **d)

    def label(self):
        if self.type == "click":
            btn = self.data.get("button", "left")
            x, y = self.data.get("x", 0), self.data.get("y", 0)
            return f"Click {btn} at ({x}, {y})"
        elif self.type == "move":
            x, y = self.data.get("x", 0), self.data.get("y", 0)
            return f"Move to ({x}, {y})"
        elif self.type == "keypress":
            keys = self.data.get("keys", "")
            dur  = self.data.get("duration_ms", 50)
            if dur != 50:
                return f"Key: {keys}  [{dur} ms hold]"
            return f"Key: {keys}"
        elif self.type == "delay":
            ms = self.data.get("ms", 500)
            return f"Delay {ms} ms"
        elif self.type == "scroll":
            direction = self.data.get("direction", "up")
            amount = self.data.get("amount", 3)
            x, y = self.data.get("x", 0), self.data.get("y", 0)
            return f"Scroll {direction} ×{amount} at ({x}, {y})"
        return "Unknown"


class MacroRunner:
    def __init__(self, on_status_change=None, on_step_change=None):
        self.steps = []
        self.running = False
        self.repeat_mode = "once"
        self.repeat_count = 1
        self._thread = None
        self.on_status_change = on_status_change
        self.on_step_change = on_step_change
        self._current_step = -1

    def start(self):
        if self.running or not self.steps:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if self.on_status_change:
            self.on_status_change(True)

    def stop(self):
        self.running = False
        self._current_step = -1
        if self.on_status_change:
            self.on_status_change(False)
        if self.on_step_change:
            self.on_step_change(-1)

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def _execute_step(self, step):
        try:
            if step.type == "click":
                x = step.data.get("x", 0)
                y = step.data.get("y", 0)
                button = step.data.get("button", "left")

                # Ensure cursor is exactly on the target (in case no move step immediately
                # preceded this click), then give the application 1ms to register hover —
                # matching TinyTask's Sleep(1) between each step in its playback loop.
                _win_move(x, y)
                time.sleep(0.001)

                # Fire click with no coordinates — cursor is already positioned.
                # This is exactly how TinyTask does it.
                _win_click(x, y, button)

            elif step.type == "move":
                x = step.data.get("x", 0)
                y = step.data.get("y", 0)
                # Inject WM_MOUSEMOVE via mouse_event(ABSOLUTE) + SetCursorPos.
                # See _win_move docstring for why this is critical for hover detection.
                _win_move(x, y)
                time.sleep(0.001)  # Sleep(1) after each move, matching TinyTask
            elif step.type == "keypress":
                keys = step.data.get("keys", "")
                dur  = step.data.get("duration_ms", 50)
                if keys:
                    _press_keys(keys, duration_ms=dur)
            elif step.type == "delay":
                ms = step.data.get("ms", 500)
                end = time.time() + ms / 1000.0
                while self.running and time.time() < end:
                    time.sleep(0.005)
            elif step.type == "scroll":
                x = step.data.get("x", 0)
                y = step.data.get("y", 0)
                amount = step.data.get("amount", 3)
                direction = step.data.get("direction", "up")
                clicks = amount if direction == "up" else -amount
                pyautogui.scroll(clicks, x=x, y=y)
        except pyautogui.FailSafeException:
            self.stop()

    def _run(self):
        runs = 0
        while self.running:
            for idx, step in enumerate(self.steps):
                if not self.running:
                    break
                self._current_step = idx
                if self.on_step_change:
                    self.on_step_change(idx)
                self._execute_step(step)

            runs += 1
            if self.repeat_mode == "once":
                break
            elif self.repeat_mode == "count" and runs >= self.repeat_count:
                break

        self.running = False
        self._current_step = -1
        if self.on_status_change:
            self.on_status_change(False)
        if self.on_step_change:
            self.on_step_change(-1)
