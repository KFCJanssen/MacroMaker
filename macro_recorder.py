"""
macro_recorder.py — Records mouse clicks, key presses, mouse moves, and scrolls
with accurate inter-step timing, then converts them into MacroStep lists
compatible with MacroRunner.
"""

import threading
import time
from pynput import mouse as pmouse, keyboard as pkeyboard
from macro_runner import MacroStep

# F-keys used internally by the app — we ignore these during recording
# so the record hotkey itself is never captured as a step.
_IGNORED_FKEYS = {
    pkeyboard.Key.f1,  pkeyboard.Key.f2,  pkeyboard.Key.f3,
    pkeyboard.Key.f4,  pkeyboard.Key.f5,  pkeyboard.Key.f6,
    pkeyboard.Key.f7,  pkeyboard.Key.f8,  pkeyboard.Key.f9,
    pkeyboard.Key.f10, pkeyboard.Key.f11, pkeyboard.Key.f12,
}

# Minimum delay (ms) between steps — smaller gaps are merged into the action
# Lowered to 10ms to match TinyTask's resolution (was 30ms)
MIN_DELAY_MS = 10

# Minimum mouse-move distance (pixels) to record as a "move" step.
# Lowered to 1px so near-stationary hover movements are captured (was 8px).
# This is critical: if the cursor sits on a button without a recorded move,
# playback jumps straight to the click with no intermediate mousemove events,
# so the button never enters its hover/hot state before the click lands.
MOVE_THRESHOLD_PX = 1

# How often (ms) we snapshot mouse position for move steps.
# Matched to TinyTask's SetTimer interval of 10ms = 100 Hz (was 80ms = 12.5 Hz).
# Higher frequency means denser move trails and reliable hover detection on playback.
MOVE_SAMPLE_MS = 10


class _RawEvent:
    """Internal timestamped event collected during recording."""
    __slots__ = ("ts", "kind", "data")

    def __init__(self, kind: str, data: dict):
        self.ts   = time.time()
        self.kind = kind   # "click", "key", "scroll", "move"
        self.data = data


class MacroRecorder:
    """
    Records user input and converts it to MacroStep objects.

    Usage
    -----
    recorder = MacroRecorder(on_status_change=..., ignored_hotkeys={"f9"})
    recorder.start()
    # ... user does things ...
    recorder.stop()
    steps = recorder.get_steps()
    """

    def __init__(self, on_status_change=None, ignored_hotkeys: set | None = None):
        self.recording = False
        self.on_status_change = on_status_change
        # Extra F-key names (lowercase strings) to suppress, e.g. {"f9"}
        self._ignored_hk_names: set[str] = ignored_hotkeys or set()

        self._events: list[_RawEvent] = []
        self._lock   = threading.Lock()
        self._mouse_listener    = None
        self._keyboard_listener = None
        self._move_thread       = None
        self._stop_move         = threading.Event()
        self._last_move_pos     = (0, 0)
        self._pressed_keys: set = set()

    # ── Public API ──────────────────────────────────────────────────────────

    def start(self):
        if self.recording:
            return
        self.recording = True
        with self._lock:
            self._events.clear()
        self._pressed_keys.clear()
        self._stop_move.clear()
        self._start_listeners()
        self._move_thread = threading.Thread(
            target=self._poll_mouse_moves, daemon=True)
        self._move_thread.start()
        if self.on_status_change:
            self.on_status_change(True)

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        self._stop_move.set()
        self._stop_listeners()
        if self.on_status_change:
            self.on_status_change(False)

    def get_steps(self) -> list[MacroStep]:
        """Convert recorded raw events into MacroStep objects with delay steps."""
        with self._lock:
            events = list(self._events)
        return _build_steps(events)

    def clear(self):
        with self._lock:
            self._events.clear()

    # ── Listeners ───────────────────────────────────────────────────────────

    def _start_listeners(self):
        self._mouse_listener = pmouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

        self._keyboard_listener = pkeyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

    def _stop_listeners(self):
        for lst in (self._mouse_listener, self._keyboard_listener):
            if lst:
                try:
                    lst.stop()
                except Exception:
                    pass
        self._mouse_listener    = None
        self._keyboard_listener = None

    # ── Raw event callbacks ─────────────────────────────────────────────────

    def _on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        if pressed:
            with self._lock:
                self._events.append(_RawEvent("click", {
                    "x": x, "y": y,
                    "button": button.name,   # "left" / "right" / "middle"
                }))

    def _on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return
        with self._lock:
            self._events.append(_RawEvent("scroll", {
                "x": x, "y": y,
                "direction": "up" if dy > 0 else "down",
                "amount": max(1, abs(dy)),
            }))

    def _on_key_press(self, key):
        if not self.recording:
            return
        # Silently skip all F-keys (app hotkeys)
        if key in _IGNORED_FKEYS:
            return
        # Also skip by name (covers user-configured record hotkey)
        name = _key_to_name(key)
        if name and name.lower() in self._ignored_hk_names:
            return
        if key in self._pressed_keys:
            return   # ignore key-repeat events
        self._pressed_keys.add(key)
        with self._lock:
            self._events.append(_RawEvent("key_down", {"key": key, "name": name}))

    def _on_key_release(self, key):
        if not self.recording:
            return
        if key in _IGNORED_FKEYS:
            return
        name = _key_to_name(key)
        if name and name.lower() in self._ignored_hk_names:
            return
        self._pressed_keys.discard(key)
        with self._lock:
            self._events.append(_RawEvent("key_up", {"key": key, "name": name}))

    # ── Mouse-move polling ──────────────────────────────────────────────────

    def _poll_mouse_moves(self):
        import pyautogui
        prev_x, prev_y = pyautogui.position()
        self._last_move_pos = (prev_x, prev_y)
        interval = MOVE_SAMPLE_MS / 1000.0

        while not self._stop_move.wait(timeout=interval):
            if not self.recording:
                break
            cx, cy = pyautogui.position()
            dx = cx - prev_x
            dy = cy - prev_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist >= MOVE_THRESHOLD_PX:
                with self._lock:
                    self._events.append(_RawEvent("move", {"x": cx, "y": cy}))
                prev_x, prev_y = cx, cy
                self._last_move_pos = (cx, cy)


# ── Step builder ─────────────────────────────────────────────────────────────

def _key_to_name(key) -> str:
    """Convert a pynput key to a human-readable name."""
    # Special keys have a .name attribute
    if hasattr(key, "name"):
        return key.name          # e.g. "ctrl_l", "shift", "enter"
    # Printable characters
    if hasattr(key, "char") and key.char:
        return key.char
    return str(key).replace("Key.", "")


def _build_steps(events: list[_RawEvent]) -> list[MacroStep]:
    """
    Turn raw events into MacroStep objects.

    Strategy
    --------
    * Pair key_down / key_up into a single keypress step (with hold duration).
    * Insert Delay steps for gaps between events.
    * Collapse consecutive move events into just the last position.
    * Combine simultaneous modifier + key into a combo (ctrl+c style).
    """
    if not events:
        return []

    steps: list[MacroStep] = []
    i = 0
    last_ts = events[0].ts   # timestamp after which we start measuring delays

    def maybe_delay(current_ts: float):
        nonlocal last_ts
        gap_ms = round((current_ts - last_ts) * 1000)
        if gap_ms >= MIN_DELAY_MS:
            steps.append(MacroStep("delay", ms=gap_ms))
        last_ts = current_ts

    while i < len(events):
        ev = events[i]

        # ── Mouse click ─────────────────────────────────────────────────────
        if ev.kind == "click":
            maybe_delay(ev.ts)
            steps.append(MacroStep("click",
                                   x=ev.data["x"],
                                   y=ev.data["y"],
                                   button=ev.data["button"]))
            last_ts = ev.ts
            i += 1

        # ── Scroll ──────────────────────────────────────────────────────────
        elif ev.kind == "scroll":
            maybe_delay(ev.ts)
            steps.append(MacroStep("scroll",
                                   x=ev.data["x"],
                                   y=ev.data["y"],
                                   direction=ev.data["direction"],
                                   amount=ev.data["amount"]))
            last_ts = ev.ts
            i += 1

        # ── Mouse move ──────────────────────────────────────────────────────
        elif ev.kind == "move":
            # Emit every recorded move individually.
            # Previously we collapsed consecutive moves to just the last position,
            # but that caused the cursor to jump large distances during playback,
            # skipping the intermediate mousemove events that buttons need to
            # enter their hover/hot state before a click registers.
            # TinyTask records at 10ms and keeps all positions — we do the same.
            maybe_delay(ev.ts)
            steps.append(MacroStep("move",
                                   x=ev.data["x"],
                                   y=ev.data["y"]))
            last_ts = ev.ts
            i += 1

        # ── Key press (with combo detection) ────────────────────────────────
        elif ev.kind == "key_down":
            # Collect all keys held simultaneously before first key_up
            combo_keys: list[str] = [ev.data["name"]]
            down_ts  = ev.ts
            key_obj  = ev.data["key"]
            held_keys = {key_obj}

            j = i + 1
            while j < len(events):
                nxt = events[j]
                if nxt.kind == "key_down":
                    name = nxt.data["name"]
                    if name and name not in combo_keys:
                        combo_keys.append(name)
                    held_keys.add(nxt.data["key"])
                    j += 1
                elif nxt.kind == "key_up":
                    if nxt.data["key"] in held_keys:
                        held_keys.discard(nxt.data["key"])
                        j += 1
                        if not held_keys:
                            break
                    else:
                        break
                else:
                    break

            # Find the corresponding key_up to measure hold duration
            up_ts = down_ts
            for k2 in range(i + 1, min(j + 1, len(events))):
                if events[k2].kind == "key_up" and events[k2].data["key"] == key_obj:
                    up_ts = events[k2].ts
                    break

            hold_ms = max(MIN_DELAY_MS, round((up_ts - down_ts) * 1000))
            combo_str = "+".join(combo_keys)

            maybe_delay(down_ts)
            steps.append(MacroStep("keypress",
                                   keys=combo_str,
                                   duration_ms=hold_ms))
            last_ts = up_ts
            i = j

        # ── Orphan key_up — skip ────────────────────────────────────────────
        elif ev.kind == "key_up":
            i += 1

        else:
            i += 1

    return steps
