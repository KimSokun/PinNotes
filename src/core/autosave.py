"""Debounced autosave controller for continuous saving without UI freezing."""

from __future__ import annotations
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal


class AutoSaveManager(QObject):
    """Coordinates debounced saving and tracks unsaved document state."""

    save_requested = Signal()
    save_status_changed = Signal(str)  # "Saved", "Saving...", "Unsaved changes", "Save error"

    def __init__(self, delay_ms: int = 600, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.delay_ms = delay_ms
        self.is_dirty: bool = False
        self._is_saving: bool = False

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(self.delay_ms)
        self._timer.timeout.connect(self._trigger_save)

    def mark_dirty(self) -> None:
        """Call when user edits document to start the debounce timer."""
        self.is_dirty = True
        self.save_status_changed.emit("Unsaved changes")
        self._timer.start(self.delay_ms)

    def mark_clean(self) -> None:
        """Call after successful save."""
        self.is_dirty = False
        self._timer.stop()
        self.save_status_changed.emit("Saved")

    def mark_saving(self) -> None:
        """Call when save operation begins."""
        self.save_status_changed.emit("Saving...")

    def mark_error(self, message: str = "Save error") -> None:
        """Call if saving fails."""
        self.save_status_changed.emit(message)

    def flush(self) -> None:
        """Immediately trigger save if there are unsaved changes."""
        if self.is_dirty:
            self._timer.stop()
            self._trigger_save()

    def _trigger_save(self) -> None:
        if self.is_dirty:
            self.save_requested.emit()
