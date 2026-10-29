"""Configuration and persistent application settings for PinNotes."""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


DEFAULT_SETTINGS: Dict[str, Any] = {
    "notes_folder": "",  # Empty means default: <base_dir>/PinNotes/notes
    "window_x": None,
    "window_y": None,
    "window_width": 460,
    "window_height": 390,
    "is_pinned": False,
    "theme": "light",
    "font_family": "Consolas, 'Cascadia Code', monospace",
    "font_size": 12,
    "tab_size": 4,
    "word_wrap": True,
    "sidebar_expanded": False,
    "last_active_note_id": None,
    "sort_by": "modified",  # "modified" or "title"
    "global_hotkey": "Ctrl+Alt+P",
    "auto_save_delay_ms": 600,
}


class SettingsManager:
    """Manages reading and writing application settings to a local JSON file."""

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            # PinNotes root config directory
            if getattr(sys, "frozen", False):
                exe_parent = Path(sys.executable).resolve().parent
                if (exe_parent.parent / "PinNotes" / "config" / "settings.json").exists():
                    self.base_dir = exe_parent.parent
                else:
                    self.base_dir = exe_parent
            else:
                self.base_dir = Path(__file__).resolve().parent.parent.parent
            self.config_dir = self.base_dir / "PinNotes" / "config"
        else:
            self.config_dir = Path(config_dir)
            self.base_dir = self.config_dir.parent.parent

        self.config_file = self.config_dir / "settings.json"
        self._data: Dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value, falling back to default."""
        return self._data.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and persist to disk."""
        self._data[key] = value
        self.save()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple settings at once and save."""
        self._data.update(updates)
        self.save()

    def get_notes_folder(self) -> Path:
        """Return the resolved notes directory Path, ensuring it exists."""
        custom_folder = self._data.get("notes_folder")
        if custom_folder and str(custom_folder).strip():
            notes_dir = Path(custom_folder)
        else:
            candidates = []
            if getattr(sys, "frozen", False):
                exe_parent = Path(sys.executable).resolve().parent
                candidates.append(exe_parent / "PinNotes" / "notes")
                candidates.append(exe_parent / "notes")
                if (exe_parent.parent / "PinNotes" / "notes").exists():
                    candidates.append(exe_parent.parent / "PinNotes" / "notes")
            else:
                base = getattr(self, "base_dir", Path(__file__).resolve().parent.parent.parent)
                candidates.append(base / "PinNotes" / "notes")
                candidates.append(base / "notes")

            notes_dir = None
            for c in candidates:
                if c.exists() and any(c.iterdir()):
                    notes_dir = c
                    break

            if notes_dir is None:
                notes_dir = candidates[0] if candidates else Path.home() / "PinNotes" / "notes"

        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir

    def set_notes_folder(self, path: Path | str) -> None:
        """Update the notes folder path."""
        p = Path(path).resolve()
        p.mkdir(parents=True, exist_ok=True)
        self.set("notes_folder", str(p))

    def load(self) -> None:
        """Load settings from JSON file. Silently handle corrupt or missing files."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # Merge with defaults to guarantee all keys exist
                        merged = dict(DEFAULT_SETTINGS)
                        merged.update(loaded)
                        self._data = merged
                        return
            except Exception:
                pass  # Fall back to default settings

        self._data = dict(DEFAULT_SETTINGS)

    def save(self) -> None:
        """Atomically save settings to JSON file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.config_dir / f"settings.json.tmp.{os.getpid()}"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            temp_file.replace(self.config_file)
        except Exception as e:
            # Log or handle save failure without terminating application
            print(f"Error saving settings: {e}")
