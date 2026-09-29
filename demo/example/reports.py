"""
Code-first report definitions for demo application.
Showcases QuerySetDataset, TableEntry, ColumnChartEntry, RichTextEntry, and Width.
"""

from django.db.models import Count

from demo.example.models import Institution, Person, Subject
from reportcraft.code import (
    CodeReport,
    ColumnChartEntry,
    QuerySetDataset,
    RichTextEntry,
    TableEntry,
    Width,
)

# 1. Dataset for Personnel (Person model)
person_summary_dataset = QuerySetDataset(
    Person.objects.values("type", "gender").annotate(count=Count("id")),
    labels={
        "type": "Role",
        "gender": "Gender",
        "count": "Total",
    },
)

# 2. Dataset for Subject affiliations (Subject and Institution models)
subject_institutions_dataset = QuerySetDataset(
    Subject.objects.annotate(institution_count=Count("institutions")).values("name", "institution_count"),
    labels={
        "name": "Subject Area",
        "institution_count": "Affiliated Institutions",
    },
)

# 3. Dataset for Geographic Distribution (Institution model)
institution_city_dataset = QuerySetDataset(
    Institution.objects.values("city").annotate(count=Count("id")),
    labels={
        "city": "City",
        "count": "Institutions Count",
    },
)

# Academic & Personnel Analytics CodeReport
academic_analytics_report = CodeReport(
    title="Academic & Personnel Directory",
    slug="academic-directory",
    description="Comprehensive code-defined report analyzing institutions, academic subjects, and personnel.",
    theme="default",
    entries=[
        RichTextEntry(
            title="Executive Overview",
            text="### Academic & Personnel Intelligence\n\n"
                 "This report is defined purely in version-controlled Python code using **Django ReportCraft**'s "
                 "code-first API (`CodeReport`, `QuerySetDataset`, and typed entries). It synthesizes operational data "
                 "across **Institutions**, **Academic Subjects**, and **Personnel** without requiring "
                 "database report rows.",
            width=Width.FULL,
        ),
        TableEntry(
            title="Personnel by Role and Gender",
            dataset=person_summary_dataset,
            rows=["type"],
            columns="gender",
            values="count",
            total_row=True,
            total_column=True,
            width=Width.HALF,
        ),
        ColumnChartEntry(
            title="Institutions per Subject Area",
            dataset=subject_institutions_dataset,
            categories="name",
            values=["institution_count"],
            scheme="Live8",
            width=Width.HALF,
        ),
        ColumnChartEntry(
            title="Institutions by City",
            dataset=institution_city_dataset,
            categories="city",
            values=["count"],
            scheme="Tableau10",
            width=Width.FULL,
        ),
    ],
)
