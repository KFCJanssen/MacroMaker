import threading
import time
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True


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
        self.repeat_mode = "once"  # "once" | "count" | "forever"
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
                if "+" in keys:
                    parts = [k.strip() for k in keys.split("+")]
                    pyautogui.hotkey(*parts)
                else:
                    pyautogui.press(keys)
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
            # "forever" keeps looping

        self.running = False
        self._current_step = -1
        if self.on_status_change:
            self.on_status_change(False)
        if self.on_step_change:
            self.on_step_change(-1)
