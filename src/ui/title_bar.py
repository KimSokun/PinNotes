"""Custom title bar featuring pushpin Always-on-Top toggle, dragging, and SVG controls."""

from __future__ import annotations
import sys
from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from src.ui.icons import (
    APP_ICON_SVG,
    CLOSE_SVG,
    MAXIMIZE_SVG,
    MINIMIZE_SVG,
    MOON_SVG,
    PIN_PINNED_SVG,
    PIN_UNPINNED_SVG,
    RESTORE_SVG,
    SIDEBAR_SVG,
    SUN_SVG,
    get_svg_icon,
    get_svg_pixmap,
)


class TitleBar(QWidget):
    """Compact floating title bar matching the reference image using vector SVG icons."""

    pin_toggled = Signal(bool)
    sidebar_toggled = Signal()
    theme_toggled = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(34)
        self._is_pinned = False
        self._is_dark = is_dark
        self._is_maximized = False
        self.setMouseTracking(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        # App SVG Icon
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setPixmap(get_svg_pixmap(APP_ICON_SVG, color="#2563eb", size=18))
        layout.addWidget(self.icon_label)

        # Title Label
        self.title_label = QLabel("Notes", self)
        self.title_label.setObjectName("appTitle")
        self.title_label.setToolTip("PinNotes • Developed by kun")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Sidebar Drawer Toggle Button
        self.btn_sidebar = QPushButton(self)
        self.btn_sidebar.setObjectName("titleButton")
        self.btn_sidebar.setToolTip("Toggle Note List Sidebar")
        self.btn_sidebar.setFixedSize(30, 26)
        self.btn_sidebar.setCursor(Qt.PointingHandCursor)
        self.btn_sidebar.clicked.connect(self.sidebar_toggled.emit)
        layout.addWidget(self.btn_sidebar)

        # Theme Switcher Button
        self.btn_theme = QPushButton(self)
        self.btn_theme.setObjectName("titleButton")
        self.btn_theme.setToolTip("Toggle Light/Dark Theme")
        self.btn_theme.setFixedSize(30, 26)
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(self.btn_theme)

        # Pushpin (Always-on-Top) Button - Most important feature
        self.btn_pin = QPushButton(self)
        self.btn_pin.setObjectName("pinButton")
        self.btn_pin.setProperty("pinned", "false")
        self.btn_pin.setToolTip("Always on Top (Ctrl+Shift+P) [Unpinned]")
        self.btn_pin.setFixedSize(30, 26)
        self.btn_pin.setCursor(Qt.PointingHandCursor)
        self.btn_pin.clicked.connect(self._toggle_pin)
        layout.addWidget(self.btn_pin)

        # Minimize Button
        self.btn_min = QPushButton(self)
        self.btn_min.setObjectName("titleButton")
        self.btn_min.setToolTip("Minimize")
        self.btn_min.setFixedSize(30, 26)
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.btn_min)

        # Maximize / Restore Button
        self.btn_max = QPushButton(self)
        self.btn_max.setObjectName("titleButton")
        self.btn_max.setToolTip("Maximize")
        self.btn_max.setFixedSize(30, 26)
        self.btn_max.setCursor(Qt.PointingHandCursor)
        self.btn_max.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(self.btn_max)

        # Close Button
        self.btn_close = QPushButton(self)
        self.btn_close.setObjectName("closeButton")
        self.btn_close.setToolTip("Close Window (Alt+F4)")
        self.btn_close.setFixedSize(32, 26)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.btn_close)

        self._update_icons()

    def set_theme(self, is_dark: bool) -> None:
        """Update SVG icon colors according to current theme."""
        self._is_dark = is_dark
        self._update_icons()

    def set_maximized(self, is_maximized: bool) -> None:
        """Update the maximize/restore button icon and tooltip."""
        self._is_maximized = is_maximized
        self._update_maximize_icon()

    def _update_icons(self) -> None:
        color = "#cccccc" if self._is_dark else "#475569"

        self.btn_sidebar.setIcon(get_svg_icon(SIDEBAR_SVG, color=color, size=15))

        # Sun icon when in dark mode (click to go light), Moon icon when in light mode (click to go dark)
        theme_svg = SUN_SVG if self._is_dark else MOON_SVG
        self.btn_theme.setIcon(get_svg_icon(theme_svg, color=color, size=15))

        self.btn_min.setIcon(get_svg_icon(MINIMIZE_SVG, color=color, size=14))
        self.btn_close.setIcon(get_svg_icon(CLOSE_SVG, color=color, size=14))

        self._update_maximize_icon()
        self._update_pin_icon()

    def _update_maximize_icon(self) -> None:
        color = "#cccccc" if self._is_dark else "#475569"
        if self._is_maximized:
            self.btn_max.setIcon(get_svg_icon(RESTORE_SVG, color=color, size=14))
            self.btn_max.setToolTip("Restore Down")
        else:
            self.btn_max.setIcon(get_svg_icon(MAXIMIZE_SVG, color=color, size=14))
            self.btn_max.setToolTip("Maximize")

    def _update_pin_icon(self) -> None:
        if self._is_pinned:
            pin_color = "#38bdf8" if self._is_dark else "#2563eb"
            icon = get_svg_icon(PIN_PINNED_SVG, color=pin_color, fill_color=pin_color, size=16)
        else:
            color = "#858585" if self._is_dark else "#64748b"
            icon = get_svg_icon(PIN_UNPINNED_SVG, color=color, size=16)
        self.btn_pin.setIcon(icon)

    def set_pinned(self, is_pinned: bool) -> None:
        """Update pin button appearance and property."""
        self._is_pinned = is_pinned
        self.btn_pin.setProperty("pinned", "true" if is_pinned else "false")
        tooltip = "Always on Top (Ctrl+Shift+P) [Pinned]" if is_pinned else "Always on Top (Ctrl+Shift+P) [Unpinned]"
        self.btn_pin.setToolTip(tooltip)
        self._update_pin_icon()
        # Re-polish stylesheet to update visual state immediately
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)

    def is_pinned(self) -> bool:
        return self._is_pinned

    def _toggle_pin(self) -> None:
        self.set_pinned(not self._is_pinned)
        self.pin_toggled.emit(self._is_pinned)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            child = self.childAt(pos)
            w = child
            while w and w != self:
                if isinstance(w, QPushButton):
                    super().mouseDoubleClickEvent(event)
                    return
                w = w.parent()
            self.maximize_clicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    # Window Dragging & Top Border Resizing support via native Qt system methods
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            child = self.childAt(pos)
            # If the click is on any QPushButton (pin, theme, sidebar, min, max, close),
            # let QPushButton handle it directly without interception!
            w = child
            while w and w != self:
                if isinstance(w, QPushButton):
                    super().mousePressEvent(event)
                    return
                w = w.parent()

            window = self.window()
            if window:
                # Top edge resize if clicked on the very top edge (y <= 5) and not maximized
                if not window.isMaximized() and pos.y() <= 5:
                    wh = window.windowHandle()
                    if wh and hasattr(wh, "startSystemResize"):
                        if wh.startSystemResize(Qt.TopEdge):
                            event.accept()
                            return

                # Otherwise start native system move (dragging title bar)
                wh = window.windowHandle()
                if wh and hasattr(wh, "startSystemMove"):
                    wh.startSystemMove()
                    event.accept()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        window = self.window()
        if not (event.buttons() & Qt.LeftButton):
            pos = event.position().toPoint()
            child = self.childAt(pos)
            # Never set resize cursor over buttons
            w = child
            is_btn = False
            while w and w != self:
                if isinstance(w, QPushButton):
                    is_btn = True
                    break
                w = w.parent()

            if is_btn:
                self.unsetCursor()
            elif window and not window.isMaximized() and pos.y() <= 5:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.unsetCursor()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self.unsetCursor()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
