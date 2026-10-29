"""PinNotes - A lightweight, Obsidian-compatible pinnable coding notes application."""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QApplication

from src.core.note_service import NoteService
from src.core.settings import SettingsManager
from src.storage.markdown_store import MarkdownStore
from src.ui.icons import APP_ICON_SVG, get_svg_icon
from src.ui.main_window import MainWindow


def create_default_icon() -> QIcon:
    """Generate or load high-resolution application icon."""
    candidates = [
        PROJECT_ROOT / "assets" / "icon.ico",
        PROJECT_ROOT / "_internal" / "assets" / "icon.ico",
        PROJECT_ROOT / "icon.ico",
        PROJECT_ROOT / "assets" / "icon.png",
        Path(sys.executable).resolve().parent / "assets" / "icon.ico",
        Path(sys.executable).resolve().parent / "_internal" / "assets" / "icon.ico",
        Path(sys.executable).resolve().parent / "icon.ico",
    ]
    for c in candidates:
        if c.exists():
            icon = QIcon(str(c))
            if not icon.isNull():
                return icon
    return get_svg_icon(APP_ICON_SVG, color="#2563eb", fill_color="#2563eb", size=64)


class PinNotesApp:
    """Entry coordinator for setting up services and launching the main window."""

    def __init__(self, sys_argv: list[str] | None = None):
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PinNotes.App.1.2.0")
            except Exception:
                pass

        argv = sys_argv if sys_argv is not None else sys.argv
        self.app = QApplication.instance() or QApplication(argv)
        self.app.setApplicationName("PinNotes")
        self.app.setApplicationDisplayName("PinNotes")
        self.app.setOrganizationName("PinNotes")

        # Set default application font
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)

        # Set app icon
        self.icon = create_default_icon()
        self.app.setWindowIcon(self.icon)

        # Initialize configurations and storage
        self.settings = SettingsManager()
        notes_folder = self.settings.get_notes_folder()
        self.store = MarkdownStore(notes_folder)
        self.note_service = NoteService(self.store)

        # Build Main Window
        self.main_window = MainWindow(self.note_service, self.settings)
        self.main_window.setWindowIcon(self.icon)

    def run(self) -> int:
        """Show the window and enter Qt main loop."""
        self.main_window.show()
        return self.app.exec()


def main():
    """Main application entry point."""
    app = PinNotesApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
