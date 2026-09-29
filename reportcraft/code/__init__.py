"""
Code-first report generation package for Django ReportCraft.
"""

from reportcraft.code.datasets import (
    InMemFieldCollection,
    InMemFieldQuerySet,
    QuerySetDataset,
    StaticDataset,
)
from reportcraft.code.entries import (
    BarChartEntry,
    CodeEntry,
    ColumnChartEntry,
    DonutChartEntry,
    GeoChartEntry,
    HistogramEntry,
    LikertEntry,
    PieChartEntry,
    PlotEntry,
    RichTextEntry,
    TableEntry,
    TimelineEntry,
    Width,
)
from reportcraft.code.report import CodeReport, LayoutRow
from reportcraft.registry import ReportRegistry, site
from reportcraft.views import CodeReportView

__all__ = [
    "CodeReport",
    "LayoutRow",
    "CodeReportView",
    "CodeEntry",
    "QuerySetDataset",
    "StaticDataset",
    "Width",
    "TableEntry",
    "BarChartEntry",
    "ColumnChartEntry",
    "PieChartEntry",
    "DonutChartEntry",
    "PlotEntry",
    "HistogramEntry",
    "TimelineEntry",
    "RichTextEntry",
    "GeoChartEntry",
    "LikertEntry",
    "InMemFieldCollection",
    "InMemFieldQuerySet",
    "ReportRegistry",
    "site",
]
