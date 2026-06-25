import threading
import time
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True


class AutoClicker:
    def __init__(self, on_status_change=None):
        self.running = False
        self.interval_ms = 1000
        self.use_cursor = True
        self.fixed_x = 500
        self.fixed_y = 500
        self.button = "left"
        self.repeat_forever = True
        self.repeat_count = 10
        self._thread = None
        self._clicks_done = 0
        self.on_status_change = on_status_change

    def start(self):
        if self.running:
            return
        self.running = True
        self._clicks_done = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if self.on_status_change:
            self.on_status_change(True)

    def stop(self):
        self.running = False
        if self.on_status_change:
            self.on_status_change(False)

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def _run(self):
        while self.running:
            try:
                if self.use_cursor:
                    pyautogui.click(button=self.button)
                else:
                    pyautogui.click(self.fixed_x, self.fixed_y, button=self.button)
                self._clicks_done += 1
                if not self.repeat_forever and self._clicks_done >= self.repeat_count:
                    self.stop()
                    return
                interval = max(10, self.interval_ms) / 1000.0
                time.sleep(interval)
            except pyautogui.FailSafeException:
                self.stop()
                return
            except Exception:
                time.sleep(0.1)
