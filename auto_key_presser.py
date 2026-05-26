"""
Auto Key Presser - Dark UI
===========================
pip install pynput
"""

import json, time, threading, sys, os, re
import random
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "config.json")

BG_MAIN      = "#0A0A0A"
BG_CARD      = "#141414"
BG_INPUT     = "#1F1F1F"
COLOR_BORDER = "#2A2A2A"
COLOR_ACCENT = "#888888"
COLOR_HOVER  = "#00C853"
COLOR_SUCCESS = "#00C853"
COLOR_DANGER  = "#FF3D00"
COLOR_TEXT   = "#FFFFFF"
COLOR_TEXT_MUTED = "#888888"
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_MAIN  = ("Segoe UI", 10)
FONT_SUB   = ("Segoe UI", 9)

CONTROL_H  = 1
GAP        = 6
CARD_PAD   = 10
LABEL_WIDTH = 8

SPECIAL_KEYS = {
    "space": Key.space, "enter": Key.enter, "tab": Key.tab,
    "backspace": Key.backspace, "delete": Key.delete,
    "escape": Key.esc, "esc": Key.esc,
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
    "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
    "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    "home": Key.home, "end": Key.end, "page_up": Key.page_up,
    "page_down": Key.page_down, "insert": Key.insert,
    "caps_lock": Key.caps_lock, "num_lock": Key.num_lock,
    "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt,
}

NUMPAD_KEYS = {
    "num": Key.num_lock,
    "numlock": Key.num_lock,
    "numpad_0": KeyCode.from_vk(96),
    "numpad_1": KeyCode.from_vk(97),
    "numpad_2": KeyCode.from_vk(98),
    "numpad_3": KeyCode.from_vk(99),
    "numpad_4": KeyCode.from_vk(100),
    "numpad_5": KeyCode.from_vk(101),
    "numpad_6": KeyCode.from_vk(102),
    "numpad_7": KeyCode.from_vk(103),
    "numpad_8": KeyCode.from_vk(104),
    "numpad_9": KeyCode.from_vk(105),
    "numpad_multiply": KeyCode.from_vk(106),
    "numpad_add": KeyCode.from_vk(107),
    "numpad_separator": KeyCode.from_vk(108),
    "numpad_subtract": KeyCode.from_vk(109),
    "numpad_decimal": KeyCode.from_vk(110),
    "numpad_divide": KeyCode.from_vk(111),
}

NUMPAD_VK_NAMES = {
    96: "numpad_0", 97: "numpad_1", 98: "numpad_2", 99: "numpad_3",
    100: "numpad_4", 101: "numpad_5", 102: "numpad_6", 103: "numpad_7",
    104: "numpad_8", 105: "numpad_9", 106: "numpad_multiply",
    107: "numpad_add", 108: "numpad_separator", 109: "numpad_subtract",
    110: "numpad_decimal", 111: "numpad_divide",
}

DEFAULT_CONFIG = {
    "start_stop_key": "numpad_decimal",
    "random_start_stop_key": "numpad_multiply",
    "key_set": {
        "name": "Key Set",
        "keys": ["1", "2", "3", "4"],
        "delay_ms": 100,
        "repeat_interval_sec": 30,
        "use_every": True,
        "repeat": "Infinity Mode"
    },
    "random_move": {
        "min_sec": 5,
        "max_sec": 20
    }
}

kb_ctrl = Controller()


def resolve_key(k):
    kl = k.lower().strip()
    if kl in SPECIAL_KEYS:
        return SPECIAL_KEYS[kl]
    if kl in NUMPAD_KEYS:
        return NUMPAD_KEYS[kl]
    if len(k) == 1:
        return k
    try:
        return getattr(Key, kl)
    except AttributeError:
        return None


def normalize_trigger_key(value):
    if value is None:
        return None
    if hasattr(value, "vk") and value.vk is not None:
        if value.vk in NUMPAD_VK_NAMES:
            return NUMPAD_VK_NAMES[value.vk]
        return f"vk:{value.vk}"
    if hasattr(value, "name") and value.name:
        return value.name.lower()
    if hasattr(value, "char") and value.char:
        return f"char:{value.char.lower()}"
    text = str(value).strip().lower()
    if not text:
        return None
    if text in SPECIAL_KEYS:
        return text
    if text in NUMPAD_KEYS:
        return text
    if len(text) == 1:
        return f"char:{text}"
    return text


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Key Presser")
        self.resizable(True, True)
        self.configure(bg=BG_MAIN)
        self.minsize(420, 400)
        self.cfg = load_config()
        self.running_presser = False
        self.running_random = False
        self.press_threads = []
        self.random_thread = None
        self.individual_threads = None
        self.listener = None
        self.pressed_keys = set()
        self.capturing_key = False
        self.capturing_random_key = False
        self.capturing_add_key = False
        self.unsaved_changes = False
        self._resize_after_id = None
        self._compact_layout = None

        self.bind('<Configure>', self._on_window_resize)
        self._build_ui()
        self._start_listener()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.update_idletasks()
        self._fit_window_to_content()

    # ── helpers ──────────────────────────────────────────────

    def _update_start_button_state(self):
        # Disabled config control updating state, buttons are now always normal
        pass

    def _disable_config_controls(self):
        if hasattr(self, 'name_entry'):
            self.name_entry.config(state="disabled")
            self.name_entry.config(insertofftime=0)
        if hasattr(self, 'delay_spin'):
            self.delay_spin.config(state="disabled")
        if hasattr(self, 'interval_buttons'):
            for btn in self.interval_buttons:
                btn.config(state="disabled")
        if hasattr(self, 'use_every_chk'):
            self.use_every_chk.config(state="disabled")
        if hasattr(self, 'once_btn'):
            self.once_btn.config(state="disabled")
        if hasattr(self, 'infinity_btn'):
            self.infinity_btn.config(state="disabled")
        if hasattr(self, 'add_key_btn'):
            self.add_key_btn.config(state="disabled")
        if hasattr(self, 'save_btn'):
            self.save_btn.config(state="disabled")
        self._refresh_wrapped_key_chips()

    def _enable_config_controls(self):
        if hasattr(self, 'name_entry'):
            self.name_entry.config(state="normal")
            self.name_entry.config(insertofftime=600)
        if hasattr(self, 'delay_spin'):
            self.delay_spin.config(state="normal")
        if hasattr(self, 'interval_buttons'):
            use_every = self.cfg.get("key_set", {}).get("use_every", True)
            for btn in self.interval_buttons:
                btn.config(state="normal" if use_every else "disabled")
        if hasattr(self, 'use_every_chk'):
            self.use_every_chk.config(state="normal")
        if hasattr(self, 'once_btn'):
            self.once_btn.config(state="normal")
        if hasattr(self, 'infinity_btn'):
            self.infinity_btn.config(state="normal")
        if hasattr(self, 'add_key_btn'):
            self.add_key_btn.config(state="normal")
        if hasattr(self, 'save_btn'):
            self.save_btn.config(state="normal")
        self._refresh_wrapped_key_chips()

    def _fit_window_to_content(self):
        self.update_idletasks()
        content_height = self.winfo_reqheight()
        screen_height = self.winfo_screenheight()
        window_height = min(content_height + 20, int(screen_height * 0.9))
        
        screen_width = self.winfo_screenwidth()
        window_width = min(520, int(screen_width * 0.35))
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
                      relief="flat", bd=0, cursor="hand2",
                      activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
                      padx=14)
        b.bind("<Enter>", lambda e: b.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        b.bind("<Leave>", lambda e: b.config(bg=BG_INPUT, fg=COLOR_HOVER))
        return b

    def _grid(self, widget, **kwargs):
        kwargs.setdefault("ipady", CONTROL_H)
        widget.grid(**kwargs)
        return widget

    def _pack(self, widget, **kwargs):
        kwargs.setdefault("ipady", CONTROL_H)
        widget.pack(**kwargs)
        return widget

    def _sep(self, parent):
        tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill="x")

    def _label(self, parent, text, width=None):
        kw = {"font": FONT_SUB, "bg": parent["bg"], "fg": COLOR_TEXT_MUTED, "anchor": "w"}
        if width:
            kw["width"] = width
        return tk.Label(parent, text=text, **kw)

    # ── UI build ─────────────────────────────────────────────

    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=BG_MAIN)
        hdr.pack(fill="x", padx=CARD_PAD, pady=(CARD_PAD, 0))
        tk.Label(hdr, text="MOD PRESSER", font=FONT_TITLE,
                 bg=BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        self.status_lbl = tk.Label(hdr, text="IDLE", font=FONT_SUB,
                                   bg=BG_MAIN, fg=COLOR_TEXT_MUTED)
        self.status_lbl.pack(side="right")

        # body
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=CARD_PAD, pady=CARD_PAD)

        # trigger controls row (Auto Presser on left, Random Move on right)
        self._sep(body)
        self._label(body, "GLOBAL TRIGGER KEYS").pack(fill="x", pady=(GAP, 2))
        tr = tk.Frame(body, bg=BG_MAIN)
        tr.pack(fill="x", pady=(0, GAP))
        tr.grid_columnconfigure(0, weight=1)
        tr.grid_columnconfigure(2, weight=1)
        self.trigger_row = tr

        # Left Column: Presser Trigger
        col1 = tk.Frame(tr, bg=BG_MAIN)
        self._grid(col1, row=0, column=0, sticky="ew")
        self._label(col1, "AUTO PRESSER").pack(fill="x", pady=(0, 2))
        tr_presser = tk.Frame(col1, bg=BG_MAIN)
        tr_presser.pack(fill="x")
        tr_presser.grid_columnconfigure(0, weight=1)
        
        self.trigger_key_btn = tk.Button(tr_presser,
            text=self.cfg.get("start_stop_key", "numpad_decimal"),
            bg=BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="arrow",
            state="disabled", disabledforeground=COLOR_HOVER)
        self._grid(self.trigger_key_btn, row=0, column=0, sticky="ew")

        self.trigger_change_btn = self._btn(tr_presser, "CHANGE", self._start_key_capture)
        self._grid(self.trigger_change_btn, row=0, column=1, padx=(GAP, 0), sticky="e")

        # Gap between columns
        tk.Frame(tr, bg=BG_MAIN, width=20).grid(row=0, column=1, sticky="ns")

        # Right Column: Random Trigger
        col2 = tk.Frame(tr, bg=BG_MAIN)
        self._grid(col2, row=0, column=2, sticky="ew")
        self._label(col2, "RANDOM MOVE").pack(fill="x", pady=(0, 2))
        tr_random = tk.Frame(col2, bg=BG_MAIN)
        tr_random.pack(fill="x")
        tr_random.grid_columnconfigure(0, weight=1)

        self.trigger_random_key_btn = tk.Button(tr_random,
            text=self.cfg.get("random_start_stop_key", "numpad_multiply"),
            bg=BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="arrow",
            state="disabled", disabledforeground=COLOR_HOVER)
        self._grid(self.trigger_random_key_btn, row=0, column=0, sticky="ew")

        self.trigger_random_change_btn = self._btn(tr_random, "CHANGE", self._start_random_key_capture)
        self._grid(self.trigger_random_change_btn, row=0, column=1, padx=(GAP, 0), sticky="e")

        # Key set card
        self._sep(body)
        self.key_set_frame = tk.Frame(body, bg=BG_MAIN)
        self.key_set_frame.pack(fill="both", expand=True, pady=(GAP, 0))
        self.key_set_ui_components = {}
        self._build_key_set_section()

        # Random move settings card
        self._sep(body)
        self.random_frame = tk.Frame(body, bg=BG_MAIN)
        self.random_frame.pack(fill="both", expand=True, pady=(GAP, 0))
        self._build_random_section()

        # footer
        self._sep(body)
        bf = tk.Frame(body, bg=BG_MAIN)
        bf.pack(fill="x", pady=(GAP, 0))
        bf.grid_columnconfigure(0, weight=1)
        self.footer_frame = bf

        self.save_btn = self._btn(bf, "SAVE ALL SETTINGS", self._save)
        self._grid(self.save_btn, row=0, column=0, sticky="ew")
        
        self._update_start_button_state()

        self._apply_responsive_layout(self.winfo_width())

    def _build_key_set_section(self):
        for w in self.key_set_frame.winfo_children():
            w.destroy()
        self.key_set_ui_components.clear()

        key_set = self.cfg.get("key_set", {})
        if not key_set:
            key_set = {"name": "Key Set", "keys": [], "delay_ms": 100,
                       "repeat_interval_sec": 30, "use_every": True,
                       "repeat": "Infinity Mode"}
            self.cfg["key_set"] = key_set
        else:
            if "repeat_interval_sec" not in key_set:
                key_set["repeat_interval_sec"] = 30

        self._build_key_set_card(key_set)

        self.after_idle(self._refresh_wrapped_key_chips)
        self.after_idle(lambda: self._apply_responsive_layout(self.winfo_width()))

    def _build_key_set_card(self, key_set):
        card = tk.Frame(self.key_set_frame, bg=BG_CARD)
        card.pack(fill="x", expand=False, pady=(0, GAP))

        # header: name
        hf = tk.Frame(card, bg=BG_CARD)
        hf.pack(fill="x", padx=CARD_PAD, pady=(CARD_PAD, 0))
        hf.grid_columnconfigure(0, weight=1)

        name_var = tk.StringVar(value=key_set.get("name", "Key Set"))
        name_entry = tk.Entry(hf, textvariable=name_var, font=FONT_MAIN,
                              bg=BG_CARD, fg=COLOR_HOVER, insertbackground=COLOR_HOVER,
                              relief="flat", bd=0)
        self._grid(name_entry, row=0, column=0, sticky="ew")
        name_entry.bind("<FocusOut>", lambda e, v=name_var: self._update_key_set_name(v.get()))
        name_entry.bind("<Return>", lambda e, v=name_var: self._update_key_set_name(v.get()))
        self.name_entry = name_entry

        # keys chips
        cf = tk.Frame(card, bg=BG_CARD)
        cf.pack(fill="x", padx=CARD_PAD, pady=(GAP, 0))
        cf.grid_columnconfigure(1, weight=1)
        self._label(cf, "Keys", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        keys_container = tk.Frame(cf, bg=BG_INPUT)
        keys_container.grid(row=0, column=1, sticky="ew", padx=(GAP, 0))
        self._render_key_set_chips(keys_container, key_set.get("keys", []))

        # settings
        sf = tk.Frame(card, bg=BG_CARD)
        sf.pack(fill="x", padx=CARD_PAD, pady=(GAP, 0))

        # delay row
        dr = tk.Frame(sf, bg=BG_CARD)
        dr.pack(fill="x", pady=(0, 2))
        dr.grid_columnconfigure(2, weight=1)
        self._label(dr, "Delay", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        delay_var = tk.IntVar(value=key_set.get("delay_ms", 100))
        delay_spin = tk.Spinbox(dr, from_=1, to=60000, textvariable=delay_var,
                                font=FONT_MAIN, bg=BG_INPUT, fg=COLOR_TEXT,
                                insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
                                buttonbackground=BG_INPUT, width=6,
                                command=lambda v=delay_var: self._update_delay(v.get()))
        self._grid(delay_spin, row=0, column=1, sticky="w", padx=(GAP, 0))
        delay_spin.bind("<KeyRelease>", lambda e, v=delay_var: self._update_delay(v.get()))
        delay_spin.bind("<Return>", lambda e: self.focus_set())
        self._label(dr, "ms").grid(row=0, column=2, sticky="w", padx=(GAP, 0))
        self.delay_spin = delay_spin

        # every row
        er = tk.Frame(sf, bg=BG_CARD)
        er.pack(fill="x", pady=(0, 2))
        er.grid_columnconfigure(3, weight=1)
        self._label(er, "Every", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        use_every_var = tk.BooleanVar(value=key_set.get("use_every", True))
        repeat_interval_var = tk.IntVar(value=key_set.get("repeat_interval_sec", 30))
        
        use_every_chk = tk.Checkbutton(er, text="Use", variable=use_every_var,
                                       command=lambda v=use_every_var: self._update_use_every(v.get()),
                                       bg=BG_CARD, fg=COLOR_TEXT_MUTED, activebackground=BG_CARD,
                                       activeforeground=COLOR_TEXT, selectcolor=BG_INPUT,
                                       relief="flat", bd=0, font=FONT_SUB)
        self._grid(use_every_chk, row=0, column=1, sticky="w", padx=(GAP, GAP))
        
        interval_btns_frame = tk.Frame(er, bg=BG_CARD)
        self._grid(interval_btns_frame, row=0, column=2, sticky="w", padx=(GAP, GAP))
        
        interval_values = [10, 20, 30, 60]
        self.interval_buttons = []
        for i, val in enumerate(interval_values):
            btn = tk.Button(interval_btns_frame, text=str(val),
                           bg=COLOR_ACCENT if repeat_interval_var.get() == val else BG_INPUT,
                           fg=COLOR_TEXT if repeat_interval_var.get() == val else COLOR_TEXT_MUTED,
                           font=FONT_MAIN,
                           relief="flat", bd=0, cursor="hand2",
                           state="normal" if use_every_var.get() else "disabled",
                           width=5,
                           command=lambda v=val: self._update_repeat_interval(v))
            btn.pack(side="left", padx=2)
            self.interval_buttons.append(btn)
        
        self._label(er, "s").grid(row=0, column=3, sticky="w", padx=(GAP, 0))
        self.use_every_chk = use_every_chk
        self.repeat_interval_var = repeat_interval_var

        # repeat row
        rr = tk.Frame(sf, bg=BG_CARD)
        rr.pack(fill="x", pady=(0, 2))
        self._label(rr, "Repeat", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        
        repeat_mode_var = tk.StringVar(value=key_set.get("repeat", "Infinity Mode"))
        
        once_btn = tk.Button(rr, text="ONCE",
                            bg=COLOR_ACCENT if repeat_mode_var.get() == "Once" else BG_INPUT,
                            fg=COLOR_TEXT if repeat_mode_var.get() == "Once" else COLOR_TEXT_MUTED,
                            font=FONT_MAIN,
                            relief="flat", bd=0, cursor="hand2",
                            width=10,
                            command=lambda: self._set_repeat_mode("Once", repeat_mode_var, once_btn, infinity_btn))
        self._grid(once_btn, row=0, column=1, sticky="w", padx=(GAP, GAP))
        once_btn.bind("<Enter>", lambda e: once_btn.config(bg=COLOR_HOVER if repeat_mode_var.get() == "Once" else COLOR_ACCENT, fg=COLOR_TEXT))
        once_btn.bind("<Leave>", lambda e: once_btn.config(bg=COLOR_ACCENT if repeat_mode_var.get() == "Once" else BG_INPUT, fg=COLOR_TEXT if repeat_mode_var.get() == "Once" else COLOR_TEXT_MUTED))
        
        infinity_btn = tk.Button(rr, text="INFINITY",
                                 bg=COLOR_ACCENT if repeat_mode_var.get() == "Infinity Mode" else BG_INPUT,
                                 fg=COLOR_TEXT if repeat_mode_var.get() == "Infinity Mode" else COLOR_TEXT_MUTED,
                                 font=FONT_MAIN,
                                 relief="flat", bd=0, cursor="hand2",
                                 width=10,
                                 command=lambda: self._set_repeat_mode("Infinity Mode", repeat_mode_var, once_btn, infinity_btn))
        self._grid(infinity_btn, row=0, column=2, sticky="w", padx=(GAP, GAP))
        infinity_btn.bind("<Enter>", lambda e: infinity_btn.config(bg=COLOR_HOVER if repeat_mode_var.get() == "Infinity Mode" else COLOR_ACCENT, fg=COLOR_TEXT))
        infinity_btn.bind("<Leave>", lambda e: infinity_btn.config(bg=COLOR_ACCENT if repeat_mode_var.get() == "Infinity Mode" else BG_INPUT, fg=COLOR_TEXT if repeat_mode_var.get() == "Infinity Mode" else COLOR_TEXT_MUTED))
        self.once_btn = once_btn
        self.infinity_btn = infinity_btn

        # add key row
        af = tk.Frame(card, bg=BG_CARD)
        af.pack(fill="x", padx=CARD_PAD, pady=(GAP, 0))
        af.grid_columnconfigure(1, weight=1)
        self._label(af, "Add", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        
        self.add_key_btn = tk.Button(af, text="PRESS KEY TO ADD",
                                     bg=BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
                                     relief="flat", bd=0, cursor="hand2",
                                     command=self._start_add_key_capture)
        self._grid(self.add_key_btn, row=0, column=1, sticky="ew", padx=(GAP, GAP))
        self.add_key_btn.bind("<Enter>", lambda e: self.add_key_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        self.add_key_btn.bind("<Leave>", lambda e: self.add_key_btn.config(bg=BG_INPUT, fg=COLOR_HOVER))

        # action row (START/STOP for Presser)
        act = tk.Frame(card, bg=BG_CARD)
        act.pack(fill="x", padx=CARD_PAD, pady=(GAP, CARD_PAD))
        self.toggle_presser_btn = self._btn(act, "START AUTO PRESSER", self._toggle_presser)
        self.toggle_presser_btn.pack(fill="x", ipady=4)

        self.key_set_ui_components = {
            'name_var': name_var,
            'delay_var': delay_var,
            'repeat_interval_var': repeat_interval_var,
            'use_every_var': use_every_var,
            'repeat_mode_var': repeat_mode_var,
            'once_btn': once_btn,
            'infinity_btn': infinity_btn,
            'chips_frame': keys_container
        }

    def _build_random_section(self):
        for w in self.random_frame.winfo_children():
            w.destroy()

        random_move = self.cfg.get("random_move", {})
        if not random_move:
            random_move = {"min_sec": 5, "max_sec": 20}
            self.cfg["random_move"] = random_move

        card = tk.Frame(self.random_frame, bg=BG_CARD)
        card.pack(fill="x", expand=False, pady=(0, GAP))

        # header
        hf = tk.Frame(card, bg=BG_CARD)
        hf.pack(fill="x", padx=CARD_PAD, pady=(CARD_PAD, 0))
        tk.Label(hf, text="RANDOM MOVE (WASD)", font=FONT_MAIN,
                bg=BG_CARD, fg=COLOR_HOVER).pack(side="left")

        # settings
        sf = tk.Frame(card, bg=BG_CARD)
        sf.pack(fill="x", padx=CARD_PAD, pady=(GAP, 0))

        # min row
        mr = tk.Frame(sf, bg=BG_CARD)
        mr.pack(fill="x", pady=(0, 2))
        mr.grid_columnconfigure(2, weight=1)
        self._label(mr, "Min", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        min_var = tk.IntVar(value=random_move.get("min_sec", 5))
        min_spin = tk.Spinbox(mr, from_=1, to=60, textvariable=min_var,
                                   font=FONT_MAIN, bg=BG_INPUT, fg=COLOR_TEXT,
                                   insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
                                   buttonbackground=BG_INPUT, width=6,
                                   command=lambda v=min_var: self._update_min_sec(v.get()))
        self._grid(min_spin, row=0, column=1, sticky="w", padx=(GAP, 0))
        min_spin.bind("<KeyRelease>", lambda e, v=min_var: self._update_min_sec(v.get()))
        min_spin.bind("<Return>", lambda e: self.focus_set())
        self._label(mr, "sec").grid(row=0, column=2, sticky="w", padx=(GAP, 0))
        self.min_spin = min_spin

        # max row
        xr = tk.Frame(sf, bg=BG_CARD)
        xr.pack(fill="x", pady=(0, 2))
        xr.grid_columnconfigure(2, weight=1)
        self._label(xr, "Max", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(GAP, GAP))
        max_var = tk.IntVar(value=random_move.get("max_sec", 20))
        max_spin = tk.Spinbox(xr, from_=1, to=60, textvariable=max_var,
                                   font=FONT_MAIN, bg=BG_INPUT, fg=COLOR_TEXT,
                                   insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
                                   buttonbackground=BG_INPUT, width=6,
                                   command=lambda v=max_var: self._update_max_sec(v.get()))
        self._grid(max_spin, row=0, column=1, sticky="w", padx=(GAP, 0))
        max_spin.bind("<KeyRelease>", lambda e, v=max_var: self._update_max_sec(v.get()))
        max_spin.bind("<Return>", lambda e: self.focus_set())
        self._label(xr, "sec").grid(row=0, column=2, sticky="w", padx=(GAP, 0))
        self.max_spin = max_spin

        # info
        info = tk.Label(card, text="Randomly press W/A/S/D keys",
                       font=FONT_SUB, bg=BG_CARD, fg=COLOR_TEXT_MUTED)
        info.pack(padx=CARD_PAD, pady=(GAP, 0))

        # action row (START/STOP for Random Move)
        act = tk.Frame(card, bg=BG_CARD)
        act.pack(fill="x", padx=CARD_PAD, pady=(GAP, CARD_PAD))
        self.toggle_random_btn = self._btn(act, "START RANDOM MOVE", self._toggle_random)
        self.toggle_random_btn.pack(fill="x", ipady=4)

    # ── chips ────────────────────────────────────────────────

    def _render_key_set_chips(self, chips_frame, keys):
        for w in chips_frame.winfo_children():
            w.destroy()
        if not keys:
            self._label(chips_frame, "No keys").pack(padx=4, pady=2)
            return

        chips_frame.update_idletasks()
        available_width = chips_frame.winfo_width()
        if available_width <= 1:
            available_width = chips_frame.winfo_reqwidth()
        if available_width <= 1:
            available_width = max(200, self.winfo_width() - 160)

        row_frame = tk.Frame(chips_frame, bg=BG_INPUT)
        row_frame.pack(fill="x", anchor="w")
        used_width = 0

        for i, k in enumerate(keys):
            est = max(44, len(k) * 8 + 34)
            if used_width and used_width + est > available_width:
                row_frame = tk.Frame(chips_frame, bg=BG_INPUT)
                row_frame.pack(fill="x", anchor="w", pady=(2, 0))
                used_width = 0

            chip = tk.Frame(row_frame, bg=BG_MAIN)
            chip.pack(side="left", padx=1, pady=1)
            tk.Label(chip, text=k, font=FONT_MAIN, bg=BG_MAIN, fg=COLOR_HOVER,
                     padx=4, pady=1).pack(side="left")
            xl = tk.Label(chip, text="X", font=FONT_MAIN, bg=BG_MAIN, fg=COLOR_TEXT_MUTED,
                          cursor="hand2", padx=2)
            xl.pack(side="left")
            xl.bind("<Button-1>", lambda e, idx=i: self._remove_key_from_set(idx))
            xl.bind("<Enter>", lambda e, w=xl: w.config(fg=COLOR_DANGER))
            xl.bind("<Leave>", lambda e, w=xl: w.config(fg=COLOR_TEXT_MUTED))
            used_width += est

    def _refresh_wrapped_key_chips(self):
        key_set = self.cfg.get("key_set", {})
        if self.key_set_ui_components:
            self._render_key_set_chips(self.key_set_ui_components['chips_frame'],
                                       key_set.get('keys', []))

    # ── responsive ───────────────────────────────────────────

    def _apply_responsive_layout(self, window_width):
        pass

    # ── data mutations ───────────────────────────────────────

    def _update_key_set_name(self, name):
        if self.running_presser:
            return
        key_set = self.cfg.get("key_set", {})
        key_set["name"] = name
        self.unsaved_changes = True
        self._update_start_button_state()

    def _add_key_to_set(self, key_string):
        if self.running_presser:
            return
        if not key_string.strip():
            return
        key_set = self.cfg.get("key_set", {})
        for k in re.split(r"[,\s]+", key_string):
            k = k.strip()
            if k:
                key_set.setdefault("keys", []).append(k)
        self.unsaved_changes = True
        self._update_start_button_state()
        self._build_key_set_section()

    def _update_delay(self, value):
        if self.running_presser:
            return
        key_set = self.cfg.get("key_set", {})
        key_set["delay_ms"] = value
        self.unsaved_changes = True
        self._update_start_button_state()

    def _update_repeat_interval(self, value):
        if self.running_presser:
            return
        key_set = self.cfg.get("key_set", {})
        key_set["repeat_interval_sec"] = value
        self.repeat_interval_var.set(value)
        self.unsaved_changes = True
        self._update_start_button_state()
        
        if hasattr(self, 'interval_buttons'):
            interval_values = [10, 20, 30, 60]
            for i, btn in enumerate(self.interval_buttons):
                btn.config(bg=COLOR_ACCENT if interval_values[i] == value else BG_INPUT,
                          fg=COLOR_TEXT if interval_values[i] == value else COLOR_TEXT_MUTED)

    def _update_use_every(self, value):
        if self.running_presser:
            return
        key_set = self.cfg.get("key_set", {})
        key_set["use_every"] = bool(value)
        if hasattr(self, 'interval_buttons'):
            for btn in self.interval_buttons:
                btn.config(state="normal" if value else "disabled")
        self.unsaved_changes = True
        self._update_start_button_state()

    def _set_repeat_mode(self, mode, var, once_btn, infinity_btn):
        if self.running_presser:
            return
        var.set(mode)
        key_set = self.cfg.get("key_set", {})
        key_set["repeat"] = mode
        self.unsaved_changes = True
        self._update_start_button_state()
        
        if mode == "Once":
            once_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)
            infinity_btn.config(bg=BG_INPUT, fg=COLOR_TEXT_MUTED)
        else:
            once_btn.config(bg=BG_INPUT, fg=COLOR_TEXT_MUTED)
            infinity_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)

    def _remove_key_from_set(self, key_index):
        if self.running_presser:
            return
        key_set = self.cfg.get("key_set", {})
        keys = key_set.get("keys", [])
        if key_index < len(keys):
            keys.pop(key_index)
            self.unsaved_changes = True
            self._update_start_button_state()
            self._build_key_set_section()

    def _update_min_sec(self, value):
        if self.running_random:
            return
        random_move = self.cfg.get("random_move", {})
        random_move["min_sec"] = value
        self.unsaved_changes = True
        self._update_start_button_state()

    def _update_max_sec(self, value):
        if self.running_random:
            return
        random_move = self.cfg.get("random_move", {})
        random_move["max_sec"] = value
        self.unsaved_changes = True
        self._update_start_button_state()

    # ── global start / stop ──────────────────────────────────

    def _get_config(self):
        return {
            "start_stop_key": self.cfg.get("start_stop_key", "numpad_decimal"),
            "random_start_stop_key": self.cfg.get("random_start_stop_key", "numpad_multiply"),
            "key_set": self.cfg.get("key_set", {}),
            "random_move": self.cfg.get("random_move", {})
        }

    def _save(self):
        if self.running_presser or self.running_random:
            messagebox.showwarning("Cannot Save", "Cannot save configuration while running.", parent=self)
            return
        self.cfg = self._get_config()
        save_config(self.cfg)
        self._restart_listener()
        self.unsaved_changes = False
        self._update_start_button_state()
        messagebox.showinfo("Saved", "Config saved!", parent=self)

    def _toggle_presser(self):
        if self.running_presser:
            self._stop_presser()
        else:
            self.cfg = self._get_config()
            self._start_presser()

    def _start_presser(self):
        self.running_presser = True
        self.toggle_presser_btn.config(text="STOP AUTO PRESSER", bg=COLOR_DANGER, activebackground="#cc2233")
        self.toggle_presser_btn.bind("<Enter>", lambda e: self.toggle_presser_btn.config(bg="#cc2233"))
        self.toggle_presser_btn.bind("<Leave>", lambda e: self.toggle_presser_btn.config(bg=COLOR_DANGER))
        
        self.status_lbl.config(text="RUNNING - AUTO PRESSER ACTIVE", fg=COLOR_SUCCESS)
        self._disable_config_controls()

        key_set = self.cfg.get("key_set", {})
        repeat = key_set.get("repeat", "Infinity Mode")
        keys = key_set.get("keys", [])
        if keys:
            delay = key_set.get("delay_ms", 100) / 1000.0
            repeat_interval = key_set.get("repeat_interval_sec", 1) * 1000 / 1000.0
            use_every = key_set.get("use_every", True)
            thread = threading.Thread(
                target=self._press_loop,
                args=(keys, delay, repeat_interval, repeat, use_every),
                daemon=True)
            thread.start()
            self.press_threads.append(thread)

    def _stop_presser(self):
        self.running_presser = False
        self.individual_threads = None
        self.toggle_presser_btn.config(text="START AUTO PRESSER", bg=COLOR_ACCENT, activebackground=COLOR_HOVER)
        self.toggle_presser_btn.bind("<Enter>", lambda e: self.toggle_presser_btn.config(bg=COLOR_HOVER))
        self.toggle_presser_btn.bind("<Leave>", lambda e: self.toggle_presser_btn.config(bg=COLOR_ACCENT))
        self.status_lbl.config(text="IDLE" if not self.running_random else "RUNNING - RANDOM MOVE ACTIVE", fg=COLOR_TEXT_MUTED if not self.running_random else COLOR_SUCCESS)
        self.press_threads.clear()
        self._enable_config_controls()

    def _toggle_random(self):
        if self.running_random:
            self._stop_random()
        else:
            self.cfg = self._get_config()
            self._start_random()

    def _start_random(self):
        self.running_random = True
        self.toggle_random_btn.config(text="STOP RANDOM MOVE", bg=COLOR_DANGER, activebackground="#cc2233")
        self.toggle_random_btn.bind("<Enter>", lambda e: self.toggle_random_btn.config(bg="#cc2233"))
        self.toggle_random_btn.bind("<Leave>", lambda e: self.toggle_random_btn.config(bg=COLOR_DANGER))
        
        self.status_lbl.config(text="RUNNING - RANDOM MOVE ACTIVE", fg=COLOR_SUCCESS)
        self._disable_config_controls()

        random_move = self.cfg.get("random_move", {})
        min_sec = random_move.get("min_sec", 5)
        max_sec = random_move.get("max_sec", 20)
        
        thread = threading.Thread(
            target=self._random_move_loop,
            args=(min_sec, max_sec),
            daemon=True)
        thread.start()
        self.random_thread = thread

    def _stop_random(self):
        self.running_random = False
        self.toggle_random_btn.config(text="START RANDOM MOVE", bg=COLOR_ACCENT, activebackground=COLOR_HOVER)
        self.toggle_random_btn.bind("<Enter>", lambda e: self.toggle_random_btn.config(bg=COLOR_HOVER))
        self.toggle_random_btn.bind("<Leave>", lambda e: self.toggle_random_btn.config(bg=COLOR_ACCENT))
        self.status_lbl.config(text="IDLE" if not self.running_presser else "RUNNING - AUTO PRESSER ACTIVE", fg=COLOR_TEXT_MUTED if not self.running_presser else COLOR_SUCCESS)
        self.random_thread = None
        self._enable_config_controls()

    def _press_loop(self, keys, delay_s, repeat_interval_s=1.0, repeat=None, use_every=True):
        resolved = [resolve_key(k) for k in keys]
        resolved = [k for k in resolved if k is not None]
        
        if repeat == "Once":
            for key in resolved:
                if not self.running_presser:
                    break
                kb_ctrl.press(key)
                time.sleep(0.02)
                kb_ctrl.release(key)
                time.sleep(delay_s)
            self.running_presser = False
            self.after(0, self._stop_presser)
        else:
            while self.running_presser:
                for key in resolved:
                    if not self.running_presser:
                        break
                    kb_ctrl.press(key)
                    time.sleep(0.02)
                    kb_ctrl.release(key)
                    time.sleep(delay_s)
                if self.running_presser and use_every:
                    time.sleep(repeat_interval_s)

    def _random_move_loop(self, min_sec, max_sec):
        wasd_keys = ['w', 'a', 's', 'd']
        resolved = [resolve_key(k) for k in wasd_keys]
        resolved = [k for k in resolved if k is not None]
        
        while self.running_random:
            if not resolved:
                break
            
            # Randomly select a direction key
            key = random.choice(resolved)
            
            # Random hold duration between min and max
            hold_duration = random.uniform(min_sec, max_sec)
            
            # Hold for the random duration with key repeat simulation
            start_time = time.time()
            repeat_interval = 0.05  # 50ms between repeats (typical keyboard repeat rate)
            last_repeat = start_time
            
            while self.running_random and (time.time() - start_time) < hold_duration:
                current_time = time.time()
                if current_time - last_repeat >= repeat_interval:
                    kb_ctrl.press(key)
                    kb_ctrl.release(key)
                    last_repeat = current_time
                time.sleep(0.01)
            
            # Small pause before next move
            if self.running_random:
                time.sleep(0.1)
        
        self.running_random = False
        self.after(0, self._stop_random)

    # ── listener ─────────────────────────────────────────────

    def _start_listener(self):
        def on_press(key):
            if self.capturing_key:
                self._set_trigger_key(key)
                return
            if self.capturing_random_key:
                self._set_random_trigger_key(key)
                return
            if self.capturing_add_key:
                self._set_add_key(key)
                return
                
            # Presser global hotkey check
            tks = self.cfg.get("start_stop_key", "numpad_decimal")
            matched_presser = normalize_trigger_key(key) == normalize_trigger_key(tks)
            if not matched_presser:
                tks_lower = tks.lower()
                tk_key = resolve_key(tks_lower)
                matched_presser = (key == tk_key) or \
                          (hasattr(key, 'name') and key.name and key.name.lower() == tks_lower)
            if matched_presser and key not in self.pressed_keys:
                self.pressed_keys.add(key)
                self.after(0, self._toggle_presser)
                return

            # Random move global hotkey check
            rtks = self.cfg.get("random_start_stop_key", "numpad_multiply")
            matched_random = normalize_trigger_key(key) == normalize_trigger_key(rtks)
            if not matched_random:
                rtks_lower = rtks.lower()
                rtk_key = resolve_key(rtks_lower)
                matched_random = (key == rtk_key) or \
                          (hasattr(key, 'name') and key.name and key.name.lower() == rtks_lower)
            if matched_random and key not in self.pressed_keys:
                self.pressed_keys.add(key)
                self.after(0, self._toggle_random)
                return

        def on_release(key):
            self.pressed_keys.discard(key)

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True
        self.listener.start()

    def _restart_listener(self):
        if self.listener:
            self.listener.stop()
        self._start_listener()

    # ── window events ────────────────────────────────────────

    def _on_window_resize(self, event):
        if event.widget != self:
            return
        self._apply_responsive_layout(event.width)
        if self._resize_after_id is not None:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(120, self._refresh_wrapped_key_chips)

    def _on_close(self):
        self.running_presser = False
        self.running_random = False
        self.individual_threads = None
        if self.listener:
            self.listener.stop()
        self.destroy()

    # ── key capture ──────────────────────────────────────────

    def _start_key_capture(self):
        self.capturing_key = True
        self.trigger_key_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_lbl.config(text="PRESS A KEY", fg=COLOR_ACCENT)

    def _start_add_key_capture(self):
        self.capturing_add_key = True
        self.add_key_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_lbl.config(text="PRESS A KEY TO ADD", fg=COLOR_ACCENT)

    def _set_trigger_key(self, key):
        if hasattr(key, 'vk') and key.vk is not None:
            if 96 <= key.vk <= 105:
                key_str = f"NUMPAD_{key.vk - 96}"
            elif key.vk == 106:
                key_str = "NUMPAD_MULTIPLY"
            elif key.vk == 107:
                key_str = "NUMPAD_ADD"
            elif key.vk == 108:
                key_str = "NUMPAD_SEPARATOR"
            elif key.vk == 109:
                key_str = "NUMPAD_SUBTRACT"
            elif key.vk == 110:
                key_str = "NUMPAD_DECIMAL"
            elif key.vk == 111:
                key_str = "NUMPAD_DIVIDE"
            else:
                key_str = None
        elif hasattr(key, 'name'):
            key_str = key.name.upper()
        elif hasattr(key, 'char') and key.char:
            key_str = key.char.upper()
        else:
            return

        self.cfg["start_stop_key"] = key_str
        self.trigger_key_btn.config(text=key_str, bg=BG_INPUT, fg=COLOR_HOVER)
        self.status_lbl.config(text="IDLE", fg=COLOR_TEXT_MUTED)
        self.capturing_key = False
        save_config(self.cfg)
        self._restart_listener()

    def _set_add_key(self, key):
        if self.running_presser:
            self.add_key_btn.config(text="PRESS KEY TO ADD", bg=BG_INPUT, fg=COLOR_HOVER)
            self.status_lbl.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            self.capturing_add_key = False
            return
        if hasattr(key, 'char') and key.char:
            key_str = key.char.lower()
        elif hasattr(key, 'vk') and key.vk is not None:
            if 96 <= key.vk <= 105:
                key_str = f"numpad_{key.vk - 96}"
            elif key.vk == 106:
                key_str = "numpad_multiply"
            elif key.vk == 107:
                key_str = "numpad_add"
            elif key.vk == 108:
                key_str = "numpad_separator"
            elif key.vk == 109:
                key_str = "numpad_subtract"
            elif key.vk == 110:
                key_str = "numpad_decimal"
            elif key.vk == 111:
                key_str = "numpad_divide"
            else:
                key_str = None
        elif hasattr(key, 'name'):
            key_str = key.name.lower()
        else:
            return

        if key_str:
            self._add_key_to_set(key_str)
            self.add_key_btn.config(text="PRESS KEY TO ADD", bg=BG_INPUT, fg=COLOR_HOVER)
            self.status_lbl.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            self.capturing_add_key = False

    def _start_random_key_capture(self):
        self.capturing_random_key = True
        self.trigger_random_key_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_lbl.config(text="PRESS A KEY", fg=COLOR_ACCENT)

    def _set_random_trigger_key(self, key):
        if hasattr(key, 'vk') and key.vk is not None:
            if 96 <= key.vk <= 105:
                key_str = f"NUMPAD_{key.vk - 96}"
            elif key.vk == 106:
                key_str = "NUMPAD_MULTIPLY"
            elif key.vk == 107:
                key_str = "NUMPAD_ADD"
            elif key.vk == 108:
                key_str = "NUMPAD_SEPARATOR"
            elif key.vk == 109:
                key_str = "NUMPAD_SUBTRACT"
            elif key.vk == 110:
                key_str = "NUMPAD_DECIMAL"
            elif key.vk == 111:
                key_str = "NUMPAD_DIVIDE"
            else:
                key_str = None
        elif hasattr(key, 'name'):
            key_str = key.name.upper()
        elif hasattr(key, 'char') and key.char:
            key_str = key.char.upper()
        else:
            return

        self.cfg["random_start_stop_key"] = key_str
        self.trigger_random_key_btn.config(text=key_str, bg=BG_INPUT, fg=COLOR_HOVER)
        self.status_lbl.config(text="IDLE", fg=COLOR_TEXT_MUTED)
        self.capturing_random_key = False
        save_config(self.cfg)
        self._restart_listener()


if __name__ == "__main__":
    app = App()
    app.mainloop()
