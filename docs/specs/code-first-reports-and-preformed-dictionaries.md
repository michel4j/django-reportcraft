# Feasibility Specification & Architecture Design: Code-First Reports & Preformed Dictionary Endpoints

## 1. Executive Summary

This specification establishes the architectural design, contracts, and implementation plan for two related capabilities in **Django ReportCraft**:
1. **Preformed Report Dictionaries**: Enabling **Integrators** to render ready-to-display or declarative report dictionaries at custom URL endpoints with single-roundtrip performance and optional JSON API support.
2. **Code-First Reports**: Providing a pure Python API (`CodeReport`, `CodeEntry`, and `QuerySetDataset`) allowing reports to be declared and maintained in version-controlled application code without requiring database persistence or graphical web editor setup.

Both features preserve 100% backwards compatibility with existing database models (`Report`, `DataSource`, `Entry`), share the existing browser rendering engine (`reportcraft.js` + Observable Plot / D3), and require zero schema migrations.

---

## 2. Domain Model Alignment

All concepts in this specification adhere strictly to [`CONTEXT.md`](../../CONTEXT.md):

| Domain Term | Definition in this Specification |
| :--- | :--- |
| **Integrator** | The developer installing and configuring Django ReportCraft, wiring custom views or declaring code reports. |
| **Report** | A curated collection of visual entries arranged across layout rows (`Report` model or in-memory `CodeReport`). |
| **Entry** | A single visual component (`Entry` model or `CodeEntry`), backed by a dataset or static configuration. |
| **Reusable Dataset** | A named query specification (`DataSource` model, `QuerySetDataset`, or `StaticDataset`). |
| **Visualization Payload** | The normalized JSON contract consumed by client entry renderers (`reportcraft.js`). |
| **Entry Generator** | The server-side generator function in `reportcraft/entries.py` that compiles entry data into a Visualization Payload. |
| **Entry Renderer** | The client-side JavaScript module that receives a Visualization Payload and renders interactive SVG/DOM elements. |
| **Runtime Filter** | Query parameters supplied via URL (`?year=2026`) that dynamically constrain dataset queries. |

---

## 3. Architecture Blueprint

```
+-----------------------------------------------------------------------------------+
| Host Application Code                                                             |
|                                                                                   |
|  +--------------------+    +----------------------+    +-----------------------+  |
|  | Preformed Dict     |    | CodeReport           |    | CodeReportView        |  |
|  | (Visualization     |    | - QuerySetDataset    |    | / DictReportView      |  |
|  |  Payload / Spec)   |    | - Typed CodeEntries  |    | (urls.py route)       |  |
|  +---------+----------+    +----------+-----------+    +-----------+-----------+  |
+------------|--------------------------|----------------------------|--------------+
             |                          |                            |
             v                          v                            v
+-----------------------------------------------------------------------------------+
| ReportCraft Engine                                                                |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | reportcraft.protocols: EntryProtocol, DatasetProtocol                       |  |
|  +-----------------------------------------------------------------------------+  |
|                                       |                                           |
|                                       v                                           |
|  +-----------------------------------------------------------------------------+  |
|  | reportcraft/entries.py (Unmodified Generator Functions)                     |  |
|  | generate_table, generate_bars, generate_plot, generate_pie, ...             |  |
|  +-----------------------------------------------------------------------------+  |
|                                       |                                           |
|                                       v                                           |
|  +-----------------------------------------------------------------------------+  |
|  | Templates: reportcraft/report.html & report-embed.html                      |  |
|  | - If payload: {{ payload|json_script:"rc-report-data" }} (Zero AJAX)        |  |
|  | - Else: fetch("{{ data_url }}{{ query }}") (Legacy AJAX Fallback)           |  |
|  +-----------------------------------------------------------------------------+  |
+---------------------------------------|-------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Browser Client                                                                    |
|                                                                                   |
|  showReport("#report-entry", sections, staticRoot) -> Observable Plot / D3 SVG     |
+-----------------------------------------------------------------------------------+
```

---

## 4. Detailed Component Specifications

### 4.1 Protocols (`reportcraft.protocols`)

Entry generators in [`reportcraft/entries.py`](../../reportcraft/entries.py) are decoupled from Django ORM models using `@runtime_checkable` Python protocols:

```python
from typing import Any, Collection, Mapping, Optional, Protocol, Sequence, runtime_checkable

@runtime_checkable
class FieldValuesListProtocol(Protocol):
    def values_list(self, field_name: str, *, flat: bool = False) -> Sequence[str]: ...

@runtime_checkable
class FieldCollectionProtocol(Protocol):
    def filter(self, *, name__in: Collection[str] = ...) -> FieldValuesListProtocol: ...

@runtime_checkable
class DatasetProtocol(Protocol):
    fields: FieldCollectionProtocol
    def get_labels(self) -> Mapping[str, str]: ...
    def get_data(self, *, select: Any = None, **kwargs: Any) -> list[dict[str, Any]]: ...

@runtime_checkable
class EntryProtocol(Protocol):
    title: str
    description: str
    notes: str
    style: Optional[str]
    attrs: Mapping[str, Any]
    source: Optional[DatasetProtocol]
    def get_filters(self) -> Any: ...

@runtime_checkable
class ReportEntryProtocol(EntryProtocol, Protocol):
    kind: str
    def generate(self, **kwargs: Any) -> dict[str, Any]: ...
```

---

### 4.2 In-Memory Datasets (`reportcraft.code.datasets`)

#### `QuerySetDataset`
Wraps a standard Django ORM `QuerySet`, automatically inspecting the underlying model:
- **Field Discovery**: Introspects model field names via `_meta.get_fields()`.
- **Label Resolution**: Maps field names to human-readable titles using `field.verbose_name` by default, with optional `labels={...}` dictionary overrides.
- **Query Execution**: In `.get_data(select=..., **kwargs)`, applies `select` (entry `Q` filters) and dynamic runtime filters (`clean_filters(kwargs.get('filters', {}))`).

#### `StaticDataset`
Wraps arbitrary in-memory data (e.g. lists of dictionaries, Pandas DataFrames converted to dicts):
- Automatically derives `fields` from dict keys.
- Accepts static `labels={...}` mapping.

---

### 4.3 Typed Entry Hierarchy (`reportcraft.code.entries`)

All code entries inherit from `CodeEntry` (implementing `ReportEntryProtocol`):

```python
class CodeEntry:
    def __init__(
        self,
        title: str,
        kind: str,
        attrs: Optional[Mapping[str, Any]] = None,
        dataset: Optional[DatasetProtocol] = None,
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
    ): ...
```

#### Specialized Subclasses:
- `TableEntry(dataset=..., rows=[...], columns=..., values=..., total_row=..., total_column=..., transpose=...)`
- `BarChartEntry(dataset=..., categories=..., values=[...], scheme="Live8", color_by=..., sort_by=...)`
- `ColumnChartEntry(dataset=..., categories=..., values=[...], scheme="Live8", grouped=..., normalize=...)`
- `PieChartEntry(dataset=..., categories=..., values=..., donut=False)`
- `DonutChartEntry(dataset=..., categories=..., values=...)`
- `PlotEntry(dataset=..., x=..., y=..., color_by=..., shape_by=...)`
- `HistogramEntry(dataset=..., values=..., bins=...)`
- `TimelineEntry(dataset=..., start=..., end=..., label=...)`
- `RichTextEntry(title=..., text=...)`
- `GeoChartEntry(dataset=..., locations=..., values=...)`
- `LikertEntry(dataset=..., questions=[...], scale=[...])`

---

### 4.4 Report Composition (`reportcraft.code.report`)

`CodeReport` represents the report container:
- **Declarative initialization**: `CodeReport(title="...", slug="...", theme="default", entries=[...])`
- **Builder methods**: `.add_entry(entry)` and `.add_section(title="...", entries=[...])`
- **Generation**: `.generate(filters=...)` iterates over entries, producing the full Visualization Payload dictionary:
  ```python
  {
      'title': self.title,
      'description': self.description,
      'theme': self.theme,
      'sections': [
          {
              'style': 'row',
              'theme': self.theme,
              'content': [entry.generate(filters=filters) for entry in self.entries],
              'notes': self.notes
          }
      ]
  }
  ```

---

### 4.5 Views & Endpoints (`reportcraft.views`)

#### `DictReportView`
A standalone `TemplateView` for rendering preformed report dictionaries:
```python
class DictReportView(TemplateView):
    template_name = 'reportcraft/report.html'
    report_dict: dict | Callable[..., dict] | None = None

    def get_report_dict(self, request=None) -> dict: ...
    def get_context_data(self, **kwargs): ...
    def get(self, request, *args, **kwargs):
        # Returns JsonResponse on ?format=json or Accept: application/json
        # Otherwise renders template with inline payload
```

#### `CodeReportView`
Subclasses `DictReportView` to accept a `CodeReport` instance:
```python
class CodeReportView(DictReportView):
    report: CodeReport | None = None

    def get_report_dict(self, request=None) -> dict:
        filters = dict(request.GET.items()) if request else {}
        return self.report.generate(filters=filters)
```

---

### 4.6 Template Integration (`reportcraft/report.html`)

```html
{% block page-scripts %}
    {% if payload %}
        {{ payload|json_script:"rc-report-data" }}
    {% endif %}
    <script type="module">
        import { showReport } from '{% static "reportcraft/reportcraft.min.js" %}';
        document.addEventListener('DOMContentLoaded', function() {
            const inlineDataEl = document.getElementById("rc-report-data");
            if (inlineDataEl) {
                try {
                    const data = JSON.parse(inlineDataEl.textContent);
                    const sections = data["sections"] || [];
                    const reportTitle = data["title"] || "{{ report.title|escapejs }}";
                    const reportDescription = data["description"] || "{{ report.description|escapejs }}";
                    const titleEl = document.getElementById("report-title");
                    const subtitleEl = document.getElementById("report-subtitle");
                    if (titleEl) titleEl.innerText = reportTitle;
                    if (subtitleEl) subtitleEl.innerText = reportDescription;
                    showReport("#report-entry", sections, "{% static 'reportcraft' %}");
                } catch (error) {
                    console.error('Error rendering inline report data:', error);
                }
            } else {
                fetch("{{ data_url }}{{ query }}")
                    .then(response => response.json())
                    .then(data => {
                        const sections = data["sections"] || [];
                        const reportTitle = data["title"] || "A Report";
                        const reportDescription = data["description"] || "";
                        const titleEl = document.getElementById("report-title");
                        const subtitleEl = document.getElementById("report-subtitle");
                        if (titleEl) titleEl.innerText = reportTitle;
                        if (subtitleEl) subtitleEl.innerText = reportDescription;
                        showReport("#report-entry", sections, "{% static 'reportcraft' %}");
                    })
                    .catch(error => console.error('Error fetching report data:', error));
            }
        });
    </script>
{% endblock %}
```

---

## 5. Usage Examples for Integrators

### 5.1 Preformed Dictionary Endpoint

```python
# myapp/views.py
from reportcraft.views import DictReportView

MY_KPI_PAYLOAD = {
    'title': 'Warehouse Daily Snapshot',
    'theme': 'default',
    'sections': [
        {
            'style': 'row',
            'content': [
                {
                    'title': 'Shipped Today',
                    'kind': 'richtext',
                    'style': 'col-md-6',
                    'text': '# 4,120 packages\n*98.4% on-time dispatch*',
                },
                {
                    'title': 'Regional Volume',
                    'kind': 'bars',
                    'style': 'col-md-6',
                    'scheme': 'Live8',
                    'categories': 'region',
                    'values': ['packages'],
                    'data': [
                        {'region': 'West', 'packages': 1800},
                        {'region': 'East', 'packages': 1320},
                        {'region': 'Central', 'packages': 1000},
                    ],
                }
            ]
        }
    ]
}

class WarehouseKPIView(DictReportView):
    report_dict = MY_KPI_PAYLOAD

# myapp/urls.py
from django.urls import path
from .views import WarehouseKPIView

urlpatterns = [
    path('kpis/warehouse/', WarehouseKPIView.as_view(), name='warehouse-kpi'),
]
```

### 5.2 Code-First ORM Report

```python
# myapp/reports.py
from reportcraft.code import (
    CodeReport, QuerySetDataset, TableEntry, ColumnChartEntry, RichTextEntry, Width
)
from myapp.models import Enrollment

enrollment_ds = QuerySetDataset(
    Enrollment.objects.all(),
    labels={"program__title": "Program", "semester": "Term"}
)

academic_report = CodeReport(
    title="Annual Enrollment Report",
    slug="annual-enrollment",
    theme="default",
    entries=[
        RichTextEntry(title="Executive Summary", text="## 2026 Admissions Overview", width=Width.FULL),
        TableEntry(
            title="Enrollments by Program and Term",
            dataset=enrollment_ds,
            rows=["program__title"],
            columns="semester",
            total_row=True,
            width=Width.HALF,
        ),
        ColumnChartEntry(
            title="Program Distribution",
            dataset=enrollment_ds,
            categories="semester",
            values=["student_count"],
            scheme="Live8",
            width=Width.HALF,
        )
    ]
)

# myapp/views.py
from reportcraft.views import CodeReportView
from .reports import academic_report

class AcademicReportView(CodeReportView):
    report = academic_report
```

---

## 6. Verification and Validation Results

1. **Protocol Adherence**: Minimal in-memory adaptations verified against all 14 generator functions in [`reportcraft/entries.py`](../../reportcraft/entries.py) with 100% test pass rate.
2. **Template Single-Roundtrip Rendering**: Validated on branch `prototype/inline-dict-report` with automated test suite `demo/example/test_prototype.py`.
3. **Backwards Compatibility**: Existing database-backed reports continue to use the AJAX endpoint without regressions. All 8 tests in the test suite pass.

---

## 7. Delivery Plan & Implementation Tasks

When ready to implement in production:
1. **Core Package Modules**:
   - Create `reportcraft/protocols.py` with `DatasetProtocol` and `EntryProtocol`.
   - Create `reportcraft/code/` package containing `datasets.py`, `entries.py`, and `report.py`.
2. **View and Template Updates**:
   - Merge `json_script` inline payload handling into `reportcraft/report.html` and `reportcraft/report-embed.html`.
   - Implement `DictReportView` and `CodeReportView` in `reportcraft/views.py`.
3. **Optional Registry**:
   - Implement `reportcraft.site.register(report, in_catalog=True)` and update `ReportIndexView` to combine ORM reports and registered code reports.
