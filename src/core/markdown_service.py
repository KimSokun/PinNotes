"""Markdown and YAML frontmatter serialization for Obsidian compatibility."""

from __future__ import annotations
import re
from typing import Any, Dict, Tuple
import yaml

from src.core.note_model import Note, current_iso_time


FRONTMATTER_REGEX = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", re.DOTALL)


class MarkdownService:
    """Handles serialization and deserialization between Note objects and Markdown files."""

    @staticmethod
    def parse_file_content(raw_text: str, default_title: str = "Untitled Note") -> Tuple[Dict[str, Any], str]:
        """Parse raw file text into metadata dictionary and body content.
        
        Handles:
        - Valid YAML frontmatter between '---' delimiters.
        - Missing frontmatter (infers title from first markdown heading or default).
        - Malformed YAML (falls back safely without crashing).
        """
        match = FRONTMATTER_REGEX.match(raw_text)
        if match:
            yaml_block = match.group(1)
            body = raw_text[match.end():]
            try:
                meta = yaml.safe_load(yaml_block)
                if not isinstance(meta, dict):
                    meta = {}
            except Exception:
                meta = {}
        else:
            meta = {}
            body = raw_text

        # If title is missing in metadata, inspect body for leading '# Title'
        if not meta.get("title"):
            first_line = body.strip().split("\n", 1)[0] if body.strip() else ""
            if first_line.startswith("# "):
                meta["title"] = first_line[2:].strip()
            else:
                meta["title"] = default_title

        return meta, body

    @staticmethod
    def extract_code_from_body(body: str, language: str) -> str:
        """If body contains a single fenced code block wrapping the entire content,
        extract inner code for code-mode editing in the editor.
        """
        stripped = body.strip()
        # Check for ```lang ... ``` or ````lang ... ````
        fence_match = re.match(r"^(`{3,})([a-zA-Z0-9_\-#+]*)\r?\n(.*?)\r?\n\1$", stripped, re.DOTALL)
        if fence_match:
            # Extracted code
            return fence_match.group(3)
        return body

    @staticmethod
    def wrap_code_for_obsidian(content: str, language: str) -> str:
        """Wrap code in markdown fence for Obsidian compatibility if not already wrapped."""
        if not content.strip():
            return ""

        # Check if already fenced
        stripped = content.strip()
        if re.match(r"^(`{3,})([a-zA-Z0-9_\-#+]*)\r?\n(.*?)\r?\n\1$", stripped, re.DOTALL):
            return content

        # Determine fence length to avoid collisions with backticks in code
        max_ticks = 0
        for match in re.finditer(r"`+", content):
            max_ticks = max(max_ticks, len(match.group(0)))
        fence = "`" * max(3, max_ticks + 1)

        lang_label = language.lower() if language and language != "text" else ""
        return f"{fence}{lang_label}\n{content}\n{fence}\n"

    @classmethod
    def note_to_markdown(cls, note: Note) -> str:
        """Serialize a Note object into a clean Obsidian-compatible Markdown string with YAML frontmatter."""
        meta = note.to_metadata_dict()
        
        # Dump YAML with clean formatting and unicode preservation
        yaml_text = yaml.safe_dump(
            meta,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        ).strip()

        # Format body content
        if note.mode == "code":
            body = cls.wrap_code_for_obsidian(note.content, note.language)
        else:
            body = note.content

        return f"---\n{yaml_text}\n---\n\n{body}"

    @classmethod
    def markdown_to_note(cls, raw_text: str, default_title: str = "Untitled Note") -> Note:
        """Deserialize a Markdown string into a Note object."""
        meta, raw_body = cls.parse_file_content(raw_text, default_title=default_title)
        language = str(meta.get("language") or "python").lower()
        mode = str(meta.get("mode") or ("code" if language != "markdown" else "markdown"))

        if mode == "code":
            clean_content = cls.extract_code_from_body(raw_body, language)
        else:
            clean_content = raw_body

        return Note.from_metadata_and_content(
            meta=meta,
            content=clean_content,
            default_title=default_title,
        )
