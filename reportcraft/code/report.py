"""
CodeReport container class for code-first reports in Django ReportCraft.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence
from reportcraft.protocols import ReportEntryProtocol


class CodeReport:
    """
    In-memory representation of a Report.
    Allows reports to be declared and maintained in version-controlled Python code.
    Generates a full Visualization Payload dictionary for browser rendering.
    """

    def __init__(
        self,
        title: str = "",
        slug: str = "",
        theme: str = "default",
        description: str = "",
        notes: str = "",
        entries: Optional[Sequence[ReportEntryProtocol]] = None,
    ):
        self.title: str = title
        self.slug: str = slug
        self.theme: str = theme
        self.description: str = description
        self.notes: str = notes
        self.entries: list[ReportEntryProtocol] = list(entries or [])
        self.sections: list[dict[str, Any]] = []

    def add_entry(self, entry: ReportEntryProtocol) -> "CodeReport":
        """
        Append a single entry to the report.
        """
        self.entries.append(entry)
        return self

    def add_section(
        self,
        title: str = "",
        entries: Optional[Sequence[ReportEntryProtocol]] = None,
        style: str = "row",
        theme: Optional[str] = None,
        notes: str = "",
    ) -> "CodeReport":
        """
        Add a layout section to the report.
        """
        section_entries = list(entries or [])
        self.sections.append({
            "title": title,
            "entries": section_entries,
            "style": style,
            "theme": theme or self.theme,
            "notes": notes,
        })
        self.entries.extend(section_entries)
        return self

    def generate(self, filters: Optional[dict[str, Any]] = None, **kwargs: Any) -> dict[str, Any]:
        """
        Iterate over entries and generate the complete Visualization Payload dictionary.
        """
        filters = filters or {}
        section_payloads: list[dict[str, Any]] = []

        if self.sections:
            for s in self.sections:
                sec_dict: dict[str, Any] = {
                    "style": s.get("style", "row"),
                    "theme": s.get("theme", self.theme),
                    "content": [
                        entry.generate(filters=filters, **kwargs)
                        for entry in s.get("entries", [])
                    ],
                    "notes": s.get("notes", ""),
                }
                if s.get("title"):
                    sec_dict["title"] = s["title"]
                section_payloads.append(sec_dict)
        else:
            section_payloads.append({
                "style": "row",
                "theme": self.theme,
                "content": [
                    entry.generate(filters=filters, **kwargs)
                    for entry in self.entries
                ],
                "notes": self.notes,
            })

        return {
            "title": self.title,
            "description": self.description,
            "theme": self.theme,
            "sections": section_payloads,
        }


__all__ = ["CodeReport"]
