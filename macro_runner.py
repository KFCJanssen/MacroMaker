import threading
import time
import pyautogui
from pynput.keyboard import Key, Controller as KeyboardController

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

_kb = KeyboardController()

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
                pyautogui.click(
                    step.data.get("x", 0),
                    step.data.get("y", 0),
                    button=step.data.get("button", "left"),
                )
            elif step.type == "move":
                pyautogui.moveTo(step.data.get("x", 0), step.data.get("y", 0))
            elif step.type == "keypress":
                keys = step.data.get("keys", "")
                dur  = step.data.get("duration_ms", 50)
                if keys:
                    _press_keys(keys, duration_ms=dur)
            elif step.type == "delay":
                ms = step.data.get("ms", 500)
                end = time.time() + ms / 1000.0
                while self.running and time.time() < end:
                    time.sleep(0.02)
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
