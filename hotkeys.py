from pynput import keyboard
import threading


AVAILABLE_KEYS = [
    "f1", "f2", "f3", "f4", "f5", "f6",
    "f7", "f8", "f9", "f10", "f11", "f12",
]

KEY_MAP = {
    "f1": keyboard.Key.f1,
    "f2": keyboard.Key.f2,
    "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4,
    "f5": keyboard.Key.f5,
    "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7,
    "f8": keyboard.Key.f8,
    "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10,
    "f11": keyboard.Key.f11,
    "f12": keyboard.Key.f12,
}


class HotkeyManager:
    """Global hotkey listener that works across windows using pynput."""

    def __init__(self):
        self._bindings = {}  # key_name -> callback
        self._listener = None
        self._lock = threading.Lock()

    def bind(self, key_name: str, callback):
        """Bind a callback to an F-key. key_name e.g. 'f6'."""
        with self._lock:
            self._bindings[key_name.lower()] = callback
            self._restart()

    def unbind(self, key_name: str):
        with self._lock:
            self._bindings.pop(key_name.lower(), None)
            self._restart()

    def _restart(self):
        self._stop_listener()
        if self._bindings:
            self._start_listener()

    def _start_listener(self):
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def _stop_listener(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _on_press(self, key):
        for key_name, cb in list(self._bindings.items()):
            target = KEY_MAP.get(key_name)
            if target and key == target:
                threading.Thread(target=cb, daemon=True).start()

    def start(self):
        with self._lock:
            if self._bindings:
                self._start_listener()

    def stop(self):
        with self._lock:
            self._stop_listener()
