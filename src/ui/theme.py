"""UI Themes (Light and Dark) and PySide6 stylesheets for PinNotes."""

from __future__ import annotations
from typing import Dict, Tuple

LIGHT_PALETTE = {
    "bg_window": "#ffffff",
    "bg_subtle": "#f8fafc",
    "bg_header": "#f1f5f9",
    "bg_editor": "#ffffff",
    "bg_hover": "#e2e8f0",
    "bg_selected": "#dbeafe",
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "border_subtle": "#e2e8f0",
    "border_focus": "#2563eb",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "accent_text": "#ffffff",
    "pin_active": "#2563eb",
    "pin_active_bg": "#dbeafe",
    "pin_inactive": "#64748b",
    "gutter_bg": "#f8fafc",
    "gutter_text": "#94a3b8",
    "gutter_border": "#e2e8f0",
    "current_line": "#f1f5f9",
    "button_bg": "#f1f5f9",
    "button_border": "#cbd5e1",
}

DARK_PALETTE = {
    "bg_window": "#1e1e1e",
    "bg_subtle": "#252526",
    "bg_header": "#2d2d2d",
    "bg_editor": "#1e1e1e",
    "bg_hover": "#37373d",
    "bg_selected": "#094771",
    "text_primary": "#cccccc",
    "text_secondary": "#9d9d9d",
    "text_muted": "#6e6e6e",
    "border_subtle": "#3e3e42",
    "border_focus": "#007acc",
    "accent": "#0e639c",
    "accent_hover": "#1177bb",
    "accent_text": "#ffffff",
    "pin_active": "#38bdf8",
    "pin_active_bg": "#0369a1",
    "pin_inactive": "#858585",
    "gutter_bg": "#1e1e1e",
    "gutter_text": "#858585",
    "gutter_border": "#2d2d2d",
    "current_line": "#282828",
    "button_bg": "#2d2d2d",
    "button_border": "#3e3e42",
}


def generate_stylesheet(is_dark: bool = False) -> str:
    """Generate comprehensive QSS stylesheet for PinNotes window and controls."""
    p = DARK_PALETTE if is_dark else LIGHT_PALETTE

    return f"""
    QWidget {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
        color: {p["text_primary"]};
        background-color: {p["bg_window"]};
    }}

    /* Title Bar */
    #titleBar {{
        background-color: {p["bg_header"]};
        border-bottom: 1px solid {p["border_subtle"]};
    }}
    #appTitle {{
        font-weight: 600;
        font-size: 13px;
        color: {p["text_primary"]};
    }}
    #titleButton, #closeButton, #pinButton {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 0px;
        margin: 0px;
        color: {p["text_secondary"]};
    }}
    #titleButton:hover {{
        background-color: {p["bg_hover"]};
        color: {p["text_primary"]};
    }}
    #titleButton:pressed {{
        background-color: {p["bg_selected"]};
    }}
    #closeButton:hover {{
        background-color: #ef4444;
        color: #ffffff;
    }}
    #closeButton:pressed {{
        background-color: #dc2626;
        color: #ffffff;
    }}
    #pinButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 0px;
        margin: 0px;
    }}
    #pinButton:hover {{
        background-color: {p["bg_hover"]};
    }}
    #pinButton:pressed {{
        background-color: {p["bg_selected"]};
    }}
    #pinButton[pinned="true"] {{
        background-color: {p["pin_active_bg"]};
        color: {p["pin_active"]};
        border: 1px solid {p["accent"]};
    }}

    /* Search Bar */
    #searchContainer {{
        background-color: {p["bg_header"]};
        padding: 6px 10px;
        border-bottom: 1px solid {p["border_subtle"]};
    }}
    #searchEdit {{
        background-color: {p["bg_window"]};
        border: 1px solid {p["border_subtle"]};
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 12px;
        color: {p["text_primary"]};
    }}
    #searchEdit:focus {{
        border: 1px solid {p["border_focus"]};
    }}

    /* Note Tab Bar */
    #noteTabBarContainer {{
        background-color: {p["bg_header"]};
        border-bottom: 1px solid {p["border_subtle"]};
    }}
    #noteTabBar {{
        background-color: transparent;
        border: none;
    }}
    #noteTabBar::tab {{
        background-color: {p["bg_subtle"]};
        color: {p["text_secondary"]};
        border: 1px solid {p["border_subtle"]};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 4px 8px;
        margin-right: 3px;
        font-size: 12px;
    }}
    #noteTabBar::tab:hover {{
        background-color: {p["bg_hover"]};
        color: {p["text_primary"]};
    }}
    #noteTabBar::tab:selected {{
        background-color: {p["bg_editor"]};
        color: {p["text_primary"]};
        font-weight: 500;
        border-top: 2px solid {p["accent"]};
    }}
    #noteTabBar QToolButton {{
        width: 0px;
        height: 0px;
        border: none;
        background: transparent;
        margin: 0px;
        padding: 0px;
    }}


    /* Note Header controls */
    #noteHeader {{
        background-color: {p["bg_window"]};
        padding: 6px 12px;
        border-bottom: 1px solid {p["border_subtle"]};
    }}
    #noteTitleEdit {{
        font-size: 14px;
        font-weight: 600;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 2px 6px;
        color: {p["text_primary"]};
        background: transparent;
    }}
    #noteTitleEdit:focus {{
        background-color: {p["bg_subtle"]};
        border: 1px solid {p["border_focus"]};
    }}

    /* Dropdown combo boxes */
    QComboBox {{
        background-color: {p["bg_subtle"]};
        border: 1px solid {p["border_subtle"]};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        color: {p["text_secondary"]};
    }}
    QComboBox:hover {{
        background-color: {p["bg_hover"]};
        color: {p["text_primary"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 14px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p["bg_window"]};
        border: 1px solid {p["border_subtle"]};
        selection-background-color: {p["bg_selected"]};
        selection-color: {p["text_primary"]};
    }}

    /* Code Editor */
    #codeEditor {{
        background-color: {p["bg_editor"]};
        color: {p["text_primary"]};
        border: none;
        selection-background-color: {p["bg_selected"]};
    }}
    #markdownViewer {{
        background-color: {p["bg_editor"]};
        color: {p["text_primary"]};
        border: none;
        padding: 10px;
    }}

    /* Note Sidebar List */
    #sidebarContainer {{
        background-color: {p["bg_subtle"]};
        border-right: 1px solid {p["border_subtle"]};
    }}
    #noteList {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    #noteList::item {{
        padding: 0px;
        margin: 2px 4px;
        border-radius: 6px;
        background: transparent;
        border: none;
    }}
    #noteList::item:hover {{
        background-color: {p["bg_hover"]};
    }}
    #noteList::item:selected {{
        background-color: {p["bg_selected"]};
    }}

    /* Select to Delete controls */
    #selectBtn, #cancelSelectBtn, #selectAllBtn {{
        background-color: transparent;
        border: 1px solid {p["border_subtle"]};
        border-radius: 4px;
        padding: 2px 7px;
        font-size: 11px;
        color: {p["text_secondary"]};
    }}
    #selectBtn:hover, #cancelSelectBtn:hover, #selectAllBtn:hover {{
        background-color: {p["bg_hover"]};
        color: {p["text_primary"]};
    }}
    #batchDeleteBtn {{
        background-color: #ef4444;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 2px 9px;
        font-size: 11px;
        font-weight: 600;
    }}
    #batchDeleteBtn:hover {{
        background-color: #dc2626;
    }}
    #batchDeleteBtn:disabled {{
        background-color: {p["bg_hover"]};
        color: {p["text_muted"]};
    }}
    #headerTrashBtn {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 3px;
        margin: 0px;
    }}
    #headerTrashBtn:hover {{
        background-color: rgba(239, 68, 68, 0.15);
    }}

    /* QSplitter Horizontal Resize Handle */
    QSplitter::handle:horizontal {{
        background-color: {p["border_subtle"]};
        width: 6px;
        margin: 0px 1px;
        border-radius: 2px;
    }}
    QSplitter::handle:horizontal:hover {{
        background-color: {p["accent"]};
    }}
    QSplitter::handle:horizontal:pressed {{
        background-color: {p["accent_hover"]};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {p["button_bg"]};
        border: 1px solid {p["button_border"]};
        border-radius: 4px;
        padding: 4px 10px;
        color: {p["text_primary"]};
        font-size: 12px;
    }}
    QPushButton:hover {{
        background-color: {p["bg_hover"]};
    }}
    #newNoteButton {{
        background-color: {p["accent"]};
        border: 1px solid {p["accent"]};
        color: {p["accent_text"]};
        font-weight: 600;
        border-radius: 5px;
        padding: 6px 14px;
    }}
    #newNoteButton:hover {{
        background-color: {p["accent_hover"]};
    }}

    /* Bottom Status Bar */
    #bottomBar {{
        background-color: {p["bg_subtle"]};
        border-top: 1px solid {p["border_subtle"]};
        padding: 4px 10px;
    }}
    #statusLabel, #devCreditLabel {{
        font-size: 11px;
        color: {p["text_muted"]};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {p["bg_window"]};
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {p["border_subtle"]};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p["text_muted"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        width: 0px;
        background: transparent;
        border: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: {p["bg_window"]};
        height: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p["border_subtle"]};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        height: 0px;
        width: 0px;
        background: transparent;
        border: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QAbstractScrollArea::corner, QScrollBar::corner {{
        background: transparent;
        border: none;
    }}
    QSizeGrip {{
        background: transparent;
        width: 14px;
        height: 14px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {p["bg_header"]};
        color: {p["text_primary"]};
        border: 1px solid {p["border_subtle"]};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
    }}

    /* Mode & Language buttons */
    #modeButton {{
        background-color: transparent;
        border: 1px solid {p["border_subtle"]};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        color: {p["text_secondary"]};
    }}
    #modeButton:hover {{
        background-color: {p["bg_hover"]};
        color: {p["text_primary"]};
    }}
    #langCombo {{
        min-width: 105px;
    }}
    """
