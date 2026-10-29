"""Full-featured code editor with syntax highlighting, line numbers, and markdown preview."""

from __future__ import annotations
import re
from typing import Dict, List, Optional

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Token,
)

from src.ui.icons import CODE_SVG, PREVIEW_SVG, get_svg_icon

# Supported programming languages and their Pygments alias mappings
SUPPORTED_LANGUAGES = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "html": "HTML",
    "css": "CSS",
    "json": "JSON",
    "c": "C",
    "cpp": "C++",
    "java": "Java",
    "sql": "SQL",
    "bash": "Bash",
    "powershell": "PowerShell",
    "markdown": "Markdown",
    "text": "Plain Text",
}

# Syntax color tokens for Light vs Dark themes
LIGHT_SYNTAX_COLORS = {
    Keyword: "#0000ff",
    Keyword.Constant: "#0000ff",
    Keyword.Declaration: "#0000ff",
    Keyword.Namespace: "#0000ff",
    Keyword.Pseudo: "#0000ff",
    Keyword.Type: "#2b91af",
    Name.Class: "#2b91af",
    Name.Function: "#795e26",
    Name.Builtin: "#0000ff",
    Name.Builtin.Pseudo: "#0000ff",
    String: "#a31515",
    String.Doc: "#a31515",
    Comment: "#008000",
    Comment.Single: "#008000",
    Comment.Multiline: "#008000",
    Number: "#098658",
    Operator: "#000000",
    Punctuation: "#000000",
}

DARK_SYNTAX_COLORS = {
    Keyword: "#569cd6",
    Keyword.Constant: "#569cd6",
    Keyword.Declaration: "#569cd6",
    Keyword.Namespace: "#569cd6",
    Keyword.Pseudo: "#569cd6",
    Keyword.Type: "#4ec9b0",
    Name.Class: "#4ec9b0",
    Name.Function: "#dcdcaa",
    Name.Builtin: "#569cd6",
    Name.Builtin.Pseudo: "#569cd6",
    String: "#ce9178",
    String.Doc: "#ce9178",
    Comment: "#6a9955",
    Comment.Single: "#6a9955",
    Comment.Multiline: "#6a9955",
    Number: "#b5cea8",
    Operator: "#d4d4d4",
    Punctuation: "#d4d4d4",
}


class PygmentsHighlighter(QSyntaxHighlighter):
    """Real-time syntax highlighter powered by Pygments and PySide6."""

    def __init__(self, document, language: str = "python", is_dark: bool = False):
        super().__init__(document)
        self.language = language
        self.is_dark = is_dark
        self._lexer = self._create_lexer(language)
        self._formats: Dict[Any, QTextCharFormat] = {}
        self._init_formats()

    def _create_lexer(self, lang: str):
        normalized = lang.lower()
        if normalized == "c++":
            normalized = "cpp"
        elif normalized == "plain text":
            normalized = "text"

        try:
            return get_lexer_by_name(normalized, stripnl=False, ensurenl=False)
        except Exception:
            return TextLexer(stripnl=False, ensurenl=False)

    def set_language(self, language: str) -> None:
        self.language = language
        self._lexer = self._create_lexer(language)
        self.rehighlight()

    def set_theme(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        self._init_formats()
        self.rehighlight()

    def _init_formats(self) -> None:
        colors = DARK_SYNTAX_COLORS if self.is_dark else LIGHT_SYNTAX_COLORS
        self._formats.clear()

        for token_type, hex_color in colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(hex_color))
            if token_type in (Keyword, Keyword.Declaration):
                fmt.setFontWeight(QFont.Bold)
            self._formats[token_type] = fmt

    def _get_format_for_token(self, token_type):
        curr = token_type
        while curr:
            if curr in self._formats:
                return self._formats[curr]
            curr = curr.parent
        return None

    def highlightBlock(self, text: str) -> None:
        if not text or isinstance(self._lexer, TextLexer):
            return

        try:
            tokens = self._lexer.get_tokens_unprocessed(text)
            for index, token_type, value in tokens:
                fmt = self._get_format_for_token(token_type)
                if fmt:
                    self.setFormat(index, len(value), fmt)
        except Exception:
            pass


class LineNumberArea(QWidget):
    """Line number gutter widget displayed to the left of the code editor."""

    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Monospaced code editor with line numbers, auto-indent, zoom, and tab controls."""

    zoom_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.setObjectName("codeEditor")
        self.is_dark = is_dark
        self._font_size = 12
        self.tab_size = 4

        self.line_number_area = LineNumberArea(self)

        # Configure font
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(self._font_size)
        self.setFont(font)

        # Tab stop width (4 spaces)
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_size)

        # Syntax highlighter
        self.highlighter = PygmentsHighlighter(self.document(), language="python", is_dark=is_dark)

        # Signals for line numbering gutter
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def set_language(self, lang: str) -> None:
        self.highlighter.set_language(lang)

    def set_theme(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        self.highlighter.set_theme(is_dark)
        self.highlight_current_line()

    def set_font_size(self, size: int) -> None:
        size = max(8, min(36, size))
        self._font_size = size
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_size)
        self.update_line_number_area_width(0)
        self.zoom_changed.emit(self._font_size)

    def zoom_in(self) -> None:
        self.set_font_size(self._font_size + 1)

    def zoom_out(self) -> None:
        self.set_font_size(self._font_size - 1)

    def reset_zoom(self) -> None:
        self.set_font_size(12)

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(max(1, self.blockCount()))))
        space = 16 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        bg_color = QColor("#1e1e1e" if self.is_dark else "#f8fafc")
        text_color = QColor("#858585" if self.is_dark else "#94a3b8")
        border_color = QColor("#2d2d2d" if self.is_dark else "#e2e8f0")

        painter.fillRect(event.rect(), bg_color)
        painter.setPen(border_color)
        painter.drawLine(event.rect().topRight(), event.rect().bottomRight())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setPen(text_color)
        painter.setFont(self.font())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#282828" if self.is_dark else "#f8fafc")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Tab handling
        if event.key() == Qt.Key_Tab and not (event.modifiers() & Qt.ShiftModifier):
            cursor = self.textCursor()
            # If multiple lines are selected, indent all selected lines
            if cursor.hasSelection() and ("\n" in cursor.selectedText() or "\u2029" in cursor.selectedText()):
                cursor.beginEditBlock()
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                cursor.setPosition(start_pos)
                start_block = cursor.block()
                cursor.setPosition(end_pos)
                end_block = cursor.block()
                curr_block = start_block
                while curr_block.isValid():
                    c = QTextCursor(curr_block)
                    c.movePosition(QTextCursor.StartOfBlock)
                    c.insertText(" " * self.tab_size)
                    if curr_block == end_block:
                        break
                    curr_block = curr_block.next()
                cursor.endEditBlock()
                event.accept()
                return

            self.insertPlainText(" " * self.tab_size)
            event.accept()
            return

        # Shift+Tab handling (unindent 4 spaces)
        if event.key() == Qt.Key_Backtab or (event.key() == Qt.Key_Tab and (event.modifiers() & Qt.ShiftModifier)):
            cursor = self.textCursor()
            cursor.beginEditBlock()
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()

            cursor.setPosition(start_pos)
            start_block = cursor.block()
            cursor.setPosition(end_pos)
            end_block = cursor.block()

            curr_block = start_block
            while curr_block.isValid():
                text = curr_block.text()
                spaces_to_remove = 0
                for char in text[:self.tab_size]:
                    if char == " ":
                        spaces_to_remove += 1
                    elif char == "\t":
                        spaces_to_remove += 1
                        break
                    else:
                        break
                if spaces_to_remove > 0:
                    c = QTextCursor(curr_block)
                    c.movePosition(QTextCursor.StartOfBlock)
                    c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, spaces_to_remove)
                    c.removeSelectedText()
                if curr_block == end_block:
                    break
                curr_block = curr_block.next()
            cursor.endEditBlock()
            event.accept()
            return

        # Auto-indent on Enter
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            block_text = cursor.block().text()
            pos_in_block = cursor.positionInBlock()
            text_before = block_text[:pos_in_block]

            # Find leading whitespace of current line
            match = re.match(r"^(\s*)", block_text)
            leading_whitespace = match.group(1) if match else ""

            # Additional indentation after colon, open brace, etc. before cursor
            if text_before.rstrip().endswith((":", "{", "[", "(")):
                leading_whitespace += " " * self.tab_size

            super().keyPressEvent(event)
            self.insertPlainText(leading_whitespace)
            event.accept()
            return

        super().keyPressEvent(event)


class NoteEditorWidget(QWidget):
    """Container widget providing editable note title, language selector,
    mode switch (Code / Markdown), CodeEditor, and Markdown preview.
    """

    content_changed = Signal()
    title_changed = Signal(str)
    language_changed = Signal(str)
    mode_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, is_dark: bool = False):
        super().__init__(parent)
        self.is_dark = is_dark
        self._current_mode = "code"
        self._current_language = "python"

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar for Note Title, Language Selector, and Mode Toggle
        self.header_widget = QWidget(self)
        self.header_widget.setObjectName("noteHeader")
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(10, 4, 10, 4)
        header_layout.setSpacing(8)

        # Editable Note Title
        self.title_edit = QLineEdit("Untitled Note", self)
        self.title_edit.setObjectName("noteTitleEdit")
        self.title_edit.setPlaceholderText("Note Title...")
        self.title_edit.textChanged.connect(self.title_changed.emit)
        self.title_edit.returnPressed.connect(lambda: self.code_editor.setFocus())
        header_layout.addWidget(self.title_edit, stretch=1)

        # Removed language selector and mode toggle buttons per user request
        self.lang_combo = None
        self.btn_mode = None

        main_layout.addWidget(self.header_widget)

        # Stacked editor views (Index 0: Code Editor, Index 1: Markdown Rendered View)
        self.stack = QStackedWidget(self)

        self.code_editor = CodeEditor(self, is_dark=self.is_dark)
        self.code_editor.textChanged.connect(self.content_changed.emit)
        self.stack.addWidget(self.code_editor)

        self.markdown_viewer = QTextBrowser(self)
        self.markdown_viewer.setObjectName("markdownViewer")
        self.markdown_viewer.setOpenExternalLinks(True)
        self.stack.addWidget(self.markdown_viewer)

        main_layout.addWidget(self.stack, stretch=1)

    def set_theme(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        self.code_editor.set_theme(is_dark)
        if self._current_mode == "markdown":
            self._render_markdown()

    def set_note_data(self, title: str, content: str, language: str, mode: str) -> None:
        """Populate editor with note data without firing spurious signals."""
        self.title_edit.blockSignals(True)
        self.code_editor.blockSignals(True)

        self.title_edit.setText(title)
        self.code_editor.setPlainText(content)

        # Language sync
        self._current_language = language.lower() if language else "python"
        self.code_editor.set_language(self._current_language)
        if self.lang_combo is not None:
            idx = self.lang_combo.findData(self._current_language)
            if idx >= 0:
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(idx)
                self.lang_combo.blockSignals(False)

        # Mode sync
        self._current_mode = mode if mode in ("code", "markdown") else "code"
        self._update_mode_ui()

        self.title_edit.blockSignals(False)
        self.code_editor.blockSignals(False)

    def get_title(self) -> str:
        return self.title_edit.text().strip() or "Untitled Note"

    def get_content(self) -> str:
        return self.code_editor.toPlainText()

    def get_language(self) -> str:
        return self._current_language or "python"

    def get_mode(self) -> str:
        return self._current_mode

    def _toggle_mode(self) -> None:
        new_mode = "markdown" if self._current_mode == "code" else "code"
        self._current_mode = new_mode
        self._update_mode_ui()
        self.mode_changed.emit(self._current_mode)

    def _on_language_combo_changed(self, index: int) -> None:
        if self.lang_combo is not None:
            lang_key = self.lang_combo.itemData(index) or "python"
            self._current_language = lang_key
            self.code_editor.set_language(lang_key)
            self.language_changed.emit(lang_key)

    def _update_mode_ui(self) -> None:
        if self.btn_mode is not None:
            color = "#cccccc" if self.is_dark else "#475569"
            if self._current_mode == "code":
                self.btn_mode.setText("Code")
                self.btn_mode.setIcon(get_svg_icon(CODE_SVG, color=color, size=14))
                self.stack.setCurrentIndex(0)
            else:
                self.btn_mode.setText("Preview")
                self.btn_mode.setIcon(get_svg_icon(PREVIEW_SVG, color=color, size=14))
                self._render_markdown()
                self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)

    def _render_markdown(self) -> None:
        """Render markdown text with styling and code blocks into the viewer."""
        raw_text = self.code_editor.toPlainText()
        bg = "#1e1e1e" if self.is_dark else "#ffffff"
        fg = "#d4d4d4" if self.is_dark else "#0f172a"
        code_bg = "#2d2d2d" if self.is_dark else "#f1f5f9"
        border = "#3e3e42" if self.is_dark else "#e2e8f0"

        doc_css = f"""
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: {bg};
                color: {fg};
                padding: 12px;
                line-height: 1.6;
            }}
            pre, code {{
                font-family: Consolas, 'Cascadia Code', monospace;
                background-color: {code_bg};
                border-radius: 4px;
                padding: 2px 4px;
            }}
            pre {{
                padding: 10px;
                border: 1px solid {border};
            }}
            h1, h2, h3 {{
                border-bottom: 1px solid {border};
                padding-bottom: 4px;
            }}
            blockquote {{
                border-left: 4px solid #2563eb;
                margin-left: 0;
                padding-left: 12px;
                color: #64748b;
            }}
        """
        self.markdown_viewer.document().setDefaultStyleSheet(doc_css)
        self.markdown_viewer.setMarkdown(raw_text)
