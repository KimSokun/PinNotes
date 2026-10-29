"""Main floating window assembling the TitleBar, SearchBar, NoteEditor, NoteList, and controls."""

from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Optional, Union

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QShortcut,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizeGrip,
    QSplitter,
    QSplitterHandle,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.core.autosave import AutoSaveManager
from src.core.custom_config import CustomResizeManager
from src.core.hotkeys import GlobalHotkeyManager, WM_HOTKEY
from src.core.note_model import Note
from src.core.note_service import NoteService
from src.core.settings import SettingsManager
from src.ui.icons import APP_ICON_SVG, FOLDER_SVG, PLUS_SVG, get_svg_icon
from src.ui.note_editor import NoteEditorWidget
from src.ui.note_list import NoteListWidget
from src.ui.search_bar import SearchBar
from src.ui.tab_bar import NoteTabBar, NoteTabBarContainer
from src.ui.theme import generate_stylesheet
from src.ui.title_bar import TitleBar


# Win32 Topmost constants
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

# Win32 Hit Test constants for native border resize cursors
WM_NCHITTEST = 0x0084
WM_NCLBUTTONDOWN = 0x00A1
HTNOWHERE = 0
HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17


class ColumnResizeHandle(QSplitterHandle):
    """Custom column/panel splitter handle with col-resize cursor and visual grip."""

    def __init__(self, orientation, parent, is_dark: bool = False):
        super().__init__(orientation, parent)
        self.is_dark = is_dark
        self._is_hovered = False
        self.setCursor(Qt.SizeHorCursor)  # ew-resize cursor

    def set_theme(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        self.update()

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        self.setCursor(Qt.SizeHorCursor)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            is_active = self._is_hovered or self.underMouse()

            # Subtle divider background
            bg = QColor("#2d2d2d" if self.is_dark else "#e2e8f0")
            if is_active:
                bg = QColor("#007acc" if self.is_dark else "#2563eb")
            painter.fillRect(self.rect(), bg)

            # Center grip handle pill (indicating column/panel resize)
            w = self.width()
            h = self.height()
            pill_w = 4
            pill_h = 28
            pill_x = (w - pill_w) // 2
            pill_y = (h - pill_h) // 2

            grip_color = QColor(
                "#ffffff" if is_active else ("#666666" if self.is_dark else "#94a3b8")
            )
            painter.setBrush(grip_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 2, 2)
        finally:
            painter.end()


class PanelSplitter(QSplitter):
    """QSplitter featuring ColumnResizeHandle with col-resize cursor."""

    def __init__(self, orientation, parent=None, is_dark: bool = False):
        super().__init__(orientation, parent)
        self.is_dark = is_dark
        self.setHandleWidth(8)
        self.setChildrenCollapsible(False)

    def set_theme(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        for i in range(self.count()):
            h = self.handle(i)
            if isinstance(h, ColumnResizeHandle):
                h.set_theme(is_dark)

    def createHandle(self):
        return ColumnResizeHandle(self.orientation(), self, is_dark=self.is_dark)


class BottomBar(QWidget):
    """Bottom action bar with bottom edge and corner resizing support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        child = self.childAt(pos)
        w = child
        is_btn = False
        while w and w != self:
            if isinstance(w, QPushButton):
                is_btn = True
                break
            w = w.parent()

        if is_btn:
            self.unsetCursor()
            super().mouseMoveEvent(event)
            return

        window = self.window()
        if window and not window.isMaximized():
            margin = 8
            if pos.y() >= self.height() - 5:
                if pos.x() <= margin:
                    self.setCursor(Qt.SizeBDiagCursor)
                elif pos.x() >= self.width() - margin:
                    self.setCursor(Qt.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.SizeVerCursor)
            elif pos.x() <= margin or pos.x() >= self.width() - margin:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.unsetCursor()
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            child = self.childAt(pos)
            w = child
            while w and w != self:
                if isinstance(w, QPushButton):
                    super().mousePressEvent(event)
                    return
                w = w.parent()

            window = self.window()
            if window and not window.isMaximized():
                margin = 8
                edges = Qt.Edges()
                if pos.y() >= self.height() - 5:
                    edges |= Qt.BottomEdge
                if pos.x() <= margin:
                    edges |= Qt.LeftEdge
                elif pos.x() >= self.width() - margin:
                    edges |= Qt.RightEdge

                if edges:
                    wh = window.windowHandle()
                    if wh and hasattr(wh, "startSystemResize"):
                        if wh.startSystemResize(edges):
                            event.accept()
                            return
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """Compact floating notes window matching reference image and specifications."""

    def __init__(self, note_service: NoteService, settings: SettingsManager):
        super().__init__()
        self.note_service = note_service
        self.settings = settings
        self.custom_config = CustomResizeManager(config_dir=self.settings.config_dir)
        self.current_note: Optional[Note] = None
        self._is_dark: bool = self.settings.get("theme", "light") == "dark"
        self._is_pinned: bool = bool(self.settings.get("is_pinned", False))
        self._sidebar_expanded: bool = bool(self.settings.get("sidebar_expanded", False))

        # Frameless floating window for custom Windows Notes utility styling
        flags = Qt.Window | Qt.FramelessWindowHint
        if self._is_pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_Hover, True)
        if self.windowIcon().isNull():
            self.setWindowIcon(get_svg_icon(APP_ICON_SVG, color="#2563eb", fill_color="#2563eb", size=64))

        # Autosave manager
        delay_ms = int(self.settings.get("auto_save_delay_ms", 600))
        self.autosave = AutoSaveManager(delay_ms=delay_ms, parent=self)
        self.autosave.save_requested.connect(self.save_current_note)

        # Resize border dragging tracking
        self._drag_border = None
        self._resize_margin = 8
        self._press_pos = QPoint()
        self._press_geo = QRect()

        self._setup_ui()
        self._setup_shortcuts()
        self._restore_geometry()
        self._apply_theme()
        if sys.platform == "win32":
            self._apply_dwm_attributes()

        # Load initial note
        self._load_initial_note()
        self.title_bar.set_pinned(self._is_pinned)

        # Install application-level event filter for smooth border resizing without button conflicts
        q_app = QApplication.instance()
        if q_app:
            q_app.installEventFilter(self)

        # Setup Windows Global Hotkey
        self.global_hotkey = GlobalHotkeyManager(
            hwnd=int(self.winId()),
            hotkey_str=self.settings.get("global_hotkey", "Ctrl+Alt+P"),
            callback=self.activate_and_focus,
        )
        self.global_hotkey.register()

    def _setup_ui(self) -> None:
        # Central widget container with 1px border
        self.central_container = QWidget(self)
        self.central_container.setObjectName("centralContainer")
        self.setCentralWidget(self.central_container)

        container_layout = QVBoxLayout(self.central_container)
        container_layout.setContentsMargins(1, 1, 1, 1)
        container_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.title_bar = TitleBar(self, is_dark=self._is_dark)
        self.title_bar.pin_toggled.connect(self.set_always_on_top)
        self.title_bar.sidebar_toggled.connect(self.toggle_sidebar)
        self.title_bar.theme_toggled.connect(self.toggle_theme)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)
        container_layout.addWidget(self.title_bar)

        # 2. Search Bar
        self.search_bar = SearchBar(self, is_dark=self._is_dark)
        self.search_bar.search_changed.connect(self._on_search_query)
        self.search_bar.search_cleared.connect(self._on_search_cleared)
        self.search_bar.escape_pressed.connect(self._on_search_escape)
        container_layout.addWidget(self.search_bar)

        # 3. Main Splitter (Sidebar + Note Editor Pane) with Column Resize Handle
        self.splitter = PanelSplitter(Qt.Horizontal, self, is_dark=self._is_dark)
        self.splitter.setHandleWidth(8)
        self.splitter.setChildrenCollapsible(False)

        # Note Sidebar
        self.note_list = NoteListWidget(self, is_dark=self._is_dark)
        self.note_list.note_selected.connect(self._switch_to_note)
        self.note_list.create_requested.connect(self.create_new_note)
        self.note_list.rename_requested.connect(self._on_rename_note)
        self.note_list.duplicate_requested.connect(self._on_duplicate_note)
        self.note_list.delete_requested.connect(self._on_delete_note)
        self.note_list.favorite_toggled.connect(self._on_favorite_toggled)
        self.note_list.reveal_requested.connect(self._on_reveal_in_explorer)
        self.note_list.sort_changed.connect(self._on_sort_changed)
        self.splitter.addWidget(self.note_list)

        # Editor pane holding NoteTabBar and NoteEditorWidget
        self.editor_pane = QWidget(self)
        self.editor_pane.setMinimumWidth(160)
        editor_pane_layout = QVBoxLayout(self.editor_pane)
        editor_pane_layout.setContentsMargins(0, 0, 0, 0)
        editor_pane_layout.setSpacing(0)

        # Open Notes Tab Bar Container with SVG '+' new tab button
        self.tab_container = NoteTabBarContainer(self, is_dark=self._is_dark)
        self.tab_bar = self.tab_container.tab_bar
        self.tab_bar.tab_switched.connect(self._switch_to_note)
        self.tab_bar.tab_closed.connect(self._on_tab_closed)
        self.tab_container.new_tab_requested.connect(self.create_new_note)
        editor_pane_layout.addWidget(self.tab_container)

        # Note Editor
        self.editor = NoteEditorWidget(self, is_dark=self._is_dark)
        self.editor.content_changed.connect(self._on_content_changed)
        self.editor.title_changed.connect(self._on_title_changed)
        self.editor.language_changed.connect(self._on_language_changed)
        self.editor.mode_changed.connect(self._on_mode_changed)
        self.editor.code_editor.cursorPositionChanged.connect(self._update_stats)
        editor_pane_layout.addWidget(self.editor, stretch=1)

        self.splitter.addWidget(self.editor_pane)

        # Configure splitter ratio from custom.json
        if not self._sidebar_expanded:
            self.note_list.hide()
        else:
            self.splitter.setSizes(self.custom_config.get_splitter_sizes())

        self.splitter.splitterMoved.connect(self._on_splitter_custom_resized)

        container_layout.addWidget(self.splitter, stretch=1)

        # 4. Bottom Action Bar with + New Note button and status
        self.bottom_bar = BottomBar(self)
        self.bottom_bar.setObjectName("bottomBar")
        self.bottom_bar.setFixedHeight(38)
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(10, 4, 8, 4)
        bottom_layout.setSpacing(10)

        # Prominent + New Note button with vector SVG plus icon
        self.btn_new_note = QPushButton("New Note", self)
        self.btn_new_note.setObjectName("newNoteButton")
        self.btn_new_note.setIcon(get_svg_icon(PLUS_SVG, color="#ffffff", size=14))
        self.btn_new_note.setToolTip("Create a new note (Ctrl+N)")
        self.btn_new_note.clicked.connect(self.create_new_note)
        bottom_layout.addWidget(self.btn_new_note)

        # Status indicators
        self.status_save = QLabel("Saved", self)
        self.status_save.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_save)

        # Developer attribution badge
        self.dev_label = QLabel("•  Developed by kun", self)
        self.dev_label.setObjectName("devCreditLabel")
        bottom_layout.addWidget(self.dev_label)

        bottom_layout.addStretch()

        self.cursor_pos_label = QLabel("Ln 1, Col 1", self)
        self.cursor_pos_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.cursor_pos_label)

        self.stats_label = QLabel("0 lines  •  0 words  •  0 chars", self)
        self.stats_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.stats_label)

        # Open in Explorer button with vector SVG folder icon
        self.btn_folder = QPushButton(self)
        self.btn_folder.setToolTip("Open Notes Folder in Windows Explorer")
        self.btn_folder.setFixedSize(26, 26)
        self.btn_folder.setIcon(get_svg_icon(FOLDER_SVG, color="#475569", size=15))
        self.btn_folder.clicked.connect(lambda: self.note_service.store.open_in_file_explorer())
        bottom_layout.addWidget(self.btn_folder)

        # Corner Size Grip
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(14, 14)
        bottom_layout.addWidget(self.size_grip)

        container_layout.addWidget(self.bottom_bar)

        # Connect autosave status signal
        self.autosave.save_status_changed.connect(self.status_save.setText)

    def _setup_shortcuts(self) -> None:
        """Register all local keyboard shortcuts."""
        # Ctrl+N: New note
        QShortcut(QKeySequence("Ctrl+N"), self, self.create_new_note)
        # Ctrl+S: Save current note
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_note)
        # Ctrl+F: Search notes
        QShortcut(QKeySequence("Ctrl+F"), self, self.search_bar.focus_search)
        # Ctrl+Shift+P: Toggle Always on Top
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, lambda: self.set_always_on_top(not self._is_pinned))
        # Ctrl+Plus / Ctrl+=: Zoom in
        QShortcut(QKeySequence("Ctrl++"), self, self.editor.code_editor.zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, self.editor.code_editor.zoom_in)
        # Ctrl+Minus: Zoom out
        QShortcut(QKeySequence("Ctrl+-"), self, self.editor.code_editor.zoom_out)
        # Ctrl+0: Reset zoom
        QShortcut(QKeySequence("Ctrl+0"), self, self.editor.code_editor.reset_zoom)
        # Esc: Exit search or clear
        QShortcut(QKeySequence("Esc"), self, self._on_search_escape)
        # Ctrl+W: Close current tab (matching VS Code / browsers)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        # Ctrl+Shift+W / Alt+F4: Close entire window
        QShortcut(QKeySequence("Ctrl+Shift+W"), self, self.close)

    def close_current_tab(self) -> None:
        """Close active tab (Ctrl+W) instead of closing the whole window."""
        cur_id = self.tab_bar.get_current_note_id()
        if cur_id:
            self.tab_bar.close_tab_by_id(cur_id)
        else:
            self.close()

    def _apply_theme(self) -> None:
        """Apply light or dark theme styling."""
        qss = generate_stylesheet(self._is_dark)
        self.setStyleSheet(qss)
        self.editor.set_theme(self._is_dark)
        self.title_bar.set_theme(self._is_dark)
        self.search_bar.set_theme(self._is_dark)
        self.note_list.set_theme(self._is_dark)
        if hasattr(self, "tab_container"):
            self.tab_container.set_theme(self._is_dark)
        else:
            self.tab_bar.set_theme(self._is_dark)
        if hasattr(self, "splitter"):
            self.splitter.set_theme(self._is_dark)
        self._update_frame_style()
        folder_color = "#cccccc" if self._is_dark else "#475569"
        self.btn_folder.setIcon(get_svg_icon(FOLDER_SVG, color=folder_color, size=15))

    def _apply_dwm_attributes(self) -> None:
        """Apply native Windows DWM hardware drop shadow and rounded corners."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            class MARGINS(ctypes.Structure):
                _fields_ = [
                    ("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int),
                ]
            hwnd = int(self.winId())
            # 1. Enable DWM drop shadow around frameless window
            margins = MARGINS(1, 1, 1, 1)
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

            # 2. Enable Windows 11 rounded corners (DWMWA_WINDOW_CORNER_PREFERENCE = 33)
            # DWMWCP_DONOTROUND = 1 when maximized, DWMWCP_ROUNDSMALL = 3 when normal
            corner_pref = 1 if self.isMaximized() else 3
            val = ctypes.c_int(corner_pref)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(val), ctypes.sizeof(val))
        except Exception:
            pass

    def _update_frame_style(self) -> None:
        """Update window frame software styling based on pinned, maximized, and theme state."""
        if self.isMaximized():
            self.central_container.setStyleSheet("#centralContainer { border: none; border-radius: 0px; }")
        elif self._is_pinned:
            accent = "#38bdf8" if self._is_dark else "#2563eb"
            self.central_container.setStyleSheet(
                f"#centralContainer {{ border: 1.5px solid {accent}; border-radius: 6px; }}"
            )
        else:
            border_color = "#3e3e42" if self._is_dark else "#cbd5e1"
            self.central_container.setStyleSheet(
                f"#centralContainer {{ border: 1px solid {border_color}; border-radius: 6px; }}"
            )

        if sys.platform == "win32":
            self._apply_dwm_attributes()

    def toggle_theme(self) -> None:
        """Switch between light and dark themes."""
        self._is_dark = not self._is_dark
        self.settings.set("theme", "dark" if self._is_dark else "light")
        self._apply_theme()

    def toggle_sidebar(self) -> None:
        """Toggle visibility of the note list sidebar."""
        self._sidebar_expanded = not self._sidebar_expanded
        self.settings.set("sidebar_expanded", self._sidebar_expanded)
        if self._sidebar_expanded:
            self.note_list.show()
            self.splitter.setSizes(self.custom_config.get_splitter_sizes())
        else:
            self.note_list.hide()

    def _on_splitter_custom_resized(self, pos: int, index: int) -> None:
        """Save custom column/panel splitter widths to custom.json."""
        if hasattr(self, "custom_config") and hasattr(self, "splitter"):
            self.custom_config.save_splitter_sizes(self.splitter.sizes())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "custom_config") and not self.isMaximized():
            self.custom_config.save_window_geometry(
                width=self.width(),
                height=self.height(),
                x=self.x(),
                y=self.y(),
                is_maximized=False,
            )

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if hasattr(self, "custom_config") and not self.isMaximized():
            self.custom_config.save_window_geometry(
                width=self.width(),
                height=self.height(),
                x=self.x(),
                y=self.y(),
                is_maximized=False,
            )

    def _toggle_maximize(self) -> None:
        """Toggle between maximized window and normal floating size."""
        if self.isMaximized():
            self.showNormal()
            self.title_bar.set_maximized(False)
            self._update_frame_style()
            if hasattr(self, "custom_config"):
                self.custom_config.save_window_geometry(
                    width=self.width(),
                    height=self.height(),
                    x=self.x(),
                    y=self.y(),
                    is_maximized=False,
                )
        else:
            self.showMaximized()
            self.title_bar.set_maximized(True)
            self._update_frame_style()
            if hasattr(self, "custom_config"):
                self.custom_config.save_window_geometry(
                    width=self.width(),
                    height=self.height(),
                    x=self.x(),
                    y=self.y(),
                    is_maximized=True,
                )

    def changeEvent(self, event) -> None:
        """Handle window state changes to keep maximize/restore button state synchronized."""
        if event.type() == QEvent.WindowStateChange:
            if hasattr(self, "title_bar"):
                self.title_bar.set_maximized(self.isMaximized())
            self._update_frame_style()
        super().changeEvent(event)

    def set_always_on_top(self, enable: bool) -> None:
        """Toggle Always on Top behavior without flicker, recreation, or losing focus."""
        self._is_pinned = enable
        self.title_bar.set_pinned(enable)
        self.settings.set("is_pinned", enable)

        was_visible = self.isVisible()

        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                target_hwnd = HWND_TOPMOST if enable else HWND_NOTOPMOST
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    target_hwnd,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED
                )
            except Exception as e:
                print(f"Warning: SetWindowPos failed: {e}")

        # Keep Qt window flag in sync and re-show if was visible
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enable)
        if was_visible:
            self.show()
        self._update_frame_style()

    def activate_and_focus(self) -> None:
        """Bring window to foreground when global hotkey is pressed."""
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        self.editor.code_editor.setFocus()

    def _load_initial_note(self) -> None:
        """Load initial note from settings or default first note."""
        last_id = self.settings.get("last_active_note_id")
        note = None
        if last_id:
            note = self.note_service.get_note_by_id(last_id)

        all_notes = self.note_service.sort_notes(sort_by=self.settings.get("sort_by", "modified"))
        if not note and all_notes:
            note = all_notes[0]

        if not note:
            note = self.note_service.create_note("Untitled Note", language="python", mode="code", content="")
            all_notes = [note]

        self._switch_to_note(note.id)
        self.note_list.set_notes(all_notes, active_id=note.id)

    def _switch_to_note(self, note_id: str) -> None:
        """Switch editor view to selected note after flushing any pending edits."""
        # Save previous note if modified
        self.autosave.flush()

        note = self.note_service.get_note_by_id(note_id)
        if not note:
            return

        self.current_note = note
        self.settings.set("last_active_note_id", note.id)

        # Update editor
        self.editor.set_note_data(
            title=note.title,
            content=note.content,
            language=note.language,
            mode=note.mode,
        )

        self._update_stats()
        self.autosave.mark_clean()
        self.note_list.select_note(note.id)
        self.tab_bar.add_or_select_tab(note.id, note.title, is_dirty=False)

    def create_new_note(self) -> None:
        """Create a new note, switch to it, and focus editor."""
        self.autosave.flush()
        new_note = self.note_service.create_note()
        self._refresh_notes_list(active_id=new_note.id)
        self._switch_to_note(new_note.id)
        self.editor.title_edit.setFocus()
        self.editor.title_edit.selectAll()

    def save_current_note(self) -> None:
        """Persist currently edited note to disk."""
        if not self.current_note:
            return

        self.autosave.mark_saving()
        try:
            self.current_note.title = self.editor.get_title()
            self.current_note.content = self.editor.get_content()
            self.current_note.language = self.editor.get_language()
            self.current_note.mode = self.editor.get_mode()

            self.note_service.save_note(self.current_note)
            self.autosave.mark_clean()
            if self.current_note:
                self.tab_bar.set_tab_dirty(self.current_note.id, False)
            self._refresh_notes_list(active_id=self.current_note.id)
            self._update_stats()
        except Exception as e:
            self.autosave.mark_error(f"Error: {e}")
            print(f"Save error: {e}")

    def _on_content_changed(self) -> None:
        self.autosave.mark_dirty()
        if self.current_note:
            self.tab_bar.set_tab_dirty(self.current_note.id, True)
        self._update_stats()

    def _on_title_changed(self, new_title: str) -> None:
        self.autosave.mark_dirty()
        if self.current_note:
            self.tab_bar.update_tab_title(self.current_note.id, new_title)
            self.tab_bar.set_tab_dirty(self.current_note.id, True)

    def _on_language_changed(self, new_lang: str) -> None:
        if self.current_note:
            self.current_note.language = new_lang
            self.autosave.mark_dirty()

    def _on_mode_changed(self, new_mode: str) -> None:
        if self.current_note:
            self.current_note.mode = new_mode
            self.autosave.mark_dirty()

    def _update_stats(self) -> None:
        cursor = self.editor.code_editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        if hasattr(self, "cursor_pos_label"):
            self.cursor_pos_label.setText(f"Ln {line}, Col {col}")

        content = self.editor.get_content()
        lines = len(content.splitlines()) if content else 0
        words = len(content.split()) if content else 0
        chars = len(content)
        self.stats_label.setText(f"{lines} lines  •  {words} words  •  {chars} chars")

    def _refresh_notes_list(self, active_id: Optional[str] = None) -> None:
        sort_by = self.settings.get("sort_by", "modified")
        notes = self.note_service.sort_notes(sort_by=sort_by)
        self.note_list.set_notes(notes, active_id=active_id or (self.current_note.id if self.current_note else None))

    def _on_rename_note(self, note_id: str) -> None:
        note = self.note_service.get_note_by_id(note_id)
        if not note:
            return
        from PySide6.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(self, "Rename Note", "New note title:", text=note.title)
        if ok and new_title.strip():
            clean_title = new_title.strip()
            self.note_service.rename_note(note_id, clean_title)
            self.tab_bar.update_tab_title(note_id, clean_title)
            if self.current_note and self.current_note.id == note_id:
                self.editor.title_edit.setText(clean_title)
            self._refresh_notes_list(active_id=note_id)

    def _on_duplicate_note(self, note_id: str) -> None:
        dup = self.note_service.duplicate_note(note_id)
        if dup:
            self._refresh_notes_list(active_id=dup.id)
            self._switch_to_note(dup.id)

    def _on_delete_note(self, note_ids: Union[str, List[str]]) -> None:
        if isinstance(note_ids, str):
            note_ids = [note_ids]
        if not note_ids:
            return

        for nid in note_ids:
            self.tab_bar.close_tab_by_id(nid)
            self.note_service.delete_note(nid)

        all_notes = self.note_service.sort_notes()
        if all_notes:
            next_id = all_notes[0].id
            self._refresh_notes_list(active_id=next_id)
            self._switch_to_note(next_id)
        else:
            self.create_new_note()

    def _on_tab_closed(self, closed_note_id: str) -> None:
        """Handle tab close request."""
        self.autosave.flush()
        if self.current_note and self.current_note.id == closed_note_id:
            next_id = self.tab_bar.get_current_note_id()
            if next_id:
                self._switch_to_note(next_id)
            else:
                all_notes = self.note_service.sort_notes()
                remaining = [n for n in all_notes if n.id != closed_note_id]
                if remaining:
                    self._switch_to_note(remaining[0].id)
                else:
                    self.create_new_note()

    def _on_favorite_toggled(self, note_id: str) -> None:
        self.note_service.toggle_favorite(note_id)
        self._refresh_notes_list(active_id=note_id)

    def _on_reveal_in_explorer(self, note_id: str) -> None:
        note = self.note_service.get_note_by_id(note_id)
        if note and note.file_path:
            self.note_service.store.open_in_file_explorer(note.file_path)

    def _on_sort_changed(self, sort_by: str) -> None:
        self.settings.set("sort_by", sort_by)
        self._refresh_notes_list()

    def _on_search_query(self, query: str) -> None:
        if query:
            results = self.note_service.search_notes(query)
            # Expand sidebar to show search results
            if not self._sidebar_expanded:
                self.toggle_sidebar()
            self.note_list.set_notes(results, active_id=self.current_note.id if self.current_note else None)
            if self.current_note:
                found = self.editor.code_editor.find(query)
                if not found:
                    cursor = self.editor.code_editor.textCursor()
                    cursor.movePosition(QTextCursor.Start)
                    self.editor.code_editor.setTextCursor(cursor)
                    self.editor.code_editor.find(query)
        else:
            self._on_search_cleared()

    def _on_search_cleared(self) -> None:
        self._refresh_notes_list()

    def _on_search_escape(self) -> None:
        self.search_bar.clear_search()
        self.editor.code_editor.setFocus()

    # Geometry persistence
    def _restore_geometry(self) -> None:
        w, h, x, y, is_max = self.custom_config.get_window_geometry()
        self.resize(w, h)

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            if x is None:
                x = self.settings.get("window_x")
            if y is None:
                y = self.settings.get("window_y")
            if x is not None and y is not None:
                cur_x = int(x)
                cur_y = int(y)
                cur_x = max(geom.left(), min(cur_x, geom.right() - w))
                cur_y = max(geom.top(), min(cur_y, geom.bottom() - h))
                self.move(cur_x, cur_y)
            else:
                self.move(geom.right() - w - 24, geom.top() + 60)

        # Restore column/panel splitter sizes from custom.json
        if self._sidebar_expanded and hasattr(self, "splitter"):
            self.splitter.setSizes(self.custom_config.get_splitter_sizes())

        # Restore maximized state
        if is_max:
            self.showMaximized()
            self.title_bar.set_maximized(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        # Flush pending autosave before exit
        self.autosave.flush()

        # Persist custom window dimensions and panel sizes to custom.json
        if hasattr(self, "custom_config"):
            self.custom_config.save_window_geometry(
                width=self.width(),
                height=self.height(),
                x=self.x(),
                y=self.y(),
                is_maximized=self.isMaximized(),
            )
            if hasattr(self, "splitter"):
                self.custom_config.save_splitter_sizes(self.splitter.sizes())

        # Save window geometry
        self.settings.update({
            "window_x": self.x(),
            "window_y": self.y(),
            "window_width": self.width(),
            "window_height": self.height(),
        })

        # Unregister hotkey
        if hasattr(self, "global_hotkey"):
            self.global_hotkey.unregister()

        # Remove event filter on exit
        q_app = QApplication.instance()
        if q_app:
            try:
                q_app.removeEventFilter(self)
            except Exception:
                pass

        event.accept()

    def eventFilter(self, watched, event):
        """Native border hover cursor and resize handling without button conflicts."""
        etype = event.type()
        if etype not in (QEvent.MouseMove, QEvent.MouseButtonPress):
            return super().eventFilter(watched, event)

        if not isinstance(watched, QWidget):
            return super().eventFilter(watched, event)

        if self.isMaximized():
            return super().eventFilter(watched, event)

        if watched.window() != self:
            return super().eventFilter(watched, event)

        # Never intercept events for buttons or button children
        w = watched
        while w and w != self:
            if isinstance(w, QPushButton):
                return super().eventFilter(watched, event)
            w = w.parent()

        gp = event.globalPosition().toPoint()

        # Ensure buttons in title_bar or bottom_bar are never intercepted
        if hasattr(self, "title_bar") and self.title_bar.isVisible():
            tb_pt = self.title_bar.mapFromGlobal(gp)
            if self.title_bar.rect().contains(tb_pt):
                child = self.title_bar.childAt(tb_pt)
                c = child
                while c and c != self.title_bar:
                    if isinstance(c, QPushButton):
                        return super().eventFilter(watched, event)
                    c = c.parent()

        if hasattr(self, "bottom_bar") and self.bottom_bar.isVisible():
            bb_pt = self.bottom_bar.mapFromGlobal(gp)
            if self.bottom_bar.rect().contains(bb_pt):
                child = self.bottom_bar.childAt(bb_pt)
                c = child
                while c and c != self.bottom_bar:
                    if isinstance(c, QPushButton):
                        return super().eventFilter(watched, event)
                    c = c.parent()

        lp = self.mapFromGlobal(gp)
        margin = 8
        w, h = self.width(), self.height()

        on_left = 0 <= lp.x() <= margin
        on_right = (w - margin) <= lp.x() <= w
        on_top = 0 <= lp.y() <= margin
        on_bottom = (h - margin) <= lp.y() <= h

        if on_left or on_right or on_top or on_bottom:
            edges = Qt.Edges()
            if on_left:
                edges |= Qt.LeftEdge
            if on_right:
                edges |= Qt.RightEdge
            if on_top:
                edges |= Qt.TopEdge
            if on_bottom:
                edges |= Qt.BottomEdge

            if etype == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                wh = self.windowHandle()
                if wh and hasattr(wh, "startSystemResize"):
                    try:
                        if wh.startSystemResize(edges):
                            return True
                    except Exception:
                        pass
                if sys.platform == "win32":
                    try:
                        import ctypes
                        ctypes.windll.user32.ReleaseCapture()
                        hwnd = int(self.winId())
                        sc_map = {
                            Qt.LeftEdge: 0xF001,
                            Qt.RightEdge: 0xF002,
                            Qt.TopEdge: 0xF003,
                            Qt.BottomEdge: 0xF006,
                            Qt.TopEdge | Qt.LeftEdge: 0xF004,
                            Qt.TopEdge | Qt.RightEdge: 0xF005,
                            Qt.BottomEdge | Qt.LeftEdge: 0xF007,
                            Qt.BottomEdge | Qt.RightEdge: 0xF008,
                        }
                        sc_code = sc_map.get(edges)
                        if sc_code:
                            ctypes.windll.user32.SendMessageW(hwnd, 0x0112, sc_code, 0)
                            return True
                    except Exception:
                        pass
            elif etype == QEvent.MouseMove and not (event.buttons() & Qt.LeftButton):
                if (on_left and on_top) or (on_right and on_bottom):
                    self.setCursor(Qt.SizeFDiagCursor)
                elif (on_right and on_top) or (on_left and on_bottom):
                    self.setCursor(Qt.SizeBDiagCursor)
                elif on_left or on_right:
                    self.setCursor(Qt.SizeHorCursor)
                elif on_top or on_bottom:
                    self.setCursor(Qt.SizeVerCursor)
        else:
            if self.cursor().shape() in (
                Qt.SizeHorCursor,
                Qt.SizeVerCursor,
                Qt.SizeFDiagCursor,
                Qt.SizeBDiagCursor,
            ):
                self.unsetCursor()

        return super().eventFilter(watched, event)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    # Native Win32 Event Filter for WM_HOTKEY
    def nativeEvent(self, eventType, message):
        if sys.platform == "win32":
            try:
                from ctypes import wintypes
                msg = wintypes.MSG.from_address(int(message))

                # Global hotkey
                if hasattr(self, "global_hotkey") and self.global_hotkey.handle_native_event(msg.message, msg.wParam):
                    return True, 0
            except Exception:
                pass

        return super().nativeEvent(eventType, message)
