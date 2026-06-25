# Macro Maker — Desktop

Auto clicker & macro tool with global F-key hotkeys.

## Setup (one time)

```bash
pip install -r requirements.txt
```

> **macOS only:** Go to System Settings → Privacy & Security → Accessibility and add your Terminal (or Python) to the allowed list. Same for Screen Recording if you use the position picker.

> **Linux only:** `pip install python3-xlib` may also be needed.

## Run

```bash
python main.py
```

## Features

### Auto Clicker
- Set click interval (ms) with presets or custom value
- **Follow cursor** — clicks wherever your mouse is
- **Fixed position** — click 📍 Pick then click anywhere on screen to capture coordinates
- Left / Right / Middle mouse button
- Repeat forever or stop after N clicks
- **Toggle hotkey** (default F6) — works while you're in any other window

### Macro Maker
- Build sequences of: Mouse Click, Mouse Move, Key Press, Delay, Scroll
- 📍 Pick position by clicking anywhere on screen for any step
- Reorder steps with ↑ ↓ buttons, double-click to edit
- Repeat: Once / N times / Forever
- **Start hotkey** (default F7) and **Stop hotkey** (default F8) — work globally
- 💾 Save macro to `macros.json` and 📂 reload it later

## Emergency Stop

Move your mouse to the **top-left corner of your screen** — pyautogui's failsafe will immediately halt all automation.

## Hotkey Reference (defaults)

| Hotkey | Action |
|--------|--------|
| F6 | Toggle Auto Clicker on/off |
| F7 | Start Macro |
| F8 | Stop Macro |

All hotkeys are configurable from the app UI.
