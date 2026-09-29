"""
CodeReport container class for code-first reports in Django ReportCraft.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, Union
from reportcraft.protocols import ReportEntryProtocol


class LayoutRow:
    """
    Represents a layout row in a report containing one or more visual entries.
    """

    def __init__(
        self,
        title: str = "",
        entries: Optional[Sequence[ReportEntryProtocol]] = None,
        style: str = "row",
        theme: Optional[str] = None,
        notes: str = "",
    ):
        self.title: str = title
        self.entries: list[ReportEntryProtocol] = list(entries or [])
        self.style: str = style
        self.theme: Optional[str] = theme
        self.notes: str = notes

    def add_entry(self, entry: ReportEntryProtocol) -> "LayoutRow":
        """
        Append an entry to this layout row.
        """
        self.entries.append(entry)
        return self

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def generate(
        self,
        filters: Optional[dict[str, Any]] = None,
        default_theme: str = "default",
        **kwargs: Any,
    ) -> dict[str, Any]:
        filters = filters or {}
        payload: dict[str, Any] = {
            "style": self.style or "row",
            "theme": self.theme or default_theme,
            "content": [
                entry.generate(filters=filters, **kwargs)
                for entry in self.entries
            ],
            "notes": self.notes or "",
        }
        if self.title:
            payload["title"] = self.title
        return payload


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
        self.rows: list[LayoutRow] = []

    @property
    def sections(self) -> list[LayoutRow]:
        return self.rows

    @sections.setter
    def sections(self, value: list[Any]) -> None:
        self.rows = value

    def add_entry(self, entry: ReportEntryProtocol) -> "CodeReport":
        """
        Append a single entry to the report.
        """
        self.entries.append(entry)
        return self

    def add_row(
        self,
        row_or_title: Union[LayoutRow, str] = "",
        entries: Optional[Sequence[ReportEntryProtocol]] = None,
        style: str = "row",
        theme: Optional[str] = None,
        notes: str = "",
    ) -> "CodeReport":
        """
        Add a layout row to the report.
        Accepts either a LayoutRow instance or parameters to construct one.
        """
        if isinstance(row_or_title, LayoutRow):
            row = row_or_title
        else:
            row = LayoutRow(
                title=row_or_title,
                entries=entries,
                style=style,
                theme=theme or self.theme,
                notes=notes,
            )
        self.rows.append(row)
        for e in row.entries:
            if e not in self.entries:
                self.entries.append(e)
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
        Backwards-compatible alias for add_row.
        """
        return self.add_row(
            row_or_title=title,
            entries=entries,
            style=style,
            theme=theme,
            notes=notes,
        )

    def generate(self, filters: Optional[dict[str, Any]] = None, **kwargs: Any) -> dict[str, Any]:
        """
        Iterate over entries and generate the complete Visualization Payload dictionary.
        Combines any standalone entries in self.entries into a default LayoutRow
        if not already assigned to a row, ensuring no entries are dropped.
        """
        filters = filters or {}
        rows_to_generate: list[Any] = list(self.rows)

        assigned_entries = set()
        for r in rows_to_generate:
            if isinstance(r, LayoutRow):
                assigned_entries.update(r.entries)
            elif isinstance(r, dict):
                assigned_entries.update(r.get("entries", []))

        standalone_entries = [e for e in self.entries if e not in assigned_entries]
        if standalone_entries:
            default_row = LayoutRow(
                title="",
                entries=standalone_entries,
                style="row",
                theme=self.theme,
                notes=self.notes if not rows_to_generate else "",
            )
            rows_to_generate.append(default_row)
        elif not rows_to_generate:
            rows_to_generate.append(
                LayoutRow(
                    title="",
                    entries=[],
                    style="row",
                    theme=self.theme,
                    notes=self.notes,
                )
            )

        section_payloads: list[dict[str, Any]] = []
        for r in rows_to_generate:
            if isinstance(r, LayoutRow):
                sec_dict = r.generate(filters=filters, default_theme=self.theme, **kwargs)
            else:
                sec_dict = {
                    "style": r.get("style", "row"),
                    "theme": r.get("theme", self.theme),
                    "content": [
                        entry.generate(filters=filters, **kwargs)
                        for entry in r.get("entries", [])
                    ],
                    "notes": r.get("notes", ""),
                }
                if r.get("title"):
                    sec_dict["title"] = r["title"]
            section_payloads.append(sec_dict)

        return {
            "title": self.title,
            "description": self.description,
            "theme": self.theme,
            "sections": section_payloads,
        }


__all__ = ["CodeReport", "LayoutRow"]
