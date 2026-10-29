"""Custom user resize and layout persistence (custom.json).

Saves customized window dimensions (width, height, position, maximized state)
and panel column splitter ratios to custom.json whenever the user resizes them.
"""

from __future__ import annotations
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_CUSTOM_CONFIG: Dict[str, Any] = {
    "window": {
        "width": 460,
        "height": 390,
        "x": None,
        "y": None,
        "is_maximized": False,
    },
    "splitter": {
        "sidebar_width": 220,
        "editor_width": 240,
        "sizes": [220, 240],
    },
    "last_customized": None,
}


class CustomResizeManager:
    """Manages reading and persisting custom resize settings in custom.json."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = Path(sys.executable).resolve().parent
            else:
                base_dir = Path(__file__).resolve().parent.parent.parent
            self.config_dir = base_dir / "PinNotes" / "config"
            self.root_file = base_dir / "custom.json"
        else:
            self.config_dir = Path(config_dir)
            self.root_file = self.config_dir.parent / "custom.json"

        self.custom_file = self.config_dir / "custom.json"
        self._data: Dict[str, Any] = dict(DEFAULT_CUSTOM_CONFIG)
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load custom resize settings from custom.json if it exists."""
        target_file = None
        if self.custom_file.exists():
            target_file = self.custom_file
        elif self.root_file.exists():
            target_file = self.root_file

        if target_file and target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Merge with defaults
                        merged = {
                            "window": {**DEFAULT_CUSTOM_CONFIG["window"], **data.get("window", {})},
                            "splitter": {**DEFAULT_CUSTOM_CONFIG["splitter"], **data.get("splitter", {})},
                            "last_customized": data.get("last_customized"),
                        }
                        self._data = merged
                        return self._data
            except Exception as e:
                print(f"Warning reading custom.json: {e}")

        self._data = {
            "window": dict(DEFAULT_CUSTOM_CONFIG["window"]),
            "splitter": dict(DEFAULT_CUSTOM_CONFIG["splitter"]),
            "last_customized": None,
        }
        return self._data

    def save_window_geometry(
        self,
        width: int,
        height: int,
        x: Optional[int] = None,
        y: Optional[int] = None,
        is_maximized: bool = False,
    ) -> None:
        """Update and persist custom window dimensions."""
        self._data["window"]["width"] = int(width)
        self._data["window"]["height"] = int(height)
        if x is not None:
            self._data["window"]["x"] = int(x)
        if y is not None:
            self._data["window"]["y"] = int(y)
        self._data["window"]["is_maximized"] = bool(is_maximized)
        self._save()

    def save_splitter_sizes(self, sizes: List[int]) -> None:
        """Update and persist custom column/panel splitter widths."""
        if len(sizes) >= 2:
            self._data["splitter"]["sidebar_width"] = int(sizes[0])
            self._data["splitter"]["editor_width"] = int(sizes[1])
            self._data["splitter"]["sizes"] = [int(s) for s in sizes]
            self._save()

    def get_window_geometry(self) -> Tuple[int, int, Optional[int], Optional[int], bool]:
        """Return (width, height, x, y, is_maximized)."""
        w = self._data["window"].get("width", 460)
        h = self._data["window"].get("height", 390)
        x = self._data["window"].get("x")
        y = self._data["window"].get("y")
        is_max = self._data["window"].get("is_maximized", False)
        return int(w), int(h), x, y, bool(is_max)

    def get_splitter_sizes(self) -> List[int]:
        """Return [sidebar_width, editor_width]."""
        sizes = self._data["splitter"].get("sizes")
        if sizes and len(sizes) >= 2:
            return [int(s) for s in sizes]
        sb = self._data["splitter"].get("sidebar_width", 220)
        ed = self._data["splitter"].get("editor_width", 240)
        return [int(sb), int(ed)]

    def _save(self) -> None:
        """Atomically persist data to custom.json and keep root copy in sync."""
        self._data["last_customized"] = datetime.now().isoformat()
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.config_dir / f"custom.json.tmp.{os.getpid()}"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.custom_file)

            # Also sync to root_file for easy user access
            try:
                with open(self.root_file, "w", encoding="utf-8") as rf:
                    json.dump(self._data, rf, indent=2, ensure_ascii=False)
            except Exception:
                pass
        except Exception as e:
            print(f"Warning saving custom.json: {e}")
