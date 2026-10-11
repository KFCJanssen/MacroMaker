"""
autostart.py — "Start with Windows" via the per-user Run registry key
(HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run). No admin rights needed.
The app is started with --tray so it goes straight to the system tray.
"""

import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "MacroMaker"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --tray'
    # Running from source: use pythonw so no console window pops up.
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{pyw}" "{main_py}" --tray'


def is_supported() -> bool:
    return sys.platform == "win32"


def is_enabled() -> bool:
    if not is_supported():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            value, _ = winreg.QueryValueEx(k, VALUE_NAME)
        return bool(value)
    except OSError:
        return False


def set_enabled(on: bool):
    if not is_supported():
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                        winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, VALUE_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(k, VALUE_NAME)
            except FileNotFoundError:
                pass


def refresh_path():
    """If enabled, rewrite the entry so it points at wherever the app is now."""
    if is_enabled():
        set_enabled(True)
