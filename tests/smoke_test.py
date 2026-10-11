"""
Windows smoke test, run by GitHub Actions before every release.
Starts the real app, exercises tray hide/restore, the jiggler and settings
persistence, then checks that a second launch hands over to the first.
"""
import os
import subprocess
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import main  # noqa: E402

errors = []


def run_app(script):
    app = main.App()

    def on_error(*exc):
        errors.append(exc)
        traceback.print_exception(*exc)
    app.report_callback_exception = on_error
    for delay_ms, fn in script(app):
        app.after(delay_ms, fn)
    app.mainloop()
    return app


# 1) version label matches VERSION file
version = open(os.path.join(ROOT, "VERSION")).read().strip()
assert main.APP_VERSION == version, f"APP_VERSION {main.APP_VERSION} != VERSION {version}"

# 2) start, hide to tray, restore, jiggler on/off, change settings, quit
if os.path.exists(main.SETTINGS_FILE):
    os.remove(main.SETTINGS_FILE)
run_app(lambda app: [
    (1500, app._hide_to_tray),
    (2500, app._show_from_tray),
    (3000, app._jiggle_panel._toggle),
    (4000, app._jiggle_panel._toggle),
    (4200, lambda: app._ac_panel._interval_var.set("1234")),
    (4200, lambda: app._macro_panel._gap_var.set("2.5")),
    (4200, lambda: app._macro_panel._speed_var.set("2×")),
    (4200, lambda: app._select_nav("Mouse Jiggler")),
    (4400, lambda: (app._settings_panel.theme_var.set("Light"),
                    app._settings_panel.apply_theme())),
    (4800, lambda: app._select_nav("Settings")),
    (5200, lambda: (app._settings_panel.theme_var.set("Dark"),
                    app._settings_panel.apply_theme())),
    (5400, lambda: app._select_nav("Mouse Jiggler")),
    (7000, app._quit),
])
assert os.path.exists(main.SETTINGS_FILE), "settings.json was not written"

# 3) settings come back after a restart
seen = {}
run_app(lambda app: [
    (1000, lambda: seen.update(
        interval=app._ac_panel._interval_var.get(),
        gap=app._macro_panel._gap_var.get(),
        speed=app._macro_panel._speed_var.get(),
        tab=app._current_tab,
        theme=app._settings_panel.theme_var.get())),
    (1500, app._quit),
])
assert seen == {"interval": "1234", "gap": "2.5", "speed": "2×",
                "tab": "Mouse Jiggler", "theme": "Dark"}, seen

# 4) --tray starts hidden
hidden = {}
app = main.App(start_hidden=True)
app.after(1500, lambda: (hidden.update(state=app.state()), app._quit()))
app.mainloop()
assert hidden["state"] == "withdrawn", hidden

# 5) a second copy hands over to the first and exits
first = subprocess.Popen([sys.executable, "main.py"])
time.sleep(6)
second = subprocess.run([sys.executable, "main.py"], timeout=30)
assert second.returncode == 0, f"second instance exit code {second.returncode}"
assert first.poll() is None, "first instance died"
first.kill()

assert os.path.exists(main.LOG_FILE), "error.log was not created"
assert not errors, f"{len(errors)} error(s) during smoke test"
print("smoke test passed")
