"""Monitors the notes folder for external modifications made by Obsidian or text editors."""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QFileSystemWatcher, QObject, Signal, QTimer


class FileWatcher(QObject):
    """Monitors directory and active note files for external modifications."""

    file_modified = Signal(str)  # Emits file path string
    directory_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._on_file_changed)
        self.watcher.directoryChanged.connect(self._on_dir_changed)

        # Debounce timer to avoid firing multiple times on single write
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._emit_pending)

        self._pending_files = set()
        self._watched_file: Optional[str] = None

    def watch_directory(self, dir_path: Path) -> None:
        """Watch a directory for file additions/deletions."""
        p_str = str(dir_path.resolve())
        if p_str not in self.watcher.directories():
            self.watcher.addPath(p_str)

    def set_active_file(self, file_path: Optional[Path]) -> None:
        """Watch the currently open note file for external updates."""
        if self._watched_file and self._watched_file in self.watcher.files():
            self.watcher.removePath(self._watched_file)
            self._watched_file = None

        if file_path and file_path.exists():
            f_str = str(file_path.resolve())
            self.watcher.addPath(f_str)
            self._watched_file = f_str

    def _on_file_changed(self, path: str) -> None:
        self._pending_files.add(path)
        self._debounce_timer.start()

    def _on_dir_changed(self, path: str) -> None:
        self.directory_changed.emit(path)

    def _emit_pending(self) -> None:
        for f in self._pending_files:
            self.file_modified.emit(f)
        self._pending_files.clear()
