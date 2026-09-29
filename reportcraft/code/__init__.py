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
from reportcraft.code.report import CodeReport

__all__ = [
    "CodeReport",
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
]
