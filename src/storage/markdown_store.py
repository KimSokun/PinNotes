"""Local filesystem storage for Markdown notes compatible with Obsidian."""

from __future__ import annotations
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from src.core.markdown_service import MarkdownService
from src.core.note_model import Note, current_iso_time


# Characters illegal in Windows filenames: \ / : * ? " < > |
WINDOWS_ILLEGAL_CHARS_REGEX = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def sanitize_filename(title: str, max_length: int = 80) -> str:
    """Sanitize note title for use as a safe Windows filename while preserving Unicode and Khmer characters."""
    sanitized = WINDOWS_ILLEGAL_CHARS_REGEX.sub("-", title)
    # Clean up whitespace surrounding hyphens and collapse multiple hyphens
    sanitized = re.sub(r'\s*-\s*', '-', sanitized)
    sanitized = re.sub(r'-+', '-', sanitized)
    sanitized = sanitized.strip(" .-_")
    if not sanitized:
        sanitized = "Untitled_Note"
    # Limit length safely while preserving unicode characters
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip(" .-_")
    return sanitized


class MarkdownStore:
    """Manages reading, writing, renaming, and deleting Markdown note files in the notes folder."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        # Default subdirectories for organized Obsidian vaults
        for sub in ("General", "Python", "JavaScript", "HTML-CSS"):
            (self.root_dir / sub).mkdir(parents=True, exist_ok=True)

    def _get_category_folder(self, category: str) -> Path:
        """Return the subfolder for the note category."""
        clean_cat = sanitize_filename(category or "General", max_length=40)
        target = self.root_dir / clean_cat
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _determine_file_path(self, note: Note) -> Path:
        """Determine the file path for a note, avoiding collision with other notes."""
        if note.file_path and note.file_path.exists():
            return note.file_path

        cat_folder = self._get_category_folder(note.category)
        safe_name = sanitize_filename(note.title)
        candidate = cat_folder / f"{safe_name}.md"

        # If file exists, check if it belongs to this note
        if candidate.exists():
            try:
                existing_text = candidate.read_text(encoding="utf-8", errors="replace")
                existing_meta, _ = MarkdownService.parse_file_content(existing_text)
                if existing_meta.get("id") == note.id:
                    return candidate
            except Exception:
                pass
            
            # File belongs to a different note; disambiguate using short note ID
            short_id = note.id[:8]
            candidate = cat_folder / f"{safe_name}_{short_id}.md"

        return candidate

    def save_note(self, note: Note) -> Path:
        """Save a note to disk atomically using a temporary file and atomic replace."""
        note.updated_at = current_iso_time()
        file_path = self._determine_file_path(note)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content_to_write = MarkdownService.note_to_markdown(note)

        # Atomic write: write to temp file in the same directory, flush, sync, then replace
        temp_file = file_path.parent / f".tmp_{note.id[:8]}_{os.getpid()}"
        try:
            with open(temp_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(content_to_write)
                f.flush()
                os.fsync(f.fileno())

            # Attempt replace with retry for transient file locks (Windows indexer / antivirus)
            for attempt in range(3):
                try:
                    temp_file.replace(file_path)
                    break
                except (PermissionError, OSError):
                    if attempt == 2:
                        raise
                    import time
                    time.sleep(0.05)

            note.file_path = file_path
            return file_path
        except Exception as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            raise IOError(f"Failed to save note '{note.title}' to '{file_path}': {e}") from e

    def rename_note_file(self, note: Note, new_title: str) -> Path:
        """Rename a note's file on disk to match a new title safely."""
        old_path = note.file_path
        note.title = new_title
        cat_folder = self._get_category_folder(note.category)
        safe_name = sanitize_filename(new_title)
        new_path = cat_folder / f"{safe_name}.md"

        # Disambiguate if target already exists and is not the current file
        if new_path.exists() and (not old_path or new_path.resolve() != old_path.resolve()):
            short_id = note.id[:8]
            new_path = cat_folder / f"{safe_name}_{short_id}.md"

        if old_path and old_path.exists() and old_path.resolve() != new_path.resolve():
            # Atomically save content under new path first
            note.file_path = new_path
            self.save_note(note)
            try:
                old_path.unlink()
            except Exception:
                pass
        else:
            note.file_path = new_path
            self.save_note(note)

        return new_path

    def delete_note_file(self, note: Note) -> bool:
        """Delete note file from disk safely."""
        if note.file_path and note.file_path.exists():
            try:
                # Ensure file is inside root_dir before deleting to prevent directory traversal
                resolved_file = note.file_path.resolve()
                if self.root_dir in resolved_file.parents or resolved_file.parent == self.root_dir:
                    resolved_file.unlink()
                    note.file_path = None
                    return True
            except Exception as e:
                raise IOError(f"Failed to delete note file '{note.file_path}': {e}") from e
        return False

    def load_all_notes(self) -> List[Note]:
        """Scan root notes directory recursively for all .md files and load them."""
        notes: List[Note] = []
        if not self.root_dir.exists():
            return notes

        for md_file in self.root_dir.rglob("*.md"):
            # Ignore hidden or temp files
            if md_file.name.startswith(".") or md_file.name.startswith("~"):
                continue
            try:
                raw_text = md_file.read_text(encoding="utf-8", errors="replace")
                note = MarkdownService.markdown_to_note(raw_text, default_title=md_file.stem)
                note.file_path = md_file
                # Infer category from subfolder if not in root
                rel_parent = md_file.parent.relative_to(self.root_dir)
                if str(rel_parent) != ".":
                    note.category = str(rel_parent).replace("\\", "/")
                notes.append(note)
            except Exception as e:
                print(f"Warning: could not load note from {md_file}: {e}")

        return notes

    def open_in_file_explorer(self, target_path: Optional[Path] = None) -> None:
        """Open the notes folder or select a specific note in Windows Explorer."""
        path_to_open = target_path or self.root_dir
        if sys.platform == "win32":
            try:
                if target_path and target_path.exists() and target_path.is_file():
                    subprocess.Popen(["explorer.exe", f"/select,{str(target_path.resolve())}"])
                else:
                    subprocess.Popen(["explorer.exe", str(path_to_open.resolve())])
            except Exception as e:
                print(f"Could not open Explorer: {e}")
