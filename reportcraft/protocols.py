"""
Protocol definitions for Django ReportCraft entries and datasets.

Enables in-memory, code-first reports (CodeEntry, CodeReport, QuerySetDataset, StaticDataset)
to plug seamlessly into existing entry generator functions without modifying reportcraft/entries.py.
"""

from __future__ import annotations

from typing import Any, Collection, Mapping, Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class FieldValuesListProtocol(Protocol):
    """
    Protocol for the return value of FieldCollectionProtocol.filter(...).
    Mimics the minimal Django QuerySet.values_list() interface needed by entries.py.
    """

    def values_list(self, field_name: str, *, flat: bool = False) -> Sequence[str]:
        """
        Return sequence of field names when called as values_list('name', flat=True).
        """
        ...


@runtime_checkable
class FieldCollectionProtocol(Protocol):
    """
    Protocol for entry.source.fields.
    Enables table and list generators to validate and extract column/row names.
    """

    def filter(self, *, name__in: Collection[str] = ...) -> FieldValuesListProtocol:
        """
        Filter fields by an iterable of candidate field names.
        """
        ...


@runtime_checkable
class DatasetProtocol(Protocol):
    """
    Protocol for Reusable Datasets consumed by entry generators.
    """

    fields: FieldCollectionProtocol

    def get_labels(self) -> Mapping[str, str]:
        """
        Return a mapping from field identifiers to human-readable labels.
        """
        ...

    def get_data(self, *, select: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Fetch records matching the entry filter and runtime filters.

        :param select: Entry-level filter expression passed from entry.get_filters().
        :param kwargs: Additional query parameters (e.g. runtime filters={'key': 'val'}).
        :return: List of record dictionaries.
        """
        ...


@runtime_checkable
class EntryProtocol(Protocol):
    """
    Minimal structural protocol required on an Entry by all 14 generator functions
    in reportcraft/entries.py.
    """

    title: str
    description: str
    notes: str
    style: Optional[str]
    attrs: Mapping[str, Any]
    source: Optional[DatasetProtocol]

    def get_filters(self) -> Any:
        """
        Return the entry-level filter constraint (Q object, dict, or None).
        Passed directly to source.get_data(select=...).
        """
        ...


@runtime_checkable
class ReportEntryProtocol(EntryProtocol, Protocol):
    """
    Extended protocol for entries used in full Report generation pipelines,
    including the entry type discriminator and self-generation method.
    """

    kind: str

    def generate(self, **kwargs: Any) -> dict[str, Any]:
        """
        Generate and return the Visualization Payload for this entry.
        """
        ...


__all__ = [
    "FieldValuesListProtocol",
    "FieldCollectionProtocol",
    "DatasetProtocol",
    "EntryProtocol",
    "ReportEntryProtocol",
]
