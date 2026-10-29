"""Compact search bar for live note searching using vector SVG icon."""

from __future__ import annotations
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from src.ui.icons import SEARCH_SVG, get_svg_icon


class SearchBar(QWidget):
    """Compact search field matching the reference design."""

    search_changed = Signal(str)
    search_cleared = Signal()
    escape_pressed = Signal()

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.setObjectName("searchContainer")
        self._is_dark = is_dark
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        self.edit = QLineEdit(self)
        self.edit.setObjectName("searchEdit")
        self.edit.setPlaceholderText("Search notes and snippets... (Ctrl+F)")
        self.edit.setClearButtonEnabled(True)

        # Vector SVG Search Icon inside line edit
        search_icon = get_svg_icon(SEARCH_SVG, color="#94a3b8", size=14)
        self.edit.addAction(search_icon, QLineEdit.LeadingPosition)

        self.edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.edit)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        icon_color = "#6e6e6e" if is_dark else "#94a3b8"
        # Refresh leading search action icon
        actions = self.edit.actions()
        if actions:
            actions[0].setIcon(get_svg_icon(SEARCH_SVG, color=icon_color, size=14))

    def _on_text_changed(self, text: str) -> None:
        clean = text.strip()
        self.search_changed.emit(clean)
        if not clean:
            self.search_cleared.emit()

    def clear_search(self) -> None:
        self.edit.clear()

    def focus_search(self) -> None:
        self.edit.setFocus()
        self.edit.selectAll()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            if self.edit.text():
                self.clear_search()
            self.escape_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)
