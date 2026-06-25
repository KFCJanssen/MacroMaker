"""
Macro Maker — Desktop Auto Clicker & Macro Tool
Run: python main.py
Requires: pip install customtkinter pyautogui pynput
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os

from auto_clicker import AutoClicker
from macro_runner import MacroRunner, MacroStep
from hotkeys import HotkeyManager, AVAILABLE_KEYS

# ── Windows 10 Dark Mode Theme ────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#202020"   # window background
NAV     = "#2B2B2B"   # sidebar / nav panel
CARD    = "#2B2B2B"   # card / input background
HOVER   = "#333333"   # hover state
BORDER  = "#3A3A3A"   # separator / border
PRIMARY = "#0078D4"   # Windows blue accent
MUTED   = "#8A8A8A"   # secondary text
DANGER  = "#D13438"   # stop / destructive
FG      = "#FFFFFF"   # primary text
ACTIVE  = "#107C10"   # running / success green
SEG_FG  = "#CCCCCC"   # unselected tab text

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_NAV   = ("Segoe UI", 13)
FONT_H     = ("Segoe UI", 13, "bold")
FONT_M     = ("Segoe UI", 12)
FONT_S     = ("Segoe UI", 11)
FONT_XS    = ("Segoe UI", 10)
FONT_SEC   = ("Segoe UI", 10, "bold")

SAVE_FILE = os.path.join(os.path.dirname(__file__), "macros.json")


# ── Utilities ─────────────────────────────────────────────────────────────────
def pick_position(root, callback):
    """Minimize window, let user click anywhere, capture position."""
    root.iconify()
    root.update()

    def on_click(x, y, button, pressed):
        if pressed:
            listener.stop()
            root.after(200, lambda: root.deiconify())
            root.after(300, lambda: callback(x, y))

    from pynput import mouse as pmouse
    listener = pmouse.Listener(on_click=on_click)
    listener.daemon = True
    listener.start()


# ── Reusable widgets ──────────────────────────────────────────────────────────
def section_label(master, text):
    """Windows 10 style blue section header."""
    ctk.CTkLabel(master, text=text.upper(), font=FONT_SEC,
                 text_color=PRIMARY).pack(anchor="w", padx=24, pady=(20, 4))


def separator(master):
    ctk.CTkFrame(master, height=1, fg_color=BORDER).pack(
        fill="x", padx=24, pady=8)


class SettingsRow(ctk.CTkFrame):
    """A settings-style row: label + description on left, widget on right."""
    def __init__(self, master, label, description="", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text=label, font=FONT_M,
                     text_color=FG, anchor="w").pack(anchor="w")
        if description:
            ctk.CTkLabel(left, text=description, font=FONT_XS,
                         text_color=MUTED, anchor="w").pack(anchor="w")

    def add_widget(self, widget):
        widget.pack(side="right", padx=(12, 0))


class W10Toggle(ctk.CTkSwitch):
    """Pre-styled toggle switch."""
    def __init__(self, master, **kwargs):
        super().__init__(master,
                         text="",
                         width=46,
                         button_color=FG,
                         button_hover_color="#E0E0E0",
                         progress_color=PRIMARY,
                         fg_color=BORDER,
                         **kwargs)


class StatusBadge(ctk.CTkFrame):
    """Small status indicator pill."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=CARD, corner_radius=4,
                         border_width=1, border_color=BORDER, **kwargs)
        self._dot = ctk.CTkLabel(self, text="●", font=("Segoe UI", 9),
                                  text_color=MUTED, width=14)
        self._dot.pack(side="left", padx=(8, 3), pady=5)
        self._label = ctk.CTkLabel(self, text="Stopped", font=FONT_XS,
                                    text_color=MUTED)
        self._label.pack(side="left", padx=(0, 10), pady=5)

    def set_running(self, running: bool, text="Running"):
        color = ACTIVE if running else MUTED
        self._dot.configure(text_color=color)
        self._label.configure(text=text if running else "Stopped",
                              text_color=color)


# ─────────────────────────────────────────────────────────────────────────────
#  AUTO CLICKER PANEL
# ─────────────────────────────────────────────────────────────────────────────
class AutoClickerPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, hotkey_mgr: HotkeyManager, **kwargs):
        super().__init__(master, fg_color="transparent",
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=HOVER, **kwargs)
        self._hk = hotkey_mgr
        self._clicker = AutoClicker(on_status_change=self._on_status)
        self._hotkey_key = "f6"
        self._build_ui()
        self._rebind_hotkey()

    def _build_ui(self):
        # Title
        ctk.CTkLabel(self, text="Auto Clicker", font=FONT_TITLE,
                     text_color=FG).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self,
                     text="Automatically click at a set interval. "
                          "Use the hotkey to toggle from any window.",
                     font=FONT_S, text_color=MUTED,
                     wraplength=520, justify="left").pack(
            anchor="w", padx=24, pady=(0, 4))

        separator(self)

        # ── INTERVAL ──────────────────────────────────────────────────────────
        section_label(self, "Interval")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(0, 8))
        self._interval_var = tk.StringVar(value="1000")
        ctk.CTkLabel(row, text="Click interval", font=FONT_M,
                     text_color=FG).pack(side="left")
        ctk.CTkLabel(row, text="How long to wait between each click",
                     font=FONT_XS, text_color=MUTED).pack(side="left", padx=8)
        ctk.CTkEntry(row, textvariable=self._interval_var, width=80,
                     fg_color=CARD, border_color=BORDER,
                     font=FONT_M).pack(side="right")
        ctk.CTkLabel(row, text="ms", font=FONT_S,
                     text_color=MUTED).pack(side="right", padx=4)

        chip_row = ctk.CTkFrame(self, fg_color="transparent")
        chip_row.pack(anchor="w", padx=24, pady=(0, 4))
        for ms in [100, 250, 500, 1000, 2000, 5000]:
            ctk.CTkButton(chip_row, text=f"{ms}ms", width=60, height=28,
                          font=FONT_S, fg_color=CARD, hover_color=HOVER,
                          border_width=1, border_color=BORDER,
                          command=lambda v=ms: self._interval_var.set(str(v))
                          ).pack(side="left", padx=(0, 6))

        separator(self)

        # ── LOCATION ──────────────────────────────────────────────────────────
        section_label(self, "Location")

        self._follow_var = tk.BooleanVar(value=True)
        self._fixed_var  = tk.BooleanVar(value=False)

        follow_row = SettingsRow(self, "Follow cursor",
                                 "Click wherever the mouse currently is")
        follow_row.pack(fill="x", padx=24, pady=(0, 2))
        self._follow_toggle = W10Toggle(follow_row,
                                        variable=self._follow_var,
                                        command=self._on_follow_toggle)
        follow_row.add_widget(self._follow_toggle)

        fixed_row = SettingsRow(self, "Fixed position",
                                "Always click the same coordinates")
        fixed_row.pack(fill="x", padx=24, pady=(0, 2))
        self._fixed_toggle = W10Toggle(fixed_row,
                                       variable=self._fixed_var,
                                       command=self._on_fixed_toggle)
        fixed_row.add_widget(self._fixed_toggle)

        pos_row = ctk.CTkFrame(self, fg_color="transparent")
        pos_row.pack(anchor="w", padx=24, pady=(4, 4))
        ctk.CTkLabel(pos_row, text="X:", font=FONT_M,
                     text_color=MUTED).pack(side="left")
        self._x_var = tk.StringVar(value="500")
        self._x_entry = ctk.CTkEntry(pos_row, textvariable=self._x_var,
                                      width=72, fg_color=CARD,
                                      border_color=BORDER)
        self._x_entry.pack(side="left", padx=(4, 14))
        ctk.CTkLabel(pos_row, text="Y:", font=FONT_M,
                     text_color=MUTED).pack(side="left")
        self._y_var = tk.StringVar(value="500")
        self._y_entry = ctk.CTkEntry(pos_row, textvariable=self._y_var,
                                      width=72, fg_color=CARD,
                                      border_color=BORDER)
        self._y_entry.pack(side="left", padx=(4, 14))
        self._pick_btn = ctk.CTkButton(pos_row, text="📍 Pick", width=72,
                                        height=30, font=FONT_S,
                                        fg_color=CARD, hover_color=HOVER,
                                        border_width=1, border_color=PRIMARY,
                                        command=self._pick_position)
        self._pick_btn.pack(side="left")
        self._on_follow_toggle()

        separator(self)

        # ── BUTTON ────────────────────────────────────────────────────────────
        section_label(self, "Button")

        btn_row = SettingsRow(self, "Mouse button",
                              "Which button to click")
        btn_row.pack(fill="x", padx=24, pady=(0, 4))
        self._btn_var = tk.StringVar(value="left")
        rb_frame = ctk.CTkFrame(btn_row, fg_color="transparent")
        for label, val in [("Left", "left"), ("Right", "right"), ("Middle", "middle")]:
            ctk.CTkRadioButton(rb_frame, text=label, variable=self._btn_var,
                               value=val, font=FONT_M).pack(side="left",
                                                              padx=(0, 14))
        btn_row.add_widget(rb_frame)

        separator(self)

        # ── REPEAT ────────────────────────────────────────────────────────────
        section_label(self, "Repeat")

        self._loop_var = tk.BooleanVar(value=True)
        loop_row = SettingsRow(self, "Loop forever",
                               "Keep clicking until manually stopped")
        loop_row.pack(fill="x", padx=24, pady=(0, 2))
        self._loop_toggle = W10Toggle(loop_row, variable=self._loop_var,
                                      command=self._on_loop_toggle)
        loop_row.add_widget(self._loop_toggle)

        count_row = ctk.CTkFrame(self, fg_color="transparent")
        count_row.pack(anchor="w", padx=24, pady=(4, 4))
        ctk.CTkLabel(count_row, text="Stop after:", font=FONT_M,
                     text_color=MUTED).pack(side="left")
        self._count_var = tk.StringVar(value="10")
        self._count_entry = ctk.CTkEntry(count_row, textvariable=self._count_var,
                                          width=60, fg_color=CARD,
                                          border_color=BORDER)
        self._count_entry.pack(side="left", padx=8)
        ctk.CTkLabel(count_row, text="clicks", font=FONT_S,
                     text_color=MUTED).pack(side="left")
        self._on_loop_toggle()

        separator(self)

        # ── HOTKEY ────────────────────────────────────────────────────────────
        section_label(self, "Hotkey")

        hk_row = SettingsRow(self, "Toggle hotkey",
                             "Press this key to start/stop from any window")
        hk_row.pack(fill="x", padx=24, pady=(0, 4))
        self._hk_var = tk.StringVar(value="F6")
        hk_menu = ctk.CTkOptionMenu(hk_row, variable=self._hk_var,
                                     values=[k.upper() for k in AVAILABLE_KEYS],
                                     width=80, font=FONT_M,
                                     fg_color=CARD,
                                     button_color=BORDER,
                                     button_hover_color=HOVER,
                                     command=self._on_hotkey_change)
        hk_row.add_widget(hk_menu)

        separator(self)

        # ── CONTROLS ──────────────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=24, pady=(4, 24))
        self._toggle_btn = ctk.CTkButton(
            ctrl, text="▶   Start", font=FONT_H, height=44,
            fg_color=PRIMARY, hover_color="#006CBE",
            command=self._toggle)
        self._toggle_btn.pack(side="left", fill="x", expand=True)
        self._status = StatusBadge(ctrl)
        self._status.pack(side="left", padx=(12, 0))

    # ── Handlers ──────────────────────────────────────────────────────────────
    def _on_follow_toggle(self):
        if self._follow_var.get():
            self._fixed_var.set(False)
        self._update_pos_state()

    def _on_fixed_toggle(self):
        if self._fixed_var.get():
            self._follow_var.set(False)
        else:
            self._follow_var.set(True)
        self._update_pos_state()

    def _update_pos_state(self):
        fixed = self._fixed_var.get()
        state = "normal" if fixed else "disabled"
        self._x_entry.configure(state=state)
        self._y_entry.configure(state=state)
        self._pick_btn.configure(state=state)

    def _on_loop_toggle(self):
        state = "disabled" if self._loop_var.get() else "normal"
        self._count_entry.configure(state=state)

    def _pick_position(self):
        root = self.winfo_toplevel()
        def got(x, y):
            self._x_var.set(str(x))
            self._y_var.set(str(y))
        pick_position(root, got)

    def _on_hotkey_change(self, val):
        self._rebind_hotkey()

    def _rebind_hotkey(self):
        self._hk.unbind(self._hotkey_key)
        self._hotkey_key = self._hk_var.get().lower()
        self._hk.bind(self._hotkey_key, self._toggle)

    def _apply_settings(self):
        try:
            interval = int(self._interval_var.get())
        except ValueError:
            interval = 1000
        self._clicker.interval_ms   = max(10, interval)
        self._clicker.use_cursor    = not self._fixed_var.get()
        try:
            self._clicker.fixed_x = int(self._x_var.get())
            self._clicker.fixed_y = int(self._y_var.get())
        except ValueError:
            pass
        self._clicker.button        = self._btn_var.get()
        self._clicker.repeat_forever = self._loop_var.get()
        try:
            self._clicker.repeat_count = int(self._count_var.get())
        except ValueError:
            self._clicker.repeat_count = 10

    def _toggle(self):
        if self._clicker.running:
            self._clicker.stop()
        else:
            self._apply_settings()
            self._clicker.start()

    def _on_status(self, running: bool):
        self.after(0, lambda: self._status.set_running(running))
        self.after(0, lambda: self._toggle_btn.configure(
            text="⏹   Stop" if running else "▶   Start",
            fg_color=DANGER if running else PRIMARY,
            hover_color="#B52F32" if running else "#006CBE",
        ))

    def cleanup(self):
        self._clicker.stop()
        self._hk.unbind(self._hotkey_key)


# ─────────────────────────────────────────────────────────────────────────────
#  ADD/EDIT STEP DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class AddStepDialog(ctk.CTkToplevel):
    def __init__(self, master, step=None, callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Edit Step" if step else "Add Step")
        self.geometry("440x460")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()
        self._callback = callback
        self._step = step
        self._build(step)

    def _build(self, step):
        ctk.CTkLabel(self, text="Step Type", font=FONT_M,
                     text_color=MUTED).pack(anchor="w", padx=20, pady=(16, 0))
        self._type_var = tk.StringVar(value=step.type if step else "click")
        types = [("Mouse Click", "click"), ("Mouse Move", "move"),
                 ("Key Press", "keypress"), ("Delay", "delay"),
                 ("Scroll", "scroll")]
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=4)
        for label, val in types:
            ctk.CTkRadioButton(row, text=label, variable=self._type_var,
                               value=val, font=FONT_S,
                               command=self._update_fields).pack(
                side="left", padx=(0, 10))

        self._fields_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._fields_frame.pack(fill="x", padx=20, pady=8)

        self._x_var   = tk.StringVar(value=str(step.data.get("x", 500)) if step else "500")
        self._y_var   = tk.StringVar(value=str(step.data.get("y", 500)) if step else "500")
        self._btn_var = tk.StringVar(value=step.data.get("button", "left") if step else "left")
        self._keys_var = tk.StringVar(value=step.data.get("keys", "") if step else "")
        self._dur_var = tk.StringVar(value=str(step.data.get("duration_ms", 50)) if step else "50")
        self._ms_var  = tk.StringVar(value=str(step.data.get("ms", 500)) if step else "500")
        self._dir_var = tk.StringVar(value=step.data.get("direction", "up") if step else "up")
        self._amt_var = tk.StringVar(value=str(step.data.get("amount", 3)) if step else "3")

        self._update_fields()

        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=10)
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(btn_row, text="Cancel", fg_color=CARD, hover_color=HOVER,
                      font=FONT_M, command=self.destroy).pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(btn_row, text="Save Step", fg_color=PRIMARY,
                      hover_color="#006CBE", font=FONT_M,
                      command=self._save).pack(side="left", fill="x", expand=True)

    def _clear_fields(self):
        for w in self._fields_frame.winfo_children():
            w.destroy()

    def _lbl(self, text):
        ctk.CTkLabel(self._fields_frame, text=text, font=FONT_S,
                     text_color=MUTED).pack(anchor="w")

    def _update_fields(self):
        self._clear_fields()
        t = self._type_var.get()

        if t in ("click", "move", "scroll"):
            self._lbl("Position")
            pos = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            pos.pack(fill="x", pady=4)
            ctk.CTkLabel(pos, text="X:", font=FONT_M,
                         text_color=MUTED).pack(side="left")
            ctk.CTkEntry(pos, textvariable=self._x_var, width=70,
                         fg_color=CARD, border_color=BORDER).pack(
                side="left", padx=(4, 12))
            ctk.CTkLabel(pos, text="Y:", font=FONT_M,
                         text_color=MUTED).pack(side="left")
            ctk.CTkEntry(pos, textvariable=self._y_var, width=70,
                         fg_color=CARD, border_color=BORDER).pack(
                side="left", padx=(4, 12))
            ctk.CTkButton(pos, text="📍 Pick", width=70, height=28,
                          font=FONT_S, fg_color=CARD, hover_color=HOVER,
                          border_width=1, border_color=PRIMARY,
                          command=self._pick).pack(side="left")

        if t == "click":
            self._lbl("Mouse Button")
            br = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            br.pack(fill="x", pady=4)
            for label, val in [("Left", "left"), ("Right", "right"),
                                ("Middle", "middle")]:
                ctk.CTkRadioButton(br, text=label, variable=self._btn_var,
                                   value=val, font=FONT_S).pack(
                    side="left", padx=(0, 12))

        if t == "keypress":
            self._lbl("Key(s) — use + for combos: ctrl+c, alt+f4, enter…")
            ctk.CTkEntry(self._fields_frame, textvariable=self._keys_var,
                         width=260, fg_color=CARD,
                         border_color=BORDER).pack(anchor="w", pady=4)
            self._lbl("Hold duration (ms) — how long the key stays pressed")
            dur_row = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            dur_row.pack(fill="x", pady=4)
            ctk.CTkEntry(dur_row, textvariable=self._dur_var, width=80,
                         fg_color=CARD, border_color=BORDER).pack(side="left")
            for v in [30, 50, 100, 200, 500]:
                ctk.CTkButton(dur_row, text=str(v), width=46, height=26,
                              font=FONT_S, fg_color=CARD, hover_color=HOVER,
                              border_width=1, border_color=BORDER,
                              command=lambda x=v: self._dur_var.set(str(x))
                              ).pack(side="left", padx=3)

        if t == "delay":
            self._lbl("Duration (ms)")
            row = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkEntry(row, textvariable=self._ms_var, width=80,
                         fg_color=CARD, border_color=BORDER).pack(side="left")
            for v in [100, 250, 500, 1000, 2000]:
                ctk.CTkButton(row, text=str(v), width=46, height=26,
                              font=FONT_S, fg_color=CARD, hover_color=HOVER,
                              border_width=1, border_color=BORDER,
                              command=lambda x=v: self._ms_var.set(str(x))
                              ).pack(side="left", padx=3)

        if t == "scroll":
            self._lbl("Direction & Amount")
            sr = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            sr.pack(fill="x", pady=4)
            ctk.CTkRadioButton(sr, text="Up", variable=self._dir_var,
                               value="up", font=FONT_S).pack(side="left")
            ctk.CTkRadioButton(sr, text="Down", variable=self._dir_var,
                               value="down", font=FONT_S).pack(
                side="left", padx=12)
            ctk.CTkEntry(sr, textvariable=self._amt_var, width=50,
                         fg_color=CARD, border_color=BORDER).pack(side="left")
            ctk.CTkLabel(sr, text="clicks", font=FONT_S,
                         text_color=MUTED).pack(side="left", padx=6)

    def _pick(self):
        root = self.winfo_toplevel()

        def got(x, y):
            self._x_var.set(str(x))
            self._y_var.set(str(y))
            self.deiconify()

        root.iconify()
        self.iconify()
        root.update()
        from pynput import mouse as pmouse

        def on_click(x, y, button, pressed):
            if pressed:
                listener.stop()
                self.after(200, lambda: got(x, y))

        listener = pmouse.Listener(on_click=on_click)
        listener.daemon = True
        listener.start()

    def _save(self):
        t = self._type_var.get()
        try:
            data = {}
            if t in ("click", "move", "scroll"):
                data["x"] = int(self._x_var.get())
                data["y"] = int(self._y_var.get())
            if t == "click":
                data["button"] = self._btn_var.get()
            if t == "keypress":
                data["keys"] = self._keys_var.get().strip()
                try:
                    data["duration_ms"] = max(0, int(self._dur_var.get()))
                except ValueError:
                    data["duration_ms"] = 50
            if t == "delay":
                data["ms"] = int(self._ms_var.get())
            if t == "scroll":
                data["direction"] = self._dir_var.get()
                data["amount"]    = int(self._amt_var.get())
            step = MacroStep(t, **data)
            if self._callback:
                self._callback(step)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  MACRO PANEL
# ─────────────────────────────────────────────────────────────────────────────
class MacroPanel(ctk.CTkFrame):
    def __init__(self, master, hotkey_mgr: HotkeyManager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._hk = hotkey_mgr
        self._runner = MacroRunner(
            on_status_change=self._on_status,
            on_step_change=self._on_step,
        )
        self._steps: list[MacroStep] = []
        self._start_hk = "f7"
        self._stop_hk  = "f8"
        self._editing_index = None
        self._build_ui()
        self._rebind_hotkeys()
        self._load_macros()

    def _build_ui(self):
        # Title + toolbar
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(hdr, text="Macro Maker", font=FONT_TITLE,
                     text_color=FG).pack(side="left")
        for label, cmd in [
            ("🗑 Clear", self._clear_steps),
            ("📂 Load", self._load_preset),
            ("💾 Save", self._save_preset),
        ]:
            ctk.CTkButton(hdr, text=label, width=80, height=30, font=FONT_S,
                          fg_color=CARD, hover_color=HOVER, border_width=1,
                          border_color=BORDER, command=cmd).pack(
                side="right", padx=(6, 0))

        ctk.CTkLabel(self,
                     text="Record a sequence of actions, then replay with a hotkey.",
                     font=FONT_S, text_color=MUTED).pack(
            anchor="w", padx=24, pady=(0, 4))

        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=24, pady=8)

        # Steps list
        section_label(self, "Steps")
        list_outer = ctk.CTkFrame(self, fg_color=CARD, corner_radius=6,
                                   border_width=1, border_color=BORDER)
        list_outer.pack(fill="both", expand=True, padx=24, pady=(4, 0))

        self._listbox = tk.Listbox(
            list_outer,
            bg=CARD, fg=FG,
            selectbackground=PRIMARY, selectforeground=FG,
            font=("Courier New", 11),
            relief="flat", bd=0, highlightthickness=0, activestyle="none",
        )
        sb = tk.Scrollbar(list_outer, orient="vertical",
                          command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self._listbox.pack(fill="both", expand=True, padx=2, pady=2)
        self._listbox.bind("<Double-Button-1>", lambda e: self._edit_step())

        # Add step buttons
        add_row = ctk.CTkFrame(self, fg_color="transparent")
        add_row.pack(fill="x", padx=24, pady=(6, 0))
        for label, t in [
            ("+ Click", "click"), ("+ Key", "keypress"),
            ("+ Delay", "delay"), ("+ Move", "move"), ("+ Scroll", "scroll"),
        ]:
            ctk.CTkButton(add_row, text=label, width=74, height=30, font=FONT_S,
                          fg_color=CARD, hover_color=HOVER, border_width=1,
                          border_color=BORDER,
                          command=lambda x=t: self._add_step(x)).pack(
                side="left", padx=(0, 6))

        # Edit/delete/reorder
        edit_row = ctk.CTkFrame(self, fg_color="transparent")
        edit_row.pack(fill="x", padx=24, pady=(4, 0))
        for label, cmd in [
            ("✎ Edit", self._edit_step),
            ("✕ Delete", self._delete_step),
            ("↑ Up", lambda: self._move_step(-1)),
            ("↓ Down", lambda: self._move_step(1)),
        ]:
            ctk.CTkButton(edit_row, text=label, width=74, height=28,
                          font=FONT_S, fg_color=CARD, hover_color=HOVER,
                          border_width=1, border_color=BORDER,
                          command=cmd).pack(side="left", padx=(0, 6))

        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=24, pady=10)

        # Repeat
        section_label(self, "Repeat")
        rep = ctk.CTkFrame(self, fg_color="transparent")
        rep.pack(fill="x", padx=24, pady=(0, 4))
        self._repeat_var = tk.StringVar(value="once")
        for label, val in [("Once", "once"), ("N times", "count"),
                            ("Forever", "forever")]:
            ctk.CTkRadioButton(rep, text=label, variable=self._repeat_var,
                               value=val, font=FONT_M,
                               command=self._on_repeat_change).pack(
                side="left", padx=(0, 16))
        self._rep_n_var = tk.StringVar(value="5")
        self._rep_n_entry = ctk.CTkEntry(rep, textvariable=self._rep_n_var,
                                          width=55, fg_color=CARD,
                                          border_color=BORDER)
        self._rep_n_entry.pack(side="left")
        ctk.CTkLabel(rep, text="times", font=FONT_S,
                     text_color=MUTED).pack(side="left", padx=6)
        self._on_repeat_change()

        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=24, pady=10)

        # Hotkeys
        section_label(self, "Hotkeys")
        hk = ctk.CTkFrame(self, fg_color="transparent")
        hk.pack(fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(hk, text="Start:", font=FONT_M,
                     text_color=MUTED).pack(side="left")
        self._start_hk_var = tk.StringVar(value="F7")
        ctk.CTkOptionMenu(hk, variable=self._start_hk_var, width=80,
                          values=[k.upper() for k in AVAILABLE_KEYS],
                          font=FONT_M, fg_color=CARD, button_color=BORDER,
                          button_hover_color=HOVER,
                          command=self._on_hotkeys_change).pack(
            side="left", padx=(6, 18))
        ctk.CTkLabel(hk, text="Stop:", font=FONT_M,
                     text_color=MUTED).pack(side="left")
        self._stop_hk_var = tk.StringVar(value="F8")
        ctk.CTkOptionMenu(hk, variable=self._stop_hk_var, width=80,
                          values=[k.upper() for k in AVAILABLE_KEYS],
                          font=FONT_M, fg_color=CARD, button_color=BORDER,
                          button_hover_color=HOVER,
                          command=self._on_hotkeys_change).pack(
            side="left", padx=(6, 10))
        ctk.CTkLabel(hk, text="(work in other windows)", font=FONT_XS,
                     text_color=MUTED).pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=24, pady=10)

        # Controls
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=24, pady=(0, 20))
        self._run_btn = ctk.CTkButton(
            ctrl, text="▶   Run Macro", font=FONT_H, height=44,
            fg_color=PRIMARY, hover_color="#006CBE", command=self._toggle)
        self._run_btn.pack(side="left", fill="x", expand=True)
        self._status = StatusBadge(ctrl)
        self._status.pack(side="left", padx=(12, 0))

    # ── Step management ───────────────────────────────────────────────────────
    def _refresh_list(self):
        self._listbox.delete(0, "end")
        for i, step in enumerate(self._steps):
            self._listbox.insert("end", f"  {i+1:>2}.  {step.label()}")
        self._runner.steps = self._steps

    def _default_data(self, t):
        if t == "click":    return {"x": 500, "y": 500, "button": "left"}
        if t == "move":     return {"x": 500, "y": 500}
        if t == "keypress": return {"keys": "", "duration_ms": 50}
        if t == "delay":    return {"ms": 500}
        if t == "scroll":   return {"x": 500, "y": 500, "direction": "up", "amount": 3}
        return {}

    def _add_step(self, step_type):
        self._editing_index = None
        AddStepDialog(self, step=MacroStep(step_type, **self._default_data(step_type)),
                      callback=self._on_step_saved)

    def _on_step_saved(self, step):
        sel = self._listbox.curselection()
        if self._editing_index is not None:
            self._steps[self._editing_index] = step
            self._editing_index = None
        else:
            idx = sel[0] + 1 if sel else len(self._steps)
            self._steps.insert(idx, step)
        self._refresh_list()

    def _edit_step(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        self._editing_index = sel[0]
        AddStepDialog(self, step=self._steps[sel[0]],
                      callback=self._on_step_saved)

    def _delete_step(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self._steps.pop(idx)
        self._refresh_list()
        if self._steps:
            self._listbox.selection_set(max(0, idx - 1))

    def _move_step(self, direction: int):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx     = sel[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self._steps):
            self._steps[idx], self._steps[new_idx] = (
                self._steps[new_idx], self._steps[idx])
            self._refresh_list()
            self._listbox.selection_set(new_idx)

    def _clear_steps(self):
        if messagebox.askyesno("Clear", "Remove all steps?"):
            self._steps.clear()
            self._refresh_list()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load_macros(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f:
                    data = json.load(f)
                if "steps" in data:
                    self._steps = [MacroStep.from_dict(s) for s in data["steps"]]
                    self._refresh_list()
            except Exception:
                pass

    def _save_preset(self):
        data = {"steps": [s.to_dict() for s in self._steps]}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", "Macro saved to macros.json")

    def _load_preset(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f:
                    data = json.load(f)
                if "steps" in data:
                    self._steps = [MacroStep.from_dict(s) for s in data["steps"]]
                    self._refresh_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showinfo("Load", "No saved macro found.")

    # ── Controls ──────────────────────────────────────────────────────────────
    def _on_repeat_change(self):
        state = "normal" if self._repeat_var.get() == "count" else "disabled"
        self._rep_n_entry.configure(state=state)

    def _on_hotkeys_change(self, _=None):
        self._rebind_hotkeys()

    def _rebind_hotkeys(self):
        self._hk.unbind(self._start_hk)
        if self._stop_hk != self._start_hk:
            self._hk.unbind(self._stop_hk)
        self._start_hk = self._start_hk_var.get().lower()
        self._stop_hk  = self._stop_hk_var.get().lower()
        self._hk.bind(self._start_hk, self._start_macro)
        if self._stop_hk != self._start_hk:
            self._hk.bind(self._stop_hk, self._stop_macro)

    def _apply_settings(self):
        self._runner.steps = self._steps
        self._runner.repeat_mode = self._repeat_var.get()
        try:
            self._runner.repeat_count = int(self._rep_n_var.get())
        except ValueError:
            self._runner.repeat_count = 1

    def _toggle(self):
        if self._runner.running:
            self._stop_macro()
        else:
            self._start_macro()

    def _start_macro(self):
        if not self._steps:
            messagebox.showwarning("No Steps", "Add steps before running.")
            return
        self._apply_settings()
        self._runner.start()

    def _stop_macro(self):
        self._runner.stop()

    def _on_status(self, running: bool):
        self.after(0, lambda: self._status.set_running(running))
        self.after(0, lambda: self._run_btn.configure(
            text="⏹   Stop Macro" if running else "▶   Run Macro",
            fg_color=DANGER if running else PRIMARY,
            hover_color="#B52F32" if running else "#006CBE",
        ))

    def _on_step(self, idx: int):
        def _do():
            self._listbox.selection_clear(0, "end")
            if idx >= 0:
                self._listbox.selection_set(idx)
                self._listbox.see(idx)
        self.after(0, _do)

    def cleanup(self):
        self._runner.stop()
        self._hk.unbind(self._start_hk)
        if self._stop_hk != self._start_hk:
            self._hk.unbind(self._stop_hk)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN WINDOW  — Windows 10 Settings style with left nav sidebar
# ─────────────────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Macro Maker")
        self.geometry("860x720")
        self.minsize(720, 560)
        self.configure(fg_color=BG)

        self._hk = HotkeyManager()
        self._hk.start()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # ── Title bar area ────────────────────────────────────────────────────
        title_bar = ctk.CTkFrame(self, fg_color=BG, height=50, corner_radius=0)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        ctk.CTkLabel(title_bar, text="⚡  Macro Maker", font=("Segoe UI", 15),
                     text_color=FG).pack(side="left", padx=20, pady=14)

        # ── Body: nav sidebar + content ───────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Left nav
        nav = ctk.CTkFrame(body, fg_color=NAV, width=200, corner_radius=0)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text="⚡ Macro Maker", font=("Segoe UI", 13, "bold"),
                     text_color=FG).pack(anchor="w", padx=16, pady=(20, 4))
        ctk.CTkLabel(nav, text="v1.0", font=FONT_XS,
                     text_color=MUTED).pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkFrame(nav, height=1, fg_color=BORDER).pack(
            fill="x", padx=8, pady=4)

        self._nav_btns: list[ctk.CTkButton] = []

        for icon, label in [("🖱", "Auto Clicker"), ("⌨", "Macro Maker")]:
            btn = ctk.CTkButton(
                nav,
                text=f"  {icon}  {label}",
                font=FONT_NAV,
                anchor="w",
                fg_color="transparent",
                hover_color=HOVER,
                text_color=FG,
                height=40,
                corner_radius=4,
                command=lambda lbl=label: self._select_nav(lbl),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns.append(btn)

        # Right content area
        self._content = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        # Build both panels, hide one
        self._hk_mgr = self._hk
        self._ac_panel = AutoClickerPanel(self._content, self._hk_mgr)
        self._macro_panel = MacroPanel(self._content, self._hk_mgr)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=NAV, corner_radius=0, height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        ctk.CTkLabel(footer,
                     text="Move mouse to top-left corner for emergency stop  |  "
                          "macros.json auto-saves in app folder",
                     font=("Segoe UI", 9), text_color=MUTED).pack(pady=6)

        self._select_nav("Auto Clicker")

    def _select_nav(self, label: str):
        for btn in self._nav_btns:
            name = btn.cget("text").strip().split("  ", 1)[-1]
            if name == label:
                btn.configure(fg_color=PRIMARY, hover_color="#006CBE")
            else:
                btn.configure(fg_color="transparent", hover_color=HOVER)

        if label == "Auto Clicker":
            self._macro_panel.pack_forget()
            self._ac_panel.pack(fill="both", expand=True)
        else:
            self._ac_panel.pack_forget()
            self._macro_panel.pack(fill="both", expand=True)

    def _on_close(self):
        self._ac_panel.cleanup()
        self._macro_panel.cleanup()
        self._hk.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
