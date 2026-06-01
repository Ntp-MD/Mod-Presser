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

MOUSE_BUTTON_MAP = {
    "mouse_4": Button.x1,  # Mouse button 4 (back/forward)
    "mouse_5": Button.x2,  # Mouse button 5 (back/forward)
    "button_x1": Button.x1,
    "button_x2": Button.x2,
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
        "delay_ms": 1000,
        "trigger_key": "numpad_multiply",
        "mode": "Order",
        "positions": []
    },
    "window_filter": {
        "enabled": False,
        "mode": "Window Title",
        "query": ""
    }
}

keyboard_controller = Controller()
mouse_controller = MouseController()


# ── Window utilities ─────────────────────────────────────────────────────────

def get_active_window_title() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception:
        return ""


def get_active_window_process_name() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes
        from ctypes import wintypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_process = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h_process:
            try:
                buf_size = wintypes.DWORD(260)
                buf = ctypes.create_unicode_buffer(buf_size.value)
                if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size)):
                    return os.path.basename(buf.value)
            finally:
                ctypes.windll.kernel32.CloseHandle(h_process)
    except Exception:
        pass
    return ""


def get_running_processes() -> list[str]:
    """Get list of unique process names from all visible windows."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        def enum_windows_proc(hwnd, lParam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                title_length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if title_length > 0:
                    pid = wintypes.DWORD()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                    h_process = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                    if h_process:
                        try:
                            buf_size = wintypes.DWORD(260)
                            buf = ctypes.create_unicode_buffer(buf_size.value)
                            if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size)):
                                process_name = os.path.basename(buf.value)
                                if process_name and process_name not in processes:
                                    processes.append(process_name)
                        finally:
                            ctypes.windll.kernel32.CloseHandle(h_process)
            return 1

        processes = []
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, ctypes.c_void_p)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
        return sorted(processes, key=str.lower)
    except Exception as e:
        print(f"Error getting running processes: {e}")
        return []


def get_running_windows() -> list[str]:
    """Get list of unique window titles from all visible windows."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        def enum_windows_proc(hwnd, lParam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                title_length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if title_length > 0:
                    buf = ctypes.create_unicode_buffer(title_length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, title_length + 1)
                    title = buf.value.strip()
                    if title and title not in titles:
                        titles.append(title)
            return 1

        titles = []
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, ctypes.c_void_p)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
        return sorted(titles, key=str.lower)
    except Exception as e:
        print(f"Error getting running windows: {e}")
        return []


def is_window_filter_matched(filter_cfg: dict) -> bool:
    try:
        if not filter_cfg or not filter_cfg.get("enabled", False):
            return True

        query = filter_cfg.get("query", "").strip().lower()
        if not query:
            return True

        mode = filter_cfg.get("mode", "Window Title")
        if mode == "Window Title":
            title = get_active_window_title().lower()
            return query in title
        elif mode == "Process Name":
            proc = get_active_window_process_name().lower()
            return query in proc or query + ".exe" in proc or proc in query

        return True
    except Exception as e:
        print(f"Error in window filter matching: {e}")
        return True  # Fail-safe: allow automation to continue if filter fails


# ── Key utilities ─────────────────────────────────────────────────────────────

def resolve_key(key_name: str):
    """Resolve a key name string to a pynput Key or character."""
    normalized = key_name.lower().strip()
    if normalized in SPECIAL_KEY_MAP:
        return SPECIAL_KEY_MAP[normalized]
    if normalized in NUMPAD_KEY_MAP:
        return NUMPAD_KEY_MAP[normalized]
    if normalized in MOUSE_BUTTON_MAP:
        return MOUSE_BUTTON_MAP[normalized]
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

    # Handle mouse buttons
    if key_value == Button.x1:
        return "mouse_4"
    if key_value == Button.x2:
        return "mouse_5"

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
    if text in MOUSE_BUTTON_MAP:
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
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        
        # If in dev mode, also save a copy to the output/ folder
        if not getattr(sys, 'frozen', False):
            dev_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(dev_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            output_config_path = os.path.join(output_dir, "config.json")
            with open(output_config_path, "w") as f_out:
                json.dump(config, f_out, indent=2)
    except IOError as e:
        print(f"Error saving config: {e}")


# ── Overlay Window ────────────────────────────────────────────────────────────

class OverlayWindow(tk.Toplevel):
    """
    Always-on-top translucent overlay that shows which features are running
    and provides stop buttons — visible even when the main window is minimized.
    """

    OVERLAY_BG       = "#0D0D0D"
    OVERLAY_ALPHA    = 0.88
    OVERLAY_ACCENT   = "#00C853"
    OVERLAY_DANGER   = "#FF3D00"
    OVERLAY_MUTED    = "#555555"
    OVERLAY_TEXT     = "#EEEEEE"
    OVERLAY_BORDER   = "#1E1E1E"

    def __init__(self, master: "App"):
        super().__init__(master)
        self.app = master

        self.overrideredirect(True)          # frameless
        self.attributes("-topmost", True)    # always on top
        self.attributes("-alpha", self.OVERLAY_ALPHA)
        self.configure(bg=self.OVERLAY_BG)
        self.resizable(False, False)

        # Show overlay by default (always visible status indicator)
        # self.withdraw()  # Removed: keep overlay visible at all times

        # Allow dragging
        self._drag_x = 0
        self._drag_y = 0
        self.bind("<ButtonPress-1>",   self._on_drag_start)
        self.bind("<B1-Motion>",       self._on_drag_motion)

        self._build()
        self._position_overlay()

        # Start update loop
        self._update_loop()

    # ── Drag ─────────────────────────────────────────────────────────────────

    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag_motion(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    # ── Position ──────────────────────────────────────────────────────────────

    def _position_overlay(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = sw - w - 16
        y = sh - h - 48           # bottom-right, above taskbar

        # Ensure overlay doesn't overflow screen edges
        if y < 16:
            y = 16
        if x < 16:
            x = 16

        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        outer = tk.Frame(self, bg=self.OVERLAY_BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg=self.OVERLAY_BG, padx=10, pady=8)
        inner.pack(fill="both", expand=True)

        # Title row
        title_row = tk.Frame(inner, bg=self.OVERLAY_BG)
        title_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            title_row, text="● MOD PRESSER", font=("Segoe UI", 9, "bold"),
            bg=self.OVERLAY_BG, fg=self.OVERLAY_ACCENT
        ).pack(side="left")

        # Show main window button
        show_btn = tk.Label(
            title_row, text="◱", font=("Segoe UI", 11),
            bg=self.OVERLAY_BG, fg=self.OVERLAY_MUTED, cursor="hand2"
        )
        show_btn.pack(side="right")
        show_btn.bind("<Button-1>", lambda e: self._show_main())
        show_btn.bind("<Enter>",    lambda e: show_btn.config(fg=self.OVERLAY_TEXT))
        show_btn.bind("<Leave>",    lambda e: show_btn.config(fg=self.OVERLAY_MUTED))

        # Separator
        tk.Frame(inner, bg=self.OVERLAY_BORDER, height=1).pack(fill="x", pady=(0, 6))

        # Feature rows container
        self._feature_frame = tk.Frame(inner, bg=self.OVERLAY_BG)
        self._feature_frame.pack(fill="x")

        self._render_features()

    def _render_features(self):
        for w in self._feature_frame.winfo_children():
            w.destroy()

        app = self.app
        any_active = False

        # Key sets
        for ks in app.config_data.get("key_sets", []):
            kid         = ks.get("id")
            name        = ks.get("name", f"Key Set {kid}")
            trigger_key = ks.get("trigger_key", "")
            running     = kid in app.running_key_sets
            if running:
                any_active = True
            self._add_feature_row(
                name, trigger_key, running,
                lambda k=kid: app._toggle_presser(k)
            )

        # Random move
        random_cfg     = app.config_data.get("random_move", {})
        random_trigger = random_cfg.get("trigger_key", "")
        random_running = app.is_random_running
        if random_running:
            any_active = True
        self._add_feature_row(
            "Random Move", random_trigger, random_running,
            lambda: app._toggle_random()
        )

        # Window Filter Match Status
        filter_cfg = app.config_data.get("window_filter", {})
        if filter_cfg.get("enabled", False):
            try:
                is_matched = is_window_filter_matched(filter_cfg)
                active_title = get_active_window_title()
                if not active_title:
                    active_title = "No active window"
                else:
                    active_title = active_title.strip()
                self._add_filter_row("Game Match", is_matched, active_title)
            except Exception as e:
                print(f"Error updating window filter status in overlay: {e}")
                # Show error state in overlay
                self._add_filter_row("Game Match", False, "Error")

        # If nothing running, show idle text
        if not any_active and not filter_cfg.get("enabled", False):
            tk.Label(
                self._feature_frame, text="No features running",
                font=("Segoe UI", 8), bg=self.OVERLAY_BG,
                fg=self.OVERLAY_MUTED
            ).pack(anchor="w", pady=2)

        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 220)
        h = self.winfo_reqheight()
        x = self.winfo_x()
        y = self.winfo_y()

        # Ensure overlay stays within screen bounds after resize
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        if x + w > sw - 16:
            x = sw - w - 16
        if y + h > sh - 48:
            y = sh - h - 48
        if y < 16:
            y = 16
        if x < 16:
            x = 16

        self.geometry(f"{w}x{h}+{x}+{y}")

    def _add_feature_row(self, name: str, trigger_key: str, running: bool, stop_cmd):
        # ── Outer row ─────────────────────────────────────────────────────────
        row = tk.Frame(self._feature_frame, bg=self.OVERLAY_BG)
        row.pack(fill="x", pady=2)

        # Status dot
        dot_color = self.OVERLAY_ACCENT if running else self.OVERLAY_MUTED
        tk.Label(
            row, text="●", font=("Segoe UI", 8),
            bg=self.OVERLAY_BG, fg=dot_color
        ).pack(side="left", padx=(0, 5))

        # Left info block: name + hotkey hint
        info = tk.Frame(row, bg=self.OVERLAY_BG)
        info.pack(side="left", fill="x", expand=True)

        name_fg = self.OVERLAY_TEXT if running else self.OVERLAY_MUTED
        tk.Label(
            info, text=name, font=("Segoe UI", 8, "bold" if running else "normal"),
            bg=self.OVERLAY_BG, fg=name_fg, anchor="w"
        ).pack(anchor="w")

        # Trigger key hint below name
        if trigger_key:
            key_display = trigger_key.upper().replace("NUMPAD_", "NUM ")
            hint_text   = f"[{key_display}] to toggle"
            tk.Label(
                info, text=hint_text,
                font=("Segoe UI", 7), bg=self.OVERLAY_BG,
                fg=self.OVERLAY_ACCENT if running else "#3a3a3a",
                anchor="w"
            ).pack(anchor="w")

        # Right side: STOP button or idle badge
        if running:
            stop_lbl = tk.Label(
                row, text="■ STOP", font=("Segoe UI", 7, "bold"),
                bg=self.OVERLAY_DANGER, fg=self.OVERLAY_TEXT,
                padx=6, pady=3, cursor="hand2"
            )
            stop_lbl.pack(side="right", padx=(8, 0))
            stop_lbl.bind("<Button-1>", lambda e, cmd=stop_cmd: cmd())
            stop_lbl.bind("<Enter>",    lambda e, w=stop_lbl: w.config(bg="#cc2000"))
            stop_lbl.bind("<Leave>",    lambda e, w=stop_lbl: w.config(bg=self.OVERLAY_DANGER))
        else:
            tk.Label(
                row, text="idle", font=("Segoe UI", 7),
                bg=self.OVERLAY_BG, fg="#3a3a3a"
            ).pack(side="right", padx=(8, 0))

        # Thin separator under each row
        tk.Frame(self._feature_frame, bg=self.OVERLAY_BORDER, height=1).pack(fill="x", pady=(0, 1))

    def _add_filter_row(self, name: str, is_matched: bool, active_title: str):
        # ── Outer row ─────────────────────────────────────────────────────────
        row = tk.Frame(self._feature_frame, bg=self.OVERLAY_BG)
        row.pack(fill="x", pady=2)

        # Status dot (green if matched, red/orange if not matched)
        dot_color = self.OVERLAY_ACCENT if is_matched else self.OVERLAY_DANGER
        tk.Label(
            row, text="●", font=("Segoe UI", 8),
            bg=self.OVERLAY_BG, fg=dot_color
        ).pack(side="left", padx=(0, 5))

        # Left info block: name + active window title
        info = tk.Frame(row, bg=self.OVERLAY_BG)
        info.pack(side="left", fill="x", expand=True)

        name_fg = self.OVERLAY_TEXT if is_matched else self.OVERLAY_MUTED
        tk.Label(
            info, text=name, font=("Segoe UI", 8, "bold"),
            bg=self.OVERLAY_BG, fg=name_fg, anchor="w"
        ).pack(anchor="w")

        # Active window title hint below name
        truncated_title = active_title[:24] + "..." if len(active_title) > 24 else active_title
        hint_text = f"Active: {truncated_title}"
        tk.Label(
            info, text=hint_text,
            font=("Segoe UI", 7), bg=self.OVERLAY_BG,
            fg=self.OVERLAY_ACCENT if is_matched else "#888888",
            anchor="w"
        ).pack(anchor="w")

        # Right side: match status text
        status_text = "MATCHED" if is_matched else "PAUSED"
        status_bg = self.OVERLAY_ACCENT if is_matched else "#333333"
        status_fg = self.OVERLAY_TEXT if is_matched else self.OVERLAY_MUTED
        tk.Label(
            row, text=status_text, font=("Segoe UI", 7, "bold"),
            bg=status_bg, fg=status_fg,
            padx=6, pady=3
        ).pack(side="right", padx=(8, 0))

        # Thin separator under each row
        tk.Frame(self._feature_frame, bg=self.OVERLAY_BORDER, height=1).pack(fill="x", pady=(0, 1))

    def _show_main(self):
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()

    # ── Update loop ───────────────────────────────────────────────────────────

    def _update_loop(self):
        try:
            if self.winfo_exists():
                # Always render features to update real-time window filter match status
                self._render_features()
                self.after(500, self._update_loop)
        except tk.TclError:
            pass

    def _should_update(self) -> bool:
        """Check if any running state changed since last update."""
        app = self.app
        key_sets = app.config_data.get("key_sets", [])

        # Check if any key set running state changed
        for ks in key_sets:
            kid = ks.get("id")
            was_running = getattr(self, f'_was_running_{kid}', False)
            is_running = kid in app.running_key_sets
            if was_running != is_running:
                setattr(self, f'_was_running_{kid}', is_running)
                return True

        # Check if random move running state changed
        was_random_running = getattr(self, '_was_random_running', False)
        is_random_running = app.is_random_running
        if was_random_running != is_random_running:
            self._was_random_running = is_random_running
            return True

        return False


# ── Main App ──────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Key Presser")
        self.resizable(True, True)
        self.configure(bg=COLOR_BG_MAIN)
        self.minsize(1000, 750)

        self.config_data = load_config()
        self.is_presser_running = False
        self.is_random_running  = False
        self.press_threads:     list[threading.Thread] = []
        self.random_thread:     threading.Thread | None = None
        self.individual_threads = None
        self.hotkey_listener:   keyboard.Listener | None = None
        self.held_keys:         dict = {}
        self.running_key_sets:  set[int] = set()

        self.is_capturing_presser_hotkey = False
        self.is_capturing_random_hotkey  = False
        self.is_capturing_add_key        = False
        self.is_capturing_trigger_key    = False
        self.is_capturing_random_trigger_key = False
        self.capturing_trigger_key_id    = None
        self.capturing_key_set_id        = None   # FIX: always initialized
        self.has_unsaved_changes = False

        self.current_tab = "key_sets"
        self.key_set_columns = 1
        self.is_rebuilding = False

        self._resize_after_id = None

        self.bind('<Configure>', self._on_window_resize)
        self._build_ui()
        self._start_hotkey_listener()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.update_idletasks()
        self._fit_window_to_content()

        # Create overlay after main window is ready
        self.after(200, self._create_overlay)

    def _create_overlay(self):
        self.overlay = OverlayWindow(self)
        # Removed minimize/restore bindings since overlay is now always visible

    def _on_window_minimize(self, event):
        """Show overlay when main window is minimized."""
        if hasattr(self, 'overlay') and self.overlay.winfo_exists():
            self.overlay.deiconify()

    def _on_window_restore(self, event):
        """Hide overlay when main window is restored."""
        if hasattr(self, 'overlay') and self.overlay.winfo_exists():
            self.overlay.withdraw()

    # ── UI state helpers ──────────────────────────────────────────────────────

    def _update_action_button_state(self):
        pass

    def _disable_settings_controls(self):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id", 1)
            self._disable_settings_controls_for_key_set(key_set_id)
        # FIX: also disable random section controls
        if hasattr(self, 'random_delay_spinbox'):
            self.random_delay_spinbox.config(state="disabled")
        if hasattr(self, 'record_btn'):
            self.record_btn.config(state="disabled")
        if hasattr(self, 'clear_positions_btn'):
            self.clear_positions_btn.config(state="disabled")
        if hasattr(self, 'order_mode_btn'):
            self.order_mode_btn.config(state="disabled")
        if hasattr(self, 'random_mode_btn'):
            self.random_mode_btn.config(state="disabled")
        if hasattr(self, 'window_filter_chk'):
            self.window_filter_chk.config(state="disabled")
        if hasattr(self, 'window_filter_title_btn'):
            self.window_filter_title_btn.config(state="disabled")
        if hasattr(self, 'window_filter_process_btn'):
            self.window_filter_process_btn.config(state="disabled")
        if hasattr(self, 'window_filter_entry'):
            self.window_filter_entry.config(state="disabled", insertofftime=0)
        if hasattr(self, 'save_btn'):
            self.save_btn.config(state="disabled")

    def _disable_settings_controls_for_key_set(self, key_set_id: int):
        refs = self.key_set_widget_refs
        if f'name_entry_{key_set_id}' in refs:
            refs[f'name_entry_{key_set_id}'].config(state="disabled", insertofftime=0)
        if f'delay_spinbox_{key_set_id}' in refs:
            refs[f'delay_spinbox_{key_set_id}'].config(state="disabled")
        if f'repeat_interval_spinbox_{key_set_id}' in refs:
            refs[f'repeat_interval_spinbox_{key_set_id}'].config(state="disabled")
        if f'use_every_checkbox_{key_set_id}' in refs:
            refs[f'use_every_checkbox_{key_set_id}'].config(state="disabled")
        if f'repeat_once_btn_{key_set_id}' in refs:
            refs[f'repeat_once_btn_{key_set_id}'].config(state="disabled")
        if f'repeat_infinity_btn_{key_set_id}' in refs:
            refs[f'repeat_infinity_btn_{key_set_id}'].config(state="disabled")
        if f'add_key_btn_{key_set_id}' in refs:
            refs[f'add_key_btn_{key_set_id}'].config(state="disabled")
        self._refresh_key_chips()

    def _enable_settings_controls(self):
        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id", 1)
            self._enable_settings_controls_for_key_set(key_set_id)
        # FIX: also re-enable random section controls
        if hasattr(self, 'random_delay_spinbox'):
            self.random_delay_spinbox.config(state="normal")
        if hasattr(self, 'record_btn'):
            self.record_btn.config(state="normal")
        if hasattr(self, 'clear_positions_btn'):
            self.clear_positions_btn.config(state="normal")
        if hasattr(self, 'order_mode_btn'):
            self.order_mode_btn.config(state="normal")
        if hasattr(self, 'random_mode_btn'):
            self.random_mode_btn.config(state="normal")
        if hasattr(self, 'window_filter_chk'):
            self.window_filter_chk.config(state="normal")
        if hasattr(self, 'window_filter_title_btn'):
            self.window_filter_title_btn.config(state="normal")
        if hasattr(self, 'window_filter_process_btn'):
            self.window_filter_process_btn.config(state="normal")
        if hasattr(self, 'window_filter_entry'):
            self.window_filter_entry.config(state="normal", insertofftime=600)
        if hasattr(self, 'save_btn'):
            self.save_btn.config(state="normal")

    def _enable_settings_controls_for_key_set(self, key_set_id: int):
        refs = self.key_set_widget_refs
        if f'name_entry_{key_set_id}' in refs:
            refs[f'name_entry_{key_set_id}'].config(state="normal", insertofftime=600)
        if f'delay_spinbox_{key_set_id}' in refs:
            refs[f'delay_spinbox_{key_set_id}'].config(state="normal")
        if f'repeat_interval_spinbox_{key_set_id}' in refs:
            use_every = True
            for ks in self.config_data.get("key_sets", []):
                if ks.get("id") == key_set_id:
                    use_every = ks.get("use_every", True)
                    break
            refs[f'repeat_interval_spinbox_{key_set_id}'].config(
                state="normal" if use_every else "disabled"
            )
        if f'use_every_checkbox_{key_set_id}' in refs:
            refs[f'use_every_checkbox_{key_set_id}'].config(state="normal")
        if f'repeat_once_btn_{key_set_id}' in refs:
            refs[f'repeat_once_btn_{key_set_id}'].config(state="normal")
        if f'repeat_infinity_btn_{key_set_id}' in refs:
            refs[f'repeat_infinity_btn_{key_set_id}'].config(state="normal")
        if f'add_key_btn_{key_set_id}' in refs:
            refs[f'add_key_btn_{key_set_id}'].config(state="normal")
        self._refresh_key_chips()

    # ── Window geometry ───────────────────────────────────────────────────────

    def _fit_window_to_content(self):
        self.update_idletasks()
        content_height  = self.winfo_reqheight()
        screen_height   = self.winfo_screenheight()
        screen_width    = self.winfo_screenwidth()

        # Minimum width 1000px, maintain 4:3 aspect ratio
        min_width = 1000
        min_height = int(min_width * 3 / 4)

        # Calculate window dimensions based on content, but respect aspect ratio
        window_height = min(content_height + 20, int(screen_height * 0.9))
        window_width = int(window_height * 4 / 3)

        # Ensure minimum dimensions
        if window_width < min_width:
            window_width = min_width
            window_height = min_height
        if window_height < min_height:
            window_height = min_height
            window_width = int(window_height * 4 / 3)

        # Ensure window fits on screen
        if window_width > screen_width:
            window_width = screen_width
            window_height = int(window_width * 3 / 4)

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

    def _select_tab(self, tab_id: str):
        pass

    # ── UI build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._build_full_ui()
        self._update_action_button_state()
        self._apply_responsive_layout(self.winfo_width())

    def _build_full_ui(self):
        # Header (pinned at top)
        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(side="top", fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(header_frame, text="MOD PRESSER", font=FONT_TITLE,
                 bg=COLOR_BG_MAIN, fg=COLOR_HOVER).pack(side="left")
        self.status_label = tk.Label(header_frame, text="IDLE", font=FONT_SMALL,
                                     bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MUTED)
        self.status_label.pack(side="right")

        # Footer (pinned at bottom)
        footer = tk.Frame(self, bg=COLOR_BG_MAIN)
        footer.pack(side="bottom", fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        self._add_separator(footer)
        footer_buttons = tk.Frame(footer, bg=COLOR_BG_MAIN)
        footer_buttons.pack(fill="x", pady=(LAYOUT_GAP, 0))
        footer_buttons.grid_columnconfigure(0, weight=1)
        footer_buttons.grid_columnconfigure(1, weight=1)
        self.footer_frame = footer_buttons

        self.save_btn = self._make_button(footer_buttons, "SAVE ALL SETTINGS", self._save_config)
        self._grid_widget(self.save_btn, row=0, column=0, sticky="ew", padx=(0, LAYOUT_GAP))

        self.clear_config_btn = self._make_button(footer_buttons, "CLEAR CONFIG", self._clear_config)
        self._grid_widget(self.clear_config_btn, row=0, column=1, sticky="ew")

        # Body (middle scrollable container)
        body = tk.Frame(self, bg=COLOR_BG_MAIN)
        body.pack(side="top", fill="both", expand=True, padx=CARD_PADDING, pady=CARD_PADDING)

        # Create Canvas and Scrollbar
        canvas = tk.Canvas(body, bg=COLOR_BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.main_layout = tk.Frame(canvas, bg=COLOR_BG_MAIN)
        canvas_window = canvas.create_window((0, 0), window=self.main_layout, anchor="nw")

        # Keep main_layout width matched with canvas width
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_canvas)

        # Update scrollregion when content changes
        def configure_layout(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.main_layout.bind("<Configure>", configure_layout)

        # Global Mousewheel scroll binding
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        self.bind_all("<MouseWheel>", _on_mousewheel)

        # Key sets frame (top-left or single column depending on layout mode)
        self.key_set_frame = tk.Frame(self.main_layout, bg=COLOR_BG_MAIN)
        self.key_set_widget_refs = {}
        self._build_key_set_section()

        # Random move frame
        self.random_move_frame = tk.Frame(self.main_layout, bg=COLOR_BG_MAIN)
        self._build_random_move_section()

        # Window Filter frame
        self.window_filter_frame = tk.Frame(self.main_layout, bg=COLOR_BG_MAIN)
        self._build_window_filter_section()

        # Apply default single-column layout first
        self.key_set_frame.pack(fill="both", expand=True, pady=(0, LAYOUT_GAP * 2))
        self.random_move_frame.pack(fill="x", pady=(0, LAYOUT_GAP * 2))
        self.window_filter_frame.pack(fill="x")

        # Then apply responsive layout based on window width
        self.after_idle(lambda: self._apply_responsive_layout(self.winfo_width()))

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

        cols = self.key_set_columns
        for i in range(cols):
            self.key_set_frame.grid_columnconfigure(i, weight=1)

        for idx, key_set in enumerate(key_sets):
            row = idx // cols
            col = idx % cols
            card = self._build_key_set_card(key_set)
            card.grid(row=row, column=col, sticky="ew",
                      padx=(0 if col == 0 else LAYOUT_GAP, 0), pady=(0, LAYOUT_GAP))
            self._set_key_set_card_collapsed(key_set.get("id", 1), not key_set.get("enabled", True))

        # Add key set button
        add_btn_row = tk.Frame(self.key_set_frame, bg=COLOR_BG_MAIN)
        add_btn_row.grid(row=len(key_sets), column=0, columnspan=cols, sticky="ew", pady=(LAYOUT_GAP, 0))
        add_btn = self._make_button(add_btn_row, "+ ADD KEY SET", self._add_key_set)
        add_btn.pack(fill="x", ipady=4)

        self.after_idle(self._refresh_key_chips)

    def _build_key_set_card(self, key_set: dict):
        key_set_id = key_set.get("id", 1)
        card = tk.Frame(self.key_set_frame, bg=COLOR_BG_CARD)

        if not hasattr(self, 'key_set_widget_refs'):
            self.key_set_widget_refs = {}
        self.key_set_widget_refs[f'card_{key_set_id}'] = card

        # Header frame
        header = tk.Frame(card, bg=COLOR_BG_CARD)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=0)

        name_var = tk.StringVar(value=key_set.get("name", f"Key Set {key_set_id}"))
        name_entry = tk.Entry(
            header, textvariable=name_var, font=("Segoe UI", 10, "bold"),
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, insertbackground=COLOR_HOVER,
            relief="flat", bd=0,
        )
        self._grid_widget(name_entry, row=0, column=0, sticky="ew")
        name_entry.bind("<FocusOut>", lambda e, v=name_var, kid=key_set_id: self._on_key_set_name_change(kid, v.get()))
        name_entry.bind("<Return>",   lambda e, v=name_var, kid=key_set_id: self._on_key_set_name_change(kid, v.get()))
        name_entry.bind("<FocusIn>",  lambda e: name_entry.config(bg=COLOR_BORDER))
        name_entry.bind("<FocusOut>", lambda e: name_entry.config(bg=COLOR_BG_INPUT))
        self.key_set_widget_refs[f'name_entry_{key_set_id}'] = name_entry

        enabled_var = tk.BooleanVar(value=key_set.get("enabled", True))
        enabled_frame = tk.Frame(header, bg=COLOR_BG_CARD)
        enabled_frame.grid(row=0, column=1, sticky="e", padx=(LAYOUT_GAP, 0))

        enabled_chk = tk.Checkbutton(
            enabled_frame, variable=enabled_var,
            command=lambda v=enabled_var, kid=key_set_id: self._on_key_set_enabled_change(kid, v.get()),
            bg=COLOR_BG_CARD, fg=COLOR_SUCCESS, activebackground=COLOR_BG_CARD,
            activeforeground=COLOR_SUCCESS, selectcolor=COLOR_BG_INPUT,
            relief="flat", bd=0, font=FONT_SMALL,
        )
        enabled_chk.pack(side="left")
        tk.Label(enabled_frame, text="Enabled", font=FONT_SMALL,
                 bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED).pack(side="left", padx=(2, 0))
        self.key_set_widget_refs[f'enabled_chk_{key_set_id}'] = enabled_chk

        delete_btn = tk.Button(
            header, text="✕", font=("Segoe UI", 10, "bold"),
            bg=COLOR_BG_CARD, fg=COLOR_DANGER, relief="flat", bd=0, cursor="hand2",
            width=2,
            command=lambda kid=key_set_id: self._delete_key_set(kid)
        )
        delete_btn.grid(row=0, column=2, sticky="e", padx=(LAYOUT_GAP, 0))
        self.key_set_widget_refs[f'delete_btn_{key_set_id}'] = delete_btn

        # Content frame (collapsible)
        content_frame = tk.Frame(card, bg=COLOR_BG_CARD)
        content_frame.pack(fill="x", expand=False, padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self.key_set_widget_refs[f'content_frame_{key_set_id}'] = content_frame

        # Trigger key
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

        # Key chips
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

        # Settings
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
            command=lambda kid=key_set_id: self._on_delay_change(kid, delay_spinbox.get()),
        )
        self._grid_widget(delay_spinbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        delay_spinbox.bind("<KeyRelease>", lambda e, kid=key_set_id: self._on_delay_change(kid, delay_spinbox.get()))
        delay_spinbox.bind("<Return>", lambda e: self.focus_set())
        self._make_label(delay_row, "ms").grid(row=0, column=2, sticky="w", padx=(LAYOUT_GAP, 0))
        self.key_set_widget_refs[f'delay_spinbox_{key_set_id}'] = delay_spinbox

        # Repeat interval
        interval_row = tk.Frame(settings_frame, bg=COLOR_BG_CARD)
        interval_row.pack(fill="x", pady=(0, 2))
        interval_row.grid_columnconfigure(3, weight=1)
        self._make_label(interval_row, "Every", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        use_every_var       = tk.BooleanVar(value=key_set.get("use_every", True))
        repeat_interval_var = tk.IntVar(value=key_set.get("repeat_interval_sec", 30))

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
            command=lambda kid=key_set_id: self._on_repeat_interval_change(kid, interval_spinbox.get()),
        )
        self._grid_widget(interval_spinbox, row=0, column=2, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        interval_spinbox.bind("<KeyRelease>", lambda e, kid=key_set_id: self._on_repeat_interval_change(kid, interval_spinbox.get()))
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
            command=lambda kid=key_set_id: self._on_repeat_mode_change(
                kid, "Once", repeat_mode_var, repeat_once_btn, repeat_infinity_btn),
        )
        self._grid_widget(repeat_once_btn, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        repeat_infinity_btn = tk.Button(
            repeat_row, text="INFINITY", width=10,
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Infinity Mode" else COLOR_BG_INPUT,
            fg=COLOR_TEXT  if repeat_mode_var.get() == "Infinity Mode" else COLOR_TEXT_MUTED,
            font=FONT_MAIN, relief="flat", bd=0, cursor="hand2",
            command=lambda kid=key_set_id: self._on_repeat_mode_change(
                kid, "Infinity Mode", repeat_mode_var, repeat_once_btn, repeat_infinity_btn),
        )
        self._grid_widget(repeat_infinity_btn, row=0, column=2, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        # Hover bindings after both buttons exist
        repeat_once_btn.bind("<Enter>",    lambda e: repeat_once_btn.config(
            bg=COLOR_HOVER if repeat_mode_var.get() == "Once" else COLOR_ACCENT, fg=COLOR_TEXT))
        repeat_once_btn.bind("<Leave>",    lambda e: repeat_once_btn.config(
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Once" else COLOR_BG_INPUT,
            fg=COLOR_TEXT if repeat_mode_var.get() == "Once" else COLOR_TEXT_MUTED))
        repeat_infinity_btn.bind("<Enter>", lambda e: repeat_infinity_btn.config(
            bg=COLOR_HOVER if repeat_mode_var.get() == "Infinity Mode" else COLOR_ACCENT, fg=COLOR_TEXT))
        repeat_infinity_btn.bind("<Leave>", lambda e: repeat_infinity_btn.config(
            bg=COLOR_ACCENT if repeat_mode_var.get() == "Infinity Mode" else COLOR_BG_INPUT,
            fg=COLOR_TEXT if repeat_mode_var.get() == "Infinity Mode" else COLOR_TEXT_MUTED))

        self.key_set_widget_refs[f'repeat_once_btn_{key_set_id}'] = repeat_once_btn
        self.key_set_widget_refs[f'repeat_infinity_btn_{key_set_id}'] = repeat_infinity_btn

        # Add key
        add_key_section = tk.Frame(content_frame, bg=COLOR_BG_CARD)
        add_key_section.pack(fill="x", pady=(LAYOUT_GAP, 0))
        tk.Frame(add_key_section, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(0, LAYOUT_GAP))

        add_key_row = tk.Frame(add_key_section, bg=COLOR_BG_CARD)
        add_key_row.pack(fill="x")
        add_key_row.grid_columnconfigure(1, weight=1)
        self._make_label(add_key_row, "Add", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        add_key_btn_frame = tk.Frame(add_key_row, bg=COLOR_BG_CARD)
        add_key_btn_frame.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, LAYOUT_GAP))
        add_key_btn_frame.grid_columnconfigure(0, weight=1)

        add_key_btn = tk.Button(
            add_key_btn_frame, text="PRESS KEY TO ADD",
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="hand2",
            command=lambda kid=key_set_id: self._begin_add_key_capture(kid),
        )
        add_key_btn.grid(row=0, column=0, sticky="ew")
        add_key_btn.bind("<Enter>", lambda e: add_key_btn.config(bg=COLOR_ACCENT,   fg=COLOR_TEXT))
        add_key_btn.bind("<Leave>", lambda e: add_key_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))
        self.key_set_widget_refs[f'add_key_btn_{key_set_id}'] = add_key_btn

        # Mouse button quick-add buttons
        mouse_btn_frame = tk.Frame(add_key_btn_frame, bg=COLOR_BG_CARD)
        mouse_btn_frame.grid(row=0, column=1, padx=(LAYOUT_GAP, 0))

        m4_btn = tk.Button(
            mouse_btn_frame, text="M4", font=FONT_SMALL,
            bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            width=3,
            command=lambda kid=key_set_id: self._add_mouse_button_to_set(kid, "mouse_4")
        )
        m4_btn.pack(side="left", padx=1)
        m4_btn.bind("<Enter>", lambda e: m4_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        m4_btn.bind("<Leave>", lambda e: m4_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED))

        m5_btn = tk.Button(
            mouse_btn_frame, text="M5", font=FONT_SMALL,
            bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            width=3,
            command=lambda kid=key_set_id: self._add_mouse_button_to_set(kid, "mouse_5")
        )
        m5_btn.pack(side="left", padx=1)
        m5_btn.bind("<Enter>", lambda e: m5_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        m5_btn.bind("<Leave>", lambda e: m5_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED))

        # Start/stop
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

        return card

    def _build_random_move_section(self):
        for w in self.random_move_frame.winfo_children():
            w.destroy()

        random_cfg = self.config_data.get("random_move", {})
        if not random_cfg:
            random_cfg = {
                "delay_ms": 1000,
                "trigger_key": "numpad_multiply",
                "mode": "Order",
                "positions": []
            }
            self.config_data["random_move"] = random_cfg
        else:
            random_cfg.setdefault("delay_ms", 1000)
            random_cfg.setdefault("mode", "Order")
            random_cfg.setdefault("positions", [])

        card = tk.Frame(self.random_move_frame, bg=COLOR_BG_CARD)
        card.pack(fill="x", expand=False, pady=(0, LAYOUT_GAP))

        header = tk.Frame(card, bg=COLOR_BG_CARD)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Label(header, text="MARK & CLICK POSITIONS", font=FONT_MAIN,
                 bg=COLOR_BG_CARD, fg=COLOR_HOVER).pack(side="left")

        settings = tk.Frame(card, bg=COLOR_BG_CARD)
        settings.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, 0))

        # Trigger key row
        trigger_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        trigger_row.pack(fill="x", pady=(0, 2))
        trigger_row.grid_columnconfigure(1, weight=1)
        self._make_label(trigger_row, "Trigger", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        trigger_hotkey_row = tk.Frame(trigger_row, bg=COLOR_BG_CARD)
        trigger_hotkey_row.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))
        trigger_hotkey_row.grid_columnconfigure(0, weight=1)

        trigger_key = random_cfg.get("trigger_key", "numpad_multiply")
        self.random_trigger_hotkey_display_btn = tk.Button(
            trigger_hotkey_row,
            text=trigger_key.upper(),
            bg=COLOR_BG_INPUT, fg=COLOR_HOVER, font=FONT_MAIN,
            relief="flat", bd=0, cursor="arrow",
            state="disabled", disabledforeground=COLOR_HOVER,
        )
        self._grid_widget(self.random_trigger_hotkey_display_btn, row=0, column=0, sticky="ew")
        random_trigger_hotkey_change_btn = self._make_button(
            trigger_hotkey_row, "CHANGE", self._begin_random_trigger_key_capture
        )
        self._grid_widget(random_trigger_hotkey_change_btn, row=0, column=1, padx=(LAYOUT_GAP, 0), sticky="e")

        # Mode row
        mode_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        mode_row.pack(fill="x", pady=(0, 2))
        mode_row.grid_columnconfigure(1, weight=1)
        self._make_label(mode_row, "Mode", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        mode_btn_frame = tk.Frame(mode_row, bg=COLOR_BG_CARD)
        mode_btn_frame.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))

        current_mode = random_cfg.get("mode", "Order")

        self.order_mode_btn = tk.Button(
            mode_btn_frame, text="ORDER", width=10,
            bg=COLOR_ACCENT if current_mode == "Order" else COLOR_BG_INPUT,
            fg=COLOR_TEXT if current_mode == "Order" else COLOR_TEXT_MUTED,
            font=FONT_MAIN, relief="flat", bd=0, cursor="hand2",
            command=lambda: self._on_random_mode_change("Order")
        )
        self.order_mode_btn.pack(side="left", padx=(0, LAYOUT_GAP))

        self.random_mode_btn = tk.Button(
            mode_btn_frame, text="RANDOM", width=10,
            bg=COLOR_ACCENT if current_mode == "Random" else COLOR_BG_INPUT,
            fg=COLOR_TEXT if current_mode == "Random" else COLOR_TEXT_MUTED,
            font=FONT_MAIN, relief="flat", bd=0, cursor="hand2",
            command=lambda: self._on_random_mode_change("Random")
        )
        self.random_mode_btn.pack(side="left")

        # Positions row
        pos_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        pos_row.pack(fill="x", pady=(0, 2))
        pos_row.grid_columnconfigure(1, weight=1)
        self._make_label(pos_row, "Positions", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        pos_info_frame = tk.Frame(pos_row, bg=COLOR_BG_CARD)
        pos_info_frame.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))

        self.clear_positions_btn = self._make_button(
            pos_info_frame, "CLEAR ALL", self._clear_recorded_positions
        )
        self.clear_positions_btn.pack(side="right")

        # Position chips container
        chips_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        chips_row.pack(fill="x", pady=(LAYOUT_GAP, 0))
        chips_row.grid_columnconfigure(1, weight=1)
        self._make_label(chips_row, "", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        positions_chips_container = tk.Frame(chips_row, bg=COLOR_BG_INPUT)
        positions_chips_container.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))
        self.positions_chips_container = positions_chips_container

        # Render position chips
        positions = random_cfg.get("positions", [])
        self._render_position_chips(positions_chips_container, positions)

        # Record row
        record_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        record_row.pack(fill="x", pady=(0, 2))
        record_row.grid_columnconfigure(1, weight=1)
        self._make_label(record_row, "Record", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        self.record_btn = self._make_button(
            record_row, "RECORD POSITIONS", self._toggle_recording
        )
        self.record_btn.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))

        # Delay row
        delay_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        delay_row.pack(fill="x", pady=(0, 2))
        delay_row.grid_columnconfigure(2, weight=1)
        self._make_label(delay_row, "Delay", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))
        random_delay_var = tk.IntVar(value=random_cfg.get("delay_ms", 1000))
        random_delay_spinbox = tk.Spinbox(
            delay_row, from_=1, to=60000, textvariable=random_delay_var,
            font=FONT_MAIN, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT_MUTED, relief="flat", bd=0,
            buttonbackground=COLOR_BG_INPUT, width=6,
            command=lambda: self._on_random_delay_change(random_delay_spinbox.get()),
        )
        self._grid_widget(random_delay_spinbox, row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))
        random_delay_spinbox.bind("<KeyRelease>", lambda e: self._on_random_delay_change(random_delay_spinbox.get()))
        random_delay_spinbox.bind("<Return>", lambda e: self.focus_set())
        self._make_label(delay_row, "ms").grid(row=0, column=2, sticky="w", padx=(LAYOUT_GAP, 0))
        self.random_delay_spinbox = random_delay_spinbox

        tk.Label(card, text="Click RECORD, move mouse to see coordinates, and left-click to save 1 position.",
                 font=FONT_SMALL, bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED).pack(padx=CARD_PADDING, pady=(LAYOUT_GAP, 0))

        action_row = tk.Frame(card, bg=COLOR_BG_CARD)
        action_row.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, CARD_PADDING))
        self.toggle_random_btn = self._make_button(action_row, "START RANDOM MOVE", self._toggle_random)
        self.toggle_random_btn.pack(fill="x", ipady=4)

    def _build_window_filter_section(self):
        for w in self.window_filter_frame.winfo_children():
            w.destroy()

        filter_cfg = self.config_data.get("window_filter", {})
        if not filter_cfg:
            filter_cfg = {
                "enabled": False,
                "mode": "Window Title",
                "query": ""
            }
            self.config_data["window_filter"] = filter_cfg
        else:
            filter_cfg.setdefault("enabled", False)
            filter_cfg["mode"] = "Window Title" # Always force Window Title mode
            filter_cfg.setdefault("query", "")

        card = tk.Frame(self.window_filter_frame, bg=COLOR_BG_CARD)
        card.pack(fill="x", expand=False, pady=(0, LAYOUT_GAP))

        header = tk.Frame(card, bg=COLOR_BG_CARD)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        tk.Label(header, text="MARK GAME OR WINDOW ACTIVE", font=FONT_MAIN,
                 bg=COLOR_BG_CARD, fg=COLOR_HOVER).grid(row=0, column=0, sticky="w")

        enabled_var = tk.BooleanVar(value=filter_cfg.get("enabled", False))
        enabled_frame = tk.Frame(header, bg=COLOR_BG_CARD)
        enabled_frame.grid(row=0, column=1, sticky="e")

        self.window_filter_chk = tk.Checkbutton(
            enabled_frame, variable=enabled_var,
            command=lambda: self._on_window_filter_enabled_change(enabled_var.get()),
            bg=COLOR_BG_CARD, fg=COLOR_SUCCESS, activebackground=COLOR_BG_CARD,
            activeforeground=COLOR_SUCCESS, selectcolor=COLOR_BG_INPUT,
            relief="flat", bd=0, font=FONT_SMALL,
        )
        self.window_filter_chk.pack(side="left")
        tk.Label(enabled_frame, text="Run In Game Only", font=FONT_SMALL,
                 bg=COLOR_BG_CARD, fg=COLOR_TEXT).pack(side="left", padx=(2, 0))

        settings = tk.Frame(card, bg=COLOR_BG_CARD)
        settings.pack(fill="x", padx=CARD_PADDING, pady=(LAYOUT_GAP, CARD_PADDING))

        # Query row
        query_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        query_row.pack(fill="x", pady=(0, 0))
        query_row.grid_columnconfigure(1, weight=1)
        self.window_filter_label = self._make_label(query_row, "Window Title", LABEL_WIDTH)
        self.window_filter_label.grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        query_input_frame = tk.Frame(query_row, bg=COLOR_BG_CARD)
        query_input_frame.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))
        query_input_frame.grid_columnconfigure(0, weight=1)

        query_var = tk.StringVar(value=filter_cfg.get("query", ""))
        self.window_filter_entry = tk.Entry(
            query_input_frame, textvariable=query_var, font=FONT_MAIN,
            bg=COLOR_BG_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_HOVER,
            relief="flat", bd=0,
        )
        self.window_filter_entry.grid(row=0, column=0, sticky="ew")
        self.window_filter_entry.bind("<FocusOut>", lambda e: self._on_window_filter_query_change(query_var.get()))
        self.window_filter_entry.bind("<Return>", lambda e: [self._on_window_filter_query_change(query_var.get()), self.focus_set()])
        self.window_filter_entry.bind("<FocusIn>", lambda e: self.window_filter_entry.config(bg=COLOR_BORDER))
        self.window_filter_entry.bind("<FocusOut>", lambda e: self.window_filter_entry.config(bg=COLOR_BG_INPUT))

        # Refresh and dropdown button
        refresh_btn = tk.Button(
            query_input_frame, text="▼", font=FONT_SMALL,
            bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED, relief="flat", bd=0, cursor="hand2",
            width=3,
            command=lambda: self._show_process_menu(query_var)
        )
        refresh_btn.grid(row=0, column=1, padx=(LAYOUT_GAP, 0))

        # Match status indicator
        status_row = tk.Frame(settings, bg=COLOR_BG_CARD)
        status_row.pack(fill="x", pady=(LAYOUT_GAP, 0))
        status_row.grid_columnconfigure(1, weight=1)
        self._make_label(status_row, "Status", LABEL_WIDTH).grid(row=0, column=0, sticky="w", padx=(LAYOUT_GAP, LAYOUT_GAP))

        self.window_filter_status_label = tk.Label(
            status_row, text="Checking...", font=FONT_SMALL,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED
        )
        self.window_filter_status_label.grid(row=0, column=1, sticky="w", padx=(LAYOUT_GAP, 0))

        tk.Label(card, text="Automation will only press keys or click when active window title matches this text.",
                 font=FONT_SMALL, bg=COLOR_BG_CARD, fg=COLOR_TEXT_MUTED).pack(padx=CARD_PADDING, pady=(0, 6))

        # Check Admin status to help user make "Run in game only" work for real
        is_admin_mode = False
        if sys.platform == "win32":
            try:
                import ctypes
                is_admin_mode = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                pass

        if not is_admin_mode:
            tk.Label(card, text="⚠️ Note: Run this app as Administrator if keys do not register in-game.",
                     font=FONT_SMALL, bg=COLOR_BG_CARD, fg=COLOR_HOVER).pack(padx=CARD_PADDING, pady=(0, CARD_PADDING))
        else:
            tk.Label(card, text="✓ App is running as Administrator (Ready for elevated games)",
                     font=FONT_SMALL, bg=COLOR_BG_CARD, fg=COLOR_SUCCESS).pack(padx=CARD_PADDING, pady=(0, CARD_PADDING))

        # Start status update loop
        self._update_window_filter_status()

    def _on_window_filter_enabled_change(self, enabled: bool):
        self.config_data.setdefault("window_filter", {})["enabled"] = bool(enabled)
        self.has_unsaved_changes = True

    def _on_window_filter_mode_change(self, mode: str):
        self.config_data.setdefault("window_filter", {})["mode"] = mode
        self.has_unsaved_changes = True
        if mode == "Window Title":
            self.window_filter_title_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)
            self.window_filter_process_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
            if hasattr(self, 'window_filter_label') and self.window_filter_label.winfo_exists():
                self.window_filter_label.config(text="Window Title")
        else:
            self.window_filter_title_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
            self.window_filter_process_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)
            if hasattr(self, 'window_filter_label') and self.window_filter_label.winfo_exists():
                self.window_filter_label.config(text="Process Name")

    def _on_window_filter_query_change(self, query: str):
        self.config_data.setdefault("window_filter", {})["query"] = query
        self.has_unsaved_changes = True
        self._update_window_filter_status()

    def _update_window_filter_status(self):
        """Update the window filter match status indicator."""
        if not hasattr(self, 'window_filter_status_label') or not self.window_filter_status_label.winfo_exists():
            return

        filter_cfg = self.config_data.get("window_filter", {})
        if not filter_cfg.get("enabled", False):
            self.window_filter_status_label.config(text="Filter disabled", fg=COLOR_TEXT_MUTED)
            self.after(500, self._update_window_filter_status)
            return

        query = filter_cfg.get("query", "").strip()
        if not query:
            self.window_filter_status_label.config(text="No query set", fg=COLOR_TEXT_MUTED)
            self.after(500, self._update_window_filter_status)
            return

        mode = filter_cfg.get("mode", "Window Title")
        try:
            if mode == "Window Title":
                title = get_active_window_title()
                if query.lower() in title.lower():
                    self.window_filter_status_label.config(text=f"✓ Matched: {title[:50]}...", fg=COLOR_SUCCESS)
                else:
                    self.window_filter_status_label.config(text=f"✗ Not matched: {title[:50]}...", fg=COLOR_DANGER)
            elif mode == "Process Name":
                proc = get_active_window_process_name()
                if query.lower() in proc.lower() or query + ".exe" in proc.lower() or proc.lower() in query.lower():
                    self.window_filter_status_label.config(text=f"✓ Matched: {proc[:50]}...", fg=COLOR_SUCCESS)
                else:
                    self.window_filter_status_label.config(text=f"✗ Not matched: {proc[:50]}...", fg=COLOR_DANGER)
        except Exception as e:
            self.window_filter_status_label.config(text="Error checking", fg=COLOR_DANGER)

        self.after(500, self._update_window_filter_status)

    def _show_process_menu(self, query_var: tk.StringVar):
        """Show dropdown menu with running processes or window titles based on mode."""
        filter_cfg = self.config_data.get("window_filter", {})
        mode = filter_cfg.get("mode", "Window Title")

        if mode == "Window Title":
            items = get_running_windows()
            title_text = "Windows"
        else:
            items = get_running_processes()
            title_text = "Processes"

        if not items:
            messagebox.showinfo("None Found", f"No visible {title_text.lower()} found.", parent=self)
            return

        # Store menu reference to prevent garbage collection
        self.process_menu = tk.Menu(self, tearoff=0, bg=COLOR_BG_INPUT, fg=COLOR_TEXT,
                                    activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
                                    relief="flat", bd=0, font=FONT_MAIN)

        # Show up to 40 items to prevent the menu from overflowing the screen height
        max_items = 40
        for item in items[:max_items]:
            if mode == "Window Title":
                display_name = item
            else:
                # Remove .exe extension for cleaner display
                display_name = item[:-4] if item.lower().endswith('.exe') else item
            
            self.process_menu.add_command(label=display_name,
                                        command=lambda val=item, v=query_var: self._select_process(val, v))

        if len(items) > max_items:
            self.process_menu.add_separator()
            self.process_menu.add_command(label=f"...and {len(items) - max_items} more", state="disabled")

        try:
            x = self.window_filter_entry.winfo_rootx()
            y = self.window_filter_entry.winfo_rooty() + self.window_filter_entry.winfo_height()
            self.process_menu.post(x, y)
        except Exception as e:
            print(f"Error showing menu: {e}")

    def _select_process(self, item_name: str, query_var: tk.StringVar):
        """Handle process or window selection from dropdown."""
        filter_cfg = self.config_data.get("window_filter", {})
        mode = filter_cfg.get("mode", "Window Title")

        if mode == "Window Title":
            clean_name = item_name
        else:
            # Remove .exe extension for storage
            clean_name = item_name[:-4] if item_name.lower().endswith('.exe') else item_name

        query_var.set(clean_name)
        self._on_window_filter_query_change(clean_name)
        if hasattr(self, 'process_menu'):
            self.process_menu.unpost()

    def _toggle_recording(self):
        if getattr(self, 'is_recording_positions', False):
            self._stop_recording_positions()
        else:
            if self.is_random_running:
                messagebox.showwarning("Cannot Record", "Cannot record positions while running.", parent=self)
                return
            self._start_recording_positions()

    def _start_recording_positions(self):
        self.is_recording_positions = True
        self.record_btn.config(text="RECORDING... MOVE MOUSE", bg=COLOR_DANGER, fg=COLOR_TEXT)
        self.record_btn.bind("<Enter>", lambda e: None)
        self.record_btn.bind("<Leave>", lambda e: None)
        self.status_label.config(text="RECORDING: MOVE MOUSE & LEFT CLICK TO SAVE ONE POSITION", fg=COLOR_SUCCESS)

        self.last_move_update_time = 0

        def on_click(x, y, button, pressed):
            if button == mouse.Button.left and pressed:
                try:
                    win_x = self.winfo_rootx()
                    win_y = self.winfo_rooty()
                    win_w = self.winfo_width()
                    win_h = self.winfo_height()
                except tk.TclError:
                    return

                # Ignore click inside our main app window
                if win_x <= x <= win_x + win_w and win_y <= y <= win_y + win_h:
                    return

                positions = self.config_data.setdefault("random_move", {}).setdefault("positions", [])
                positions.append([x, y])
                self.has_unsaved_changes = True

                try:
                    import winsound
                    winsound.Beep(1000, 100)
                except Exception:
                    pass

                self.after(0, self._update_positions_display)
                # Auto-stop after recording 1 position (toggle 1-by-1)
                self.after(0, self._stop_recording_positions)

        def on_move(x, y):
            try:
                if self.is_recording_positions:
                    now = time.time()
                    if now - self.last_move_update_time >= 0.05: # Limit update to 20 FPS
                        self.last_move_update_time = now
                        self.after(0, lambda: self.record_btn.config(text=f"CLICK TO RECORD ({x}, {y})"))
            except Exception:
                pass

        self.mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

    def _stop_recording_positions(self):
        self.is_recording_positions = False
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

        self.record_btn.config(text="RECORD POSITIONS", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
        self.record_btn.bind("<Enter>", lambda e: self.record_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        self.record_btn.bind("<Leave>", lambda e: self.record_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))
        self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)

    def _clear_recorded_positions(self):
        if self.is_random_running:
            messagebox.showwarning("Cannot Clear", "Cannot clear positions while running.", parent=self)
            return
        if messagebox.askyesno("Clear Positions", "Are you sure you want to clear all recorded positions?", parent=self):
            self.config_data.setdefault("random_move", {})["positions"] = []
            self.has_unsaved_changes = True
            self._update_positions_display()

    def _update_positions_display(self):
        positions = self.config_data.setdefault("random_move", {}).get("positions", [])
        # Refresh position chips instead of old labels
        if hasattr(self, 'positions_chips_container') and self.positions_chips_container.winfo_exists():
            self._render_position_chips(self.positions_chips_container, positions)

    def _on_random_mode_change(self, mode: str):
        self.config_data.setdefault("random_move", {})["mode"] = mode
        self.has_unsaved_changes = True

        if mode == "Order":
            self.order_mode_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)
            self.random_mode_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
        else:
            self.order_mode_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
            self.random_mode_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)

    # ── Key chips ─────────────────────────────────────────────────────────────

    def _render_position_chips(self, chips_container, positions: list):
        """Render position chips similar to key chips with delete buttons."""
        try:
            for w in chips_container.winfo_children():
                w.destroy()
        except (tk.TclError, AttributeError):
            return

        if not positions:
            try:
                self._make_label(chips_container, "No positions recorded").pack(padx=4, pady=2)
            except tk.TclError:
                pass
            return

        try:
            chips_container.update_idletasks()
            available_width = chips_container.winfo_width()
            if available_width <= 1:
                available_width = chips_container.winfo_reqwidth()
            if available_width <= 1:
                # Estimate based on layout columns
                cols = getattr(self, 'key_set_columns', 1)
                win_w = self.winfo_width()
                if win_w <= 1:
                    win_w = self.winfo_reqwidth()
                if win_w <= 1:
                    win_w = 800
                card_w = (win_w - 40) if cols == 1 else ((win_w - 60) / 2)
                # Chips container is in column 1, subtract label width and padding
                available_width = max(300, card_w - 80)
        except tk.TclError:
            available_width = 400

        current_row = tk.Frame(chips_container, bg=COLOR_BG_INPUT)
        current_row.pack(fill="x", anchor="w")
        used_width = 0

        try:
            for idx, (x, y) in enumerate(positions):
                coord_text = f"({x}, {y})"
                estimated_width = max(60, len(coord_text) * 8 + 34)
                if used_width and used_width + estimated_width > available_width:
                    current_row = tk.Frame(chips_container, bg=COLOR_BG_INPUT)
                    current_row.pack(fill="x", anchor="w", pady=(2, 0))
                    used_width = 0

                chip = tk.Frame(current_row, bg=COLOR_BG_MAIN)
                chip.pack(side="left", padx=1, pady=1)
                tk.Label(chip, text=coord_text, font=FONT_MAIN, bg=COLOR_BG_MAIN,
                         fg=COLOR_HOVER, padx=4, pady=1).pack(side="left")
                remove_label = tk.Label(chip, text="X", font=FONT_MAIN, bg=COLOR_BG_MAIN,
                                        fg=COLOR_TEXT_MUTED, cursor="hand2", padx=2)
                remove_label.pack(side="left")
                remove_label.bind("<Button-1>", lambda e, i=idx: self._remove_position_at_index(i))
                remove_label.bind("<Enter>",    lambda e, w=remove_label: w.config(fg=COLOR_DANGER))
                remove_label.bind("<Leave>",    lambda e, w=remove_label: w.config(fg=COLOR_TEXT_MUTED))
                used_width += estimated_width
        except (tk.TclError, AttributeError) as e:
            print(f"Error rendering position chips: {e}")

    def _remove_position_at_index(self, position_index: int):
        """Remove a position at the given index."""
        positions = self.config_data.get("random_move", {}).get("positions", [])
        if position_index < len(positions):
            positions.pop(position_index)
            self.has_unsaved_changes = True
            # Refresh position chips
            if hasattr(self, 'positions_chips_container') and self.positions_chips_container.winfo_exists():
                self._render_position_chips(self.positions_chips_container, positions)

    def _render_key_chips(self, chips_container, keys: list, key_set_id: int = 1):
        try:
            # Verify container is still valid before proceeding
            if not chips_container.winfo_exists():
                return
        except (tk.TclError, AttributeError):
            return

        try:
            for w in chips_container.winfo_children():
                w.destroy()
        except (tk.TclError, AttributeError):
            return

        if not keys:
            try:
                self._make_label(chips_container, "No keys").pack(padx=4, pady=2)
            except tk.TclError:
                pass
            return

        try:
            chips_container.update_idletasks()
            available_width = chips_container.winfo_width()
            if available_width <= 1:
                available_width = chips_container.winfo_reqwidth()
            if available_width <= 1:
                # Estimate based on layout columns
                cols = getattr(self, 'key_set_columns', 1)
                win_w = self.winfo_width()
                if win_w <= 1:
                    win_w = self.winfo_reqwidth()
                if win_w <= 1:
                    win_w = 800
                card_w = (win_w - 40) if cols == 1 else ((win_w - 60) / 2)
                # Chips container is in column 1, subtract label width and padding
                available_width = max(300, card_w - 80)
        except (tk.TclError, AttributeError):
            try:
                # Fallback estimation
                cols = getattr(self, 'key_set_columns', 1)
                win_w = self.winfo_width()
                card_w = (win_w - 40) if cols == 1 else ((win_w - 60) / 2)
                available_width = max(300, card_w - 80)
            except (tk.TclError, AttributeError):
                available_width = 400

        try:
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
        except (tk.TclError, AttributeError) as e:
            print(f"Error rendering key chips: {e}")

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
                # Double-check container is still valid before rendering
                chips_container.update_idletasks()
                self._render_key_chips(chips_container, key_set.get('keys', []), key_set_id)
            except (tk.TclError, AttributeError):
                continue

    # ── Responsive layout ─────────────────────────────────────────────────────

    def _apply_responsive_layout(self, window_width: int):
        if self.is_rebuilding:
            return

        # Check if frames exist before applying layout
        if not hasattr(self, 'key_set_frame') or not hasattr(self, 'random_move_frame') or not hasattr(self, 'window_filter_frame'):
            return

        new_layout_mode = "2col" if window_width >= 950 else "1col"
        if new_layout_mode == "2col":
            new_key_set_cols = 2 if window_width >= 1200 else 1
        else:
            new_key_set_cols = 2 if window_width >= 600 else 1

        layout_changed = (getattr(self, 'current_layout_mode', '') != new_layout_mode)
        cols_changed = (new_key_set_cols != self.key_set_columns)

        if layout_changed or cols_changed:
            self.is_rebuilding = True
            self.current_layout_mode = new_layout_mode
            self.key_set_columns = new_key_set_cols

            # Unpack everything first (with existence checks)
            try:
                if hasattr(self, 'key_set_frame') and self.key_set_frame.winfo_exists():
                    self.key_set_frame.pack_forget()
                    self.key_set_frame.grid_forget()
            except (tk.TclError, AttributeError):
                pass

            try:
                if hasattr(self, 'random_move_frame') and self.random_move_frame.winfo_exists():
                    self.random_move_frame.pack_forget()
                    self.random_move_frame.grid_forget()
            except (tk.TclError, AttributeError):
                pass

            try:
                if hasattr(self, 'window_filter_frame') and self.window_filter_frame.winfo_exists():
                    self.window_filter_frame.pack_forget()
                    self.window_filter_frame.grid_forget()
            except (tk.TclError, AttributeError):
                pass

            # Reset grid configure on main_layout
            try:
                self.main_layout.grid_columnconfigure(0, weight=1, uniform="")
                self.main_layout.grid_columnconfigure(1, weight=0, uniform="")
            except (tk.TclError, AttributeError):
                pass

            if new_layout_mode == "2col":
                try:
                    self.main_layout.grid_columnconfigure(0, weight=6, uniform="col")
                    self.main_layout.grid_columnconfigure(1, weight=4, uniform="col")

                    # Column 0: Key Sets (spanning 2 rows)
                    self.key_set_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, LAYOUT_GAP))

                    # Column 1: Random Move (row 0)
                    self.random_move_frame.grid(row=0, column=1, sticky="ew", padx=(LAYOUT_GAP, 0), pady=(0, LAYOUT_GAP * 2))

                    # Column 1: Window Filter (row 1)
                    self.window_filter_frame.grid(row=1, column=1, sticky="ew", padx=(LAYOUT_GAP, 0))
                except (tk.TclError, AttributeError) as e:
                    print(f"Error applying 2col layout: {e}")
            else:
                try:
                    # Single column: Stacked
                    self.key_set_frame.pack(fill="both", expand=True, pady=(0, LAYOUT_GAP * 2))
                    self.random_move_frame.pack(fill="x", pady=(0, LAYOUT_GAP * 2))
                    self.window_filter_frame.pack(fill="x")
                except (tk.TclError, AttributeError) as e:
                    print(f"Error applying 1col layout: {e}")

            self._build_key_set_section()
            self.is_rebuilding = False
        else:
            # Columns didn't change, but we still need to refresh chips to wrap nicely at the new width
            try:
                self._refresh_key_chips()
                self._update_positions_display()
            except Exception as e:
                print(f"Error refreshing chips during resize: {e}")

    # ── Config mutation handlers ──────────────────────────────────────────────

    def _on_key_set_name_change(self, key_set_id: int, name: str):
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["name"] = name
                break
        self.has_unsaved_changes = True

    def _on_key_set_enabled_change(self, key_set_id: int, enabled: bool):
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["enabled"] = bool(enabled)
                break
        self.has_unsaved_changes = True
        self._update_action_button_state()
        self._set_key_set_card_collapsed(key_set_id, not enabled)
        if not enabled and key_set_id in self.running_key_sets:
            self._toggle_presser(key_set_id)

    def _set_key_set_card_collapsed(self, key_set_id: int, collapsed: bool):
        content_frame = self.key_set_widget_refs.get(f'content_frame_{key_set_id}')
        if content_frame:
            if collapsed:
                content_frame.pack_forget()
            else:
                content_frame.pack(fill="x", expand=False, padx=CARD_PADDING, pady=(0, CARD_PADDING))

    def _delete_key_set(self, key_set_id: int):
        key_sets = self.config_data.get("key_sets", [])
        if len(key_sets) <= 1:
            messagebox.showwarning("Cannot Delete", "You must have at least one key set.", parent=self)
            return
        if key_set_id in self.running_key_sets:
            messagebox.showwarning("Cannot Delete", "Cannot delete a key set that is currently running.", parent=self)
            return
        if messagebox.askyesno("Delete Key Set", "Are you sure you want to delete this key set?", parent=self):
            self.config_data["key_sets"] = [ks for ks in key_sets if ks.get("id") != key_set_id]
            self.has_unsaved_changes = True
            self._build_key_set_section()

    def _add_key_set(self):
        key_sets = self.config_data.get("key_sets", [])
        max_id  = max((ks.get("id", 0) for ks in key_sets), default=0)
        new_id  = max_id + 1
        self.config_data["key_sets"].append({
            "id": new_id,
            "name": f"Key Set {new_id}",
            "keys": [],
            "delay_ms": 100,
            "repeat_interval_sec": 30,
            "use_every": True,
            "repeat": "Infinity Mode",
            "enabled": True,
            "trigger_key": "numpad_decimal"
        })
        self.has_unsaved_changes = True
        self._build_key_set_section()

    def _on_delay_change(self, key_set_id: int, value):
        try:
            val = int(value)
        except (ValueError, TypeError):
            return
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["delay_ms"] = val
                break
        self.has_unsaved_changes = True

    def _on_repeat_interval_change(self, key_set_id: int, value):
        try:
            val = int(value)
        except (ValueError, TypeError):
            return
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["repeat_interval_sec"] = val
                self.key_set_widget_refs[f'repeat_interval_var_{key_set_id}'].set(val)
                break
        self.has_unsaved_changes = True

    def _on_use_every_change(self, key_set_id: int, value: bool):
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["use_every"] = bool(value)
                self.key_set_widget_refs[f'repeat_interval_spinbox_{key_set_id}'].config(
                    state="normal" if value else "disabled"
                )
                break
        self.has_unsaved_changes = True

    def _on_repeat_mode_change(self, key_set_id: int, mode: str, mode_var, once_btn, infinity_btn):
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["repeat"] = mode
                break
        mode_var.set(mode)
        self.has_unsaved_changes = True
        if mode == "Once":
            once_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)
            infinity_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
        else:
            once_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_TEXT_MUTED)
            infinity_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT)

    def _remove_key_at_index(self, key_set_id: int, key_index: int):
        try:
            for ks in self.config_data.get("key_sets", []):
                if ks.get("id") == key_set_id:
                    keys = ks.get("keys", [])
                    if key_index < len(keys):
                        keys.pop(key_index)
                    break
            self.has_unsaved_changes = True
            # Only refresh the key chips for this specific key set to avoid flickering
            chips_container = self.key_set_widget_refs.get(f'chips_container_{key_set_id}')
            if chips_container and chips_container.winfo_exists():
                key_set = next((ks for ks in self.config_data.get("key_sets", []) if ks.get("id") == key_set_id), None)
                if key_set:
                    try:
                        self._render_key_chips(chips_container, key_set.get('keys', []), key_set_id)
                    except (tk.TclError, AttributeError) as e:
                        print(f"Error refreshing key chips: {e}")
        except Exception as e:
            print(f"Error removing key at index: {e}")

    def _on_random_delay_change(self, value):
        if self.is_random_running:
            return
        try:
            val = int(value)
        except (ValueError, TypeError):
            return
        self.config_data.get("random_move", {})["delay_ms"] = val
        self.has_unsaved_changes = True

    # ── Start / stop actions ──────────────────────────────────────────────────

    def _collect_current_config(self) -> dict:
        return {
            "random_start_stop_key": self.config_data.get("random_start_stop_key", "numpad_multiply"),
            "key_sets":              self.config_data.get("key_sets", []),
            "random_move":           self.config_data.get("random_move", {}),
            "window_filter":         self.config_data.get("window_filter", {
                "enabled": False,
                "mode": "Window Title",
                "query": ""
            }),
        }

    def _save_config(self):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Save", "Cannot save configuration while running.", parent=self)
            return
        self.config_data = self._collect_current_config()
        save_config(self.config_data)
        self._restart_hotkey_listener()
        self.has_unsaved_changes = False
        messagebox.showinfo("Saved", "Config saved!", parent=self)

    def _clear_config(self):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Clear", "Cannot clear configuration while running.", parent=self)
            return
        if messagebox.askyesno("Clear Config", "Are you sure you want to reset to default configuration?", parent=self):
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            self.config_data = dict(DEFAULT_CONFIG)
            self._build_ui()
            self._start_hotkey_listener()
            self.has_unsaved_changes = False
            messagebox.showinfo("Cleared", "Configuration reset to default!", parent=self)

    def _toggle_presser(self, key_set_id: int):
        if key_set_id in self.running_key_sets:
            self._stop_presser(key_set_id)
        else:
            self.config_data = self._collect_current_config()
            self._start_presser(key_set_id)

    def _start_presser(self, key_set_id: int):
        self.running_key_sets.add(key_set_id)
        self.is_presser_running = True

        btn = self.key_set_widget_refs.get(f'toggle_presser_btn_{key_set_id}')
        if btn:
            btn.config(text="STOP AUTO PRESSER", bg=COLOR_DANGER, fg=COLOR_TEXT,
                       activebackground="#cc2233", activeforeground=COLOR_TEXT)
            btn.bind("<Enter>", lambda e: btn.config(bg="#cc2233", fg=COLOR_TEXT))
            btn.bind("<Leave>", lambda e: btn.config(bg=COLOR_DANGER, fg=COLOR_TEXT))

        self.status_label.config(
            text=f"RUNNING - {len(self.running_key_sets)} KEY SET(S) ACTIVE", fg=COLOR_SUCCESS
        )
        self._disable_settings_controls_for_key_set(key_set_id)

        key_set = next((ks for ks in self.config_data.get("key_sets", []) if ks.get("id") == key_set_id), None)
        if not key_set:
            return

        keys              = key_set.get("keys", [])
        repeat_mode       = key_set.get("repeat", "Infinity Mode")
        delay_s           = key_set.get("delay_ms", 100) / 1000.0
        repeat_interval_s = key_set.get("repeat_interval_sec", 1)
        use_every         = key_set.get("use_every", True)

        if keys:
            thread = threading.Thread(
                target=self._presser_loop,
                args=(key_set_id, keys, delay_s, repeat_interval_s, repeat_mode, use_every),
                daemon=True,
            )
            thread.start()
            self.press_threads.append(thread)

    def _stop_presser(self, key_set_id: int):
        self.running_key_sets.discard(key_set_id)

        if not self.running_key_sets:
            self.is_presser_running = False
            self.individual_threads = None
            status_text  = "IDLE" if not self.is_random_running else "RUNNING - RANDOM MOVE ACTIVE"
            status_color = COLOR_TEXT_MUTED if not self.is_random_running else COLOR_SUCCESS
            self.status_label.config(text=status_text, fg=status_color)
            # FIX: only clear threads that have actually finished
            self.press_threads = [t for t in self.press_threads if t.is_alive()]
        else:
            self.status_label.config(
                text=f"RUNNING - {len(self.running_key_sets)} KEY SET(S) ACTIVE", fg=COLOR_SUCCESS
            )

        btn = self.key_set_widget_refs.get(f'toggle_presser_btn_{key_set_id}')
        if btn:
            btn.config(text="START AUTO PRESSER", bg=COLOR_BG_INPUT, fg=COLOR_HOVER,
                       activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT)
            btn.bind("<Enter>", lambda e: btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
            btn.bind("<Leave>", lambda e: btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))

        self._enable_settings_controls_for_key_set(key_set_id)

    def _toggle_random(self):
        if self.is_random_running:
            self._stop_random()
        else:
            if getattr(self, 'is_recording_positions', False):
                self._stop_recording_positions()
            self.config_data = self._collect_current_config()

            positions = self.config_data.get("random_move", {}).get("positions", [])
            if not positions:
                messagebox.showwarning("No Positions", "Please record at least one position first.", parent=self)
                return

            self._start_random()

    def _start_random(self):
        self.is_random_running = True
        self.toggle_random_btn.config(text="STOP RANDOM MOVE", bg=COLOR_DANGER, fg=COLOR_TEXT,
                                       activebackground="#cc2233", activeforeground=COLOR_TEXT)
        self.toggle_random_btn.bind("<Enter>", lambda e: self.toggle_random_btn.config(bg="#cc2233", fg=COLOR_TEXT))
        self.toggle_random_btn.bind("<Leave>", lambda e: self.toggle_random_btn.config(bg=COLOR_DANGER, fg=COLOR_TEXT))
        self.status_label.config(text="RUNNING - RANDOM MOVE ACTIVE", fg=COLOR_SUCCESS)
        self._disable_settings_controls()

        random_cfg = self.config_data.get("random_move", {})
        delay_ms = random_cfg.get("delay_ms", 1000)
        positions = random_cfg.get("positions", [])
        mode = random_cfg.get("mode", "Order")

        thread = threading.Thread(
            target=self._random_move_loop,
            args=(delay_ms, positions, mode),
            daemon=True,
        )
        thread.start()
        self.random_thread = thread

    def _stop_random(self):
        self.is_random_running = False
        self.toggle_random_btn.config(text="START RANDOM MOVE", bg=COLOR_BG_INPUT, fg=COLOR_HOVER,
                                       activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT)
        self.toggle_random_btn.bind("<Enter>", lambda e: self.toggle_random_btn.config(bg=COLOR_ACCENT, fg=COLOR_TEXT))
        self.toggle_random_btn.bind("<Leave>", lambda e: self.toggle_random_btn.config(bg=COLOR_BG_INPUT, fg=COLOR_HOVER))
        status_text  = "IDLE" if not self.is_presser_running else "RUNNING - AUTO PRESSER ACTIVE"
        status_color = COLOR_TEXT_MUTED if not self.is_presser_running else COLOR_SUCCESS
        self.status_label.config(text=status_text, fg=status_color)
        if self.random_thread and self.random_thread.is_alive():
            self.random_thread.join(timeout=0.5)
        self.random_thread = None
        self._enable_settings_controls()

    # ── Background loops ──────────────────────────────────────────────────────

    def _presser_loop(self, key_set_id: int, keys: list, delay_s: float,
                      repeat_interval_s: float = 1.0,
                      repeat_mode: str = "Infinity Mode",
                      use_every: bool = True):
        resolved_keys = [k for k in (resolve_key(k) for k in keys) if k is not None]

        if repeat_mode == "Once":
            for key in resolved_keys:
                if key_set_id not in self.running_key_sets:
                    break
                # Pause loop if target game/window is not active
                while key_set_id in self.running_key_sets and not is_window_filter_matched(self.config_data.get("window_filter", {})):
                    time.sleep(0.2)
                if key_set_id not in self.running_key_sets:
                    break
                try:
                    # Check if key is a mouse button
                    if key in MOUSE_BUTTON_MAP.values():
                        mouse_controller.press(key)
                        time.sleep(0.02)
                        mouse_controller.release(key)
                    else:
                        keyboard_controller.press(key)
                        time.sleep(0.02)
                        keyboard_controller.release(key)
                except Exception as e:
                    print(f"Error pressing key {key}: {e}")
                time.sleep(delay_s)
            # FIX: use discard instead of remove to avoid KeyError if already removed
            self.running_key_sets.discard(key_set_id)
            self.after(0, lambda: self._stop_presser(key_set_id))
        else:
            while key_set_id in self.running_key_sets:
                for key in resolved_keys:
                    if key_set_id not in self.running_key_sets:
                        break
                    # Pause loop if target game/window is not active
                    while key_set_id in self.running_key_sets and not is_window_filter_matched(self.config_data.get("window_filter", {})):
                        time.sleep(0.2)
                    if key_set_id not in self.running_key_sets:
                        break
                    try:
                        # Check if key is a mouse button
                        if key in MOUSE_BUTTON_MAP.values():
                            mouse_controller.press(key)
                            time.sleep(0.02)
                            mouse_controller.release(key)
                        else:
                            keyboard_controller.press(key)
                            time.sleep(0.02)
                            keyboard_controller.release(key)
                    except Exception as e:
                        print(f"Error pressing key {key}: {e}")
                    time.sleep(delay_s)
                if key_set_id in self.running_key_sets and use_every:
                    # Also respect window active filter during the interval sleep
                    interval_elapsed = 0.0
                    while key_set_id in self.running_key_sets and interval_elapsed < repeat_interval_s:
                        if is_window_filter_matched(self.config_data.get("window_filter", {})):
                            time.sleep(min(0.1, repeat_interval_s - interval_elapsed))
                            interval_elapsed += 0.1
                        else:
                            time.sleep(0.2)

    def _random_move_loop(self, delay_ms: int, positions: list, mode: str):
        between_click_delay_s = max(delay_ms, 1) / 1000.0
        num_positions = len(positions)
        if num_positions == 0:
            self.is_random_running = False
            self.after(0, self._stop_random)
            return

        index = 0
        while self.is_random_running:
            # Pause loop if target game/window is not active
            while self.is_random_running and not is_window_filter_matched(self.config_data.get("window_filter", {})):
                time.sleep(0.2)
            if not self.is_random_running:
                break

            if mode == "Order":
                x, y = positions[index]
                index = (index + 1) % num_positions
            else: # Random Mode
                x, y = random.choice(positions)

            try:
                mouse_controller.position = (x, y)
                time.sleep(0.05)
                mouse_controller.press(Button.left)
                time.sleep(0.05)
                mouse_controller.release(Button.left)
            except Exception as e:
                print(f"Error clicking at ({x}, {y}): {e}")

            if self.is_random_running:
                time.sleep(between_click_delay_s)

        self.after(0, self._stop_random)

    # ── Hotkey listener ───────────────────────────────────────────────────────

    def _start_hotkey_listener(self):
        def on_key_press(key):
            try:
                # ESC cancels any capture in progress
                if key == Key.esc and any([
                    self.is_capturing_presser_hotkey,
                    self.is_capturing_random_hotkey,
                    self.is_capturing_add_key,
                    self.is_capturing_trigger_key,
                    self.is_capturing_random_trigger_key,
                ]):
                    self.after(0, self._cancel_all_captures)
                    return

                if self.is_capturing_presser_hotkey:
                    self.after(0, lambda k=key: self._apply_presser_hotkey(k))
                    return
                if self.is_capturing_random_hotkey:
                    self.after(0, lambda k=key: self._apply_random_hotkey(k))
                    return
                if self.is_capturing_add_key:
                    self.after(0, lambda k=key: self._apply_add_key(k))
                    return
                if self.is_capturing_trigger_key:
                    self.after(0, lambda k=key: self._apply_trigger_key(k))
                    return
                if self.is_capturing_random_trigger_key:
                    self.after(0, lambda k=key: self._apply_random_trigger_key(k))
                    return

                now = time.time()
                self.held_keys = {k: t for k, t in self.held_keys.items() if now - t < 1.5}

                key_sets = self.config_data.get("key_sets", [])
                matched_key_sets = []
                for key_set in key_sets:
                    key_set_id  = key_set.get("id")
                    trigger_key = key_set.get("trigger_key")
                    if not trigger_key or not key_set.get("enabled", True):
                        continue

                    matched = normalize_hotkey(key) == normalize_hotkey(trigger_key)
                    if not matched:
                        resolved = resolve_key(trigger_key.lower())
                        matched  = (key == resolved) or (
                            hasattr(key, 'name') and key.name and key.name.lower() == trigger_key.lower()
                        )
                    if matched:
                        matched_key_sets.append(key_set_id)

                if matched_key_sets and key not in self.held_keys:
                    self.held_keys[key] = now
                    for kid in matched_key_sets:
                        self.after(0, lambda kid_id=kid: self._toggle_presser(kid_id))
                    return

                random_trigger_key = self.config_data.get("random_move", {}).get("trigger_key", "numpad_multiply")
                if random_trigger_key:
                    matched = normalize_hotkey(key) == normalize_hotkey(random_trigger_key)
                    if not matched:
                        resolved = resolve_key(random_trigger_key.lower())
                        matched  = (key == resolved) or (
                            hasattr(key, 'name') and key.name and key.name.lower() == random_trigger_key.lower()
                        )
                    if matched and key not in self.held_keys:
                        self.held_keys[key] = now
                        self.after(0, self._toggle_random)
            except Exception as e:
                print(f"Error in hotkey listener: {e}")

        def on_key_release(key):
            try:
                self.held_keys.pop(key, None)
            except Exception as e:
                print(f"Error in key release: {e}")

        def on_mouse_click(x, y, button, pressed):
            try:
                if not pressed:
                    return  # Only handle press events

                # Handle mouse button capture for trigger keys
                if button == Button.x1 or button == Button.x2:
                    if any([
                        self.is_capturing_presser_hotkey,
                        self.is_capturing_random_hotkey,
                        self.is_capturing_add_key,
                        self.is_capturing_trigger_key,
                        self.is_capturing_random_trigger_key,
                    ]):
                        self.after(0, lambda b=button: self._apply_mouse_button_capture(b))
                        return

                now = time.time()
                self.held_keys = {k: t for k, t in self.held_keys.items() if now - t < 1.5}

                # Check key sets for mouse button triggers
                key_sets = self.config_data.get("key_sets", [])
                matched_key_sets = []
                for key_set in key_sets:
                    key_set_id  = key_set.get("id")
                    trigger_key = key_set.get("trigger_key")
                    if not trigger_key or not key_set.get("enabled", True):
                        continue

                    # Check if trigger is a mouse button
                    if trigger_key in MOUSE_BUTTON_MAP:
                        if button == MOUSE_BUTTON_MAP[trigger_key]:
                            matched_key_sets.append(key_set_id)

                if matched_key_sets and button not in self.held_keys:
                    self.held_keys[button] = now
                    for kid in matched_key_sets:
                        self.after(0, lambda kid_id=kid: self._toggle_presser(kid_id))
                    return

                # Check random move trigger
                random_trigger_key = self.config_data.get("random_move", {}).get("trigger_key", "numpad_multiply")
                if random_trigger_key in MOUSE_BUTTON_MAP:
                    if button == MOUSE_BUTTON_MAP[random_trigger_key] and button not in self.held_keys:
                        self.held_keys[button] = now
                        self.after(0, self._toggle_random)
            except Exception as e:
                print(f"Error in mouse click handler: {e}")

        def on_mouse_release(x, y, button):
            try:
                self.held_keys.pop(button, None)
            except Exception as e:
                print(f"Error in mouse release: {e}")

        try:
            self.hotkey_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()

            self.mouse_hotkey_listener = mouse.Listener(on_click=on_mouse_click, on_release=on_mouse_release)
            self.mouse_hotkey_listener.daemon = True
            self.mouse_hotkey_listener.start()
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")

    def _restart_hotkey_listener(self):
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
                self.hotkey_listener.join(timeout=0.5)
            except Exception as e:
                print(f"Error stopping hotkey listener: {e}")
        if hasattr(self, 'mouse_hotkey_listener') and self.mouse_hotkey_listener:
            try:
                self.mouse_hotkey_listener.stop()
                self.mouse_hotkey_listener.join(timeout=0.5)
            except Exception as e:
                print(f"Error stopping mouse hotkey listener: {e}")
        self._start_hotkey_listener()

    def _cancel_all_captures(self):
        self.is_capturing_presser_hotkey     = False
        self.is_capturing_random_hotkey      = False
        self.is_capturing_add_key            = False
        self.is_capturing_trigger_key        = False
        self.is_capturing_random_trigger_key = False
        self.capturing_trigger_key_id        = None
        self.capturing_key_set_id            = None

        key_sets = self.config_data.get("key_sets", [])
        for key_set in key_sets:
            key_set_id = key_set.get("id")
            btn = self.key_set_widget_refs.get(f'trigger_hotkey_display_btn_{key_set_id}')
            if btn and btn.winfo_exists():
                try:
                    trigger_key = key_set.get("trigger_key", "numpad_decimal")
                    btn.config(text=trigger_key.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass
            add_btn = self.key_set_widget_refs.get(f'add_key_btn_{key_set_id}')
            if add_btn and add_btn.winfo_exists():
                try:
                    add_btn.config(text="PRESS KEY TO ADD", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass

        # Reset main hotkey buttons
        if hasattr(self, 'presser_hotkey_display_btn') and self.presser_hotkey_display_btn.winfo_exists():
            try:
                self.presser_hotkey_display_btn.config(
                    text=self.config_data.get("start_stop_key", "F6").upper(),
                    bg=COLOR_BG_INPUT, fg=COLOR_HOVER
                )
            except tk.TclError:
                pass

        if hasattr(self, 'random_hotkey_display_btn') and self.random_hotkey_display_btn.winfo_exists():
            try:
                self.random_hotkey_display_btn.config(
                    text=self.config_data.get("random_start_stop_key", "numpad_multiply").upper(),
                    bg=COLOR_BG_INPUT, fg=COLOR_HOVER
                )
            except tk.TclError:
                pass

        if hasattr(self, 'random_trigger_hotkey_display_btn') and self.random_trigger_hotkey_display_btn.winfo_exists():
            try:
                trigger_key = self.config_data.get("random_move", {}).get("trigger_key", "numpad_multiply")
                self.random_trigger_hotkey_display_btn.config(
                    text=trigger_key.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER
                )
            except tk.TclError:
                pass

        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            except tk.TclError:
                pass

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
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
        if hasattr(self, 'mouse_hotkey_listener') and self.mouse_hotkey_listener:
            try:
                self.mouse_hotkey_listener.stop()
            except Exception:
                pass
        # Destroy overlay first
        if hasattr(self, 'overlay') and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.destroy()

    # ── Key capture ───────────────────────────────────────────────────────────

    def _begin_presser_hotkey_capture(self):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Change", "Cannot change hotkey while running.", parent=self)
            return
        self.is_capturing_presser_hotkey = True
        if hasattr(self, 'presser_hotkey_display_btn') and self.presser_hotkey_display_btn.winfo_exists():
            try:
                self.presser_hotkey_display_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)
            except tk.TclError:
                pass

    def _begin_add_key_capture(self, key_set_id: int):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Change", "Cannot add keys while running.", parent=self)
            return
        self.is_capturing_add_key   = True
        self.capturing_key_set_id   = key_set_id
        btn = self.key_set_widget_refs.get(f'add_key_btn_{key_set_id}')
        if btn and btn.winfo_exists():
            try:
                btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="PRESS A KEY TO ADD", fg=COLOR_ACCENT)
            except tk.TclError:
                pass

    def _apply_presser_hotkey(self, key):
        key_str = self._resolve_captured_key_upper(key)
        if key_str is None:
            return
        self.config_data["start_stop_key"] = key_str
        if hasattr(self, 'presser_hotkey_display_btn') and self.presser_hotkey_display_btn.winfo_exists():
            try:
                self.presser_hotkey_display_btn.config(text=key_str, bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            except tk.TclError:
                pass
        self.is_capturing_presser_hotkey = False
        save_config(self.config_data)
        self._restart_hotkey_listener()

    def _add_mouse_button_to_set(self, key_set_id: int, mouse_button: str):
        """Manually add a mouse button to a key set."""
        if key_set_id in self.running_key_sets:
            messagebox.showwarning("Cannot Add", "Cannot add keys while running.", parent=self)
            return

        # Append mouse button to config
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks.setdefault("keys", []).append(mouse_button)
                break

        self.has_unsaved_changes = True

        # Refresh chips widget
        chips_container = self.key_set_widget_refs.get(f'chips_container_{key_set_id}')
        if chips_container and chips_container.winfo_exists():
            try:
                keys = next(
                    (ks.get("keys", []) for ks in self.config_data.get("key_sets", [])
                     if ks.get("id") == key_set_id),
                    []
                )
                self._render_key_chips(chips_container, keys, key_set_id)
            except tk.TclError:
                pass

    def _apply_add_key(self, key):
        key_set_id = self.capturing_key_set_id
        self.is_capturing_add_key = False
        self.capturing_key_set_id = None

        if key_set_id is None:
            return

        btn = self.key_set_widget_refs.get(f'add_key_btn_{key_set_id}')

        # Reset button appearance first
        if btn and btn.winfo_exists():
            try:
                btn.config(text="PRESS KEY TO ADD", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            except tk.TclError:
                pass

        if key_set_id in self.running_key_sets:
            return

        # Handle mouse buttons
        if key == Button.x1:
            key_str = "mouse_4"
        elif key == Button.x2:
            key_str = "mouse_5"
        else:
            key_str = self._resolve_captured_key_lower(key)
        if not key_str:
            return

        # Append key to config
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks.setdefault("keys", []).append(key_str)
                break

        self.has_unsaved_changes = True

        # Only refresh chips widget — no full rebuild needed
        chips_container = self.key_set_widget_refs.get(f'chips_container_{key_set_id}')
        if chips_container:
            try:
                keys = next(
                    (ks.get("keys", []) for ks in self.config_data.get("key_sets", [])
                     if ks.get("id") == key_set_id),
                    []
                )
                self._render_key_chips(chips_container, keys, key_set_id)
            except tk.TclError:
                pass

    def _begin_random_hotkey_capture(self):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Change", "Cannot change hotkey while running.", parent=self)
            return
        self.is_capturing_random_hotkey = True
        if hasattr(self, 'random_hotkey_display_btn') and self.random_hotkey_display_btn.winfo_exists():
            try:
                self.random_hotkey_display_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)
            except tk.TclError:
                pass

    def _apply_random_hotkey(self, key):
        key_str = self._resolve_captured_key_upper(key)
        if key_str is None:
            return
        self.config_data["random_start_stop_key"] = key_str
        if hasattr(self, 'random_hotkey_display_btn') and self.random_hotkey_display_btn.winfo_exists():
            try:
                self.random_hotkey_display_btn.config(text=key_str, bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            except tk.TclError:
                pass
        self.is_capturing_random_hotkey = False
        save_config(self.config_data)
        self._restart_hotkey_listener()

    def _begin_trigger_key_capture(self, key_set_id: int):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Change", "Cannot change trigger key while running.", parent=self)
            return
        self.is_capturing_trigger_key   = True
        self.capturing_trigger_key_id   = key_set_id
        btn = self.key_set_widget_refs.get(f'trigger_hotkey_display_btn_{key_set_id}')
        if btn and btn.winfo_exists():
            try:
                btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)
            except tk.TclError:
                pass

    def _begin_random_trigger_key_capture(self):
        if self.is_presser_running or self.is_random_running:
            messagebox.showwarning("Cannot Change", "Cannot change trigger key while running.", parent=self)
            return
        self.is_capturing_random_trigger_key = True
        if hasattr(self, 'random_trigger_hotkey_display_btn') and self.random_trigger_hotkey_display_btn.winfo_exists():
            try:
                self.random_trigger_hotkey_display_btn.config(text="PRESS KEY", bg=COLOR_ACCENT, fg=COLOR_TEXT)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="PRESS A KEY", fg=COLOR_ACCENT)
            except tk.TclError:
                pass

    def _apply_trigger_key(self, key):
        key_set_id = self.capturing_trigger_key_id
        if key_set_id is None:
            return
        key_str = self._resolve_captured_key_lower(key)
        if key_str is None:
            return
        for ks in self.config_data.get("key_sets", []):
            if ks.get("id") == key_set_id:
                ks["trigger_key"] = key_str
                break
        btn = self.key_set_widget_refs.get(f'trigger_hotkey_display_btn_{key_set_id}')
        if btn and btn.winfo_exists():
            try:
                btn.config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            except tk.TclError:
                pass
        self.is_capturing_trigger_key   = False
        self.capturing_trigger_key_id   = None
        self.has_unsaved_changes        = True
        save_config(self.config_data)
        self._restart_hotkey_listener()

    def _apply_random_trigger_key(self, key):
        key_str = self._resolve_captured_key_lower(key)
        if key_str is None:
            return
        self.config_data.setdefault("random_move", {})["trigger_key"] = key_str
        if hasattr(self, 'random_trigger_hotkey_display_btn') and self.random_trigger_hotkey_display_btn.winfo_exists():
            try:
                self.random_trigger_hotkey_display_btn.config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
            except tk.TclError:
                pass
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            try:
                self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
            except tk.TclError:
                pass
        self.is_capturing_random_trigger_key = False
        self.has_unsaved_changes             = True
        save_config(self.config_data)
        self._restart_hotkey_listener()

    # ── Key capture helpers ───────────────────────────────────────────────────

    def _apply_mouse_button_capture(self, button):
        """Handle mouse button capture for trigger keys."""
        # Convert mouse button to string name
        if button == Button.x1:
            key_str = "mouse_4"
        elif button == Button.x2:
            key_str = "mouse_5"
        else:
            return

        # Apply to the appropriate capture context
        if self.is_capturing_presser_hotkey:
            self.config_data["start_stop_key"] = key_str
            if hasattr(self, 'presser_hotkey_display_btn') and self.presser_hotkey_display_btn.winfo_exists():
                try:
                    self.presser_hotkey_display_btn.config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                try:
                    self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
                except tk.TclError:
                    pass
            self.is_capturing_presser_hotkey = False
            save_config(self.config_data)
            self._restart_hotkey_listener()

        elif self.is_capturing_random_hotkey:
            self.config_data["random_start_stop_key"] = key_str
            if hasattr(self, 'random_hotkey_display_btn') and self.random_hotkey_display_btn.winfo_exists():
                try:
                    self.random_hotkey_display_btn.config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                try:
                    self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
                except tk.TclError:
                    pass
            self.is_capturing_random_hotkey = False
            save_config(self.config_data)
            self._restart_hotkey_listener()

        elif self.is_capturing_trigger_key:
            key_set_id = self.capturing_trigger_key_id
            if key_set_id is None:
                return
            for ks in self.config_data.get("key_sets", []):
                if ks.get("id") == key_set_id:
                    ks["trigger_key"] = key_str
                    break
            btn = self.key_set_widget_refs.get(f'trigger_hotkey_display_btn_{key_set_id}')
            if btn and btn.winfo_exists():
                try:
                    btn.config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                try:
                    self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
                except tk.TclError:
                    pass
            self.is_capturing_trigger_key = False
            self.capturing_trigger_key_id = None
            self.has_unsaved_changes = True
            save_config(self.config_data)
            self._restart_hotkey_listener()

        elif self.is_capturing_random_trigger_key:
            self.config_data.setdefault("random_move", {})["trigger_key"] = key_str
            if hasattr(self, 'random_trigger_hotkey_display_btn') and self.random_trigger_hotkey_display_btn.winfo_exists():
                try:
                    self.random_trigger_hotkey_display_btn.config(text=key_str.upper(), bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                try:
                    self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
                except tk.TclError:
                    pass
            self.is_capturing_random_trigger_key = False
            self.has_unsaved_changes = True
            save_config(self.config_data)
            self._restart_hotkey_listener()

        elif self.is_capturing_add_key:
            key_set_id = self.capturing_key_set_id
            if key_set_id is None:
                return

            # Reset button appearance
            btn = self.key_set_widget_refs.get(f'add_key_btn_{key_set_id}')
            if btn and btn.winfo_exists():
                try:
                    btn.config(text="PRESS KEY TO ADD", bg=COLOR_BG_INPUT, fg=COLOR_HOVER)
                except tk.TclError:
                    pass
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                try:
                    self.status_label.config(text="IDLE", fg=COLOR_TEXT_MUTED)
                except tk.TclError:
                    pass

            if key_set_id in self.running_key_sets:
                self.is_capturing_add_key = False
                self.capturing_key_set_id = None
                return

            # Append mouse button to config
            for ks in self.config_data.get("key_sets", []):
                if ks.get("id") == key_set_id:
                    ks.setdefault("keys", []).append(key_str)
                    break

            self.has_unsaved_changes = True
            self.is_capturing_add_key = False
            self.capturing_key_set_id = None

            # Refresh chips widget
            chips_container = self.key_set_widget_refs.get(f'chips_container_{key_set_id}')
            if chips_container and chips_container.winfo_exists():
                try:
                    keys = next(
                        (ks.get("keys", []) for ks in self.config_data.get("key_sets", [])
                         if ks.get("id") == key_set_id),
                        []
                    )
                    self._render_key_chips(chips_container, keys, key_set_id)
                except tk.TclError:
                    pass

    def _resolve_captured_key_upper(self, key) -> str | None:
        # Handle mouse buttons
        if key == Button.x1:
            return "MOUSE_4"
        if key == Button.x2:
            return "MOUSE_5"
        if hasattr(key, 'vk') and key.vk is not None:
            return _vk_to_numpad_name(key.vk)
        if hasattr(key, 'name'):
            return key.name.upper()
        if hasattr(key, 'char') and key.char:
            return key.char.upper()
        return None

    def _resolve_captured_key_lower(self, key) -> str | None:
        # Handle mouse buttons
        if key == Button.x1:
            return "mouse_4"
        if key == Button.x2:
            return "mouse_5"
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