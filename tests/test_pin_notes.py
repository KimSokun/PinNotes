"""Comprehensive automated test suite for PinNotes."""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import QApplication

from src.core.autosave import AutoSaveManager
from src.core.custom_config import CustomResizeManager
from src.core.hotkeys import parse_hotkey_string
from src.core.markdown_service import MarkdownService
from src.core.note_model import Note
from src.core.note_service import NoteService
from src.core.settings import SettingsManager
from src.storage.markdown_store import MarkdownStore, sanitize_filename
from src.ui.note_editor import CodeEditor, NoteEditorWidget
from src.ui.note_list import NoteListWidget
from src.ui.search_bar import SearchBar
from src.ui.tab_bar import NoteTabBar, NoteTabBarContainer
from src.ui.title_bar import TitleBar


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single offscreen QApplication instance is created for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


# ==========================================
# 1. Note Model & Serialization Tests
# ==========================================

def test_note_model_defaults():
    note = Note()
    assert note.title == "Untitled Note"
    assert note.language == "python"
    assert note.mode == "code"
    assert not note.pinned
    assert note.category == "General"
    assert len(note.id) > 10


def test_markdown_service_roundtrip():
    note = Note(
        title="Quick Sort Algorithm",
        content="def quicksort(arr):\n    return arr",
        language="python",
        mode="code",
        tags=["algorithms", "sorting"],
        pinned=True,
        category="Python",
    )
    md_text = MarkdownService.note_to_markdown(note)
    assert "---" in md_text
    assert "language: python" in md_text
    assert "```python" in md_text
    assert "def quicksort" in md_text

    reconstructed = MarkdownService.markdown_to_note(md_text, default_title="Untitled")
    assert reconstructed.title == "Quick Sort Algorithm"
    assert reconstructed.language == "python"
    assert reconstructed.mode == "code"
    assert reconstructed.pinned is True
    assert reconstructed.content.strip() == "def quicksort(arr):\n    return arr"


def test_sanitize_filename():
    assert sanitize_filename("Simple Note") == "Simple Note"
    assert sanitize_filename('Illegal/\\:*?"<>|Chars') == "Illegal-Chars"
    assert sanitize_filename("   Spaces   ") == "Spaces"
    assert sanitize_filename("") == "Untitled_Note"


# ==========================================
# 2. Markdown Storage & Service Tests
# ==========================================

def test_markdown_store_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MarkdownStore(Path(tmpdir))
        note = Note(title="Test Storage Note", content="print('hello')", language="python")

        # Save
        saved_path = store.save_note(note)
        assert saved_path.exists()
        assert note.file_path == saved_path

        # Load
        all_notes = store.load_all_notes()
        assert len(all_notes) == 1
        assert all_notes[0].title == "Test Storage Note"

        # Rename
        new_path = store.rename_note_file(note, "Renamed Storage Note")
        assert new_path.exists()
        assert not saved_path.exists()
        assert note.title == "Renamed Storage Note"

        # Delete
        deleted = store.delete_note_file(note)
        assert deleted is True
        assert not new_path.exists()


def test_note_service_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MarkdownStore(Path(tmpdir))
        svc = NoteService(store)

        # Initial sample note is auto-populated
        notes = svc.get_all_notes()
        assert len(notes) >= 1

        # Create note
        n1 = svc.create_note("Asyncio Basics", language="python", content="import asyncio")
        assert n1.title == "Asyncio Basics"

        # Search notes
        search_res = svc.search_notes("asyncio")
        assert len(search_res) == 1
        assert search_res[0].id == n1.id

        # Duplicate note
        dup = svc.duplicate_note(n1.id)
        assert dup is not None
        assert "Copy" in dup.title

        # Toggle favorite/pin
        assert not n1.pinned
        svc.toggle_favorite(n1.id)
        assert n1.pinned

        # Sort with pinned first
        sorted_notes = svc.sort_notes()
        assert sorted_notes[0].id == n1.id

        # Delete note
        deleted = svc.delete_note(n1.id)
        assert deleted is True
        assert svc.get_note_by_id(n1.id) is None


# ==========================================
# 3. Settings & Custom Config Tests
# ==========================================

def test_settings_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SettingsManager(config_dir=Path(tmpdir))
        assert sm.get("theme") == "light"
        sm.set("theme", "dark")
        assert sm.get("theme") == "dark"

        # Reload from disk
        sm2 = SettingsManager(config_dir=Path(tmpdir))
        assert sm2.get("theme") == "dark"


def test_custom_resize_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        crm = CustomResizeManager(config_dir=Path(tmpdir))
        crm.save_window_geometry(width=600, height=500, x=150, y=120, is_maximized=False)
        crm.save_splitter_sizes([250, 350])

        crm2 = CustomResizeManager(config_dir=Path(tmpdir))
        w, h, x, y, is_max = crm2.get_window_geometry()
        assert w == 600
        assert h == 500
        assert x == 150
        assert y == 120
        assert is_max is False
        assert crm2.get_splitter_sizes() == [250, 350]


def test_hotkey_parser():
    mods, vk = parse_hotkey_string("Ctrl+Alt+P")
    assert mods > 0
    assert vk == ord("P")


# ==========================================
# 4. UI Components Tests (Offscreen)
# ==========================================

def test_code_editor_tab_and_shift_tab(qapp):
    editor = CodeEditor()
    editor.setPlainText("    first line\n    second line")

    # Move cursor to end of second line
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.End)
    editor.setTextCursor(cursor)

    # Trigger Shift+Tab
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Backtab, Qt.ShiftModifier)
    editor.keyPressEvent(event)

    # First line must remain indented; second line must be unindented
    lines = editor.toPlainText().splitlines()
    assert lines[0] == "    first line"
    assert lines[1] == "second line"


def test_code_editor_multiline_tab(qapp):
    editor = CodeEditor()
    editor.setPlainText("line1\nline2")

    # Select all text
    cursor = editor.textCursor()
    cursor.select(QTextCursor.Document)
    editor.setTextCursor(cursor)

    # Trigger Tab
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier)
    editor.keyPressEvent(event)

    # Both lines must be indented by 4 spaces
    lines = editor.toPlainText().splitlines()
    assert lines[0] == "    line1"
    assert lines[1] == "    line2"


def test_tab_bar_reordering(qapp):
    tab_bar = NoteTabBar()
    tab_bar.add_or_select_tab("id-1", "Note 1")
    tab_bar.add_or_select_tab("id-2", "Note 2")
    tab_bar.add_or_select_tab("id-3", "Note 3")

    assert tab_bar.get_open_note_ids() == ["id-1", "id-2", "id-3"]

    # Simulate tab drag/move from index 0 to index 2
    tab_bar._on_tab_moved(0, 2)
    assert tab_bar.get_open_note_ids() == ["id-2", "id-3", "id-1"]


def test_title_bar_pin_toggle(qapp):
    tb = TitleBar()
    assert not tb.is_pinned()

    tb.set_pinned(True)
    assert tb.is_pinned()

    tb.set_pinned(False)
    assert not tb.is_pinned()


def test_search_wrap_in_main_window(qapp):
    from app import PinNotesApp
    app = PinNotesApp(["test", "-platform", "offscreen"])
    mw = app.main_window

    # Searching a nonexistent query must not throw NameError
    mw._on_search_query("nonexistent_test_string_12345")
    mw._on_search_cleared()
    mw.close()


# ==========================================
# 5. Installer & Windows Integration Tests
# ==========================================

def test_windows_utils():
    from src.installer.windows_utils import (
        get_default_install_dir,
        get_desktop_dir,
        get_start_menu_programs_dir,
    )
    inst_dir = get_default_install_dir()
    assert "PinNotes" in str(inst_dir)

    desktop = get_desktop_dir()
    assert desktop.exists() or "Desktop" in str(desktop)

    start_menu = get_start_menu_programs_dir()
    assert "Programs" in str(start_menu)


def test_installer_path_resolution():
    from src.installer.installer_gui import get_bundle_dir, get_payload_path, get_app_icon
    bundle_dir = get_bundle_dir()
    assert bundle_dir.exists()

    payload_path = get_payload_path()
    assert "payload.zip" in str(payload_path)

    icon = get_app_icon()
    assert not icon.isNull()


