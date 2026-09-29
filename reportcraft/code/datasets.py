"""
Reusable Dataset implementations for code-first reports in Django ReportCraft.

Provides InMemFieldCollection, InMemFieldQuerySet, StaticDataset, and QuerySetDataset,
all conforming to DatasetProtocol.
"""

from __future__ import annotations

from typing import Any, Collection, Mapping, Optional, Sequence
from django.db.models import Q


class InMemFieldQuerySet:
    """
    Implements FieldValuesListProtocol for in-memory field collections.
    Mimics the minimal Django QuerySet.values_list() interface needed by entries.py.
    """

    def __init__(self, names: Sequence[str]):
        self._names = list(names)

    def values_list(self, field_name: str = "name", *field_names: str, flat: bool = False) -> Sequence[Any]:
        if flat:
            return list(self._names)
        all_fields = (field_name,) + field_names if field_names else (field_name,)
        if len(all_fields) <= 1:
            return [(name,) for name in self._names]
        return [tuple(name for _ in all_fields) for name in self._names]

    def __iter__(self):
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)

    def __contains__(self, item: Any) -> bool:
        return item in self._names

    def __repr__(self) -> str:
        return f"<InMemFieldQuerySet {self._names!r}>"


class InMemFieldCollection:
    """
    Implements FieldCollectionProtocol for in-memory field collections.
    Enables table and list entry generators to validate and extract column/row names.
    """

    def __init__(self, names: Sequence[str]):
        self._names = list(names)

    def filter(self, *, name__in: Collection[str] = ()) -> InMemFieldQuerySet:
        if name__in is None:
            return InMemFieldQuerySet([])
        if isinstance(name__in, (list, tuple)):
            valid = set(self._names)
            matched = [n for n in name__in if n in valid]
        else:
            candidates = set(name__in)
            matched = [n for n in self._names if n in candidates]
        return InMemFieldQuerySet(matched)

    def all(self) -> Sequence[str]:
        return list(self._names)

    def values_list(self, field_name: str = "name", *field_names: str, flat: bool = False) -> Sequence[Any]:
        return InMemFieldQuerySet(self._names).values_list(field_name, *field_names, flat=flat)

    def __iter__(self):
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)

    def __contains__(self, item: Any) -> bool:
        return item in self._names

    def __repr__(self) -> str:
        return f"<InMemFieldCollection {self._names!r}>"


class StaticDataset:
    """
    In-memory Reusable Dataset conforming to DatasetProtocol.
    Wraps arbitrary in-memory data (lists of dicts, Pandas DataFrames converted to dicts).
    """

    def __init__(
        self,
        data: Any = None,
        labels: Optional[Mapping[str, str]] = None,
        fields: Optional[Sequence[str]] = None,
    ):
        if data is None:
            data = []
        elif hasattr(data, "to_dict"):
            data = data.to_dict(orient="records")
        elif not isinstance(data, list):
            data = list(data)

        self._data: list[dict[str, Any]] = data
        self._labels: dict[str, str] = dict(labels or {})

        discovered_fields: list[str] = []
        if fields is not None:
            discovered_fields = list(fields)
        else:
            if self._data and isinstance(self._data[0], dict):
                discovered_fields = list(self._data[0].keys())
            for k in self._labels.keys():
                if k not in discovered_fields:
                    discovered_fields.append(k)

        self.fields = InMemFieldCollection(discovered_fields)

    def get_labels(self) -> dict[str, str]:
        labels = {f: f.replace("_", " ").title() for f in self.fields.all()}
        labels.update(self._labels)
        return labels

    def clean_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        if not filters or not isinstance(filters, dict):
            return {}
        valid_fields = set(self.fields.all())
        cleaned = {}
        for k, v in filters.items():
            if v is None or v == "":
                continue
            base_field = k.split("__")[0]
            if base_field in valid_fields or k in valid_fields:
                cleaned[k] = v
        return cleaned

    def get_data(self, *, select: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        data = list(self._data)
        if callable(select):
            data = [row for row in data if select(row)]

        runtime_filters = kwargs.get("filters")
        if runtime_filters and isinstance(runtime_filters, dict):
            cleaned = self.clean_filters(runtime_filters)
            for k, v in cleaned.items():
                field_name = k.split("__")[0]
                data = [
                    row for row in data
                    if field_name in row and str(row[field_name]) == str(v)
                ]
        return data


class QuerySetDataset:
    """
    Reusable Dataset conforming to DatasetProtocol wrapping a Django QuerySet.
    Automatically introspects model fields, maps verbose_name to human labels,
    detects QuerySet annotations, and applies entry filters (select) and runtime filters.
    """

    def __init__(
        self,
        queryset: Any,
        labels: Optional[Mapping[str, str]] = None,
        fields: Optional[Sequence[str]] = None,
    ):
        self.queryset = queryset
        self.model = getattr(queryset, "model", None)
        self._custom_labels = dict(labels or {})

        discovered_fields: list[str] = []
        if fields is not None:
            discovered_fields = list(fields)
        else:
            if self.model and hasattr(self.model, "_meta"):
                for f in self.model._meta.get_fields():
                    if hasattr(f, "name"):
                        if getattr(f, "is_relation", False) and not (
                            getattr(f, "many_to_one", False) or getattr(f, "one_to_one", False)
                        ):
                            continue
                        if f.name not in discovered_fields:
                            discovered_fields.append(f.name)

            if hasattr(queryset, "query") and hasattr(queryset.query, "annotations"):
                for ann_name in queryset.query.annotations.keys():
                    if ann_name not in discovered_fields:
                        discovered_fields.append(ann_name)

            for k in self._custom_labels.keys():
                if k not in discovered_fields:
                    discovered_fields.append(k)

        self._fields_list = discovered_fields
        self.fields = InMemFieldCollection(self._fields_list)

    def get_labels(self) -> dict[str, str]:
        labels: dict[str, str] = {}
        for name in self.fields.all():
            resolved = None
            if self.model and hasattr(self.model, "_meta"):
                try:
                    parts = name.split("__")
                    curr_model = self.model
                    f = None
                    for part in parts:
                        f = curr_model._meta.get_field(part)
                        if getattr(f, "is_relation", False) and getattr(f, "related_model", None):
                            curr_model = f.related_model
                    if f and hasattr(f, "verbose_name"):
                        resolved = str(f.verbose_name).title()
                except Exception:
                    pass
            if not resolved:
                resolved = name.replace("_", " ").title()
            labels[name] = resolved

        labels.update(self._custom_labels)
        return labels

    def clean_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        if not filters or not isinstance(filters, dict):
            return {}
        valid_fields = set(self.fields.all())
        cleaned = {}
        for k, v in filters.items():
            if v is None or v == "":
                continue
            base_field = k.split("__")[0]
            if (base_field in valid_fields or k in valid_fields) and k.count("__") <= 2:
                cleaned[k] = v
        return cleaned

    def get_data(self, *, select: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        qs = self.queryset.all()

        select_fields: list[str] = []
        if select:
            if isinstance(select, Q):
                qs = qs.filter(select)
            elif isinstance(select, dict):
                qs = qs.filter(**select)
            elif callable(select):
                qs = select(qs)
            elif isinstance(select, str):
                select_fields = [select]
            elif isinstance(select, (list, tuple, set)):
                for item in select:
                    if isinstance(item, Q):
                        qs = qs.filter(item)
                    elif isinstance(item, str):
                        select_fields.append(item)

        runtime_filters = kwargs.get("filters")
        if runtime_filters and isinstance(runtime_filters, dict):
            cleaned = self.clean_filters(runtime_filters)
            if cleaned:
                qs = qs.filter(**cleaned)

        if "order_by" in kwargs and kwargs["order_by"]:
            order = kwargs["order_by"]
            qs = qs.order_by(*order if isinstance(order, (list, tuple)) else [order])

        if "limit" in kwargs and kwargs["limit"]:
            qs = qs[:kwargs["limit"]]

        # Determine fields to select: requested via select or declared in self.fields
        fields_to_select: list[str] = []
        if select_fields:
            fields_to_select = list(select_fields)
        elif hasattr(self, "fields") and hasattr(self.fields, "all"):
            fields_to_select = list(self.fields.all())
        elif self._fields_list:
            fields_to_select = list(self._fields_list)

        if fields_to_select:
            try:
                qs = qs.values(*fields_to_select)
            except Exception:
                valid_fields = []
                for f in fields_to_select:
                    try:
                        self.queryset.values(f)
                        valid_fields.append(f)
                    except Exception:
                        pass
                if valid_fields:
                    qs = qs.values(*valid_fields)
                else:
                    qs = qs.values()
        elif getattr(qs, "_fields", None) is None:
            qs = qs.values()

        return list(qs)


__all__ = [
    "InMemFieldQuerySet",
    "InMemFieldCollection",
    "StaticDataset",
    "QuerySetDataset",
]
