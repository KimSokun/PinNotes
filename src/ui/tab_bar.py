"""Open notes tab bar widget matching editor / VS Code tabs with SVG icons."""

from __future__ import annotations
from typing import Dict, List, Optional

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QTabBar,
    QWidget,
)

from src.ui.icons import CLOSE_SVG, PLUS_SVG, get_svg_icon


class TabCloseButtonWidget(QWidget):
    """Wrapper holding a close button with right margin so hover highlight never touches tab border."""

    def __init__(self, note_id: str, is_dark: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedSize(26, 16)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(0)

        self.btn = QPushButton(self)
        self.btn.setFixedSize(16, 16)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setToolTip("Close Tab (Ctrl+W)")
        layout.addWidget(self.btn)

        self.set_theme(is_dark)

    def set_theme(self, is_dark: bool) -> None:
        color = "#cccccc" if is_dark else "#64748b"
        self.btn.setIcon(get_svg_icon(CLOSE_SVG, color=color, size=10))
        hover_bg = "rgba(255, 255, 255, 0.16)" if is_dark else "rgba(100, 116, 139, 0.2)"
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 3px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """)


class NoteTabBar(QTabBar):
    """Horizontal tab bar for managing open note history and switching."""

    tab_switched = Signal(str)  # Emits note_id
    tab_closed = Signal(str)    # Emits note_id

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.setObjectName("noteTabBar")
        self._is_dark = is_dark
        self._note_ids: List[str] = []
        self._dirty_states: Dict[str, bool] = {}
        self._titles: Dict[str, str] = {}

        self.setTabsClosable(False)  # We manage custom clean SVG close buttons
        self.setMovable(True)
        self.setUsesScrollButtons(False)
        self.setElideMode(Qt.ElideRight)
        self.setExpanding(False)

        self.currentChanged.connect(self._on_current_changed)
        self.tabMoved.connect(self._on_tab_moved)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _on_tab_moved(self, from_idx: int, to_idx: int) -> None:
        """Keep internal note ID ordering in sync when tabs are dragged."""
        if 0 <= from_idx < len(self._note_ids) and 0 <= to_idx < len(self._note_ids):
            nid = self._note_ids.pop(from_idx)
            self._note_ids.insert(to_idx, nid)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self._refresh_close_buttons()

    def _create_close_button_widget(self, note_id: str) -> TabCloseButtonWidget:
        w = TabCloseButtonWidget(note_id, is_dark=self._is_dark, parent=self)
        w.btn.clicked.connect(lambda _, nid=note_id: self.close_tab_by_id(nid))
        return w

    def _refresh_close_buttons(self) -> None:
        for i in range(self.count()):
            w = self.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if isinstance(w, TabCloseButtonWidget):
                w.set_theme(self._is_dark)

    def add_or_select_tab(self, note_id: str, title: str, is_dirty: bool = False) -> None:
        """Add a note tab if not present, or select it if already open."""
        self._titles[note_id] = title
        self._dirty_states[note_id] = is_dirty

        if note_id in self._note_ids:
            index = self._note_ids.index(note_id)
            self._update_tab_text(index, note_id)
            self.blockSignals(True)
            self.setCurrentIndex(index)
            self.blockSignals(False)
            return

        # Add new tab
        self._note_ids.append(note_id)
        display_text = self._format_tab_label(title, is_dirty)
        self.blockSignals(True)
        index = self.addTab(display_text)

        # Attach clean vector SVG close button wrapper with right padding
        close_widget = self._create_close_button_widget(note_id)
        self.setTabButton(index, QTabBar.ButtonPosition.RightSide, close_widget)

        self.setCurrentIndex(index)
        self.blockSignals(False)

    def _format_tab_label(self, title: str, is_dirty: bool) -> str:
        clean_title = title.strip() or "Untitled Note"
        if len(clean_title) > 24:
            clean_title = clean_title[:22] + "..."
        dot = " •" if is_dirty else ""
        return f"{clean_title}{dot}"

    def _update_tab_text(self, index: int, note_id: str) -> None:
        if 0 <= index < self.count():
            title = self._titles.get(note_id, "Untitled Note")
            is_dirty = self._dirty_states.get(note_id, False)
            self.setTabText(index, self._format_tab_label(title, is_dirty))

    def set_tab_dirty(self, note_id: str, is_dirty: bool) -> None:
        """Update dirty indicator dot on tab."""
        self._dirty_states[note_id] = is_dirty
        if note_id in self._note_ids:
            index = self._note_ids.index(note_id)
            self._update_tab_text(index, note_id)

    def update_tab_title(self, note_id: str, new_title: str) -> None:
        """Update tab label when note is renamed."""
        self._titles[note_id] = new_title
        if note_id in self._note_ids:
            index = self._note_ids.index(note_id)
            self._update_tab_text(index, note_id)

    def close_tab_by_id(self, note_id: str) -> None:
        """Close tab corresponding to note_id."""
        if note_id in self._note_ids:
            index = self._note_ids.index(note_id)
            self.remove_tab_at(index)

    def remove_tab_at(self, index: int) -> None:
        if 0 <= index < len(self._note_ids):
            note_id = self._note_ids.pop(index)
            self._dirty_states.pop(note_id, None)
            self._titles.pop(note_id, None)

            self.blockSignals(True)
            self.removeTab(index)
            self.blockSignals(False)

            self.tab_closed.emit(note_id)

    def get_current_note_id(self) -> Optional[str]:
        idx = self.currentIndex()
        if 0 <= idx < len(self._note_ids):
            return self._note_ids[idx]
        return None

    def get_open_note_ids(self) -> List[str]:
        return list(self._note_ids)

    def _on_current_changed(self, index: int) -> None:
        if 0 <= index < len(self._note_ids):
            note_id = self._note_ids[index]
            self.tab_switched.emit(note_id)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            idx = self.tabAt(event.position().toPoint())
            if idx < 0:
                parent = self.parent()
                if isinstance(parent, NoteTabBarContainer):
                    parent.new_tab_requested.emit()
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:
        # Middle-click closes tab
        if event.button() == Qt.MiddleButton:
            idx = self.tabAt(event.position().toPoint())
            if idx >= 0:
                self.remove_tab_at(idx)
                event.accept()
                return
        super().mousePressEvent(event)

    def wheelEvent(self, event) -> None:
        """Wheel scroll switches through open tabs."""
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta > 0:
            if self.currentIndex() > 0:
                self.setCurrentIndex(self.currentIndex() - 1)
        elif delta < 0:
            if self.currentIndex() < self.count() - 1:
                self.setCurrentIndex(self.currentIndex() + 1)
        event.accept()

    def _show_context_menu(self, pos: QPoint) -> None:
        tab_idx = self.tabAt(pos)
        if tab_idx < 0:
            return

        menu = QMenu(self)
        act_close = menu.addAction("Close Tab")
        act_close_others = menu.addAction("Close Other Tabs")
        act_close_right = menu.addAction("Close Tabs to the Right")

        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_close:
            self.remove_tab_at(tab_idx)
        elif chosen == act_close_others:
            note_id = self._note_ids[tab_idx]
            to_remove = [nid for nid in self._note_ids if nid != note_id]
            for nid in to_remove:
                self.close_tab_by_id(nid)
        elif chosen == act_close_right:
            while len(self._note_ids) > tab_idx + 1:
                self.remove_tab_at(tab_idx + 1)


class NoteTabBarContainer(QWidget):
    """Container holding NoteTabBar and SVG '+' new tab button matching VS Code."""

    new_tab_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.setObjectName("noteTabBarContainer")
        self._is_dark = is_dark

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(4)

        self.tab_bar = NoteTabBar(self, is_dark=is_dark)
        layout.addWidget(self.tab_bar)

        self.new_tab_btn = QPushButton(self)
        self.new_tab_btn.setObjectName("newTabBtn")
        self.new_tab_btn.setFixedSize(24, 24)
        self.new_tab_btn.setCursor(Qt.PointingHandCursor)
        self.new_tab_btn.setToolTip("New Note (Ctrl+N)")
        self.new_tab_btn.clicked.connect(self.new_tab_requested.emit)
        layout.addWidget(self.new_tab_btn, alignment=Qt.AlignVCenter)

        layout.addStretch(1)

        self.set_theme(is_dark)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.new_tab_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self.tab_bar.set_theme(is_dark)
        color = "#cccccc" if is_dark else "#64748b"
        self.new_tab_btn.setIcon(get_svg_icon(PLUS_SVG, color=color, size=13))
        hover_bg = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(100, 116, 139, 0.15)"
        self.new_tab_btn.setStyleSheet(f"""
            QPushButton#newTabBtn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 3px;
            }}
            QPushButton#newTabBtn:hover {{
                background-color: {hover_bg};
            }}
        """)
