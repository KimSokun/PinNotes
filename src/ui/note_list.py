"""Note list navigation drawer with sorting, multi-select deletion, and vector SVG badges."""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional, Union

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.note_model import Note
from src.ui.icons import (
    CHECK_SVG,
    COPY_SVG,
    EDIT_SVG,
    FOLDER_SVG,
    STAR_FILLED_SVG,
    STAR_OUTLINE_SVG,
    TRASH_SVG,
    get_svg_icon,
    get_svg_pixmap,
)


def format_relative_time(iso_str: str) -> str:
    """Format ISO timestamp into clean, modern readable display."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        # Today
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        # Yesterday
        yesterday = (now - timedelta(days=1)).date()
        if dt.date() == yesterday:
            return "Yesterday"
        # Within past 6 days
        if diff.days < 7:
            return dt.strftime("%a")
        # This year
        if dt.year == now.year:
            return dt.strftime("%b %d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return ""


class NoteListItemWidget(QWidget):
    """Custom widget rendered inside each list item showing checkbox, interactive star, title, date, and preview."""

    toggled = Signal(bool)
    favorite_clicked = Signal(str)

    def __init__(self, note: Note, is_dark: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.note = note
        self._is_dark = is_dark
        self._is_checked = False
        self._selection_mode = False

        self.setFixedHeight(54)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(8, 6, 8, 6)
        root_layout.setSpacing(8)

        # Checkbox for select mode
        self.check_btn = QPushButton(self)
        self.check_btn.setFixedSize(18, 18)
        self.check_btn.setCursor(Qt.PointingHandCursor)
        self.check_btn.setVisible(False)
        self.check_btn.clicked.connect(self._on_check_clicked)
        root_layout.addWidget(self.check_btn, alignment=Qt.AlignVCenter)

        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(3)

        # Top row: Star SVG + Title
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # Interactive Star Button (Click to toggle pin/favorite)
        self.star_btn = QPushButton(self)
        self.star_btn.setFixedSize(16, 16)
        self.star_btn.setCursor(Qt.PointingHandCursor)
        self.star_btn.clicked.connect(lambda: self.favorite_clicked.emit(self.note.id))
        self._update_star_style()
        top_row.addWidget(self.star_btn)

        self.title_lbl = QLabel(note.title, self)
        self.title_lbl.setStyleSheet("font-weight: 600; font-size: 13px; background: transparent; border: none;")
        top_row.addWidget(self.title_lbl, stretch=1)

        content_layout.addLayout(top_row)

        # Bottom row: modified time & preview snippet
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)
        snippet = note.content.strip().split("\n", 1)[0][:40] if note.content else "(empty)"
        self.preview_lbl = QLabel(snippet, self)
        self.preview_lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent; border: none;")
        bottom_row.addWidget(self.preview_lbl, stretch=1)

        date_str = format_relative_time(note.updated_at)
        self.date_lbl = QLabel(date_str, self)
        self.date_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; background: transparent; border: none;")
        bottom_row.addWidget(self.date_lbl)

        content_layout.addLayout(bottom_row)
        root_layout.addLayout(content_layout, stretch=1)

        self._update_check_style()

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self._update_check_style()
        self._update_star_style()

    def _update_star_style(self) -> None:
        if self.note.pinned:
            self.star_btn.setIcon(get_svg_icon(STAR_FILLED_SVG, color="#eab308", fill_color="#eab308", size=13))
            self.star_btn.setToolTip("Unpin Note")
            self.star_btn.setStyleSheet("background: transparent; border: none; padding: 0px;")
        else:
            color = "#6e6e6e" if self._is_dark else "#cbd5e1"
            self.star_btn.setIcon(get_svg_icon(STAR_OUTLINE_SVG, color=color, size=13))
            self.star_btn.setToolTip("Pin Note to Top")
            self.star_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(234, 179, 8, 0.2);
                    border-radius: 3px;
                }
            """)

    def set_selection_mode(self, enabled: bool) -> None:
        self._selection_mode = enabled
        self.check_btn.setVisible(enabled)

    def set_checked(self, checked: bool) -> None:
        self._is_checked = checked
        self._update_check_style()

    def is_checked(self) -> bool:
        return self._is_checked

    def toggle_checked(self) -> bool:
        self.set_checked(not self._is_checked)
        self.toggled.emit(self._is_checked)
        return self._is_checked

    def _on_check_clicked(self) -> None:
        self.toggle_checked()

    def _update_check_style(self) -> None:
        border_color = "#475569" if self._is_dark else "#cbd5e1"
        accent_color = "#0e639c" if self._is_dark else "#2563eb"
        if self._is_checked:
            self.check_btn.setIcon(get_svg_icon(CHECK_SVG, color="#ffffff", size=11))
            self.check_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent_color};
                    border: 1.5px solid {accent_color};
                    border-radius: 4px;
                    padding: 0px;
                }}
            """)
        else:
            self.check_btn.setIcon(QIcon())
            self.check_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1.5px solid {border_color};
                    border-radius: 4px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    border-color: {accent_color};
                }}
            """)


class NoteCustomListWidget(QListWidget):
    """Subclassed QListWidget for custom keyboard handling (Delete key and Ctrl+A)."""

    delete_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class NoteListWidget(QWidget):
    """Collapsible sidebar list displaying all saved notes with multi-selection deletion."""

    note_selected = Signal(str)  # Emits note_id
    create_requested = Signal()
    rename_requested = Signal(str)  # Emits note_id
    duplicate_requested = Signal(str)  # Emits note_id
    delete_requested = Signal(list)  # Emits List[str] of note_ids
    favorite_toggled = Signal(str)  # Emits note_id
    reveal_requested = Signal(str)  # Emits note_id
    sort_changed = Signal(str)  # "modified" or "title"

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.setObjectName("sidebarContainer")
        self.setMinimumWidth(120)
        self.setMaximumWidth(800)
        self._is_dark = is_dark
        self._notes: List[Note] = []
        self._current_note_id: Optional[str] = None
        self._is_selection_mode = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. Normal Header
        self.normal_header = QWidget(self)
        nh_layout = QHBoxLayout(self.normal_header)
        nh_layout.setContentsMargins(2, 2, 2, 2)
        nh_layout.setSpacing(6)

        self.sort_combo = QComboBox(self.normal_header)
        self.sort_combo.addItem("Recent", "modified")
        self.sort_combo.addItem("Title (A-Z)", "title")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        nh_layout.addWidget(self.sort_combo)

        nh_layout.addStretch(1)

        self.count_label = QLabel("0 notes", self.normal_header)
        self.count_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        nh_layout.addWidget(self.count_label)

        self.select_btn = QPushButton("Select", self.normal_header)
        self.select_btn.setObjectName("selectBtn")
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.setToolTip("Select notes to delete (or hold Ctrl/Shift)")
        self.select_btn.clicked.connect(lambda: self.toggle_selection_mode(True))
        nh_layout.addWidget(self.select_btn)

        self.trash_btn = QPushButton(self.normal_header)
        self.trash_btn.setObjectName("headerTrashBtn")
        self.trash_btn.setFixedSize(22, 22)
        self.trash_btn.setCursor(Qt.PointingHandCursor)
        self.trash_btn.setToolTip("Delete selected note(s) (Del)")
        self.trash_btn.setIcon(get_svg_icon(TRASH_SVG, color="#ef4444", size=13))
        self.trash_btn.clicked.connect(self._on_header_trash_clicked)
        nh_layout.addWidget(self.trash_btn)

        layout.addWidget(self.normal_header)

        # 2. Selection Mode Header (Select to Delete toolbar)
        self.select_header = QWidget(self)
        self.select_header.setVisible(False)
        sh_layout = QHBoxLayout(self.select_header)
        sh_layout.setContentsMargins(2, 2, 2, 2)
        sh_layout.setSpacing(6)

        self.select_all_btn = QPushButton("Select All", self.select_header)
        self.select_all_btn.setObjectName("selectAllBtn")
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.clicked.connect(self._on_select_all_clicked)
        sh_layout.addWidget(self.select_all_btn)

        self.selected_count_label = QLabel("0 selected", self.select_header)
        self.selected_count_label.setStyleSheet("color: #2563eb; font-weight: 600; font-size: 11px;")
        sh_layout.addWidget(self.selected_count_label)

        sh_layout.addStretch(1)

        self.batch_delete_btn = QPushButton("Delete", self.select_header)
        self.batch_delete_btn.setObjectName("batchDeleteBtn")
        self.batch_delete_btn.setCursor(Qt.PointingHandCursor)
        self.batch_delete_btn.setToolTip("Delete selected notes permanently")
        self.batch_delete_btn.setEnabled(False)
        self.batch_delete_btn.clicked.connect(self._delete_checked_notes)
        sh_layout.addWidget(self.batch_delete_btn)

        self.cancel_select_btn = QPushButton("Done", self.select_header)
        self.cancel_select_btn.setObjectName("cancelSelectBtn")
        self.cancel_select_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_select_btn.clicked.connect(lambda: self.toggle_selection_mode(False))
        sh_layout.addWidget(self.cancel_select_btn)

        layout.addWidget(self.select_header)

        # 3. Note List Widget
        self.list_widget = NoteCustomListWidget(self)
        self.list_widget.setObjectName("noteList")
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.delete_requested.connect(self._on_key_delete_pressed)
        layout.addWidget(self.list_widget, stretch=1)

        # 4. Empty State Widget (shown when 0 notes)
        self.empty_widget = QWidget(self)
        ew_layout = QVBoxLayout(self.empty_widget)
        ew_layout.setContentsMargins(16, 40, 16, 20)
        ew_layout.setSpacing(10)
        ew_layout.setAlignment(Qt.AlignCenter)

        self.empty_msg = QLabel("No notes yet", self.empty_widget)
        self.empty_msg.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        self.empty_msg.setAlignment(Qt.AlignCenter)
        ew_layout.addWidget(self.empty_msg)

        self.empty_btn = QPushButton("+ New Note", self.empty_widget)
        self.empty_btn.setObjectName("selectBtn")
        self.empty_btn.setCursor(Qt.PointingHandCursor)
        self.empty_btn.clicked.connect(self.create_requested.emit)
        ew_layout.addWidget(self.empty_btn, alignment=Qt.AlignCenter)

        layout.addWidget(self.empty_widget)
        self.empty_widget.setVisible(False)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self.trash_btn.setIcon(get_svg_icon(TRASH_SVG, color="#ef4444", size=13))
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, NoteListItemWidget):
                widget.set_theme(is_dark)

    def toggle_selection_mode(self, enabled: bool) -> None:
        """Switch between normal navigation mode and select-to-delete mode."""
        self._is_selection_mode = enabled
        self.normal_header.setVisible(not enabled)
        self.select_header.setVisible(enabled)

        # Show or hide checkboxes on all note item widgets
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, NoteListItemWidget):
                widget.set_selection_mode(enabled)
                if not enabled:
                    widget.set_checked(False)

        if enabled:
            # Transfer any existing selected items into checked state
            for item in self.list_widget.selectedItems():
                widget = self.list_widget.itemWidget(item)
                if isinstance(widget, NoteListItemWidget):
                    widget.set_checked(True)

        self._update_checked_count()

    def _on_sort_changed(self, index: int) -> None:
        sort_mode = self.sort_combo.itemData(index)
        self.sort_changed.emit(sort_mode)

    def set_sort_mode(self, sort_by: str) -> None:
        idx = self.sort_combo.findData(sort_by)
        if idx >= 0:
            self.sort_combo.blockSignals(True)
            self.sort_combo.setCurrentIndex(idx)
            self.sort_combo.blockSignals(False)

    def set_notes(self, notes: List[Note], active_id: Optional[str] = None) -> None:
        """Update note list items."""
        self._notes = notes
        self._current_note_id = active_id
        self.list_widget.clear()
        self.count_label.setText(f"{len(notes)} note{'s' if len(notes) != 1 else ''}")

        for note in notes:
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.UserRole, note.id)

            item_widget = NoteListItemWidget(note, is_dark=self._is_dark, parent=self)
            item_widget.favorite_clicked.connect(self.favorite_toggled.emit)
            if self._is_selection_mode:
                item_widget.set_selection_mode(True)

            item.setSizeHint(QSize(200, 54))
            self.list_widget.setItemWidget(item, item_widget)

            if note.id == active_id and not self._is_selection_mode:
                self.list_widget.setCurrentItem(item)

        if len(notes) == 0:
            self.empty_widget.setVisible(True)
            self.list_widget.setVisible(False)
        else:
            self.empty_widget.setVisible(False)
            self.list_widget.setVisible(True)

        if self._is_selection_mode:
            self._update_checked_count()

    def select_note(self, note_id: str) -> None:
        """Programmatically select note in list."""
        self._current_note_id = note_id
        if self._is_selection_mode:
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == note_id:
                self.list_widget.setCurrentItem(item)
                break

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        widget = self.list_widget.itemWidget(item)
        if self._is_selection_mode:
            if isinstance(widget, NoteListItemWidget):
                widget.toggle_checked()
                self._update_checked_count()
        else:
            note_id = item.data(Qt.UserRole)
            self._current_note_id = note_id
            self.note_selected.emit(note_id)

    def _on_selection_changed(self) -> None:
        if not self._is_selection_mode:
            count = len(self.list_widget.selectedItems())
            if count > 1:
                self.trash_btn.setToolTip(f"Delete {count} selected notes (Del)")
            else:
                self.trash_btn.setToolTip("Delete selected note (Del)")

    def _on_select_all_clicked(self) -> None:
        total = self.list_widget.count()
        if total == 0:
            return

        checked_count = sum(
            1 for i in range(total)
            if isinstance(self.list_widget.itemWidget(self.list_widget.item(i)), NoteListItemWidget)
            and self.list_widget.itemWidget(self.list_widget.item(i)).is_checked()
        )

        all_checked = (checked_count == total)
        new_state = not all_checked

        for i in range(total):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, NoteListItemWidget):
                widget.set_checked(new_state)

        self.select_all_btn.setText("Deselect All" if new_state else "Select All")
        self._update_checked_count()

    def get_checked_note_ids(self) -> List[str]:
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, NoteListItemWidget) and widget.is_checked():
                nid = item.data(Qt.UserRole)
                if nid:
                    result.append(nid)
        return result

    def _update_checked_count(self) -> None:
        checked_ids = self.get_checked_note_ids()
        count = len(checked_ids)
        self.selected_count_label.setText(f"{count} selected")
        if count > 0:
            self.batch_delete_btn.setText(f"Delete ({count})")
            self.batch_delete_btn.setEnabled(True)
        else:
            self.batch_delete_btn.setText("Delete")
            self.batch_delete_btn.setEnabled(False)

    def _delete_checked_notes(self) -> None:
        checked_ids = self.get_checked_note_ids()
        if checked_ids:
            self._confirm_and_delete(checked_ids)

    def _on_header_trash_clicked(self) -> None:
        if self._is_selection_mode:
            checked_ids = self.get_checked_note_ids()
            if checked_ids:
                self._confirm_and_delete(checked_ids)
            return

        selected_items = self.list_widget.selectedItems()
        if selected_items:
            ids = [it.data(Qt.UserRole) for it in selected_items if it.data(Qt.UserRole)]
            self._confirm_and_delete(ids)
        elif self._current_note_id:
            self._confirm_and_delete([self._current_note_id])

    def _on_key_delete_pressed(self) -> None:
        if self._is_selection_mode:
            checked_ids = self.get_checked_note_ids()
            if checked_ids:
                self._confirm_and_delete(checked_ids)
        else:
            selected_items = self.list_widget.selectedItems()
            if selected_items:
                ids = [it.data(Qt.UserRole) for it in selected_items if it.data(Qt.UserRole)]
                self._confirm_and_delete(ids)
            elif self._current_note_id:
                self._confirm_and_delete([self._current_note_id])

    def _show_context_menu(self, pos: QPoint) -> None:
        item = self.list_widget.itemAt(pos)
        if not item:
            # Right clicked on empty space in list
            menu = QMenu(self)
            act_select_mode = menu.addAction("Select Notes to Delete...")
            act_select_all = menu.addAction("Select All (Ctrl+A)")
            chosen = menu.exec(self.list_widget.mapToGlobal(pos))
            if chosen == act_select_mode:
                self.toggle_selection_mode(True)
            elif chosen == act_select_all:
                self.list_widget.selectAll()
            return

        # Ensure right-clicked item is selected
        if not item.isSelected():
            self.list_widget.setCurrentItem(item)

        selected_items = self.list_widget.selectedItems()
        selected_ids = [it.data(Qt.UserRole) for it in selected_items if it.data(Qt.UserRole)]

        menu = QMenu(self)
        icon_color = "#cccccc" if self._is_dark else "#475569"

        if len(selected_ids) > 1:
            # Multi-selection context menu
            act_del = menu.addAction(
                get_svg_icon(TRASH_SVG, color="#ef4444", size=14),
                f"Delete {len(selected_ids)} Selected Notes... (Del)",
            )
            menu.addSeparator()
            act_select_mode = menu.addAction("Enter Selection Mode")
            act_select_all = menu.addAction("Select All (Ctrl+A)")

            action = menu.exec(self.list_widget.mapToGlobal(pos))
            if action == act_del:
                self._confirm_and_delete(selected_ids)
            elif action == act_select_mode:
                self.toggle_selection_mode(True)
            elif action == act_select_all:
                self.list_widget.selectAll()
            return

        # Single item context menu
        note_id = item.data(Qt.UserRole)
        act_star = menu.addAction(
            get_svg_icon(STAR_FILLED_SVG, color="#eab308", fill_color="#eab308", size=14),
            "Toggle Favorite / Pin",
        )
        act_rename = menu.addAction(
            get_svg_icon(EDIT_SVG, color=icon_color, size=14),
            "Rename Note",
        )
        act_dup = menu.addAction(
            get_svg_icon(COPY_SVG, color=icon_color, size=14),
            "Duplicate Note",
        )
        act_reveal = menu.addAction(
            get_svg_icon(FOLDER_SVG, color=icon_color, size=14),
            "Open in Explorer",
        )
        menu.addSeparator()
        act_del = menu.addAction(
            get_svg_icon(TRASH_SVG, color="#ef4444", size=14),
            "Delete Note... (Del)",
        )
        menu.addSeparator()
        act_select_mode = menu.addAction("Select Notes to Delete...")
        act_select_all = menu.addAction("Select All (Ctrl+A)")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == act_star:
            self.favorite_toggled.emit(note_id)
        elif action == act_rename:
            self.rename_requested.emit(note_id)
        elif action == act_dup:
            self.duplicate_requested.emit(note_id)
        elif action == act_reveal:
            self.reveal_requested.emit(note_id)
        elif action == act_del:
            self._confirm_and_delete([note_id])
        elif action == act_select_mode:
            self.toggle_selection_mode(True)
        elif action == act_select_all:
            self.list_widget.selectAll()

    def _confirm_and_delete(self, note_ids: List[str]) -> None:
        if not note_ids:
            return

        count = len(note_ids)
        if count == 1:
            note_title = "this note"
            for n in self._notes:
                if n.id == note_ids[0]:
                    note_title = f"'{n.title}'"
                    break
            msg = f"Are you sure you want to permanently delete {note_title}?"
        else:
            msg = f"Are you sure you want to permanently delete {count} selected notes?"

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.delete_requested.emit(note_ids)
            if self._is_selection_mode:
                self.toggle_selection_mode(False)
