# Research: Entry Generator Protocol Surface across `reportcraft/entries.py`

**Ticket**: [#4](https://github.com/michel4j/django-reportcraft/issues/4)  
**Parent Map**: [#3 - Map: Preformed Report Dictionaries and Code-First Reports](https://github.com/michel4j/django-reportcraft/issues/3)  
**Author**: Antigravity Agent  
**Date**: September 2026  
**Status**: Completed  

---

## Executive Summary

To enable code-first reports and in-memory datasets (`CodeDataset`, `CodeEntry`) that plug directly into existing entry generators without modifying `reportcraft/entries.py`, this research audits all 14 generator functions in `reportcraft/entries.py`.

### Key Findings

1. **Uniform Entry Protocol Surface**: Across all generators, `entry` is accessed as a structural duck-type expecting:
   - `title`: `str` (or string-like)
   - `description`: `str` (or string-like)
   - `notes`: `str` (or string-like)
   - `style`: `str | None` (Bootstrap width or layout classes, e.g. `"col-md-12"`)
   - `attrs`: `Mapping[str, Any]` (dictionary of visualization parameters, accessed exclusively via `.get(key, default)`)
   - `source`: `DatasetProtocol | None` (the backing dataset; optional only for `generate_text`)
   - `get_filters()`: `Callable[[], Any]` (returns the entry-level filter expression, passed directly into `source.get_data(select=...)`)

2. **Source Protocol Surface**:
   - `source.get_labels()`: Returns `Mapping[str, str]` mapping field identifiers to human-readable labels.
   - `source.get_data(select=..., **kwargs)`: Returns `list[dict[str, Any]]` representing records. The entry-level filter (`entry.get_filters()`) is passed into `select`. Any caller-supplied keyword arguments (such as `filters` representing runtime filters from `ReportView`) are forwarded transparently via `**kwargs`.

3. **Critical QuerySet Coupling in `table` and `list`**:
   - Two generators—`generate_table` ([entries.py:29](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L29)) and `generate_list` ([entries.py:217-219](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L217-L219))—do not treat `entry.source.fields` as a simple list. Instead, they invoke:
     ```python
     entry.source.fields.filter(name__in=entry.attrs.get('...')).values_list('name', flat=True)
     ```
   - Any in-memory `CodeDataset` implementation **must** provide a `fields` attribute whose object implements `.filter(name__in=...).values_list('name', flat=True)` to avoid `AttributeError` when generating tables or lists.

4. **Self-Contained Text Generator**:
   - `generate_text` ([entries.py:422-437](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L422-L437)) does not access `entry.source` or `entry.get_filters()`. It reads only `title`, `description`, `notes`, `style`, and `attrs['rich_text']`.

---

## Generator Audit Breakdown

This section details the attributes, dictionary keys, methods, and parameters accessed across each generator in `reportcraft/entries.py`.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       reportcraft/entries.py                                    │
├───────────────────────────────┬─────────────────────────────────┬───────────────────────────────┤
│ Generator Function            │ Entry Attributes Accessed       │ Dataset Methods & Attributes  │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_table                │ title, description, notes,      │ fields.filter().values_list() │
│                               │ style, attrs, source,           │ get_labels()                  │
│                               │ get_filters()                   │ get_data(select=..., **kwargs)│
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_bars                 │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_columns              │ (Delegates to generate_bars)    │ (Delegates to generate_bars)  │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_area                 │ (Delegates to generate_plot)    │ (Delegates to generate_plot)  │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_line                 │ (Delegates to generate_plot)    │ (Delegates to generate_plot)  │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_list                 │ title, description, notes,      │ fields.filter().values_list() │
│                               │ style, attrs, source,           │ get_labels()                  │
│                               │ get_filters()                   │ get_data(select=..., **kwargs)│
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_plot                 │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_pie                  │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_donut                │ (Delegates to generate_pie)     │ (Delegates to generate_pie)   │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_histogram            │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_timeline             │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_text                 │ title, description, notes,      │ None (source not accessed)    │
│                               │ style, attrs                    │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_geochart             │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
├───────────────────────────────┼─────────────────────────────────┼───────────────────────────────┤
│ generate_likert               │ title, description, notes,      │ get_labels()                  │
│                               │ style, attrs, source,           │ get_data(select=..., **kwargs)│
│                               │ get_filters()                   │                               │
└───────────────────────────────┴─────────────────────────────────┴───────────────────────────────┘
```

---

### 1. `generate_table(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:22-103](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L22-L103)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `fields`, `get_labels()`, and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked to produce `select` argument for `get_data`.
  - `entry.style`: read as string (`entry.style or ""`) and augmented with CSS classes (`" table-flip-headers"`, `" table-nowrap-headers"`).
  - `entry.title`: read as string for output payload.
  - `entry.description`: read as string for output payload.
  - `entry.notes`: read as string for output payload.
- **Keys inspected in `entry.attrs`**:
  - `'rows'`: `list[str]` (default `[]`)
  - `'columns'`: `list[str] | str` (default `[]`)
  - `'values'`: `str` (default `''`)
  - `'total_column'`: `bool` (default `False`)
  - `'total_row'`: `bool` (default `False`)
  - `'force_strings'`: `bool` (default `False`)
  - `'flip_headers'`: `bool` (default `False`)
  - `'wrap_headers'`: `bool` (default `False`)
  - `'transpose'`: `bool` (default `False`)
  - `'max_cols'`: `int | None` (default `None`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.fields.filter(name__in=entry.attrs.get('rows', [])).values_list('name', flat=True)`
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs` (transparently forwards runtime filters like `filters={...}`)
- **Early exit / preconditions**:
  - `if not columns or not rows: return {}`
- **Visualization Payload output**:
  - `'kind'`: `'table'`
  - `'data'`: `list[list[list[Any]]]` (array of tables, chunked by `max_cols` if set)
  - `'header'`: `"column row"`

---

### 2. `generate_bars(entry, kind='bars', **kwargs) -> dict`
*Location*: [reportcraft/entries.py:105-197](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L105-L197)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'categories'`: `str` (default `''`)
  - `'values'`: `list[str]` (default `[]`)
  - `'color_by'`: `str | None` (default `None`)
  - `'grouped'`: `bool` (default `False`)
  - `'sort_by'`: `str | None` (default `None`)
  - `'sort_desc'`: `bool` (default `False`)
  - `'ticks_every'`: `int` (default `1`)
  - `'limit'`: `int | None` (default `None`)
  - `'scheme'`: `str` (default `'Live8'`)
  - `'scale'`: `str` (default `'linear'`)
  - `'normalize'`: `bool` (default `False`)
  - `'facets'`: `str | None` (default `None`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Early exit / preconditions**:
  - `if not categories or not values: return {}`
- **Visualization Payload output**:
  - `'kind'`: `'bars'` (or `'columns'`)
  - Category axis (`'x'` if columns, `'y'` if bars) and Value axis (`'y'` if columns, `'x'` if bars)
  - `'data'`: `list[dict[str, Any]]` (reshaped with `'Variable'` and `'Value'` if multiple values plotted)

---

### 3. `generate_columns(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:199-201](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L199-L201)

- Direct delegate to `generate_bars(entry, kind='columns', **kwargs)`.
- Surfaces identical requirements to `generate_bars`.

---

### 4. `generate_area(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:203-205](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L203-L205)

- Direct delegate to `generate_plot(entry, **kwargs)`.
- Surfaces identical requirements to `generate_plot`.

---

### 5. `generate_line(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:207-209](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L207-L209)

- Direct delegate to `generate_plot(entry, **kwargs)`.
- Surfaces identical requirements to `generate_plot`.

---

### 6. `generate_list(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:211-253](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L211-L253)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `fields`, `get_labels()`, and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string, formatted as `f"{entry.style} first-col-left"`.
- **Keys inspected in `entry.attrs`**:
  - `'columns'`: `list[str]` (default `[]`)
  - `'order_by'`: `str | None` (default `None`)
  - `'order_desc'`: `bool` (default `False`)
  - `'limit'`: `int | None` (default `None`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.fields.filter(name__in=entry.attrs.get('columns', [])).values_list('name', flat=True)`
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Early exit / preconditions**:
  - `if not columns: return {}` (where columns is the result of filtering against `source.fields`)
- **Visualization Payload output**:
  - `'kind'`: `'table'`
  - `'data'`: `[table_data]` where row 0 is header labels, followed by data rows
  - `'header'`: `"row"`

---

### 7. `generate_plot(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:255-305](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L255-L305)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'groups'`: `list[dict[str, Any]]` (default `[]`, items contain keys `'type'`, `'y'`, optional `'z'`)
  - `'x_label'`: `str` (default `''`)
  - `'y_label'`: `str` (default `''`)
  - `'x_value'`: `str` (default `''`)
  - `'x_scale'`: `str` (default `'linear'`)
  - `'y_scale'`: `str` (default `'linear'`)
  - `'group_by'`: `str | None` (default `None`)
  - `'scheme'`: `str` (default `'Live8'`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Early exit / preconditions**:
  - `if not (x_value and groups): return {}`
- **Visualization Payload output**:
  - `'kind'`: `'xyplot'`
  - `'features'`: feature channel definitions for Observable Plot / D3 mark rendering
  - `'data'`: prepared data records sorted by `x_value`

---

### 8. `generate_pie(entry, kind: Literal['pie', 'donut'] = 'pie', **kwargs) -> dict`
*Location*: [reportcraft/entries.py:307-334](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L307-L334)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'colors'`: `str | None` (default `None`)
  - `'value'`: `str` (default `''`)
  - `'label'`: `str` (default `''`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Visualization Payload output**:
  - `'kind'`: `'pie'` (or `'donut'`)
  - `'scheme'`: palette configuration
  - `'data'`: list of `{'label': str, 'value': numeric}` aggregated via `defaultdict(int)`

---

### 9. `generate_donut(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:336-343](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L336-L343)

- Direct delegate to `generate_pie(entry, kind='donut', **kwargs)`.
- Surfaces identical requirements to `generate_pie`.

---

### 10. `generate_histogram(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:345-384](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L345-L384)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'bins'`: `int | str | None` (default `None`)
  - `'values'`: `str` (default `''`)
  - `'scheme'`: `str | None` (default `None`)
  - `'group_by'`: `str | None` (default `None`)
  - `'binning'`: `str` (default `'auto'`)
  - `'stack'`: `bool` (default `True`)
  - `'scale'`: `str` (default `'linear'`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Early exit / preconditions**:
  - `if not values: return {}`
- **Visualization Payload output**:
  - `'kind'`: `'histogram'`
  - `'bins'`: explicit bin count or binning strategy (`'auto'`)
  - `'data'`: records prepared with numeric values and optional dimension groupings

---

### 11. `generate_timeline(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:386-420](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L386-L420)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'start_value'`: `str | None` (default `None`)
  - `'end_value'`: `str | None` (default `None`)
  - `'labels'`: `str | None` (default `None`)
  - `'color_by'`: `str | None` (default `None`)
  - `'scheme'`: `str` (default `'Live8'`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Early exit / preconditions**:
  - `if not start_value or not end_value: return {}`
- **Visualization Payload output**:
  - `'kind'`: `'timeline'`
  - `'start'`, `'end'`, `'labels'`, `'colors'`: translated label keys
  - `'data'`: records prepared and sorted chronologically by `start_value`

---

### 12. `generate_text(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:422-437](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L422-L437)

- **Attributes accessed on `entry`**:
  - `entry.attrs`: accessed via `.get('rich_text', '')`.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'rich_text'`: `str` (default `''`)
- **Methods and attributes accessed on `entry.source`**:
  - **None**. `entry.source` is never touched.
- **Parameters passed to `entry.source.get_data(...)`**:
  - **None**.
- **Visualization Payload output**:
  - `'kind'`: `'richtext'`
  - `'text'`: HTML or markdown content string

---

### 13. `generate_geochart(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:439-485](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L439-L485)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'groups'`: `list[dict[str, Any]]` (default `[]`, items contain `'value'`, `'type'`)
  - `'map'`: `str` (default `'001'`)
  - `'mode'`: `str` (default `'area'`)
  - `'location'`: `str | None` (default `None`)
  - `'latitude'`: `str | None` (default `None`)
  - `'longitude'`: `str | None` (default `None`)
  - `'map_labels'`: `Any` (default `None`)
  - `'scheme'`: `str` (default `'Live8'`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Visualization Payload output**:
  - `'kind'`: `'geochart'`
  - `'map'`, `'mode'`, `'latitude'`, `'longitude'`, `'location'`, `'features'`: geo mapping configuration
  - `'data'`: geographic records prepared with labels

---

### 14. `generate_likert(entry, **kwargs) -> dict`
*Location*: [reportcraft/entries.py:487-518](file:///home/michel/Projects/django-reportcraft/reportcraft/entries.py#L487-L518)

- **Attributes accessed on `entry`**:
  - `entry.source`: accessed for `get_labels()` and `get_data(...)`.
  - `entry.attrs`: accessed via `.get(...)`.
  - `entry.get_filters()`: invoked for `select` parameter.
  - `entry.title`, `entry.description`, `entry.notes`: strings.
  - `entry.style`: string.
- **Keys inspected in `entry.attrs`**:
  - `'scheme'`: `str` (default `'Live8'`)
  - `'questions'`: `str` (default `''`)
  - `'answers'`: `str` (default `''`)
  - `'counts'`: `str` (default `''`)
  - `'scores'`: `str` (default `''`)
  - `'facets'`: `str` (default `''`)
- **Methods and attributes accessed on `entry.source`**:
  - `entry.source.get_labels()`: returns `dict[str, str]`
  - `entry.source.get_data(select=entry.get_filters(), **kwargs)`: returns `list[dict[str, Any]]`
- **Parameters passed to `entry.source.get_data(...)`**:
  - `select=entry.get_filters()`
  - `**kwargs`
- **Visualization Payload output**:
  - `'kind'`: `'likert'`
  - `'domain'`: sorted list of `(answer, score)` tuples derived from raw data
  - `'data'`: records prepared with labels for Likert diverging bar visualization

---

## Detailed Analysis of Parameters and Filters

### 1. `entry.get_filters()`
In database-backed reports (`reportcraft/models.py`), `Entry.get_filters()` parses the entry's filter expression text into a Django `models.Q` instance (or returns `Q()` if empty).

In generator functions:
```python
raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
```
Generators never inspect or mutate the value returned by `entry.get_filters()`. They pass it unconditionally as `select=...` to `entry.source.get_data(...)`.

Therefore:
- In `EntryProtocol`, `get_filters()` can return `Any` (`Q | dict | Callable | None`).
- In `DatasetProtocol`, `get_data(select=...)` receives this parameter as `select: Any = None`.

### 2. Runtime Filters via `**kwargs`
In `reportcraft/views.py:87`, `ReportView.get_report()` calls:
```python
filters = dict(self.request.GET.items())
content = [block.generate(filters=filters) for block in report.entries.all()]
```
`block.generate(**kwargs)` passes `filters=filters` to the generator, which in turn forwards `**kwargs` to:
```python
raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
```
Thus, `entry.source.get_data` receives runtime URL filters as the `filters` keyword argument (e.g. `filters={'year': '2024'}`).

---

## Formal Python Protocol Definitions

Below are the canonical `typing.Protocol` definitions that capture the complete interface required by `reportcraft/entries.py`.

```python
"""
Protocol definitions for Django ReportCraft entries and datasets.

Enables in-memory, code-first reports (CodeEntry, CodeDataset) to plug seamlessly
into existing entry generator functions without modifying reportcraft/entries.py.
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
```

---

## Reference Implementation: Minimal In-Memory Adaptors

To verify these protocols in practice, the following minimal in-memory classes plug into all 14 generators without requiring Django database models:

```python
from typing import Any, Collection, Mapping, Optional, Sequence


class InMemFieldQuerySet:
    """Implements FieldValuesListProtocol for in-memory collections."""
    def __init__(self, names: Sequence[str]):
        self._names = list(names)

    def values_list(self, field_name: str, *, flat: bool = False) -> Sequence[str]:
        if field_name == 'name' and flat:
            return self._names
        return self._names


class InMemFieldCollection:
    """Implements FieldCollectionProtocol for in-memory collections."""
    def __init__(self, names: Sequence[str]):
        self._names = list(names)

    def filter(self, *, name__in: Collection[str] = ()) -> InMemFieldQuerySet:
        # Preserve order of declared fields, or order of requested fields
        candidates = set(name__in)
        matched = [n for n in self._names if n in candidates]
        return InMemFieldQuerySet(matched)


class CodeDataset:
    """
    In-memory Reusable Dataset conforming to DatasetProtocol.
    """
    def __init__(
        self,
        data: list[dict[str, Any]],
        labels: Optional[Mapping[str, str]] = None,
        field_names: Optional[Sequence[str]] = None,
    ):
        self._data = data
        self._labels = dict(labels or {})
        fields = list(field_names) if field_names is not None else list(self._labels.keys())
        if not fields and data:
            fields = list(data[0].keys())
        self.fields = InMemFieldCollection(fields)

    def get_labels(self) -> Mapping[str, str]:
        return self._labels

    def get_data(self, *, select: Any = None, **kwargs: Any) -> list[dict[str, Any]]:
        # In a full implementation, apply select filters and runtime kwargs['filters']
        return self._data


class CodeEntry:
    """
    In-memory Entry conforming to EntryProtocol and ReportEntryProtocol.
    """
    def __init__(
        self,
        title: str,
        kind: str,
        attrs: Optional[Mapping[str, Any]] = None,
        source: Optional[DatasetProtocol] = None,
        style: Optional[str] = "col-md-12",
        description: str = "",
        notes: str = "",
        filters: Any = None,
    ):
        self.title = title
        self.kind = kind
        self.attrs = dict(attrs or {})
        self.source = source
        self.style = style
        self.description = description
        self.notes = notes
        self._filters = filters

    def get_filters(self) -> Any:
        return self._filters

    def generate(self, **kwargs: Any) -> dict[str, Any]:
        from reportcraft.models import Entry
        generator = Entry.GENERATORS.get(self.kind)
        if not generator:
            raise ValueError(f"Unsupported entry type: {self.kind}")
        return generator(self, **kwargs)
```

---

## Architectural Recommendations for Downstream Issues

### For Issue #5: Prototype Inline JSON Visualization Payload Rendering in ReportView
- When `ReportView` renders inline JSON payloads, it can bypass entry generators if the incoming payload is already pre-formed (`'sections': [...]`).
- When given declarative specifications (`CodeEntry`), `ReportView` can invoke `entry.generate(filters=filters)` uniformly, treating ORM `Entry` and in-memory `CodeEntry` interchangeably under `ReportEntryProtocol`.

### For Issue #6: Design `CodeDataset` and `CodeReport` Python API Ergonomics
- **Decouple QuerySet Mechanics**: `CodeDataset` should automatically construct `self.fields` from dictionaries or querysets, wrapping them in an adaptor like `InMemFieldCollection` so Integrators never have to manually mock Django QuerySets.
- **Support Multiple Dataset Backends**:
  - `StaticDataset`: Backed by in-memory `list[dict]` or Pandas/Polars DataFrames.
  - `QuerySetDataset`: Backed by a Django `models.QuerySet`, translating `select` and runtime filters into ORM queries while reusing ORM model field metadata for `fields` and `labels`.
  - `ExpressionDataset`: Supporting Python expressions or calculation expressions.

### For Issue #7: Synthesize Feasibility Specification and ADR Proposal
- Formalize `DatasetProtocol` and `EntryProtocol` into an ADR proposing `reportcraft.protocols` or `reportcraft.types`.
- Propose an internal refactor for future major versions: update `entries.py:29` and `entries.py:218` to check if `entry.source.fields` is a `Sequence[str]` or mapping before falling back to `.filter().values_list()`, simplifying dataset implementations.
