"""
tray.py — System tray (notification area) icon for Macro Maker.

Closing or minimising the window hides it to the tray instead of quitting, so
hotkeys, the auto clicker, macros and the mouse jiggler keep running.
pystray runs its own message loop on a background thread; every callback is
handed back to the Tk thread via `schedule` (tk's after()), because Tk is not
thread-safe.
"""

from PIL import Image, ImageDraw
import pystray

PRIMARY = "#0078D4"


def make_icon_image(size: int = 64) -> Image.Image:
    """Blue rounded square with a white lightning bolt (matches the ⚡ in the app)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=PRIMARY)
    s = size / 64
    bolt = [(36, 6), (14, 36), (30, 36), (24, 58), (50, 24), (34, 24), (40, 6)]
    d.polygon([(x * s, y * s) for x, y in bolt], fill="white")
    return img


class TrayIcon:
    def __init__(self, schedule, on_show, on_quit, toggles):
        """
        schedule(fn)  – run fn on the Tk thread (e.g. lambda fn: app.after(0, fn))
        on_show()     – bring the window back
        on_quit()     – really exit the app
        toggles       – list of (label, is_on: () -> bool, toggle: () -> None)
        """
        self._schedule = schedule
        self._toggles = toggles

        items = [pystray.MenuItem("Open Macro Maker",
                                  self._action(on_show), default=True),
                 pystray.Menu.SEPARATOR]
        for label, is_on, toggle in toggles:
            items.append(pystray.MenuItem(label, self._action(toggle),
                                          checked=self._checked(is_on)))
        items += [pystray.Menu.SEPARATOR,
                  pystray.MenuItem("Quit", self._action(on_quit))]

        self._icon = pystray.Icon("MacroMaker", make_icon_image(),
                                  "Macro Maker", menu=pystray.Menu(*items))

    # pystray decides how to call an action by counting its parameters (default
    # arguments included), so build zero-argument closures instead of lambdas
    # with defaults.
    def _action(self, fn):
        def action():
            self._schedule(fn)
        return action

    @staticmethod
    def _checked(is_on):
        def checked(_item):
            return bool(is_on())
        return checked

    def start(self):
        self._icon.run_detached()

    def refresh(self):
        """Call after a toggle changes so the check marks and tooltip update."""
        on = [label for label, is_on, _ in self._toggles if is_on()]
        self._icon.title = "Macro Maker" + (f" — {', '.join(on)} on" if on else "")
        self._icon.update_menu()

    def notify(self, message: str):
        try:
            self._icon.notify(message, "Macro Maker")
        except Exception:
            pass   # notifications are a nicety; never let them break anything

    def stop(self):
        try:
            self._icon.stop()
        except Exception:
            pass
