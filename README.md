# Macro Maker — Desktop

Auto clicker, macro tool and mouse jiggler for Windows with global F-key hotkeys. Record your actions or build a macro step by step, then replay it from any window.

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
- Repeat: Once / N times / Forever, with an optional **wait between repeats** (e.g. run, wait 30 s, run again)
- **Playback speed** (0.25× – 4×) and optional **random timing variation** (±5–30 %) so repeats look less robotic
- **Start hotkey** (default F7) and **Stop hotkey** (default F8) — work globally
- 💾 Save macros and 📂 reload them later (stored in `%APPDATA%\MacroMaker\macros.json`)
- On Windows, playback uses the legacy `mouse_event` / `SetCursorPos` input path (like TinyTask), so it also works in games that ignore normal simulated input

### Mouse Jiggler
- Nudges the mouse a few pixels and straight back, so your PC doesn't sleep and games like Roblox don't kick you for being idle
- Simple on/off button, no hotkey needed
- Jiggle every 10 s – 5 min (or any custom number of seconds), distance 1–25 px
- **Only when idle** (on by default) — pauses while you're using the mouse or keyboard yourself
- While on, Windows is told not to sleep or turn off the screen

### Runs in the system tray
- Clicking **X** or minimising hides Macro Maker to the system tray (the **^** next to the clock) instead of quitting — hotkeys, the auto clicker, macros and the jiggler keep running
- **Left-click** the tray icon to bring the window back
- **Right-click** for a menu: open, turn the Auto Clicker / Mouse Jiggler on or off, or **Quit**

### Settings page
- **Start with Windows** — opens quietly in the tray when you log in
- **Close button hides to tray** — turn off if you'd rather the X quits
- **Theme** — follow Windows, or always Light / Dark (Windows 11 colours)
- **Automatic updates** — checks GitHub on start; when a new version is out a button appears in the title bar and **Update now** downloads it and restarts the app in place (your taskbar pin keeps working)
- Quick links to the data folder (macros, settings, error log) and GitHub

### Quality of life
- **Remembers your settings** (intervals, hotkeys, repeat options, last open page…) in `%APPDATA%\MacroMaker\settings.json`
- **Only one copy runs at a time** — launching it again just brings the existing window back from the tray
- **Error log** at `%APPDATA%\MacroMaker\error.log` — if something goes wrong, that file says what happened

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

- **1.8** — Settings page: start with Windows, light/dark theme, close-to-tray option, automatic updates
- **1.7** — Wait between repeats, playback speed & timing variation, remembers settings, single instance, error log
- **1.6** — Same ⚡ icon for the .exe, window, taskbar (also when pinned) and tray
- **1.5** — Runs in the system tray when closed or minimised
- **1.4** — Mouse Jiggler page
- **1.3** — Macro recorder (F9), Win32 legacy input for playback, smoother cursor movement
- **1.2** — Bug fixes
- **1.1** — Bug fixes
- **1.0** — First release

## Releasing a new version

Bump the number in `VERSION` (and the changelog above) and push to `main`. GitHub Actions builds `MacroMaker.exe` and publishes the release automatically.
