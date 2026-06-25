# MacroMaker | Windows Desktop Automation Tool 🚀

A modular, lightweight Python application designed to automate repetitive desktop tasks. This project features a high-performance **Auto-Clicker** and a customizable **Macro Runner**, all controlled seamlessly via global **Hotkeys**. 

It comes pre-packaged with convenient Windows batch scripts to install dependencies locally or compile the entire project into a standalone `.exe` file with a single click (also found in dits file).

---

## ✨ Features

* **Advanced Auto-Clicker:** High-frequency, reliable automated clicking.
* **Macro Runner:** Record and replay automated keyboard and mouse sequences.
* **Global Hotkeys:** Start, stop, or toggle features instantly from anywhere in Windows without needing to focus on the application window.
* **One-Click Setup:** Zero-friction installation using automated batch scripts.
* **Portable Executable:** Ready to be compiled into a standalone Windows `.exe` using PyInstaller.

---

## 📂 Project Structure

* **`main.py`** – The main entry point of the application.
* **`auto_clicker.py`** – Core logic governing mouse clicking operations.
* **`macro_runner.py`** – Core logic handling macro sequences and automation.
* **`hotkeys.py`** – Manages global keyboard shortcuts for toggling actions.
* **`requirements.txt`** – Lists necessary Python dependencies (e.g., `pynput`, `pyautogui`).
* **`install_and_run.bat`** – Automates setting up your Python environment and launching the app.
* **`build_exe.bat`** – Compiles the Python scripts into a standalone Windows executable (`.exe`).

---

## 🚀 Getting Started

### Option 1: Run via Python (For Developers)
If you want to run the application using Python on your machine:
1. Clone this repository to your local machine.
2. Double-click **`install_and_run.bat`**. This script will automatically install the required dependencies from `requirements.txt` and boot up the app.

### Option 2: Build the Standalone Executable (`.exe`)
If you want to distribute the app or run it without needing Python installed:
1. Double-click **`build_exe.bat`**.
2. Once the compilation finishes, look for the newly created `dist/` folder.
3. Your standalone application will be waiting inside as a single `.exe` file!

---

## 🛠️ Configuration & Customization

You can tweak the default settings, click rates, and macro configurations directly within the source files:
* Open `hotkeys.py` to change the default keybinds for triggering the clicker or macro runner.
* Open `auto_clicker.py` or `macro_runner.py` to adjust specific execution delays or click intervals.

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).
