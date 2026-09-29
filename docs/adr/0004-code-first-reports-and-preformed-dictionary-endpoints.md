# 4. Code-First Reports and Preformed Dictionary Endpoints

## Status
accepted

## Context & Problem
Integrators frequently need to serve reports from pre-aggregated external sources (e.g. data warehouses, microservices, pandas DataFrames) or specify reports purely in version-controlled Python code alongside their Django models without having to create database rows in `reportcraft_report`, `reportcraft_datasource`, and `reportcraft_entry`. Previously, all reports, datasets, and entries required persistence in Django ORM models and a two-tier request cycle (initial HTML fetch followed by a client-side AJAX call to `/reports/api/reports/<slug>/`).

## Decision
We chose to:
1. **Decouple Entry Generators via Python Protocols**: Define `@runtime_checkable` `EntryProtocol` and `DatasetProtocol` in `reportcraft.protocols`. Generator functions in `reportcraft/entries.py` operate on duck-typed objects rather than requiring `django.db.models.Model` instances.
2. **Single-Roundtrip Inline JSON Embedding**: Update `report.html` and `report-embed.html` to leverage Django's `json_script` template filter. When a `payload` is present in the view context, the browser client initializes `showReport()` synchronously on `DOMContentLoaded` without an extra HTTP round-trip, while gracefully falling back to AJAX `fetch()` for legacy database reports.
3. **Dual-Mode Preformed Dictionaries via `DictReportView`**: Provide a standalone `TemplateView` subclass capable of rendering preformed Visualization Payloads or callable report generators directly at any URL endpoint, with dual HTML/JSON content negotiation (`?format=json` or `Accept: application/json`).
4. **First-Class In-Memory Code Abstractions**:
   - `CodeReport`: Encapsulates title, slug, theme, and entries, with declarative constructor and procedural builder methods (`.add_entry()`, `.add_section()`).
   - `QuerySetDataset`: Wraps standard Django `QuerySet` instances, automatically introspecting model fields, extracting `verbose_name` as human labels, and supporting custom label overrides.
   - `StaticDataset`: Wraps arbitrary in-memory iterables of dictionaries.
   - **Typed Entry Classes**: Provide specialized subclasses (`TableEntry`, `BarChartEntry`, `ColumnChartEntry`, `PieChartEntry`, `PlotEntry`, `HistogramEntry`, `TimelineEntry`, `RichTextEntry`, `GeoChartEntry`, `LikertEntry`) that translate chart kwargs into `attrs` with IDE autocompletion and static type safety.
5. **Decoupled URL Routing & Opt-In Catalog**: Allow code reports to be mounted on custom application routes via `CodeReportView` or registered in the central ReportCraft catalog via an opt-in registry (`in_catalog=True`).

### Considered Options
- **Unsaved Model Instances (`pk=None`)**: Rejected because Django ORM foreign key traversals (`entry.source`, `source.fields.all()`) expect database backing and break when models are kept solely in memory.
- **Code-to-Database Sync / Migration Fixtures**: Rejected because it causes database write side-effects on startup, creates synchronization drift across deployment environments, and prevents dynamic, user- or tenant-specific report generation.
- **Mandatory AJAX Architecture**: Rejected because requiring two HTTP requests for static or code-defined reports introduces unnecessary network latency and requires registering two distinct URL patterns in the host application for every report.

### Consequences
- Existing database models (`Report`, `DataSource`, `Entry`) remain 100% backwards-compatible and continue to function without database schema migrations.
- `reportcraft/entries.py` generators can be reused without modification across both database reports and code reports.
- Host applications can version-control business intelligence reports in git as Python modules.
- Browser rendering performance is improved by eliminating client AJAX roundtrips when using inline payloads.
