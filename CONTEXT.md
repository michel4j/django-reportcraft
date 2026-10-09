# Django ReportCraft

A reusable Django application for dynamically designing and generating business intelligence reports and data visualizations.

## Language

### Actors

**Integrator**:
A developer who installs and configures Django ReportCraft in a host Django application, setting allowed apps, view mixins, and custom functions.
_Avoid_: Developer, system admin, site manager

**Report Designer**:
A user who creates and configures reports, datasets, calculated fields, and visualization entries using the graphical web editor.
_Avoid_: Author, report builder, power user, admin

**Report Consumer**:
A user who views generated reports, interacts with visual entries, applies runtime URL filters, and exports data.
_Avoid_: Viewer, visitor, reader, client

### Core Concepts

**Report**:
A curated collection of visual entries arranged across layout rows to present business intelligence insights.
_Avoid_: Dashboard, page, sheet

**Section**:
A categorization slug used to group related reports for catalog indexing and access control.
_Avoid_: Category, folder, layout row

**Layout Row**:
A horizontal grid container in a report layout that holds one or more entries sized by responsive column widths.
_Avoid_: Section, row, band

**Reusable Dataset**:
A named, standalone query specification defining underlying models, fields, formulas, grouping, and baseline filters, capable of being reused across multiple entries and reports.
_Avoid_: Query, data source, table

**Composite Dataset**:
A reusable dataset composed of multiple underlying models whose aggregated query outputs are merged in memory along shared grouping keys.
_Avoid_: Federated query, joined query, multi-model source

**Entry**:
A single visual component (e.g. chart, table, list, map, or rich text block) placed within a report and optionally backed by a dataset.
_Avoid_: Widget, card, block, visual component

**Visualization Payload**:
The structured JSON data contract emitted by an entry generator that supplies data and configuration to the client renderer.
_Avoid_: Chart data, JSON response, view model

**Entry Generator**:
The server-side component responsible for querying dataset records, transforming aggregations, and constructing a visualization payload for an entry.
_Avoid_: Serializer, view handler, data fetcher

**Entry Renderer**:
The client-side JavaScript module that receives a visualization payload and constructs interactive DOM and SVG graphics.
_Avoid_: Chart runner, frontend widget, canvas

### Data and Query Model

**Dimension**:
A categorical attribute used for grouping, bucketing, or slicing dataset records.
_Avoid_: Group field, category, slice, bucket

**Metric**:
A quantitative numeric calculation produced by aggregating records across dimensions.
_Avoid_: Value, aggregation, measure, summary field

**Model Field**:
A direct attribute or relation mapped from an underlying Django model into a dataset.
_Avoid_: Raw field, database column, native field

**Calculated Field**:
A field whose value is derived through an expression rather than directly mapped from a model attribute.
_Avoid_: Computed field, virtual field, formula field

**Calculation Expression**:
A domain formula specifying arithmetic and database functions applied to model fields and metrics.
_Avoid_: Expression, formula, script, query

**Temporal Function**:
A calculation expression function that dynamically evaluates current date or time values (such as `ThisYear()`, `ThisMonth()`, `Today()`, or `Now()`) relative to the active session timezone at query generation time.
_Avoid_: Clock function, date macro, dynamic timestamp

**Period Bucketing Function**:
A database function that groups dates or integer years into standardized multi-year temporal intervals (such as `Decade()`, `Lustrum()`, `Triennial()`, `Biennial()`, `Quadrennial()`, or `Century()`) for dimension slicing.
_Avoid_: Date binner, year grouper, time slicer

**Filter Expression**:
A boolean predicate defining comparison conditions used to restrict dataset records.
_Avoid_: Filter, query clause, condition

**Dataset Filter**:
A baseline filter expression defined on a reusable dataset that applies to all queries executed against it.
_Avoid_: Source filter, base query, global filter

**Entry Filter**:
A filter expression configured on a specific entry to constrain data beyond the dataset baseline.
_Avoid_: Widget filter, local filter, card filter

**Runtime Filter**:
A dynamic query constraint supplied by a report consumer via URL query parameters when viewing a report.
_Avoid_: User filter, query parameter, interactive filter

### Aesthetics and Presentation

**Theme**:
The global artistic motif applied to a report that governs typography and chart mark styling.
_Avoid_: Skin, style, CSS template

**Palette**:
A curated sequence of categorical colors or continuous gradients assigned to data series within an entry.
_Avoid_: Color scheme, color map, swatch

**Width**:
The responsive grid span assigned to an entry to govern its horizontal proportion within a layout row.
_Avoid_: Column span, style, size
