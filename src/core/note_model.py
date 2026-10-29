"""Data model representing a note in PinNotes."""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def current_iso_time() -> str:
    """Return the current UTC time formatted as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Note:
    """Represents a single coding note with frontmatter metadata and content."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Note"
    content: str = ""
    language: str = "python"
    mode: str = "code"  # "code" or "markdown"
    tags: List[str] = field(default_factory=list)
    pinned: bool = False
    created_at: str = field(default_factory=current_iso_time)
    updated_at: str = field(default_factory=current_iso_time)
    category: str = "General"
    file_path: Optional[Path] = None

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert note attributes to frontmatter dictionary for Obsidian compatibility."""
        meta: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "language": self.language,
            "mode": self.mode,
            "pinned": self.pinned,
            "category": self.category,
            "created": self.created_at,
            "modified": self.updated_at,
        }
        if self.tags:
            meta["tags"] = list(self.tags)
        return meta

    @classmethod
    def from_metadata_and_content(
        cls,
        meta: Dict[str, Any],
        content: str,
        file_path: Optional[Path] = None,
        default_title: str = "Untitled Note",
    ) -> Note:
        """Construct a Note from parsed frontmatter metadata and body content."""
        note_id = str(meta.get("id") or uuid.uuid4())
        title = str(meta.get("title") or default_title)
        language = str(meta.get("language") or "python").lower()
        mode = str(meta.get("mode") or ("code" if language != "markdown" else "markdown"))
        pinned = bool(meta.get("pinned", False))
        category = str(meta.get("category") or "General")

        raw_tags = meta.get("tags") or []
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        elif isinstance(raw_tags, list):
            tags = [str(t) for t in raw_tags]
        else:
            tags = []

        created_at = str(meta.get("created") or current_iso_time())
        updated_at = str(meta.get("modified") or current_iso_time())

        return cls(
            id=note_id,
            title=title,
            content=content,
            language=language,
            mode=mode,
            tags=tags,
            pinned=pinned,
            created_at=created_at,
            updated_at=updated_at,
            category=category,
            file_path=file_path,
        )
