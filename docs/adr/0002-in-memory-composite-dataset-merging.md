# 2. In-Memory Merging for Composite Datasets

## Status
accepted

To support reporting across multiple unrelated or loosely-related Django models, datasets can define multiple models. We chose to execute independent database queries per model and merge their aggregated result dictionaries in Python memory along shared dimensional grouping keys (`group_by`). This enables cross-model reporting without requiring foreign key relationships, complex database-level full outer joins, or schema-aligned SQL unions.

### Considered Options
- **Database-Level SQL Joins / Unions**: Rejected because models may belong to distinct applications without direct foreign key relationships or schema compatibility.
- **External OLAP / ETL pipelines**: Rejected to keep Django ReportCraft a lightweight, drop-in reusable Django application with zero external infrastructure dependencies.

### Consequences
- Composite datasets rely on grouping and aggregation at the database layer before in-memory merging to keep payload sizes small.
- Records without matching dimensional keys across models result in sparse merged entries populated with default values.
