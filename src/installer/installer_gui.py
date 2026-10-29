"""PinNotes Setup - Modern, professional installer wizard for Windows."""

from __future__ import annotations
import base64
import os
import shutil
import subprocess
import sys
import time
import zipfile
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
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.installer.windows_utils import (
    create_shortcut,
    get_default_install_dir,
    get_desktop_dir,
    get_start_menu_programs_dir,
    register_uninstaller,
    set_autostart,
)


def get_bundle_dir() -> Path:
    """Return the base directory where assets and bundled data reside."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS).resolve()
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def get_payload_path() -> Path:
    """Find embedded payload.zip in frozen package or local build directory."""
    base = get_bundle_dir()
    candidates = [
        base / "payload.zip",
        base / "dist" / "payload.zip",
        PROJECT_ROOT / "dist" / "payload.zip",
        PROJECT_ROOT / "payload.zip",
        Path(sys.executable).resolve().parent / "payload.zip" if getattr(sys, "frozen", False) else None,
    ]
    for c in candidates:
        if c and c.exists():
            return c
    return base / "payload.zip"


EMBEDDED_ICON_PNG_B64 = (
    "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"
    "TkSuQmCC"
)


def get_app_icon() -> QIcon:
    """Load high-resolution application icon with multiple fallback sources."""
    base = get_bundle_dir()

    # 1. Multi-resolution ICO file
    ico_candidates = [
        base / "assets" / "icon.ico",
        base / "icon.ico",
        PROJECT_ROOT / "assets" / "icon.ico",
        Path(sys.executable).resolve().parent / "assets" / "icon.ico" if getattr(sys, "frozen", False) else None,
        Path(sys.executable).resolve().parent / "icon.ico" if getattr(sys, "frozen", False) else None,
    ]
    for c in ico_candidates:
        if c and c.exists():
            icon = QIcon(str(c))
            if not icon.isNull():
                return icon

    # 2. High-res PNG file
    png_candidates = [
        base / "assets" / "icon.png",
        base / "icon.png",
        PROJECT_ROOT / "assets" / "icon.png",
        Path(sys.executable).resolve().parent / "assets" / "icon.png" if getattr(sys, "frozen", False) else None,
    ]
    for c in png_candidates:
        if c and c.exists():
            icon = QIcon(str(c))
            if not icon.isNull():
                return icon

    # 3. Guaranteed in-memory fallback from embedded PNG
    try:
        raw_bytes = base64.b64decode(EMBEDDED_ICON_PNG_B64)
        pix = QPixmap()
        if pix.loadFromData(raw_bytes, "PNG"):
            return QIcon(pix)
    except Exception:
        pass

    # 4. Vector SVG fallback
    try:
        from src.ui.icons import APP_ICON_SVG, get_svg_icon
        return get_svg_icon(APP_ICON_SVG, color="#2563eb", fill_color="#2563eb", size=64)
    except Exception:
        pass

    return QIcon()


class InstallWorker(QThread):
    progress_changed = Signal(int, str)
    finished_signal = Signal(bool, str)

    def __init__(
        self,
        install_dir: Path,
        create_desktop: bool,
        create_start_menu: bool,
        launch_on_startup: bool,
    ):
        super().__init__()
        self.install_dir = install_dir
        self.create_desktop = create_desktop
        self.create_start_menu = create_start_menu
        self.launch_on_startup = launch_on_startup

    def run(self):
        try:
            self.progress_changed.emit(5, "Preparing destination directory...")
            self.install_dir.mkdir(parents=True, exist_ok=True)

            payload_zip = get_payload_path()
            if not payload_zip.exists():
                raise FileNotFoundError(f"Installation payload not found at {payload_zip}")

            self.progress_changed.emit(15, "Opening package archive...")
            with zipfile.ZipFile(payload_zip, "r") as z:
                total_files = len(z.infolist())
                for idx, item in enumerate(z.infolist()):
                    z.extract(item, self.install_dir)
                    percent = 15 + int((idx / max(1, total_files)) * 65)
                    self.progress_changed.emit(percent, f"Extracting {item.filename}...")

            self.progress_changed.emit(82, "Configuring shortcuts and application icons...")
            app_exe = self.install_dir / "PinNotes.exe"
            icon_ico = self.install_dir / "_internal" / "assets" / "icon.ico"
            if not icon_ico.exists():
                icon_ico = self.install_dir / "assets" / "icon.ico"
            if not icon_ico.exists():
                icon_ico = app_exe

            # Desktop shortcut
            if self.create_desktop:
                desktop_lnk = get_desktop_dir() / "PinNotes.lnk"
                create_shortcut(
                    target_path=app_exe,
                    shortcut_path=desktop_lnk,
                    icon_path=icon_ico,
                    description="PinNotes - Obsidian-Compatible Coding Notes",
                    work_dir=self.install_dir,
                )

            # Start Menu shortcut
            if self.create_start_menu:
                start_lnk = get_start_menu_programs_dir() / "PinNotes.lnk"
                create_shortcut(
                    target_path=app_exe,
                    shortcut_path=start_lnk,
                    icon_path=icon_ico,
                    description="PinNotes - Obsidian-Compatible Coding Notes",
                    work_dir=self.install_dir,
                )

            self.progress_changed.emit(90, "Registering Windows uninstaller...")
            uninstaller_exe = self.install_dir / "Uninstall.exe"
            register_uninstaller(
                install_dir=self.install_dir,
                uninstaller_exe=uninstaller_exe,
                app_version="1.2.0",
                estimated_kb=95000,
            )

            # Autostart
            if self.launch_on_startup:
                set_autostart(app_exe, enable=True)

            self.progress_changed.emit(100, "Installation complete!")
            time.sleep(0.4)
            self.finished_signal.emit(True, "Success")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PinNotes Setup v1.2.0")
        self.setFixedSize(540, 390)
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # Set Setup Icon
        self.icon = get_app_icon()
        self.setWindowIcon(self.icon)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Header Banner
        header = QFrame(self)
        header.setFixedHeight(75)
        header.setStyleSheet("background-color: #2563eb; color: #ffffff;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 10, 20, 10)
        h_layout.setSpacing(14)

        icon_label = QLabel(header)
        icon_label.setFixedSize(48, 48)
        pix = self.icon.pixmap(48, 48)
        if not pix.isNull():
            icon_label.setPixmap(pix)
        else:
            try:
                from src.ui.icons import APP_ICON_SVG, get_svg_pixmap
                icon_label.setPixmap(get_svg_pixmap(APP_ICON_SVG, color="#ffffff", fill_color="#ffffff", size=48))
            except Exception:
                pass
        h_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        h_title = QLabel("PinNotes Setup", header)
        h_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        h_title.setStyleSheet("color: #ffffff;")
        h_sub = QLabel("Fast, Obsidian-compatible pinnable coding notes application • Developed by kun", header)
        h_sub.setStyleSheet("color: #dbeafe; font-size: 11px;")
        title_layout.addWidget(h_title)
        title_layout.addWidget(h_sub)
        h_layout.addLayout(title_layout, stretch=1)

        ver_badge = QLabel("v1.2.0 (x64)", header)
        ver_badge.setStyleSheet("color: #bfdbfe; font-size: 10px; font-weight: bold;")
        h_layout.addWidget(ver_badge, alignment=Qt.AlignRight | Qt.AlignTop)

        main_layout.addWidget(header)

        # Wizard Pages Stack
        self.stack = QStackedWidget(self)

        # Page 0: Options Page
        self.page_options = QWidget()
        po_layout = QVBoxLayout(self.page_options)
        po_layout.setContentsMargins(24, 18, 24, 14)
        po_layout.setSpacing(10)

        dest_title = QLabel("Select Installation Folder:", self.page_options)
        dest_title.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        po_layout.addWidget(dest_title)

        dest_row = QHBoxLayout()
        dest_row.setSpacing(8)
        self.dest_edit = QLineEdit(str(get_default_install_dir()), self.page_options)
        self.dest_edit.setFixedHeight(30)
        dest_row.addWidget(self.dest_edit, stretch=1)

        self.btn_browse = QPushButton("Browse...", self.page_options)
        self.btn_browse.setFixedHeight(30)
        self.btn_browse.clicked.connect(self._browse_dir)
        dest_row.addWidget(self.btn_browse)
        po_layout.addLayout(dest_row)

        space_info = QLabel("Space required: 95 MB  •  Per-user installation (No Admin / UAC prompt needed)", self.page_options)
        space_info.setStyleSheet("color: #64748b; font-size: 10px;")
        po_layout.addWidget(space_info)

        po_layout.addSpacing(10)

        opt_title = QLabel("Installation Options:", self.page_options)
        opt_title.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        po_layout.addWidget(opt_title)

        self.chk_desktop = QCheckBox("Create a Desktop shortcut", self.page_options)
        self.chk_desktop.setChecked(True)
        po_layout.addWidget(self.chk_desktop)

        self.chk_start = QCheckBox("Create a Start Menu shortcut", self.page_options)
        self.chk_start.setChecked(True)
        po_layout.addWidget(self.chk_start)

        self.chk_startup = QCheckBox("Launch PinNotes automatically on Windows startup", self.page_options)
        self.chk_startup.setChecked(False)
        po_layout.addWidget(self.chk_startup)

        po_layout.addStretch()
        self.stack.addWidget(self.page_options)

        # Page 1: Installing Progress Page
        self.page_installing = QWidget()
        pi_layout = QVBoxLayout(self.page_installing)
        pi_layout.setContentsMargins(28, 40, 28, 20)
        pi_layout.setSpacing(14)

        inst_title = QLabel("Installing PinNotes...", self.page_installing)
        inst_title.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        pi_layout.addWidget(inst_title)

        self.progress_bar = QProgressBar(self.page_installing)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                text-align: center;
                background-color: #f1f5f9;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
        """)
        pi_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Extracting files...", self.page_installing)
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        pi_layout.addWidget(self.status_label)

        pi_layout.addStretch()
        self.stack.addWidget(self.page_installing)

        # Page 2: Finish Page
        self.page_finish = QWidget()
        pf_layout = QVBoxLayout(self.page_finish)
        pf_layout.setContentsMargins(32, 35, 32, 20)
        pf_layout.setSpacing(12)

        fin_title = QLabel("Setup Completed Successfully!", self.page_finish)
        fin_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        fin_title.setStyleSheet("color: #16a34a;")
        pf_layout.addWidget(fin_title)

        fin_desc = QLabel("PinNotes has been installed on your computer.\nYour notes vault is initialized and ready to use.", self.page_finish)
        fin_desc.setStyleSheet("color: #334155; line-height: 1.5;")
        pf_layout.addWidget(fin_desc)

        pf_layout.addSpacing(10)

        self.chk_launch_now = QCheckBox("Launch PinNotes now", self.page_finish)
        self.chk_launch_now.setChecked(True)
        self.chk_launch_now.setFont(QFont("Segoe UI", 10))
        pf_layout.addWidget(self.chk_launch_now)

        pf_layout.addStretch()
        self.stack.addWidget(self.page_finish)

        main_layout.addWidget(self.stack, stretch=1)

        # Bottom Action Bar
        bottom_bar = QFrame(self)
        bottom_bar.setFixedHeight(54)
        bottom_bar.setStyleSheet("background-color: #f8fafc; border-top: 1px solid #e2e8f0;")
        b_layout = QHBoxLayout(bottom_bar)
        b_layout.setContentsMargins(20, 10, 20, 10)
        b_layout.setSpacing(10)
        b_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", bottom_bar)
        self.btn_cancel.setFixedSize(86, 32)
        self.btn_cancel.clicked.connect(self.close)
        b_layout.addWidget(self.btn_cancel)

        self.btn_action = QPushButton("Install", bottom_bar)
        self.btn_action.setFixedSize(96, 32)
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_action.clicked.connect(self._on_action_clicked)
        b_layout.addWidget(self.btn_action)

        main_layout.addWidget(bottom_bar)

    def _browse_dir(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Installation Directory", self.dest_edit.text())
        if chosen:
            self.dest_edit.setText(chosen)

    def _on_action_clicked(self):
        curr_idx = self.stack.currentIndex()
        if curr_idx == 0:
            # Start installation
            target_dir = Path(self.dest_edit.text()).resolve()
            self.stack.setCurrentIndex(1)
            self.btn_cancel.setEnabled(False)
            self.btn_action.setEnabled(False)

            self.worker = InstallWorker(
                install_dir=target_dir,
                create_desktop=self.chk_desktop.isChecked(),
                create_start_menu=self.chk_start.isChecked(),
                launch_on_startup=self.chk_startup.isChecked(),
            )
            self.worker.progress_changed.connect(self._on_progress)
            self.worker.finished_signal.connect(self._on_install_finished)
            self.worker.start()

        elif curr_idx == 2:
            # Finish clicked
            target_dir = Path(self.dest_edit.text()).resolve()
            app_exe = target_dir / "PinNotes.exe"
            if self.chk_launch_now.isChecked() and app_exe.exists():
                subprocess.Popen([str(app_exe)], cwd=str(target_dir))
            self.close()

    def _on_progress(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def _on_install_finished(self, success: bool, msg: str):
        if success:
            self.stack.setCurrentIndex(2)
            self.btn_cancel.setVisible(False)
            self.btn_action.setText("Finish")
            self.btn_action.setEnabled(True)
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Installation Failed")
            msg_box.setWindowIcon(self.icon)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText(f"Setup encountered an error:\n{msg}")
            msg_box.exec()

            self.stack.setCurrentIndex(0)
            self.btn_cancel.setEnabled(True)
            self.btn_action.setEnabled(True)


def silent_install(target_dir: Path):
    """Perform silent installation without GUI."""
    target_dir.mkdir(parents=True, exist_ok=True)
    payload_zip = get_payload_path()
    with zipfile.ZipFile(payload_zip, "r") as z:
        z.extractall(target_dir)

    app_exe = target_dir / "PinNotes.exe"
    icon_ico = target_dir / "_internal" / "assets" / "icon.ico"
    if not icon_ico.exists():
        icon_ico = target_dir / "assets" / "icon.ico"
    if not icon_ico.exists():
        icon_ico = app_exe

    desktop_lnk = get_desktop_dir() / "PinNotes.lnk"
    create_shortcut(app_exe, desktop_lnk, icon_ico, work_dir=target_dir)

    start_lnk = get_start_menu_programs_dir() / "PinNotes.lnk"
    create_shortcut(app_exe, start_lnk, icon_ico, work_dir=target_dir)

    uninstaller_exe = target_dir / "Uninstall.exe"
    register_uninstaller(target_dir, uninstaller_exe, app_version="1.2.0")


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PinNotes.Setup.1.2.0")
        except Exception:
            pass

    args = sys.argv[1:]
    is_silent = any(a.lower() in ("/s", "/silent", "--silent", "-s", "/verysilent") for a in args)

    target_dir = get_default_install_dir()

    if is_silent:
        silent_install(target_dir)
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("PinNotes Setup")
    app.setApplicationDisplayName("PinNotes Setup")
    app.setOrganizationName("PinNotes")

    # Set icon at application level so all windows and QMessageBox dialogs inherit it
    app_icon = get_app_icon()
    app.setWindowIcon(app_icon)

    win = InstallerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
