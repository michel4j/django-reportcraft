"""
Typed entry classes for code-first reports in Django ReportCraft.

Provides Width, CodeEntry, and specialized subclasses conforming to ReportEntryProtocol
and EntryProtocol.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Union

from reportcraft.protocols import DatasetProtocol


class Width(str, Enum):
    """
    Width choices matching Entry.Widths (Bootstrap 12-column grid classes).
    Accepts integers 1..12, enum members, or raw CSS class strings.
    """

    QUARTER = "col-md-3"
    THIRD = "col-md-4"
    HALF = "col-md-6"
    TWO_THIRDS = "col-md-8"
    THREE_QUARTERS = "col-md-9"
    FULL = "col-md-12"

    @classmethod
    def _missing_(cls, value: Any) -> Optional["Width"]:
        if isinstance(value, int) and 1 <= value <= 12:
            target = f"col-md-{value}"
            for member in cls:
                if member.value == target:
                    return member
        elif isinstance(value, str):
            upper = value.upper()
            if upper in cls.__members__:
                return cls[upper]
            for member in cls:
                if member.value == value:
                    return member
        return None

    @classmethod
    def resolve(cls, value: Union[int, "Width", str, None]) -> str:
        """
        Resolve a width specification into a CSS class string.
        Supports integers 1..12, Width enum members, and arbitrary CSS class strings.
        """
        if value is None:
            return cls.FULL.value
        if isinstance(value, Width):
            return value.value
        if isinstance(value, int):
            if 1 <= value <= 12:
                return f"col-md-{value}"
            raise ValueError(f"Width integer must be between 1 and 12, got {value}")
        if isinstance(value, str):
            if value.isdigit():
                val_int = int(value)
                if 1 <= val_int <= 12:
                    return f"col-md-{val_int}"
                raise ValueError(f"Width integer must be between 1 and 12, got {value}")
            upper = value.upper()
            if upper in cls.__members__:
                return cls[upper].value
            return value
        return str(value)


class CodeEntry:
    """
    Base class for code-first entries, conforming to ReportEntryProtocol and EntryProtocol.
    Dispatches .generate(**kwargs) via Entry.GENERATORS[self.kind](self, **kwargs).
    """

    def __init__(
        self,
        title: str = "",
        kind: str = "table",
        attrs: Optional[Mapping[str, Any]] = None,
        dataset: Optional[DatasetProtocol] = None,
        source: Optional[DatasetProtocol] = None,
        width: Union[int, Width, str] = Width.FULL,
        style: Optional[str] = None,
        description: str = "",
        notes: str = "",
        filters: Any = None,
    ):
        self.title: str = title
        self.kind: str = kind
        self.attrs: dict[str, Any] = dict(attrs or {})
        self.source: Optional[DatasetProtocol] = dataset if dataset is not None else source
        self.style: str = style if style is not None else Width.resolve(width)
        self.description: str = description
        self.notes: str = notes
        self._filters: Any = filters

    def get_filters(self) -> Any:
        """
        Return the entry-level filter constraint passed directly to source.get_data(select=...).
        """
        if self._filters is None:
            from django.db.models import Q
            return Q()
        if isinstance(self._filters, str):
            from reportcraft import utils

            parser = utils.FilterParser()
            return parser.parse(self._filters, silent=True)
        return self._filters

    def generate(self, **kwargs: Any) -> dict[str, Any]:
        """
        Generate and return the Visualization Payload for this entry.
        """
        try:
            from reportcraft.models import Entry
            generator = Entry.GENERATORS.get(self.kind)
        except Exception:
            from reportcraft import entries
            kind_generators = {
                "bars": entries.generate_bars,
                "columns": entries.generate_columns,
                "donut": entries.generate_donut,
                "histogram": entries.generate_histogram,
                "list": entries.generate_list,
                "map": entries.generate_geochart,
                "pie": entries.generate_pie,
                "text": entries.generate_text,
                "table": entries.generate_table,
                "timeline": entries.generate_timeline,
                "plot": entries.generate_plot,
                "likert": entries.generate_likert,
            }
            generator = kind_generators.get(self.kind)

        if not generator:
            from reportcraft import entries
            aliases = {
                "richtext": entries.generate_text,
                "rich_text": entries.generate_text,
                "geochart": entries.generate_geochart,
                "geo": entries.generate_geochart,
                "bar": entries.generate_bars,
                "column": entries.generate_columns,
            }
            generator = aliases.get(self.kind)

        if not generator:
            raise ValueError(f"Unsupported entry type: {self.kind}")
        return generator(self, **kwargs)


class TableEntry(CodeEntry):
    """
    Specialized CodeEntry for rendering tabular data or crosstabs.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        rows: Any = None,
        columns: Any = None,
        values: str = "",
        total_row: bool = False,
        total_column: bool = False,
        transpose: bool = False,
        max_cols: Optional[int] = None,
        force_strings: bool = False,
        flip_headers: bool = False,
        wrap_headers: bool = False,
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        table_attrs = dict(attrs or {})
        table_attrs.update(extra_attrs)

        if rows is not None:
            table_attrs["rows"] = [rows] if isinstance(rows, str) else list(rows)
        elif "rows" not in table_attrs:
            table_attrs["rows"] = []

        if columns is not None:
            table_attrs["columns"] = columns
        elif "columns" not in table_attrs:
            table_attrs["columns"] = []

        if values is not None:
            table_attrs["values"] = values
        if total_row:
            table_attrs["total_row"] = total_row
        if total_column:
            table_attrs["total_column"] = total_column
        if transpose:
            table_attrs["transpose"] = transpose
        if max_cols is not None:
            table_attrs["max_cols"] = max_cols
        if force_strings:
            table_attrs["force_strings"] = force_strings
        if flip_headers:
            table_attrs["flip_headers"] = flip_headers
        if wrap_headers:
            table_attrs["wrap_headers"] = wrap_headers

        super().__init__(
            title=title,
            kind="table",
            attrs=table_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class BarChartEntry(CodeEntry):
    """
    Specialized CodeEntry for horizontal bar charts.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        categories: str = "",
        values: Any = None,
        scheme: str = "Live8",
        color_by: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        grouped: bool = False,
        limit: Optional[int] = None,
        scale: str = "linear",
        normalize: bool = False,
        facets: Optional[str] = None,
        ticks_every: int = 1,
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        chart_attrs = dict(attrs or {})
        chart_attrs.update(extra_attrs)

        chart_attrs["categories"] = categories
        if values is not None:
            chart_attrs["values"] = [values] if isinstance(values, str) else list(values)
        elif "values" not in chart_attrs:
            chart_attrs["values"] = []

        chart_attrs["scheme"] = scheme
        if color_by is not None:
            chart_attrs["color_by"] = color_by
        if sort_by is not None:
            chart_attrs["sort_by"] = sort_by
        if sort_desc:
            chart_attrs["sort_desc"] = sort_desc
        if grouped:
            chart_attrs["grouped"] = grouped
        if limit is not None:
            chart_attrs["limit"] = limit
        if scale:
            chart_attrs["scale"] = scale
        if normalize:
            chart_attrs["normalize"] = normalize
        if facets is not None:
            chart_attrs["facets"] = facets
        if ticks_every != 1:
            chart_attrs["ticks_every"] = ticks_every

        super().__init__(
            title=title,
            kind="bars",
            attrs=chart_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class ColumnChartEntry(CodeEntry):
    """
    Specialized CodeEntry for vertical column charts.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        categories: str = "",
        values: Any = None,
        scheme: str = "Live8",
        color_by: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        grouped: bool = False,
        limit: Optional[int] = None,
        scale: str = "linear",
        normalize: bool = False,
        facets: Optional[str] = None,
        ticks_every: int = 1,
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        chart_attrs = dict(attrs or {})
        chart_attrs.update(extra_attrs)

        chart_attrs["categories"] = categories
        if values is not None:
            chart_attrs["values"] = [values] if isinstance(values, str) else list(values)
        elif "values" not in chart_attrs:
            chart_attrs["values"] = []

        chart_attrs["scheme"] = scheme
        if color_by is not None:
            chart_attrs["color_by"] = color_by
        if sort_by is not None:
            chart_attrs["sort_by"] = sort_by
        if sort_desc:
            chart_attrs["sort_desc"] = sort_desc
        if grouped:
            chart_attrs["grouped"] = grouped
        if limit is not None:
            chart_attrs["limit"] = limit
        if scale:
            chart_attrs["scale"] = scale
        if normalize:
            chart_attrs["normalize"] = normalize
        if facets is not None:
            chart_attrs["facets"] = facets
        if ticks_every != 1:
            chart_attrs["ticks_every"] = ticks_every

        super().__init__(
            title=title,
            kind="columns",
            attrs=chart_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class PieChartEntry(CodeEntry):
    """
    Specialized CodeEntry for pie charts (and donut charts when donut=True).
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        categories: str = "",
        values: Any = "",
        donut: bool = False,
        colors: Optional[str] = None,
        scheme: str = "Live8",
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        pie_attrs = dict(attrs or {})
        pie_attrs.update(extra_attrs)

        label_field = categories or pie_attrs.get("label", "")
        value_field = values if isinstance(values, str) else (values[0] if values else "")
        if not value_field and "value" in pie_attrs:
            value_field = pie_attrs["value"]

        pie_attrs["label"] = label_field
        pie_attrs["value"] = value_field
        pie_attrs["colors"] = colors or scheme or pie_attrs.get("colors")

        super().__init__(
            title=title,
            kind="donut" if donut else "pie",
            attrs=pie_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class DonutChartEntry(PieChartEntry):
    """
    Specialized CodeEntry for donut charts.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        categories: str = "",
        values: Any = "",
        colors: Optional[str] = None,
        scheme: str = "Live8",
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        super().__init__(
            title=title,
            dataset=dataset,
            categories=categories,
            values=values,
            donut=True,
            colors=colors,
            scheme=scheme,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
            attrs=attrs,
            **extra_attrs,
        )


class PlotEntry(CodeEntry):
    """
    Specialized CodeEntry for XY scatter, line, or area plots.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        x: str = "",
        y: Any = None,
        color_by: Optional[str] = None,
        shape_by: Optional[str] = None,
        scheme: str = "Live8",
        x_label: str = "",
        y_label: str = "",
        x_scale: str = "linear",
        y_scale: str = "linear",
        plot_type: str = "points",
        groups: Optional[Sequence[dict[str, Any]]] = None,
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        plot_attrs = dict(attrs or {})
        plot_attrs.update(extra_attrs)

        plot_attrs["x_value"] = x or plot_attrs.get("x_value", "")
        if color_by is not None:
            plot_attrs["group_by"] = color_by
        plot_attrs["scheme"] = scheme
        plot_attrs["x_label"] = x_label
        plot_attrs["y_label"] = y_label
        plot_attrs["x_scale"] = x_scale
        plot_attrs["y_scale"] = y_scale

        if groups is not None:
            plot_attrs["groups"] = [dict(g) for g in groups]
        elif "groups" not in plot_attrs:
            if y is not None:
                if isinstance(y, str):
                    group_entry = {"type": plot_type, "y": y}
                    if shape_by:
                        group_entry["shape"] = shape_by
                    plot_attrs["groups"] = [group_entry]
                elif isinstance(y, (list, tuple)):
                    group_list = []
                    for item in y:
                        g = {"type": plot_type, "y": item}
                        if shape_by:
                            g["shape"] = shape_by
                        group_list.append(g)
                    plot_attrs["groups"] = group_list
                else:
                    plot_attrs["groups"] = []
            else:
                plot_attrs["groups"] = []

        super().__init__(
            title=title,
            kind="plot",
            attrs=plot_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class HistogramEntry(CodeEntry):
    """
    Specialized CodeEntry for frequency distribution histograms.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        values: str = "",
        bins: Any = None,
        scheme: Optional[str] = None,
        group_by: Optional[str] = None,
        binning: Optional[str] = None,
        stack: bool = True,
        scale: str = "linear",
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        hist_attrs = dict(attrs or {})
        hist_attrs.update(extra_attrs)

        hist_attrs["values"] = values or hist_attrs.get("values", "")
        if bins is not None:
            hist_attrs["bins"] = bins
        if binning is not None:
            hist_attrs["binning"] = binning
        elif bins is not None:
            hist_attrs["binning"] = "manual"
        elif "binning" not in hist_attrs:
            hist_attrs["binning"] = "auto"

        if scheme is not None:
            hist_attrs["scheme"] = scheme
        if group_by is not None:
            hist_attrs["group_by"] = group_by
        hist_attrs["stack"] = stack
        hist_attrs["scale"] = scale

        super().__init__(
            title=title,
            kind="histogram",
            attrs=hist_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class TimelineEntry(CodeEntry):
    """
    Specialized CodeEntry for chronological event timelines.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        label: Optional[str] = None,
        color_by: Optional[str] = None,
        scheme: str = "Live8",
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        tl_attrs = dict(attrs or {})
        tl_attrs.update(extra_attrs)

        if start is not None:
            tl_attrs["start_value"] = start
        if end is not None:
            tl_attrs["end_value"] = end
        if label is not None:
            tl_attrs["labels"] = label
        if color_by is not None:
            tl_attrs["color_by"] = color_by
        tl_attrs["scheme"] = scheme

        super().__init__(
            title=title,
            kind="timeline",
            attrs=tl_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class RichTextEntry(CodeEntry):
    """
    Specialized CodeEntry for HTML or Markdown explanatory text blocks.
    Does not require a dataset.
    """

    def __init__(
        self,
        title: str = "",
        text: str = "",
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        txt_attrs = dict(attrs or {})
        txt_attrs.update(extra_attrs)
        txt_attrs["rich_text"] = text or txt_attrs.get("rich_text", "")

        super().__init__(
            title=title,
            kind="text",
            attrs=txt_attrs,
            dataset=None,
            width=width,
            description=description,
            notes=notes,
        )


class GeoChartEntry(CodeEntry):
    """
    Specialized CodeEntry for geographic map charts.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        locations: Optional[str] = None,
        values: Any = None,
        map_id: str = "001",
        mode: str = "area",
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        map_labels: Any = None,
        scheme: str = "Live8",
        groups: Optional[Sequence[dict[str, Any]]] = None,
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        geo_attrs = dict(attrs or {})
        geo_attrs.update(extra_attrs)

        if locations is not None:
            geo_attrs["location"] = locations
        geo_attrs["map"] = map_id
        geo_attrs["mode"] = mode
        if latitude is not None:
            geo_attrs["latitude"] = latitude
        if longitude is not None:
            geo_attrs["longitude"] = longitude
        if map_labels is not None:
            geo_attrs["map_labels"] = map_labels
        geo_attrs["scheme"] = scheme

        if groups is not None:
            geo_attrs["groups"] = [dict(g) for g in groups]
        elif "groups" not in geo_attrs:
            if values is not None:
                if isinstance(values, str):
                    geo_attrs["groups"] = [{"value": values, "type": mode}]
                elif isinstance(values, (list, tuple)):
                    geo_attrs["groups"] = [{"value": v, "type": mode} for v in values]
                else:
                    geo_attrs["groups"] = []
            else:
                geo_attrs["groups"] = []

        super().__init__(
            title=title,
            kind="map",
            attrs=geo_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


class LikertEntry(CodeEntry):
    """
    Specialized CodeEntry for Likert scale survey responses.
    """

    def __init__(
        self,
        title: str = "",
        dataset: Optional[DatasetProtocol] = None,
        questions: str = "",
        scale: Any = None,
        answers: Any = None,
        counts: str = "",
        scores: str = "",
        facets: str = "",
        scheme: str = "Live8",
        width: Union[int, Width, str] = Width.FULL,
        description: str = "",
        notes: str = "",
        filters: Any = None,
        attrs: Optional[Mapping[str, Any]] = None,
        **extra_attrs: Any,
    ):
        likert_attrs = dict(attrs or {})
        likert_attrs.update(extra_attrs)

        likert_attrs["questions"] = questions or likert_attrs.get("questions", "")
        likert_attrs["answers"] = answers or scale or likert_attrs.get("answers", "")
        likert_attrs["counts"] = counts or likert_attrs.get("counts", "")
        likert_attrs["scores"] = scores or likert_attrs.get("scores", "")
        likert_attrs["facets"] = facets or likert_attrs.get("facets", "")
        likert_attrs["scheme"] = scheme

        super().__init__(
            title=title,
            kind="likert",
            attrs=likert_attrs,
            dataset=dataset,
            width=width,
            description=description,
            notes=notes,
            filters=filters,
        )


__all__ = [
    "Width",
    "CodeEntry",
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
]
