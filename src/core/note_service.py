"""High-level service managing note lifecycles, searches, ordering, and operations."""

from __future__ import annotations
import copy
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from src.core.note_model import Note, current_iso_time
from src.storage.markdown_store import MarkdownStore


class NoteService:
    """Coordinates note management, searching, sorting, and persistence."""

    def __init__(self, store: MarkdownStore):
        self.store = store
        self._notes: Dict[str, Note] = {}
        self.reload_notes()

    def reload_notes(self) -> None:
        """Reload all notes from markdown storage."""
        loaded = self.store.load_all_notes()
        self._notes.clear()
        for note in loaded:
            self._notes[note.id] = note

        # If completely empty, populate a clean empty note
        if not self._notes:
            self._create_initial_samples()

    def _create_initial_samples(self) -> None:
        """Create a clean, empty note ready for user input."""
        note = Note(
            id=str(uuid.uuid4()),
            title="Untitled Note",
            content="",
            language="python",
            mode="code",
            pinned=False,
            category="General",
        )
        self.save_note(note)

    def get_all_notes(self) -> List[Note]:
        """Return all notes in memory."""
        return list(self._notes.values())

    def get_note_by_id(self, note_id: str) -> Optional[Note]:
        """Find a note by its unique ID."""
        return self._notes.get(note_id)

    def get_next_untitled_name(self) -> str:
        """Generate a unique untitled note name."""
        base = "Untitled Note"
        existing_titles = {n.title.lower() for n in self._notes.values()}
        if base.lower() not in existing_titles:
            return base

        counter = 1
        while f"{base} {counter}".lower() in existing_titles:
            counter += 1
        return f"{base} {counter}"

    def create_note(
        self,
        title: Optional[str] = None,
        language: str = "python",
        mode: str = "code",
        content: str = "",
        category: str = "General",
    ) -> Note:
        """Create, store, and return a brand new note."""
        if not title or not title.strip():
            title = self.get_next_untitled_name()

        note = Note(
            id=str(uuid.uuid4()),
            title=title.strip(),
            content=content,
            language=language.lower(),
            mode=mode,
            category=category,
            pinned=False,
        )
        self.save_note(note)
        return note

    def save_note(self, note: Note) -> Note:
        """Save note to disk and register in active map."""
        note.updated_at = current_iso_time()
        self.store.save_note(note)
        self._notes[note.id] = note
        return note

    def rename_note(self, note_id: str, new_title: str) -> Optional[Note]:
        """Rename a note and update its file path on disk."""
        note = self.get_note_by_id(note_id)
        if not note or not new_title.strip():
            return None

        clean_title = new_title.strip()
        self.store.rename_note_file(note, clean_title)
        self._notes[note.id] = note
        return note

    def duplicate_note(self, note_id: str) -> Optional[Note]:
        """Duplicate an existing note with a '(Copy)' suffix."""
        source = self.get_note_by_id(note_id)
        if not source:
            return None

        dup_title = f"{source.title} (Copy)"
        # Disambiguate if needed
        existing = {n.title.lower() for n in self._notes.values()}
        counter = 2
        while dup_title.lower() in existing:
            dup_title = f"{source.title} (Copy {counter})"
            counter += 1

        new_note = Note(
            id=str(uuid.uuid4()),
            title=dup_title,
            content=source.content,
            language=source.language,
            mode=source.mode,
            tags=list(source.tags),
            pinned=False,
            category=source.category,
        )
        self.save_note(new_note)
        return new_note

    def delete_note(self, note_id: str) -> bool:
        """Delete a note from memory and disk."""
        note = self.get_note_by_id(note_id)
        if not note:
            return False

        self.store.delete_note_file(note)
        self._notes.pop(note_id, None)
        return True

    def toggle_favorite(self, note_id: str) -> bool:
        """Toggle favorite/pinned status within note library."""
        note = self.get_note_by_id(note_id)
        if not note:
            return False

        note.pinned = not note.pinned
        self.save_note(note)
        return note.pinned

    def search_notes(self, query: str) -> List[Note]:
        """Search notes by title and body content. Case-insensitive and multi-token."""
        q = query.strip().lower()
        if not q:
            return self.get_all_notes()

        tokens = q.split()
        results: List[Note] = []

        for note in self._notes.values():
            haystack = f"{note.title} {note.content} {' '.join(note.tags)} {note.language}".lower()
            if all(tok in haystack for tok in tokens):
                results.append(note)

        return results

    def sort_notes(
        self,
        notes: Optional[List[Note]] = None,
        sort_by: str = "modified",
    ) -> List[Note]:
        """Sort notes list. Pinned/favorite notes always appear first.
        
        Args:
            notes: List of notes to sort (defaults to all notes).
            sort_by: "modified" (recently updated first) or "title" (alphabetical A-Z).
        """
        target = list(notes if notes is not None else self._notes.values())

        if sort_by == "title":
            target.sort(key=lambda n: n.title.lower())
        else:  # modified
            target.sort(key=lambda n: n.updated_at, reverse=True)

        # Stable partition: favorite/pinned notes first
        pinned = [n for n in target if n.pinned]
        unpinned = [n for n in target if not n.pinned]
        return pinned + unpinned
