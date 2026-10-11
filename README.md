# Macro Maker — Desktop

Auto clicker & macro tool for Windows with global F-key hotkeys. Record your actions or build a macro step by step, then replay it from any window.

## Download

Grab `MacroMaker.exe` from the [Releases](../../releases) page. No Python needed, just run it.

## Run from source

```bash
pip install -r requirements.txt
python main.py
```

Or double-click `install_and_run.bat`.

## Build the .exe yourself

Double-click `build_exe.bat`. The result lands in `dist\MacroMaker.exe`.

## Features

### Auto Clicker
- Set click interval (ms) with presets or custom value
- **Follow cursor** — clicks wherever your mouse is
- **Fixed position** — click 📍 Pick then click anywhere on screen to capture coordinates
- Left / Right / Middle mouse button
- Repeat forever or stop after N clicks
- **Toggle hotkey** (default F6) — works while you're in any other window

### Macro Maker
- **⏺ Record** (default F9) — captures mouse moves, clicks, key presses and scrolls with their real timing (10 ms resolution), then turns them into editable steps
- Build sequences by hand: Mouse Click, Mouse Move, Key Press, Delay, Scroll
- 📍 Pick position by clicking anywhere on screen for any step
- Reorder steps with ↑ ↓ buttons, double-click to edit
- Repeat: Once / N times / Forever
- **Start hotkey** (default F7) and **Stop hotkey** (default F8) — work globally
- 💾 Save macros and 📂 reload them later (stored in `%APPDATA%\MacroMaker\macros.json`)
- On Windows, playback uses the legacy `mouse_event` / `SetCursorPos` input path (like TinyTask), so it also works in games that ignore normal simulated input

## Emergency Stop

Move your mouse to the **top-left corner of your screen** — pyautogui's failsafe will immediately halt all automation.

## Hotkey Reference (defaults)

| Hotkey | Action |
|--------|--------|
| F6 | Toggle Auto Clicker on/off |
| F7 | Start Macro |
| F8 | Stop Macro |
| F9 | Start / stop recording |

All hotkeys are configurable from the app UI.

## Changelog

- **1.3** — Macro recorder (F9), Win32 legacy input for playback, smoother cursor movement
- **1.2** — Bug fixes
- **1.1** — Bug fixes
- **1.0** — First release
