"""PinNotes Uninstaller - Clean, professional uninstaller for Windows."""

from __future__ import annotations
import base64
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.installer.windows_utils import (
    get_default_install_dir,
    get_desktop_dir,
    get_start_menu_programs_dir,
    remove_shortcut,
    set_autostart,
    unregister_uninstaller,
)


def get_bundle_dir() -> Path:
    """Return the base directory where assets and bundled data reside."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS).resolve()
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


EMBEDDED_ICON_PNG_B64 = (
    "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"
    "TkSuQmCC"
)


def get_app_icon(install_dir: Path | None = None) -> QIcon:
    """Load high-resolution application icon with multiple fallback sources."""
    base = get_bundle_dir()
    candidates = [
        base / "assets" / "icon.ico",
        base / "icon.ico",
        base / "assets" / "icon.png",
        PROJECT_ROOT / "assets" / "icon.ico",
        PROJECT_ROOT / "assets" / "icon.png",
    ]
    if install_dir:
        candidates.extend([
            install_dir / "_internal" / "assets" / "icon.ico",
            install_dir / "assets" / "icon.ico",
            install_dir / "icon.ico",
        ])
    for c in candidates:
        if c.exists():
            icon = QIcon(str(c))
            if not icon.isNull():
                return icon

    # Embedded PNG in-memory fallback
    try:
        raw_bytes = base64.b64decode(EMBEDDED_ICON_PNG_B64)
        pix = QPixmap()
        if pix.loadFromData(raw_bytes, "PNG"):
            return QIcon(pix)
    except Exception:
        pass

    try:
        from src.ui.icons import APP_ICON_SVG, get_svg_icon
        return get_svg_icon(APP_ICON_SVG, color="#2563eb", fill_color="#2563eb", size=64)
    except Exception:
        return QIcon()


class UninstallWorker(QThread):
    progress_changed = Signal(int, str)
    finished_signal = Signal(bool, str)

    def __init__(self, install_dir: Path, keep_notes: bool):
        super().__init__()
        self.install_dir = install_dir
        self.keep_notes = keep_notes

    def run(self):
        try:
            # Safety check: never delete dist, build, or source root
            if self.install_dir.name.lower() in ("dist", "build") or (self.install_dir / "scripts").exists():
                self.install_dir = get_default_install_dir()

            self.progress_changed.emit(10, "Removing shortcuts...")
            # 1. Remove Desktop shortcut
            desktop_lnk = get_desktop_dir() / "PinNotes.lnk"
            remove_shortcut(desktop_lnk)

            # 2. Remove Start Menu shortcut
            start_lnk = get_start_menu_programs_dir() / "PinNotes.lnk"
            remove_shortcut(start_lnk)

            self.progress_changed.emit(30, "Removing Windows registry entries...")
            unregister_uninstaller()
            set_autostart(self.install_dir / "PinNotes.exe", enable=False)

            self.progress_changed.emit(60, "Removing application files...")
            # If keep_notes is True, remove everything EXCEPT notes & config
            if self.keep_notes:
                for item in self.install_dir.iterdir():
                    # Skip PinNotes notes vault
                    if item.name.lower() in ("pinnotes", "notes"):
                        continue
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        elif item.name.lower() != "uninstall.exe":
                            item.unlink()
                    except Exception:
                        pass
            else:
                for item in self.install_dir.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        elif item.name.lower() != "uninstall.exe":
                            item.unlink()
                    except Exception:
                        pass

            self.progress_changed.emit(90, "Finalizing cleanup...")
            time.sleep(0.3)
            self.progress_changed.emit(100, "Uninstallation complete!")
            self.finished_signal.emit(True, "PinNotes was successfully uninstalled.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class UninstallerWindow(QWidget):
    def __init__(self, install_dir: Path):
        super().__init__()
        self.install_dir = install_dir
        self.setWindowTitle("PinNotes Uninstall")
        self.setFixedSize(480, 260)
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # Set Icon
        self.icon = get_app_icon(self.install_dir)
        self.setWindowIcon(self.icon)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(48, 48)
        pix = self.icon.pixmap(48, 48)
        if not pix.isNull():
            self.icon_label.setPixmap(pix)
        else:
            try:
                from src.ui.icons import APP_ICON_SVG, get_svg_pixmap
                self.icon_label.setPixmap(get_svg_pixmap(APP_ICON_SVG, color="#2563eb", fill_color="#2563eb", size=48))
            except Exception:
                pass
        header_layout.addWidget(self.icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Uninstall PinNotes", self)
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        subtitle = QLabel("Developed by kun • Are you sure you want to completely remove PinNotes?", self)
        subtitle.setStyleSheet("color: #64748b; font-size: 11px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout, stretch=1)
        layout.addLayout(header_layout)

        # Keep notes checkbox
        self.chk_keep_notes = QCheckBox("Keep my markdown notes vault and personal settings", self)
        self.chk_keep_notes.setChecked(True)
        self.chk_keep_notes.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.chk_keep_notes)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(14)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: #64748b; font-size: 10px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setFixedSize(84, 30)
        self.btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_uninstall = QPushButton("Uninstall", self)
        self.btn_uninstall.setFixedSize(94, 30)
        self.btn_uninstall.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.btn_uninstall.clicked.connect(self._start_uninstall)
        btn_layout.addWidget(self.btn_uninstall)

        layout.addLayout(btn_layout)

    def _start_uninstall(self):
        self.btn_uninstall.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.chk_keep_notes.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)

        self.worker = UninstallWorker(self.install_dir, self.chk_keep_notes.isChecked())
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def _on_finished(self, success: bool, msg: str):
        if success:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Uninstall Complete")
            msg_box.setWindowIcon(self.icon)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText("PinNotes has been successfully uninstalled.")
            msg_box.exec()
            # Schedule self-deletion of uninstaller executable
            uninstaller_exe = self.install_dir / "Uninstall.exe"
            cmd = f'cmd.exe /c ping 127.0.0.1 -n 2 > nul & del /f /q "{uninstaller_exe}" & rmdir "{self.install_dir}"'
            subprocess.Popen(cmd, shell=True)
            self.close()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Uninstall Error")
            msg_box.setWindowIcon(self.icon)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText(f"An error occurred:\n{msg}")
            msg_box.exec()
            self.btn_cancel.setEnabled(True)


def silent_uninstall(install_dir: Path):
    """Perform non-interactive silent uninstallation."""
    if install_dir.name.lower() in ("dist", "build") or (install_dir / "scripts").exists() or (install_dir.parent / "src").exists():
        install_dir = get_default_install_dir()
    if not install_dir.exists():
        return
    desktop_lnk = get_desktop_dir() / "PinNotes.lnk"
    remove_shortcut(desktop_lnk)
    start_lnk = get_start_menu_programs_dir() / "PinNotes.lnk"
    remove_shortcut(start_lnk)
    unregister_uninstaller()
    set_autostart(install_dir / "PinNotes.exe", enable=False)

    for item in install_dir.iterdir():
        if item.name.lower() in ("pinnotes", "notes"):
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.name.lower() != "uninstall.exe":
                item.unlink()
        except Exception:
            pass


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PinNotes.Uninstall.1.2.0")
        except Exception:
            pass

    args = sys.argv[1:]
    is_silent = any(a.lower() in ("/s", "/silent", "--silent", "-s") for a in args)

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if exe_dir.name.lower() in ("dist", "build") or (exe_dir / "scripts").exists() or (exe_dir.parent / "src").exists():
            install_dir = get_default_install_dir()
        else:
            install_dir = exe_dir
    else:
        install_dir = get_default_install_dir()

    if is_silent:
        silent_uninstall(install_dir)
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("PinNotes Uninstaller")
    app.setApplicationDisplayName("PinNotes Uninstaller")
    app.setOrganizationName("PinNotes")

    app_icon = get_app_icon(install_dir)
    app.setWindowIcon(app_icon)

    win = UninstallerWindow(install_dir)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
