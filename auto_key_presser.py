"""
Auto Key Presser - Dark UI
===========================
pip install pynput
"""

import json, time, threading, sys, os, re
import random
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode, Controller
from pynput.mouse import Button, Controller as MouseController

# ── Config path ──────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "config.json")
else:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ── Theme colors ─────────────────────────────────────────────────────────────
COLOR_BG_MAIN        = "#0A0A0A"
COLOR_BG_CARD        = "#141414"
COLOR_BG_INPUT       = "#1F1F1F"
COLOR_BORDER         = "#2A2A2A"
COLOR_ACCENT         = "#888888"
COLOR_HOVER          = "#00C853"
COLOR_SUCCESS        = "#00C853"
COLOR_DANGER         = "#FF3D00"
COLOR_TEXT           = "#FFFFFF"
COLOR_TEXT_MUTED     = "#888888"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_MAIN  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)

# ── Layout constants ──────────────────────────────────────────────────────────
CONTROL_HEIGHT = 1
LAYOUT_GAP     = 6
CARD_PADDING   = 10
LABEL_WIDTH    = 8

# ── Key maps ──────────────────────────────────────────────────────────────────
SPECIAL_KEY_MAP = {
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

NUMPAD_KEY_MAP = {
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
    "numpad_multiply":  KeyCode.from_vk(106),
    "numpad_add":       KeyCode.from_vk(107),
    "numpad_separator": KeyCode.from_vk(108),
    "numpad_subtract":  KeyCode.from_vk(109),
    "numpad_decimal":   KeyCode.from_vk(110),
    "numpad_divide":    KeyCode.from_vk(111),
}

NUMPAD_VK_TO_NAME = {
    96: "numpad_0",  97: "numpad_1",  98: "numpad_2",  99: "numpad_3",
    100: "numpad_4", 101: "numpad_5", 102: "numpad_6", 103: "numpad_7",
    104: "numpad_8", 105: "numpad_9", 106: "numpad_multiply",
    107: "numpad_add", 108: "numpad_separator", 109: "numpad_subtract",
    110: "numpad_decimal", 111: "numpad_divide",
}

DEFAULT_CONFIG = {
    "random_start_stop_key": "numpad_multiply",
    "key_sets": [
        {
            "id": 1,
            "name": "Key Set 1",
            "keys": ["1", "2", "3", "4"],
            "delay_ms": 100,
            "repeat_interval_sec": 30,
            "use_every": True,
            "repeat": "Infinity Mode",
            "enabled": True,
            "trigger_key": "numpad_decimal"
        },
        {
            "id": 2,
            "name": "Key Set 2",
            "keys": ["q", "w", "e", "r"],
            "delay_ms": 100,
            "repeat_interval_sec": 30,
            "use_every": True,
            "repeat": "Infinity Mode",
            "enabled": True,
            "trigger_key": "numpad_divide"
        },
        {
            "id": 3,
            "name": "Key Set 3",
            "keys": ["a", "s", "d", "f"],
            "delay_ms": 100,
            "repeat_interval_sec": 30,
            "use_every": True,
            "repeat": "Infinity Mode",
            "enabled": True,
            "trigger_key": "numpad_subtract"
        },
        {
            "id": 4,
            "name": "Key Set 4",
            "keys": ["z", "x", "c", "v"],
            "delay_ms": 100,
            "repeat_interval_sec": 30,
            "use_every": True,
            "repeat": "Infinity Mode",
            "enabled": True,
            "trigger_key": "numpad_add"
        }
    ],
    "random_move": {
        "min_sec": 5,
        "max_sec": 20,
        "delay_ms": 100,
    },
    "window_position": "top-left",
    "transparency": 1.0,
    "always_on_top": True,
    "compact_mode": False,
    "fullscreen": True
}

keyboard_controller = Controller()
mouse_controller = MouseController()


# ── Key utilities ─────────────────────────────────────────────────────────────

def resolve_key(key_name: str):
    """Resolve a key name string to a pynput Key or character."""
    normalized = key_name.lower().strip()
    if normalized in SPECIAL_KEY_MAP:
        return SPECIAL_KEY_MAP[normalized]
    if normalized in NUMPAD_KEY_MAP:
        return NUMPAD_KEY_MAP[normalized]
    if len(key_name) == 1:
        return key_name
    try:
        return getattr(Key, normalized)
    except AttributeError:
        return None


def normalize_hotkey(key_value) -> str | None:
    """Normalize a pynput key object or string to a consistent string form."""
    if key_value is None:
        return None
    if hasattr(key_value, "vk") and key_value.vk is not None:
        if key_value.vk in NUMPAD_VK_TO_NAME:
            return NUMPAD_VK_TO_NAME[key_value.vk]
        return f"vk:{key_value.vk}"
    if hasattr(key_value, "name") and key_value.name:
        return key_value.name.lower()
    if hasattr(key_value, "char") and key_value.char:
        return f"char:{key_value.char.lower()}"
    text = str(key_value).strip().lower()
    if not text:
        return None
    if text in SPECIAL_KEY_MAP:
        return text
    if text in NUMPAD_KEY_MAP:
        return text
    if len(text) == 1:
        return f"char:{text}"
    return text


def _vk_to_numpad_name(vk: int) -> str | None:
    """Convert a virtual key code to an uppercase numpad name string, or None."""
    name = NUMPAD_VK_TO_NAME.get(vk)
    return name.upper() if name else None


def _vk_to_numpad_name_lower(vk: int) -> str | None:
    """Convert a virtual key code to a lowercase numpad name string, or None."""
    return NUMPAD_VK_TO_NAME.get(vk)


# ── Config I/O ────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# ── Main App ──────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Key Presser")
        self.resizable(True, True)
        self.configure(bg=COLOR_BG_MAIN)
        self.minsize(420, 400)

        self.config_data = load_config()
        self.is_presser_running = False
        self.is_random_running  = False
        self.press_threads:     list[threading.Thread] = []
        self.random_thread:     threading.Thread | None = None
        self.individual_threads = None
        self.hotkey_listener:   keyboard.Listener | None = None
        self.held_keys:         dict = {}
        self.running_key_sets:  set[int] = set()  # Track which key sets are running

        self.is_capturing_presser_hotkey = False
        self.is_capturing_random_hotkey  = False
        self.is_capturing_add_key        = False
        self.is_capturing_trigger_key    = False
        self.capturing_trigger_key_id    = None
        self.has_unsaved_changes = False

        self.collapsed_sections = {
            "key_sets": False,
            "random_move": False,
            "window_settings": False
        }
        self.key_set_columns = 2
        self.is_rebuilding = False

        self._resize_after_id = None
        self._compact_layout  = None
        self.is_compact_mode  = self.config_data.get("compact_mode", False)

        self.bind('<Configure>', self._on_window_resize)
        self._build_ui()
        self._apply_window_settings()
        self._apply_fullscreen()
        self._start_hotkey_listener()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.update_idletasks()
        self._fit_window_to_content()

    # ── UI state helpers ──────────────────────────────────────────────────────

    def _update_action_button_state(self):
        pass  # Buttons are always enabled; reserved for future use.

    def _disable_settings_controls(self):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id", 1)
            self._disable_settings_controls_for_key_set(key_set_id)
        if hasattr(self, 'random_delay_spinbox'):
            self.random_delay_spinbox.config(state="disabled")
        if hasattr(self, 'save_btn'):
            self.save_btn.config(state="disabled")

    def _disable_settings_controls_for_key_set(self, key_set_id: int):
        if f'name_entry_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'name_entry_{key_set_id}'].config(state="disabled", insertofftime=0)
        if f'delay_spinbox_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'delay_spinbox_{key_set_id}'].config(state="disabled")
        if f'repeat_interval_spinbox_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'repeat_interval_spinbox_{key_set_id}'].config(state="disabled")
        if f'use_every_checkbox_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'use_every_checkbox_{key_set_id}'].config(state="disabled")
        if f'repeat_once_btn_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'repeat_once_btn_{key_set_id}'].config(state="disabled")
        if f'repeat_infinity_btn_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'repeat_infinity_btn_{key_set_id}'].config(state="disabled")
        if f'add_key_btn_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'add_key_btn_{key_set_id}'].config(state="disabled")
        self._refresh_key_chips()

    def _enable_settings_controls(self):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id", 1)
            self._enable_settings_controls_for_key_set(key_set_id)
        if hasattr(self, 'random_delay_spinbox'):
            self.random_delay_spinbox.config(state="normal")
        if hasattr(self, 'save_btn'):
            self.save_btn.config(state="normal")

    def _enable_settings_controls_for_key_set(self, key_set_id: int):
        if f'name_entry_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'name_entry_{key_set_id}'].config(state="normal", insertofftime=600)
        if f'delay_spinbox_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'delay_spinbox_{key_set_id}'].config(state="normal")
        if f'repeat_interval_spinbox_{key_set_id}' in self.key_set_widget_refs:
            use_every = self.config_data.get("key_sets", [{}])[0].get("use_every", True)
            for key_set in self.config_data.get("key_sets", []):
                if key_set.get("id") == key_set_id:
                    use_every = key_set.get("use_every", True)
                    break
            self.key_set_widget_refs[f'repeat_interval_spinbox_{key_set_id}'].config(state="normal" if use_every else "disabled")
        if f'use_every_checkbox_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'use_every_checkbox_{key_set_id}'].config(state="normal")
        if f'repeat_once_btn_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'repeat_once_btn_{key_set_id}'].config(state="normal")
        if f'repeat_infinity_btn_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'repeat_infinity_btn_{key_set_id}'].config(state="normal")
        if f'add_key_btn_{key_set_id}' in self.key_set_widget_refs:
            self.key_set_widget_refs[f'add_key_btn_{key_set_id}'].config(state="normal")
        self._refresh_key_chips()

    # ── Window geometry ───────────────────────────────────────────────────────

    def _fit_window_to_content(self):
        self.update_idletasks()
        content_height  = self.winfo_reqheight()
        screen_height   = self.winfo_screenheight()
        window_height   = min(content_height + 20, int(screen_height * 0.9))
        window_width    = min(520, int(self.winfo_screenwidth() * 0.35))
        position_key    = self.config_data.get("window_position", "top-left")
        x, y = self._calculate_window_position(window_width, window_height, position_key)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _calculate_window_position(self, width: int, height: int, position: str) -> tuple[int, int]:
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        positions = {
            "top-left":     (10, 10),
            "top-right":    (sw - width - 10, 10),
            "bottom-left":  (10, sh - height - 10),
            "bottom-right": (sw - width - 10, sh - height - 10),
        }
        return positions.get(position, ((sw - width) // 2, (sh - height) // 2))

    def _apply_window_settings(self):
        self.attributes('-alpha',   self.config_data.get("transparency", 1.0))
        self.attributes('-topmost', self.config_data.get("always_on_top", True))

    def _apply_fullscreen(self):
        if self.config_data.get("fullscreen", False):
            self.state('zoomed')

    # ── Widget factory helpers ────────────────────────────────────────────────

    def _make_button(self, parent, label: str, command) -> tk.Button:
        btn = tk.Button(
            parent, text=label, command=command,
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="hand2",
            activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
            padx=16, pady=6,
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=COLOR_ACCENT,   fg=COLOR_TEXT))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))
        return btn

    def _grid_widget(self, widget, **kwargs):
        kwargs.setdefault("ipady", CONTROL_HEIGHT)
        widget.grid(**kwargs)
        return widget

    def _pack_widget(self, widget, **kwargs):
        kwargs.setdefault("ipady", CONTROL_HEIGHT)
        widget.pack(**kwargs)
        return widget

    def _add_separator(self, parent):
        tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill="x")

    def _make_label(self, parent, text: str, width: int = None) -> tk.Label:
        kw = {"font": FONT_SMALL, "bg": parent["bg"], "fg": COLOR_TEXT_MUTED, "anchor": "w"}
        if width:
            kw["width"] = width
        return tk.Label(parent, text=text, **kw)

    # ── UI build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        if self.is_compact_mode:
            self._build_compact_ui()
        else:
            self._build_full_ui()
        self._update_action_button_state()
        self._apply_responsive_layout(self.winfo_width())

    def _build_full_ui(self):
        # Header
        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(header_frame, text="MOD PRESSER", font=FONT_TITLE,
                 bg=COLOR_BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        self.status_label = tk.Label(header_frame, text="IDLE", font=FONT_SMALL,
                                     bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MUTED)
        self.status_label.pack(side="right")

        # Body
        body = tk.Frame(self, bg=COLOR_BG_MAIN)
        body.pack(fill="both", expand=True, padx=CARD_PADDING, pady=CARD_PADDING)

        # Key set section
        self._add_separator(body)
        key_set_header = tk.Frame(body, bg=COLOR_BG_MAIN)
        key_set_header.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Label(key_set_header, text="KEY SETS", font=FONT_MAIN,
                 bg=COLOR_BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        key_set_toggle_btn = tk.Button(
            key_set_header, text="▼", font=FONT_SMALL,
            bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            command=lambda: self._toggle_section("key_sets")
        )
        key_set_toggle_btn.pack(side="right")
        self.key_set_toggle_btn = key_set_toggle_btn
        
        self.key_set_frame = tk.Frame(body, bg=COLOR_BG_MAIN)
        self.key_set_frame.pack(fill="both", expand=True, pady=(LAYOUT_GAP, 0))
        self.key_set_widget_refs = {}
        self._build_key_set_section()

        # Random move section
        self._add_separator(body)
        random_move_header = tk.Frame(body, bg=COLOR_BG_MAIN)
        random_move_header.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Label(random_move_header, text="RANDOM MOVE", font=FONT_MAIN,
                 bg=COLOR_BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        random_move_toggle_btn = tk.Button(
            random_move_header, text="▼", font=FONT_SMALL,
            bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            command=lambda: self._toggle_section("random_move")
        )
        random_move_toggle_btn.pack(side="right")
        self.random_move_toggle_btn = random_move_toggle_btn
        
        self.random_move_frame = tk.Frame(body, bg=COLOR_BG_MAIN)
        self.random_move_frame.pack(fill="both", expand=True, pady=(LAYOUT_GAP, 0))
        self._build_random_move_section()

        # Window settings section
        self._add_separator(body)
        window_settings_header = tk.Frame(body, bg=COLOR_BG_MAIN)
        window_settings_header.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Label(window_settings_header, text="WINDOW SETTINGS", font=FONT_MAIN,
                 bg=COLOR_BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        window_settings_toggle_btn = tk.Button(
            window_settings_header, text="▼", font=FONT_SMALL,
            bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            command=lambda: self._toggle_section("window_settings")
        )
        window_settings_toggle_btn.pack(side="right")
        self.window_settings_toggle_btn = window_settings_toggle_btn
        
        self.window_settings_frame = tk.Frame(body, bg=COLOR_BG_MAIN)
        self.window_settings_frame.pack(fill="both", expand=True, pady=(LAYOUT_GAP, 0))
        self._build_window_settings_section()

        # Footer
        self._add_separator(body)
        footer = tk.Frame(body, bg=COLOR_BG_MAIN)
        footer.pack(fill="x", pady=(LAYOUT_GAP, 0))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        self.footer_frame = footer

        self.save_btn = self._make_button(footer, "SAVE ALL SETTINGS", self._save_config)
        self._grid_widget(self.save_btn, row=0, column=0, sticky="ew", padx=(0, LAYOUT_GAP))

        self.compact_toggle_btn = self._make_button(footer, "COMPACT MODE", self._toggle_compact_mode_ui)
        self._grid_widget(self.compact_toggle_btn, row=0, column=1, sticky="ew")

    def _build_compact_ui(self):
        # Header
        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(header_frame, text="MOD PRESSER", font=FONT_TITLE,
                 bg=COLOR_BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        self.status_label = tk.Label(header_frame, text="IDLE", font=FONT_SMALL,
                                     bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MUTED)
        self.status_label.pack(side="right")

        body = tk.Frame(self, bg=COLOR_BG_MAIN)
        body.pack(fill="both", expand=True, padx=CARD_PADDING, pady=CARD_PADDING)

        # Key set cards for compact mode
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id", 1)
            key_set_name = key_set.get("name", f"Key Set {key_set_id}")
            
            self._add_separator(body)
            presser_card = tk.Frame(body, bg=COLOR_BG_CARD)
            presser_card.pack(fill="x", pady=(LAYOUT_GAP, 0))
            ph = tk.Frame(presser_card, bg=COLOR_BG_CARD)
            ph.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
            tk.Label(ph, text=key_set_name.upper(), font=FONT_MAIN, bg=COLOR_BG_CARD, fg=COLOR_HOVER).pack(side="left")
            pa = tk.Frame(presser_card, bg=COLOR_BG_CARD)
            pa.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, CARD_PADDING))
            toggle_btn = self._make_button(pa, "START", lambda kid=key_set_id: self._toggle_presser(kid))
            toggle_btn.pack(fill="x", ipady=4)
            self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'] = toggle_btn

        # Random move card
        self._add_separator(body)
        random_card = tk.Frame(body, bg=COLOR_BG_CARD)
        random_card.pack(fill="x", pady=(LAYOUT_GAP, 0))
        rh = tk.Frame(random_card, bg=COLOR_BG_CARD)
        rh.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(rh, text="RANDOM CLICK", font=FONT_MAIN, bg=COLOR_BG_CARD, fg=COLOR_HOVER).pack(side="left")
        ra = tk.Frame(random_card, bg=COLOR_BG_CARD)
        ra.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, CARD_PADDING))
        self.toggle_random_btn = self._make_button(ra, "START RANDOM CLICK", self._toggle_random)
        self.toggle_random_btn.pack(fill="x", ipady=4)

        # Footer
        self._add_separator(body)
        footer = tk.Frame(body, bg=COLOR_BG_MAIN)
        footer.pack(fill="x", pady=(LAYOUT_GAP, 0))
        footer.grid_columnconfigure(0, weight=1)
        self.compact_toggle_btn = self._make_button(footer, "FULL MODE", self._toggle_compact_mode_ui)
        self._grid_widget(self.compact_toggle_btn, row=0, column=0, sticky="ew")

    def _build_key_set_section(self):
        for w in self.key_set_frame.winfo_children():
            w.destroy()
        self.key_set_widget_refs.clear()

        key_sets = self.config_data.get("key_sets", [])
        if not key_sets:
            key_sets = [
                {
                    "id": 1,
                    "name": "Key Set 1",
                    "keys": [],
                    "delay_ms": 100,
                    "repeat_interval_sec": 30,
                    "use_every": True,
                    "repeat": "Infinity Mode",
                    "enabled": True
                }
            ]
            self.config_data["key_sets"] = key_sets

        # Create dynamic column grid
        cols = self.key_set_columns
        for i in range(cols):
            self.key_set_frame.grid_columnconfigure(i, weight=1)
        
        for idx, key_set in enumerate(key_sets):
            row = idx // cols
            col = idx % cols
            card = self._build_key_set_card(key_set)
            card.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else LAYOUT_GAP, 0), pady=(0, LAYOUT_GAP))
        
        self.after_idle(self._refresh_key_chips)
        self.after_idle(lambda: self._apply_responsive_layout(self.winfo_width()))

    def _build_key_set_card(self, key_set: dict):
        key_set_id = key_set.get("id", 1)
        card = tk.Frame(self.key_set_frame, bg=COLOR_BG_CARD)
        
        if not hasattr(self, 'key_set_widget_refs'):
            self.key_set_widget_refs = {}
        self.key_set_widget_refs[f'card_{key_set_id}'] = card
        
        # Header frame (always visible)
        header = tk.Frame(card, bg=COLOR_BG_CARD)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)
        
        # Expand/collapse button
        expand_btn = tk.Button(
            header, text="▲", font=("Segoe UI", 8),
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            width=3,
            command=lambda kid=key_set_id: self._toggle_key_set_collapse(kid)
        )
        self._grid_widget(expand_btn, row=0, column=0, sticky="w", padx=(0, 4))
        self.key_set_widget_refs[f'expand_btn_{key_set_id}'] = expand_btn
        
        # Name entry with better styling
        name_var = tk.StringVar(value=key_set.get("name", f"Key Set {key_set_id}"))
        name_entry = tk.Entry(
            header, textvariable=name_var, font=("Segoe UI", 10, "bold"),
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, insertbackground=COLOR_HOVER,
            relief="flat", bd=0,
        )
        self._grid_widget(name_entry, row=0, column=1, sticky="ew")
        name_entry.bind("<FocusOut>", lambda e, v=name_var, kid=key_set_id: self._on_key_set_name_change(kid, v.get()))
        name_entry.bind("<Return>",   lambda e, v=name_var, kid=key_set_id: self._on_key_set_name_change(kid, v.get()))
        name_entry.bind("<FocusIn>", lambda e: name_entry.config(bg=COLOR_BORDER))
        name_entry.bind("<FocusOut>", lambda e: name_entry.config(bg=COLOR_BG_INPUT))
        self.key_set_widget_refs[f'name_entry_{key_set_id}'] = name_entry
        
        # Enable checkbox with label
        enabled_var = tk.BooleanVar(value=key_set.get("enabled", True))
        enabled_frame = tk.Frame(header, bg=COLOR_BG_CARD)
        enabled_frame.grid(row=0, column=2, sticky="e", padx=(LAYOUT_GAP, 0))
        
        enabled_chk = tk.Checkbutton(
            enabled_frame, variable=enabled_var,
            command=lambda v=enabled_var, kid=key_set_id: self._on_key_set_enabled_change(kid, v.get()),
            bg=COLOR_BG_CARD, fg=COLOR_SUCCESS, activebackground=COLOR_BG_CARD,
            activeforeground=COLOR_SUCCESS, selectcolor=COLOR_BG_INPUT,
            relief="flat", bd=0, font=FONT_SMALL,
        )
        enabled_chk.pack(side="left")
        tk.Label(enabled_frame, text="Enabled", font=FONT_SMALL, bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED).pack(side="left", padx=(2, 0))
        self.key_set_widget_refs[f'enabled_chk_{key_set_id}'] = enabled_chk
        
        # Content frame (collapsible)
        content_frame = tk.Frame(card, bg=COLOR_BG_CARD)
        content_frame.pack(fill="x", expand=False, padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self.key_set_widget_refs[f'content_frame_{key_set_id}'] = content_frame

        # Trigger key section with separator
        trigger_section = tk.Frame(content_frame, bg=COLOR_BG_CARD)
        trigger_section.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Frame(trigger_section, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(0, LAYOUT_GAP))
        
        trigger_key_row = tk.Frame(trigger_section, bg=COLOR_BG_CARD)
        trigger_key_row.pack(fill="x")
        trigger_key_row.grid_columnconfigure(1, weight=1)
        self._make_label(trigger_key_row, "Trigger", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        trigger_hotkey_row = tk.Frame(trigger_key_row, bg=COLOR_BG_CARD)
        trigger_hotkey_row.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))
        trigger_hotkey_row.grid_columnconfigure(0, weight=1)

        trigger_key = key_set.get("trigger_key", "numpad_decimal")
        trigger_hotkey_display_btn = tk.Button(
            trigger_hotkey_row,
            text=trigger_key.upper(),
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="arrow",
            state="disabled", disabledforeground=COLOR_HOVER,
        )
        self._grid_widget(trigger_hotkey_display_btn, row=0, column=0, sticky="ew")
        trigger_hotkey_change_btn = self._make_button(
            trigger_hotkey_row, "CHANGE", lambda kid=key_set_id: self._begin_trigger_key_capture(kid)
        )
        self._grid_widget(trigger_hotkey_change_btn, row=0, column=1, padx=(LAYOUT_GAP, 0), sticky="e")
        self.key_set_widget_refs[f'trigger_hotkey_display_btn_{key_set_id}'] = trigger_hotkey_display_btn
        self.key_set_widget_refs[f'trigger_hotkey_change_btn_{key_set_id}'] = trigger_hotkey_change_btn

        # Key chips section with separator
        chips_section = tk.Frame(content_frame, bg=COLOR_BG_CARD)
        chips_section.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Frame(chips_section, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(0, LAYOUT_GAP))
        
        chips_row = tk.Frame(chips_section, bg=COLOR_BG_CARD)
        chips_row.pack(fill="x")
        chips_row.grid_columnconfigure(1, weight=1)
        self._make_label(chips_row, "Keys", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        chips_container = tk.Frame(chips_row, bg=COLOR_BG_INPUT)
        chips_container.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))
        self._render_key_chips(chips_container, key_set.get("keys", []), key_set_id)
        self.key_set_widget_refs[f'chips_container_{key_set_id}'] = chips_container

        # Settings section with separator
        settings_frame = tk.Frame(content_frame, bg=COLOR_BG_CARD)
        settings_frame.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Frame(settings_frame, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(0, LAYOUT_GAP))

        # Delay
        delay_row = tk.Frame(settings_frame, bg=COLOR_BG_CARD)
        delay_row.pack(fill="x", pady=(0, 2))
        delay_row.grid_columnconfigure(2, weight=1)
        self._make_label(delay_row, "Delay", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        delay_var = tk.IntVar(value=key_set.get("delay_ms", 100))
        delay_spinbox = tk.Spinbox(
            delay_row, from_=1, to=60000, textvariable=delay_var,
            font=FONT_MAIN, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
            buttonbackground=COLOR_BG_INPUT, width=6,
            command=lambda v=delay_var, kid=key_set_id: self._on_delay_change(kid, v.get()),
        )
        self._grid_widget(delay_spinbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        delay_spinbox.bind("<KeyRelease>", lambda e, v=delay_var, kid=key_set_id: self._on_delay_change(kid, v.get()))
        delay_spinbox.bind("<Return>", lambda e: self.focus_set())
        self._make_label(delay_row, "ms").grid(row=0, column=2, sticky="w", padx=(LAYOUT_GAP, 0))
        self.key_set_widget_refs[f'delay_spinbox_{key_set_id}'] = delay_spinbox

        # Repeat interval
        interval_row = tk.Frame(settings_frame, bg=COLOR_BG_CARD)
        interval_row.pack(fill="x", pady=(0, 2))
        interval_row.grid_columnconfigure(3, weight=1)
        self._make_label(interval_row, "Every", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        use_every_var        = tk.BooleanVar(value=key_set.get("use_every", True))
        repeat_interval_var  = tk.IntVar(value=key_set.get("repeat_interval_sec", 30))

        use_every_checkbox = tk.Checkbutton(
            interval_row, text="Use", variable=use_every_var,
            command=lambda v=use_every_var, kid=key_set_id: self._on_use_every_change(kid, v.get()),
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED, activebackground=COLOR_BG_CARD,
            activeforeground=COLOR_TEXT, selectcolor=COLOR_BG_INPUT,
            relief="flat", bd=0, font=FONT_SMALL,
        )
        self._grid_widget(use_every_checkbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        interval_spinbox = tk.Spinbox(
            interval_row, from_=1, to=3600, textvariable=repeat_interval_var,
            font=FONT_MAIN, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
            buttonbackground=COLOR_BG_INPUT, width=6,
            state="normal" if use_every_var.get() else "disabled",
            command=lambda v=repeat_interval_var, kid=key_set_id: self._on_repeat_interval_change(kid, v.get()),
        )
        self._grid_widget(interval_spinbox, row=0, column=2, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        interval_spinbox.bind("<KeyRelease>", lambda e, v=repeat_interval_var, kid=key_set_id: self._on_repeat_interval_change(kid, v.get()))
        interval_spinbox.bind("<Return>", lambda e: self.focus_set())

        self._make_label(interval_row, "s").grid(row=0, column=3, sticky="w", padx=(LAYOUT_GAP, 0))
        self.key_set_widget_refs[f'use_every_checkbox_{key_set_id}'] = use_every_checkbox
        self.key_set_widget_refs[f'repeat_interval_var_{key_set_id}'] = repeat_interval_var
        self.key_set_widget_refs[f'repeat_interval_spinbox_{key_set_id}'] = interval_spinbox

        # Repeat mode
        repeat_row = tk.Frame(settings_frame, bg=COLOR_BG_CARD)
        repeat_row.pack(fill="x", pady=(0, 2))
        self._make_label(repeat_row, "Repeat", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        repeat_mode_var = tk.StringVar(value=key_set.get("repeat", "Infinity Mode"))

        repeat_once_btn = tk.Button(
            repeat_row, text="ONCE", width=10,
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Once" else COLOR_BG_INPUT,
            fg=COLOR_TEXT  if repeat_mode_var.get() == "Once" else COLOR_TEXT_MUTED,
            font=FONT_MAIN, relief="flat", bd=0, cursor="hand2",
            command=lambda kid=key_set_id: self._on_repeat_mode_change(kid, "Once", repeat_mode_var, repeat_once_btn, repeat_infinity_btn),
        )
        self._grid_widget(repeat_once_btn, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        repeat_once_btn.bind("<Enter>", lambda e: repeat_once_btn.config(
            bg=COLOR_HOVER if repeat_mode_var.get() == "Once" else COLOR_ACCENT, fg=COLOR_TEXT))
        repeat_once_btn.bind("<Leave>", lambda e: repeat_once_btn.config(
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Once" else COLOR_BG_INPUT,
            fg=COLOR_TEXT if repeat_mode_var.get() == "Once" else COLOR_TEXT_MUTED))

        repeat_infinity_btn = tk.Button(
            repeat_row, text="INFINITY", width=10,
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Infinity Mode" else COLOR_BG_INPUT,
            fg=COLOR_TEXT  if repeat_mode_var.get() == "Infinity Mode" else COLOR_TEXT_MUTED,
            font=FONT_MAIN, relief="flat", bd=0, cursor="hand2",
            command=lambda kid=key_set_id: self._on_repeat_mode_change(kid, "Infinity Mode", repeat_mode_var, repeat_once_btn, repeat_infinity_btn),
        )
        self._grid_widget(repeat_infinity_btn, row=0, column=2, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        repeat_infinity_btn.bind("<Enter>", lambda e: repeat_infinity_btn.config(
            bg=COLOR_HOVER if repeat_mode_var.get() == "Infinity Mode" else COLOR_ACCENT, fg=COLOR_TEXT))
        repeat_infinity_btn.bind("<Leave>", lambda e: repeat_infinity_btn.config(
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Infinity Mode" else COLOR_BG_INPUT,
            fg=COLOR_TEXT if repeat_mode_var.get() == "Infinity Mode" else COLOR_TEXT_MUTED))

        self.key_set_widget_refs[f'repeat_once_btn_{key_set_id}'] = repeat_once_btn
        self.key_set_widget_refs[f'repeat_infinity_btn_{key_set_id}'] = repeat_infinity_btn

        # Add key section with separator
        add_key_section = tk.Frame(content_frame, bg=COLOR_BG_CARD)
        add_key_section.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Frame(add_key_section, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(0, LAYOUT_GAP))
        
        add_key_row = tk.Frame(add_key_section, bg=COLOR_BG_CARD)
        add_key_row.pack(fill="x")
        add_key_row.grid_columnconfigure(1, weight=1)
        self._make_label(add_key_row, "Add", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        add_key_btn = tk.Button(
            add_key_row, text="PRESS KEY TO ADD",
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="hand2",
            command=lambda kid=key_set_id: self._begin_add_key_capture(kid),
        )
        self._grid_widget(add_key_btn, row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, LAYOUT_GAP))
        add_key_btn.bind("<Enter>", lambda e: add_key_btn.config(bg=COLOR_ACCENT,   fg=COLOR_TEXT))
        add_key_btn.bind("<Leave>", lambda e: add_key_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))
        self.key_set_widget_refs[f'add_key_btn_{key_set_id}'] = add_key_btn

        # Start/stop presser section with separator
        action_section = tk.Frame(content_frame, bg=COLOR_BG_CARD)
        action_section.pack(fill="x", pady=(LAYOUT_GAP, CARD_PADDING))
        tk.Frame(action_section, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(0, LAYOUT_GAP))
        
        action_row = tk.Frame(action_section, bg=COLOR_BG_CARD)
        action_row.pack(fill="x")
        toggle_btn = tk.Button(
            action_row, text="START AUTO PRESSER",
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=16, pady=8,
            command=lambda kid=key_set_id: self._toggle_presser(kid)
        )
        toggle_btn.pack(fill="x")
        toggle_btn.bind("<Enter>", lambda e: toggle_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        toggle_btn.bind("<Leave>", lambda e: toggle_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))
        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'] = toggle_btn
        
        # Apply initial collapsed state
        if not key_set.get("enabled", True):
            content_frame.pack_forget()
            expand_btn.config(text="▼")
        
        return card

    def _build_random_move_section(self):
        for w in self.random_move_frame.winfo_children():
            w.destroy()

        random_cfg = self.config_data.get("random_move", {})
        if not random_cfg:
            random_cfg = {"min_sec": 5, "max_sec": 20, "delay_ms": 100}
            self.config_data["random_move"] = random_cfg
        else:
            random_cfg.setdefault("delay_ms", 100)

        card = tk.Frame(self.random_move_frame, bg=COLOR_BG_CARD)
        card.pack(fill="x", expand=False, pady=(0, LAYOUT_GAP))

        header = tk.Frame(card, bg=COLOR_BG_CARD)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(header, text="RANDOM CLICK (ZONE 5)", font=FONT_MAIN,
                 bg=COLOR_BG_CARD, fg=COLOR_HOVER).pack(side="left")

        settings = tk.Frame(card, bg=COLOR_BG_CARD)
        settings.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, 0))

        # Min row
        min_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        min_row.pack(fill="x", pady=(0, 2))
        min_row.grid_columnconfigure(2, weight=1)
        self._make_label(min_row, "Min", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        min_var = tk.IntVar(value=random_cfg.get("min_sec", 5))
        min_spinbox = tk.Spinbox(
            min_row, from_=1, to=60, textvariable=min_var,
            font=FONT_MAIN, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
            buttonbackground=COLOR_BG_INPUT, width=6,
            command=lambda v=min_var: self._on_random_min_change(v.get()),
        )
        self._grid_widget(min_spinbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        min_spinbox.bind("<KeyRelease>", lambda e, v=min_var: self._on_random_min_change(v.get()))
        min_spinbox.bind("<Return>", lambda e: self.focus_set())
        self._make_label(min_row, "sec").grid(row=0, column=2, sticky="w", padx=(LAYOUT_GAP, 0))
        self.min_spinbox = min_spinbox

        # Max row
        max_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        max_row.pack(fill="x", pady=(0, 2))
        max_row.grid_columnconfigure(2, weight=1)
        self._make_label(max_row, "Max", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        max_var = tk.IntVar(value=random_cfg.get("max_sec", 20))
        max_spinbox = tk.Spinbox(
            max_row, from_=1, to=60, textvariable=max_var,
            font=FONT_MAIN, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
            buttonbackground=COLOR_BG_INPUT, width=6,
            command=lambda v=max_var: self._on_random_max_change(v.get()),
        )
        self._grid_widget(max_spinbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        max_spinbox.bind("<KeyRelease>", lambda e, v=max_var: self._on_random_max_change(v.get()))
        max_spinbox.bind("<Return>", lambda e: self.focus_set())
        self._make_label(max_row, "sec").grid(row=0, column=2, sticky="w", padx=(LAYOUT_GAP, 0))
        self.max_spinbox = max_spinbox

        # Delay row
        delay_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        delay_row.pack(fill="x", pady=(0, 2))
        delay_row.grid_columnconfigure(2, weight=1)
        self._make_label(delay_row, "Delay", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        random_delay_var = tk.IntVar(value=random_cfg.get("delay_ms", 100))
        random_delay_spinbox = tk.Spinbox(
            delay_row, from_=1, to=60000, textvariable=random_delay_var,
            font=FONT_MAIN, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
            buttonbackground=COLOR_BG_INPUT, width=6,
            command=lambda v=random_delay_var: self._on_random_delay_change(v.get()),
        )
        self._grid_widget(random_delay_spinbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        random_delay_spinbox.bind("<KeyRelease>", lambda e, v=random_delay_var: self._on_random_delay_change(v.get()))
        random_delay_spinbox.bind("<Return>", lambda e: self.focus_set())
        self._make_label(delay_row, "ms").grid(row=0, column=2, sticky="w", padx=(LAYOUT_GAP, 0))
        self.random_delay_spinbox = random_delay_spinbox

        tk.Label(card, text="Randomly left-click in center zone (zone 5)",
                 font=FONT_SMALL, bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED).pack(padx=CARD_PADDING, pady=(LAYOUT_GAP, 0))

        action_row = tk.Frame(card, bg=COLOR_BG_CARD)
        action_row.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, CARD_PADDING))
        self.toggle_random_btn = self._make_button(action_row, "START RANDOM MOVE", self._toggle_random)
        self.toggle_random_btn.pack(fill="x", ipady=4)

    def _build_window_settings_section(self):
        for w in self.window_settings_frame.winfo_children():
            w.destroy()

        card = tk.Frame(self.window_settings_frame, bg=COLOR_BG_CARD)
        card.pack(fill="x", expand=False, pady=(0, LAYOUT_GAP))

        header = tk.Frame(card, bg=COLOR_BG_CARD)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(header, text="WINDOW SETTINGS", font=FONT_MAIN,
                 bg=COLOR_BG_CARD, fg=COLOR_HOVER).pack(side="left")

        settings = tk.Frame(card, bg=COLOR_BG_CARD)
        settings.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, 0))

        # Position
        position_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        position_row.pack(fill="x", pady=(0, 2))
        self._make_label(position_row, "Position", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        position_btn_frame = tk.Frame(position_row, bg=COLOR_BG_CARD)
        position_btn_frame.grid(row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))

        position_var = tk.StringVar(value=self.config_data.get("window_position", "top-left"))
        position_options = ["top-left", "top-right", "bottom-left", "bottom-right"]
        self.position_buttons = []
        for pos in position_options:
            is_active = position_var.get() == pos
            btn = tk.Button(
                position_btn_frame, text=pos.replace("-", " ").title(), width=12,
                bg=COLOR_ACCENT if is_active else COLOR_BG_INPUT,
                fg=COLOR_TEXT  if is_active else COLOR_TEXT_MUTED,
                font=FONT_SMALL, relief="flat", bd=0, cursor="hand2",
                command=lambda p=pos: self._on_window_position_change(p),
            )
            btn.pack(side="left", padx=2)
            self.position_buttons.append(btn)
        self.position_var = position_var

        # Transparency
        opacity_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        opacity_row.pack(fill="x", pady=(0, 2))
        opacity_row.grid_columnconfigure(2, weight=1)
        self._make_label(opacity_row, "Opacity", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        opacity_var = tk.DoubleVar(value=self.config_data.get("transparency", 1.0))
        opacity_scale = tk.Scale(
            opacity_row, from_=0.1, to=1.0, resolution=0.05,
            orient="horizontal", variable=opacity_var,
            command=self._on_opacity_change,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT, troughcolor=COLOR_BG_INPUT,
            highlightthickness=0, font=FONT_SMALL, length=150,
        )
        opacity_scale.grid(row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        self.opacity_var = opacity_var

        # Always on top
        on_top_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        on_top_row.pack(fill="x", pady=(0, 2))
        self._make_label(on_top_row, "On Top", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        always_on_top_var = tk.BooleanVar(value=self.config_data.get("always_on_top", True))
        always_on_top_chk = tk.Checkbutton(
            on_top_row, variable=always_on_top_var,
            command=lambda v=always_on_top_var: self._on_always_on_top_change(v.get()),
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED, activebackground=COLOR_BG_CARD,
            activeforeground=COLOR_TEXT, selectcolor=COLOR_BG_INPUT,
            relief="flat", bd=0, font=FONT_SMALL,
        )
        always_on_top_chk.grid(row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        self.always_on_top_var = always_on_top_var

        # Compact mode
        compact_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        compact_row.pack(fill="x", pady=(0, 2))
        self._make_label(compact_row, "Compact", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        compact_mode_var = tk.BooleanVar(value=self.config_data.get("compact_mode", False))
        compact_mode_chk = tk.Checkbutton(
            compact_row, variable=compact_mode_var,
            command=lambda v=compact_mode_var: self._on_compact_mode_change(v.get()),
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED, activebackground=COLOR_BG_CARD,
            activeforeground=COLOR_TEXT, selectcolor=COLOR_BG_INPUT,
            relief="flat", bd=0, font=FONT_SMALL,
        )
        compact_mode_chk.grid(row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        self.compact_mode_var = compact_mode_var

    # ── Key chips ─────────────────────────────────────────────────────────────

    def _render_key_chips(self, chips_container, keys: list, key_set_id: int = 1):
        for w in chips_container.winfo_children():
            w.destroy()
        if not keys:
            self._make_label(chips_container, "No keys").pack(padx=4, pady=2)
            return

        try:
            chips_container.update_idletasks()
            available_width = chips_container.winfo_width()
            if available_width <= 1:
                available_width = chips_container.winfo_reqwidth()
            if available_width <= 1:
                available_width = max(200, self.winfo_width() - 160)
        except tk.TclError:
            available_width = max(200, self.winfo_width() - 160)

        current_row = tk.Frame(chips_container, bg=COLOR_BG_INPUT)
        current_row.pack(fill="x", anchor="w")
        used_width = 0

        for idx, key_name in enumerate(keys):
            estimated_width = max(44, len(key_name) * 8 + 34)
            if used_width and used_width + estimated_width > available_width:
                current_row = tk.Frame(chips_container, bg=COLOR_BG_INPUT)
                current_row.pack(fill="x", anchor="w", pady=(2, 0))
                used_width = 0

            chip = tk.Frame(current_row, bg=COLOR_BG_MAIN)
            chip.pack(side="left", padx=1, pady=1)
            tk.Label(chip, text=key_name, font=FONT_MAIN, bg=COLOR_BG_MAIN,
                     fg=COLOR_HOVER, padx=4, pady=1).pack(side="left")
            remove_label = tk.Label(chip, text="X", font=FONT_MAIN, bg=COLOR_BG_MAIN,
                                    fg=COLOR_TEXT_MUTED, cursor="hand2", padx=2)
            remove_label.pack(side="left")
            remove_label.bind("<Button-1>", lambda e, i=idx, kid=key_set_id: self._remove_key_at_index(kid, i))
            remove_label.bind("<Enter>",    lambda e, w=remove_label: w.config(fg=COLOR_DANGER))
            remove_label.bind("<Leave>",    lambda e, w=remove_label: w.config(fg=COLOR_TEXT_MUTED))
            used_width += estimated_width

    def _refresh_key_chips(self):
        if not self.key_set_widget_refs or self.is_rebuilding:
            return
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id", 1)
            chips_container = self.key_set_widget_refs.get(f'chips_container_{key_set_id}')
            if not chips_container:
                continue
            try:
                if not chips_container.winfo_exists():
                    continue
                keys = key_set.get('keys', [])
                self._render_key_chips(chips_container, keys, key_set_id)
            except (tk.TclError, AttributeError):
                continue

    # ── Responsive layout ─────────────────────────────────────────────────────

    def _apply_responsive_layout(self, window_width: int):
        if self.is_compact_mode or self.is_rebuilding:
            return
        
        # Breakpoint: switch to 1 column below 800px width
        new_columns = 1 if window_width < 800 else 2
        
        if new_columns != self.key_set_columns:
            self.key_set_columns = new_columns
            self.is_rebuilding = True
            self._build_key_set_section()
            self.is_rebuilding = False

    # ── Config mutation handlers ──────────────────────────────────────────────

    def _on_key_set_name_change(self, key_set_id: int, name: str):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                key_set["name"] = name
                break
        self.has_unsaved_changes = True

    def _on_key_set_enabled_change(self, key_set_id: int, enabled: bool):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                key_set["enabled"] = bool(enabled)
                break
        self.has_unsaved_changes = True
        self._update_action_button_state()
        
        # Collapse/expand the card in place
        self._set_key_set_card_collapsed(key_set_id, not enabled)
        
        # Stop presser if disabled while running
        if not enabled and key_set_id in self.running_key_sets:
            self._toggle_presser(key_set_id)
        self._update_action_button_state()

    def _set_key_set_card_collapsed(self, key_set_id: int, collapsed: bool):
        card = self.key_set_widget_refs.get(f'card_{key_set_id}')
        if not card:
            return
        
        # Toggle visibility of content frame (everything except header)
        content_frame = self.key_set_widget_refs.get(f'content_frame_{key_set_id}')
        if content_frame:
            if collapsed:
                content_frame.pack_forget()
            else:
                content_frame.pack(fill="x", expand=False, padx=CARD_PADDING, pady=(0, CARD_PADDING))
        
        # Update expand/collapse button
        expand_btn = self.key_set_widget_refs.get(f'expand_btn_{key_set_id}')
        if expand_btn:
            expand_btn.config(text="▼" if collapsed else "▲")

    def _toggle_key_set_collapse(self, key_set_id: int):
        content_frame = self.key_set_widget_refs.get(f'content_frame_{key_set_id}')
        if not content_frame:
            return
        
        # Toggle based on current visibility
        is_visible = content_frame.winfo_ismapped()
        self._set_key_set_card_collapsed(key_set_id, is_visible)

    def _add_keys_from_string(self, key_string: str):
        if self.is_presser_running or not key_string.strip():
            return
        key_set = self.config_data.get("key_set", {})
        for token in re.split(r"[,\s]+", key_string):
            token = token.strip()
            if token:
                key_set.setdefault("keys", []).append(token)
        self.has_unsaved_changes = True
        self._update_action_button_state()
        self._build_key_set_section()

    def _on_delay_change(self, key_set_id: int, value):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                key_set["delay_ms"] = value
                break
        self.has_unsaved_changes = True
        self._update_action_button_state()

    def _on_repeat_interval_change(self, key_set_id: int, value: int):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                try:
                    val = int(value)
                except ValueError:
                    return
                key_set["repeat_interval_sec"] = val
                self.key_set_widget_refs[f'repeat_interval_var_{key_set_id}'].set(val)
                break
        self.has_unsaved_changes = True
        self._update_action_button_state()

    def _on_use_every_change(self, key_set_id: int, value: bool):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                key_set["use_every"] = bool(value)
                self.key_set_widget_refs[f'repeat_interval_spinbox_{key_set_id}'].config(state="normal" if value else "disabled")
                break
        self.has_unsaved_changes = True
        self._update_action_button_state()

    def _on_repeat_mode_change(self, key_set_id: int, mode: str, mode_var, once_btn, infinity_btn):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                key_set["repeat"] = mode
                break
        mode_var.set(mode)
        self.has_unsaved_changes = True
        self._update_action_button_state()
        if mode == "Once":
            once_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)
            infinity_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
        else:
            once_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
            infinity_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)

    def _remove_key_at_index(self, key_set_id: int, key_index: int):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                keys = key_set.get("keys", [])
                if key_index < len(keys):
                    keys.pop(key_index)
                break
        self.has_unsaved_changes = True
        self._update_action_button_state()
        self._build_key_set_section()

    def _on_random_min_change(self, value):
        if self.is_random_running:
            return
        try:
            val = int(value)
        except ValueError:
            return
        max_val = self.config_data.get("random_move", {}).get("max_sec", 20)
        if val > max_val:
            val = max_val
            if hasattr(self, 'min_spinbox'):
                self.min_spinbox.delete(0, "end")
                self.min_spinbox.insert(0, str(val))
        self.config_data.get("random_move", {})["min_sec"] = val
        self.has_unsaved_changes = True
        self._update_action_button_state()

    def _on_random_max_change(self, value):
        if self.is_random_running:
            return
        try:
            val = int(value)
        except ValueError:
            return
        min_val = self.config_data.get("random_move", {}).get("min_sec", 5)
        if val < min_val:
            val = min_val
            if hasattr(self, 'max_spinbox'):
                self.max_spinbox.delete(0, "end")
                self.max_spinbox.insert(0, str(val))
        self.config_data.get("random_move", {})["max_sec"] = val
        self.has_unsaved_changes = True
        self._update_action_button_state()

    def _on_random_delay_change(self, value):
        if self.is_random_running:
            return
        self.config_data.get("random_move", {})["delay_ms"] = value
        self.has_unsaved_changes = True
        self._update_action_button_state()

    def _on_window_position_change(self, position: str):
        self.config_data["window_position"] = position
        self.position_var.set(position)
        self.has_unsaved_changes = True
        position_options = ["top-left", "top-right", "bottom-left", "bottom-right"]
        for i, btn in enumerate(self.position_buttons):
            btn.config(
                bg=COLOR_ACCENT if position_options[i] == position else COLOR_BG_INPUT,
                fg=COLOR_TEXT  if position_options[i] == position else COLOR_TEXT_MUTED,
            )
        self.update_idletasks()
        x, y = self._calculate_window_position(self.winfo_width(), self.winfo_height(), position)
        self.geometry(f"+{x}+{y}")

    def _on_opacity_change(self, value):
        self.config_data["transparency"] = float(value)
        self.attributes('-alpha', float(value))
        self.has_unsaved_changes = True

    def _on_always_on_top_change(self, value: bool):
        self.config_data["always_on_top"] = bool(value)
        self.attributes('-topmost', bool(value))
        self.has_unsaved_changes = True

    def _on_compact_mode_change(self, value: bool):
        self.config_data["compact_mode"] = bool(value)
        self.is_compact_mode = bool(value)
        self.has_unsaved_changes = True
        self._build_ui()
        self._apply_window_settings()
        self.update_idletasks()
        self._fit_window_to_content()

    def _toggle_section(self, section_name: str):
        self.collapsed_sections[section_name] = not self.collapsed_sections[section_name]
        is_collapsed = self.collapsed_sections[section_name]
        
        if section_name == "key_sets":
            self.key_set_frame.pack_forget() if is_collapsed else self.key_set_frame.pack(fill="both", expand=True, pady=(LAYOUT_GAP, 0))
            self.key_set_toggle_btn.config(text="▲" if is_collapsed else "▼")
        elif section_name == "random_move":
            self.random_move_frame.pack_forget() if is_collapsed else self.random_move_frame.pack(fill="both", expand=True, pady=(LAYOUT_GAP, 0))
            self.random_move_toggle_btn.config(text="▲" if is_collapsed else "▼")
        elif section_name == "window_settings":
            self.window_settings_frame.pack_forget() if is_collapsed else self.window_settings_frame.pack(fill="both", expand=True, pady=(LAYOUT_GAP, 0))
            self.window_settings_toggle_btn.config(text="▲" if is_collapsed else "▼")
        
        self.update_idletasks()
        self._fit_window_to_content()

    def _toggle_compact_mode_ui(self):
        self.is_compact_mode = not self.is_compact_mode
        self.config_data["compact_mode"] = self.is_compact_mode
        self.has_unsaved_changes = True
        self._build_ui()
        self._apply_window_settings()
        self.update_idletasks()
        self._fit_window_to_content()

    # ── Start / stop actions ──────────────────────────────────────────────────

    def _collect_current_config(self) -> dict:
        return {
            "random_start_stop_key": self.config_data.get("random_start_stop_key", "numpad_multiply"),
            "key_sets":              self.config_data.get("key_sets", []),
            "random_move":           self.config_data.get("random_move", {}),
            "window_position":       self.config_data.get("window_position", "top-left"),
            "transparency":          self.config_data.get("transparency", 1.0),
            "always_on_top":         self.config_data.get("always_on_top", True),
            "compact_mode":          self.config_data.get("compact_mode", False),
            "fullscreen":            self.config_data.get("fullscreen", True),
        }

    def _save_config(self):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Save", "Cannot save configuration while running.", parent=self)
            return
        self.config_data = self._collect_current_config()
        save_config(self.config_data)
        self._restart_hotkey_listener()
        self.has_unsaved_changes = False
        self._update_action_button_state()
        messagebox.showinfo("Saved", "Config saved!", parent=self)

    def _toggle_presser(self, key_set_id: int):
        if key_set_id in self.running_key_sets:
            self._stop_presser(key_set_id)
        else:
            self.config_data = self._collect_current_config()
            self._start_presser(key_set_id)

    def _start_presser(self, key_set_id: int):
        self.running_key_sets.add(key_set_id)
        self.is_presser_running = True
        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].config(text="STOP AUTO PRESSER", bg=COLOR_DANGER, activebackground="#cc2233")
        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].bind("<Enter>", lambda e: self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].config(bg="#cc2233"))
        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].bind("<Leave>", lambda e: self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].config(bg=COLOR_DANGER))
        self.status_label.config(text=f"RUNNING - KEY SET {key_set_id} ACTIVE", fg=COLOR_SUCCESS)
        self._disable_settings_controls_for_key_set(key_set_id)

        key_sets = self.config_data.get("key_sets", [])
        key_set = None
        for ks in key_sets:
            if ks.get("id") == key_set_id:
                key_set = ks
                break
        
        if not key_set:
            return

        keys           = key_set.get("keys", [])
        repeat_mode    = key_set.get("repeat", "Infinity Mode")
        delay_s        = key_set.get("delay_ms", 100) / 1000.0
        repeat_interval_s = key_set.get("repeat_interval_sec", 1) * 1000 / 1000.0
        use_every      = key_set.get("use_every", True)

        if keys:
            thread = threading.Thread(
                target=self._presser_loop,
                args=(key_set_id, keys, delay_s, repeat_interval_s, repeat_mode, use_every),
                daemon=True,
            )
            thread.start()
            self.press_threads.append(thread)

    def _stop_presser(self, key_set_id: int):
        if key_set_id in self.running_key_sets:
            self.running_key_sets.remove(key_set_id)
        
        if not self.running_key_sets:
            self.is_presser_running = False
            self.individual_threads = None
            status_text  = "IDLE" if not self.is_random_running else "RUNNING - RANDOM MOVE ACTIVE"
            status_color = COLOR_TEXT_MUTED if not self.is_random_running else COLOR_SUCCESS
            self.status_label.config(text=status_text, fg=status_color)
            self._enable_settings_controls()
        else:
            self.status_label.config(text=f"RUNNING - {len(self.running_key_sets)} KEY SET(S) ACTIVE", fg=COLOR_SUCCESS)

        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].config(text="START AUTO PRESSER", bg=COLOR_ACCENT, activebackground=COLOR_HOVER)
        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].bind("<Enter>", lambda e: self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].config(bg=COLOR_HOVER))
        self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].bind("<Leave>", lambda e: self.key_set_widget_refs[f'toggle_presser_btn_{key_set_id}'].config(bg=COLOR_ACCENT))
        self._enable_settings_controls_for_key_set(key_set_id)
        
        for t in self.press_threads:
            if t.is_alive():
                t.join(timeout=0.2)
        self.press_threads.clear()

    def _toggle_random(self):
        if self.is_random_running:
            self._stop_random()
        else:
            self.config_data = self._collect_current_config()
            self._start_random()

    def _start_random(self):
        self.is_random_running = True
        self.toggle_random_btn.config(text="STOP RANDOM MOVE", bg=COLOR_DANGER, activebackground="#cc2233")
        self.toggle_random_btn.bind("<Enter>", lambda e: self.toggle_random_btn.config(bg="#cc2233"))
        self.toggle_random_btn.bind("<Leave>", lambda e: self.toggle_random_btn.config(bg=COLOR_DANGER))
        self.status_label.config(text="RUNNING - RANDOM MOVE ACTIVE", fg=COLOR_SUCCESS)
        self._disable_settings_controls()

        random_cfg = self.config_data.get("random_move", {})
        min_sec = random_cfg.get("min_sec", 5)
        max_sec = random_cfg.get("max_sec", 20)
        # Safe clamp min/max
        if min_sec > max_sec:
            min_sec, max_sec = max_sec, min_sec

        thread = threading.Thread(
            target=self._random_move_loop,
            args=(min_sec, max_sec, random_cfg.get("delay_ms", 100)),
            daemon=True,
        )
        thread.start()
        self.random_thread = thread

    def _stop_random(self):
        self.is_random_running = False
        self.toggle_random_btn.config(text="START RANDOM MOVE", bg=COLOR_ACCENT, activebackground=COLOR_HOVER)
        self.toggle_random_btn.bind("<Enter>", lambda e: self.toggle_random_btn.config(bg=COLOR_HOVER))
        self.toggle_random_btn.bind("<Leave>", lambda e: self.toggle_random_btn.config(bg=COLOR_ACCENT))
        status_text  = "IDLE" if not self.is_presser_running else "RUNNING - AUTO PRESSER ACTIVE"
        status_color = COLOR_TEXT_MUTED if not self.is_presser_running else COLOR_SUCCESS
        self.status_label.config(text=status_text, fg=status_color)
        if self.random_thread and self.random_thread.is_alive():
            self.random_thread.join(timeout=0.2)
        self.random_thread = None
        self._enable_settings_controls()

    # ── Background loops ──────────────────────────────────────────────────────

    def _presser_loop(self, key_set_id: int, keys: list, delay_s: float, repeat_interval_s: float = 1.0,
                      repeat_mode: str = None, use_every: bool = True):
        resolved_keys = [k for k in (resolve_key(k) for k in keys) if k is not None]

        if repeat_mode == "Once":
            for key in resolved_keys:
                if key_set_id not in self.running_key_sets:
                    break
                try:
                    keyboard_controller.press(key)
                    time.sleep(0.02)
                    keyboard_controller.release(key)
                except Exception as e:
                    print(f"Error pressing key {key}: {e}")
                time.sleep(delay_s)
            if key_set_id in self.running_key_sets:
                self.running_key_sets.remove(key_set_id)
                self.after(0, lambda: self._stop_presser(key_set_id))
        else:
            while key_set_id in self.running_key_sets:
                for key in resolved_keys:
                    if key_set_id not in self.running_key_sets:
                        break
                    try:
                        keyboard_controller.press(key)
                        time.sleep(0.02)
                        keyboard_controller.release(key)
                    except Exception as e:
                        print(f"Error pressing key {key}: {e}")
                    time.sleep(delay_s)
                if key_set_id in self.running_key_sets and use_every:
                    time.sleep(repeat_interval_s)

    def _random_move_loop(self, min_sec: float, max_sec: float, delay_ms: int = 100):
        between_click_delay_s = delay_ms / 1000.0
        
        # Get screen dimensions
        screen = self.winfo_screenwidth(), self.winfo_screenheight()
        screen_width, screen_height = screen
        
        # Calculate zone 5 (center zone) - 3x3 grid like numpad
        # Zone 5 is the center third of the screen
        zone_width = screen_width // 3
        zone_height = screen_height // 3
        zone5_x_start = zone_width
        zone5_x_end = zone_width * 2
        zone5_y_start = zone_height
        zone5_y_end = zone_height * 2

        while self.is_random_running:
            # Random position within zone 5
            x = random.randint(zone5_x_start, zone5_x_end - 1)
            y = random.randint(zone5_y_start, zone5_y_end - 1)
            
            hold_duration = random.uniform(min_sec, max_sec)
            
            try:
                # Move mouse to random position in zone 5
                mouse_controller.position = (x, y)
                time.sleep(0.05)
                
                # Hold left button for hold_duration
                mouse_controller.press(Button.left)
                time.sleep(hold_duration)
                mouse_controller.release(Button.left)
            except Exception as e:
                print(f"Error in random click: {e}")

            # Pause before next click
            if self.is_random_running:
                time.sleep(between_click_delay_s)

        self.is_random_running = False
        self.after(0, self._stop_random)

    # ── Hotkey listener ───────────────────────────────────────────────────────

    def _start_hotkey_listener(self):
        def on_key_press(key):
            # Check for Escape to cancel key capturing
            if key == Key.esc and (self.is_capturing_presser_hotkey or 
                                   self.is_capturing_random_hotkey or 
                                   self.is_capturing_add_key or
                                   self.is_capturing_trigger_key):
                self.after(0, self._cancel_all_captures)
                return

            if self.is_capturing_presser_hotkey:
                self._apply_presser_hotkey(key)
                return
            if self.is_capturing_random_hotkey:
                self._apply_random_hotkey(key)
                return
            if self.is_capturing_add_key:
                self._apply_add_key(key)
                return
            if self.is_capturing_trigger_key:
                self._apply_trigger_key(key)
                return

            # Clean up old held keys (older than 1.5 seconds)
            now = time.time()
            self.held_keys = {k: t for k, t in self.held_keys.items() if now - t < 1.5}

            # Check per-key-set trigger keys
            key_sets = self.config_data.get("key_sets", [])
            for key_set in key_sets:
                key_set_id = key_set.get("id")
                trigger_key = key_set.get("trigger_key")
                if not trigger_key or not key_set.get("enabled", True):
                    continue
                
                matched = normalize_hotkey(key) == normalize_hotkey(trigger_key)
                if not matched:
                    resolved = resolve_key(trigger_key.lower())
                    matched  = (key == resolved) or (
                        hasattr(key, 'name') and key.name and key.name.lower() == trigger_key.lower()
                    )
                if matched and key not in self.held_keys:
                    self.held_keys[key] = now
                    self.after(0, lambda kid=key_set_id: self._toggle_presser(kid))
                    return

            # Random hotkey
            random_hotkey = self.config_data.get("random_start_stop_key", "numpad_multiply")
            matched = normalize_hotkey(key) == normalize_hotkey(random_hotkey)
            if not matched:
                resolved = resolve_key(random_hotkey.lower())
                matched  = (key == resolved) or (
                    hasattr(key, 'name') and key.name and key.name.lower() == random_hotkey.lower()
                )
            if matched and key not in self.held_keys:
                self.held_keys[key] = now
                self.after(0, self._toggle_random)

        def on_key_release(key):
            self.held_keys.pop(key, None)

        self.hotkey_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()

    def _restart_hotkey_listener(self):
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
                self.hotkey_listener.join(timeout=0.5)
            except Exception as e:
                print(f"Error stopping hotkey listener: {e}")
        self._start_hotkey_listener()

    def _cancel_all_captures(self):
        self.is_capturing_presser_hotkey = False
        self.is_capturing_random_hotkey = False
        self.is_capturing_add_key = False
        self.is_capturing_trigger_key = False
        self.capturing_trigger_key_id = None

        if hasattr(self, 'presser_hotkey_display_btn'):
            self.presser_hotkey_display_btn.config(
                text=self.config_data.get("start_stop_key", "numpad_decimal"),
                bg=COLOR_BG_INPUT, fg=COLOR_HOVER
            )
        if hasattr(self, 'random_hotkey_display_btn'):
            self.random_hotkey_display_btn.config(
                text=self.config_data.get("random_start_stop_key", "numpad_multiply"),
                bg=COLOR_BG_INPUT, fg=COLOR_HOVER
            )
        if hasattr(self, 'add_key_btn'):
            self.add_key_btn.config(text="PRESS KEY TO ADD", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)

        # Reset trigger key buttons
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id")
            if f'trigger_hotkey_display_btn_{key_set_id}' in self.key_set_widget_refs:
                trigger_key = key_set.get("trigger_key", "numpad_decimal")
                self.key_set_widget_refs[f'trigger_hotkey_display_btn_{key_set_id}'].config(
                    text=trigger_key.upper(),
                    bg=COLOR_BG_INPUT, fg=COLOR_HOVER
                )

        self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)

    # ── Window events ─────────────────────────────────────────────────────────

    def _on_window_resize(self, event):
        if event.widget != self:
            return
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(200, lambda: self._apply_responsive_layout(event.width))

    def _on_close(self):
        self.is_presser_running = False
        self.is_random_running  = False
        self.individual_threads = None
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.destroy()

    # ── Key capture ───────────────────────────────────────────────────────────

    def _begin_presser_hotkey_capture(self):
        self.is_capturing_presser_hotkey = True
        self.presser_hotkey_display_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)

    def _begin_add_key_capture(self, key_set_id: int):
        self.is_capturing_add_key = True
        self.capturing_key_set_id = key_set_id
        self.key_set_widget_refs[f'add_key_btn_{key_set_id}'].config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_label.config(text="PRESS A KEY TO ADD", fg=COLOR_ACCENT)

    def _apply_presser_hotkey(self, key):
        key_str = self._resolve_captured_key_upper(key)
        if key_str is None:
            return
        self.config_data["start_stop_key"] = key_str
        self.presser_hotkey_display_btn.config(text=key_str, bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
        self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
        self.is_capturing_presser_hotkey = False
        save_config(self.config_data)
        self._restart_hotkey_listener()

    def _apply_add_key(self, key):
        key_set_id = getattr(self, 'capturing_key_set_id', 1)
        if key_set_id in self.running_key_sets:
            self.key_set_widget_refs[f'add_key_btn_{key_set_id}'].config(text="PRESS KEY TO ADD", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            self.is_capturing_add_key = False
            return
        key_str = self._resolve_captured_key_lower(key)
        if key_str:
            key_sets = self.config_data.get("key_sets", [])
            for key_set in key_sets:
                if key_set.get("id") == key_set_id:
                    keys = key_set.get("keys", [])
                    keys.append(key_str)
                    break
            self.has_unsaved_changes = True
            self._build_key_set_section()
            self.key_set_widget_refs[f'add_key_btn_{key_set_id}'].config(text="PRESS KEY TO ADD", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            self.is_capturing_add_key = False

    def _begin_random_hotkey_capture(self):
        self.is_capturing_random_hotkey = True
        self.random_hotkey_display_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)

    def _apply_random_hotkey(self, key):
        key_str = self._resolve_captured_key_upper(key)
        if key_str is None:
            return
        self.config_data["random_start_stop_key"] = key_str
        self.random_hotkey_display_btn.config(text=key_str, bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
        self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
        self.is_capturing_random_hotkey = False
        save_config(self.config_data)
        self._restart_hotkey_listener()

    def _begin_trigger_key_capture(self, key_set_id: int):
        self.is_capturing_trigger_key = True
        self.capturing_trigger_key_id = key_set_id
        self.key_set_widget_refs[f'trigger_hotkey_display_btn_{key_set_id}'].config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)

    def _apply_trigger_key(self, key):
        key_set_id = self.capturing_trigger_key_id
        if key_set_id is None:
            return
        
        key_str = self._resolve_captured_key_lower(key)
        if key_str is None:
            return
        
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            if key_set.get("id") == key_set_id:
                key_set["trigger_key"] = key_str
                break
        
        self.key_set_widget_refs[f'trigger_hotkey_display_btn_{key_set_id}'].config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
        self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
        self.is_capturing_trigger_key = False
        self.capturing_trigger_key_id = None
        self.has_unsaved_changes = True
        save_config(self.config_data)
        self._restart_hotkey_listener()

    # ── Key capture helpers ───────────────────────────────────────────────────

    def _resolve_captured_key_upper(self, key) -> str | None:
        """Resolve a captured pynput key to an uppercase display name."""
        if hasattr(key, 'vk') and key.vk is not None:
            return _vk_to_numpad_name(key.vk)
        if hasattr(key, 'name'):
            return key.name.upper()
        if hasattr(key, 'char') and key.char:
            return key.char.upper()
        return None

    def _resolve_captured_key_lower(self, key) -> str | None:
        """Resolve a captured pynput key to a lowercase key string for storage."""
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        if hasattr(key, 'vk') and key.vk is not None:
            return _vk_to_numpad_name_lower(key.vk)
        if hasattr(key, 'name'):
            return key.name.lower()
        return None


if __name__ == "__main__":
    app = App()
    app.mainloop()