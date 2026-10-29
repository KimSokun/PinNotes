"""Windows Global Hotkey management using native Win32 RegisterHotKey."""

from __future__ import annotations
import sys
from typing import Callable, Optional

# Win32 Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
HOTKEY_ID = 9001


def parse_hotkey_string(hotkey_str: str) -> tuple[int, int]:
    """Parse hotkey string like 'Ctrl+Alt+P' into (win32_modifiers, virtual_key_code)."""
    parts = [p.strip().upper() for p in hotkey_str.split("+") if p.strip()]
    modifiers = 0
    vk = 0

    for part in parts:
        if part in ("CTRL", "CONTROL"):
            modifiers |= MOD_CONTROL
        elif part == "ALT":
            modifiers |= MOD_ALT
        elif part == "SHIFT":
            modifiers |= MOD_SHIFT
        elif part in ("WIN", "WINDOWS", "SUPER"):
            modifiers |= MOD_WIN
        else:
            # Key code
            if len(part) == 1:
                vk = ord(part)
            elif part.startswith("F") and part[1:].isdigit():
                # F1 - F12 (0x70 - 0x7B)
                f_num = int(part[1:])
                if 1 <= f_num <= 12:
                    vk = 0x70 + (f_num - 1)
            elif part == "SPACE":
                vk = 0x20

    return modifiers, vk


class GlobalHotkeyManager:
    """Manages Windows system-wide global hotkey registration without third-party keyloggers."""

    def __init__(self, hwnd: int, hotkey_str: str = "Ctrl+Alt+P", callback: Optional[Callable[[], None]] = None):
        self.hwnd = hwnd
        self.hotkey_str = hotkey_str
        self.callback = callback
        self.registered = False
        self._user32 = None

        if sys.platform == "win32":
            import ctypes
            self._user32 = ctypes.windll.user32

    def register(self, hotkey_str: Optional[str] = None) -> bool:
        """Register the global hotkey with Windows."""
        if not self._user32 or not self.hwnd:
            return False

        if hotkey_str:
            self.hotkey_str = hotkey_str

        # Unregister existing first
        self.unregister()

        modifiers, vk = parse_hotkey_string(self.hotkey_str)
        if not vk:
            return False

        success = bool(self._user32.RegisterHotKey(self.hwnd, HOTKEY_ID, modifiers, vk))
        self.registered = success
        return success

    def unregister(self) -> None:
        """Unregister the global hotkey."""
        if self._user32 and self.hwnd and self.registered:
            try:
                self._user32.UnregisterHotKey(self.hwnd, HOTKEY_ID)
            except Exception:
                pass
            self.registered = False

    def handle_native_event(self, msg_type: int, msg_wparam: int) -> bool:
        """Check if native window message is the registered WM_HOTKEY."""
        if msg_type == WM_HOTKEY and msg_wparam == HOTKEY_ID:
            if self.callback:
                self.callback()
            return True
        return False
