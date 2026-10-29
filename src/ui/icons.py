"""SVG icon definitions and dynamic icon generator for PinNotes without emojis."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# SVG Templates (viewBox="0 0 24 24", standard Lucide / Feather stroke-based modern desktop icons)

APP_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
  <polyline points="14 2 14 8 20 8"></polyline>
  <line x1="16" y1="13" x2="8" y2="13"></line>
  <line x1="16" y1="17" x2="8" y2="17"></line>
  <line x1="10" y1="9" x2="8" y2="9"></line>
</svg>"""

PIN_UNPINNED_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 17v5"></path>
  <path d="M5 17h14l-2-6V4a1 1 0 0 0-1-1h-8a1 1 0 0 0-1 1v7l-2 6z"></path>
  <line x1="8" y1="3" x2="16" y2="3"></line>
</svg>"""

PIN_PINNED_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill_color}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 17v5"></path>
  <path d="M5 17h14l-2-6V4a1 1 0 0 0-1-1h-8a1 1 0 0 0-1 1v7l-2 6z"></path>
  <line x1="8" y1="3" x2="16" y2="3"></line>
</svg>"""

SEARCH_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="11" cy="11" r="7.5"></circle>
  <path d="m21 21-4.35-4.35"></path>
</svg>"""

SIDEBAR_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
  <line x1="9" y1="3" x2="9" y2="21"></line>
</svg>"""

MOON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path>
</svg>"""

SUN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="4.5"></circle>
  <line x1="12" y1="2" x2="12" y2="4.5"></line>
  <line x1="12" y1="19.5" x2="12" y2="22"></line>
  <line x1="2" y1="12" x2="4.5" y2="12"></line>
  <line x1="19.5" y1="12" x2="22" y2="12"></line>
  <line x1="4.93" y1="4.93" x2="6.7" y2="6.7"></line>
  <line x1="17.3" y1="17.3" x2="19.07" y2="19.07"></line>
  <line x1="4.93" y1="19.07" x2="6.7" y2="17.3"></line>
  <line x1="17.3" y1="6.7" x2="19.07" y2="4.93"></line>
</svg>"""

MINIMIZE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="4" y1="12" x2="20" y2="12"></line>
</svg>"""

MAXIMIZE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <rect x="4.5" y="4.5" width="15" height="15" rx="1.5"></rect>
</svg>"""

RESTORE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M8 5h10a1.5 1.5 0 0 1 1.5 1.5v10"></path>
  <rect x="4.5" y="7.5" width="12" height="12" rx="1.5"></rect>
</svg>"""

CLOSE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="6" y1="6" x2="18" y2="18"></line>
  <line x1="18" y1="6" x2="6" y2="18"></line>
</svg>"""

PLUS_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
  <line x1="12" y1="5" x2="12" y2="19"></line>
  <line x1="5" y1="12" x2="19" y2="12"></line>
</svg>"""

FOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path>
</svg>"""

STAR_FILLED_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill_color}" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
</svg>"""

STAR_OUTLINE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
</svg>"""

CODE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="16 18 22 12 16 6"></polyline>
  <polyline points="8 6 2 12 8 18"></polyline>
</svg>"""

PREVIEW_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
  <circle cx="12" cy="12" r="3"></circle>
</svg>"""

EDIT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
  <path d="m15 5 4 4"></path>
</svg>"""

COPY_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect width="13" height="13" x="8" y="8" rx="2" ry="2"></rect>
  <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path>
</svg>"""

TRASH_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 6h18"></path>
  <path d="M19 6v14c0 1.1-.9 2-2 2H7c-1.1 0-2-.9-2-2V6"></path>
  <path d="M8 6V4c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2v2"></path>
  <line x1="10" y1="11" x2="10" y2="17"></line>
  <line x1="14" y1="11" x2="14" y2="17"></line>
</svg>"""

CHECK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>"""


def get_svg_pixmap(
    svg_template: str,
    color: str = "#475569",
    size: int = 18,
    fill_color: Optional[str] = None,
) -> QPixmap:
    """Render an SVG template into a crisp, high-DPI QPixmap."""
    formatted_svg = svg_template.format(
        color=color,
        fill_color=fill_color or color,
    )
    data = QByteArray(formatted_svg.encode("utf-8"))
    renderer = QSvgRenderer(data)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    return pixmap


def get_svg_icon(
    svg_template: str,
    color: str = "#475569",
    size: int = 18,
    fill_color: Optional[str] = None,
) -> QIcon:
    """Render an SVG template into a QIcon."""
    pixmap = get_svg_pixmap(svg_template, color=color, size=size, fill_color=fill_color)
    return QIcon(pixmap)


def export_svg_files(assets_dir: Path) -> None:
    """Persist all SVG icons as standalone files under PinNotes/assets/icons/."""
    icons_dir = assets_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        "app.svg": APP_ICON_SVG.format(color="#2563eb", fill_color="#2563eb"),
        "pin_unpinned.svg": PIN_UNPINNED_SVG.format(color="#64748b"),
        "pin_pinned.svg": PIN_PINNED_SVG.format(color="#2563eb", fill_color="#2563eb"),
        "search.svg": SEARCH_SVG.format(color="#64748b"),
        "sidebar.svg": SIDEBAR_SVG.format(color="#64748b"),
        "theme_light.svg": SUN_SVG.format(color="#64748b"),
        "theme_dark.svg": MOON_SVG.format(color="#64748b"),
        "minimize.svg": MINIMIZE_SVG.format(color="#64748b"),
        "close.svg": CLOSE_SVG.format(color="#64748b"),
        "plus.svg": PLUS_SVG.format(color="#ffffff"),
        "folder.svg": FOLDER_SVG.format(color="#64748b"),
        "star.svg": STAR_FILLED_SVG.format(color="#eab308", fill_color="#eab308"),
        "code.svg": CODE_SVG.format(color="#64748b"),
        "preview.svg": PREVIEW_SVG.format(color="#64748b"),
        "edit.svg": EDIT_SVG.format(color="#64748b"),
        "duplicate.svg": COPY_SVG.format(color="#64748b"),
        "trash.svg": TRASH_SVG.format(color="#ef4444"),
    }

    for fname, content in file_map.items():
        (icons_dir / fname).write_text(content, encoding="utf-8")
