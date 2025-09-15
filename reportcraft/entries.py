import math
from collections import defaultdict
from typing import Any, Literal

import numpy

from .utils import (
    regroup_data, MinMax, epoch, get_histogram_points, wrap_table,
    prepare_data, debug_value
)


def generate_table(entry, **kwargs) -> dict:
    """
    Generate a table from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """

    rows = list(entry.source.fields.filter(name__in=entry.attrs.get('rows', [])).values_list('name', flat=True))
    columns = entry.attrs.get('columns', [])
    values = entry.attrs.get('values', '')
    total_column = entry.attrs.get('total_column', False)
    total_row = entry.attrs.get('total_row', False)
    force_strings = entry.attrs.get('force_strings', False)
    flip_headers = entry.attrs.get('flip_headers', False)
    wrap_headers = entry.attrs.get('wrap_headers', False)
    transpose = entry.attrs.get('transpose', False)
    max_cols = entry.attrs.get('max_cols', None)
    labels = entry.source.get_labels()

    if not columns or not rows:
        return {}

    if isinstance(rows, str) and isinstance(columns, list):
        rows, columns = columns, rows
        transpose = True
    first_row_name = labels.get(columns, columns)

    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    num_columns = len(set(item[columns] for item in raw_data))
    if len(rows) == 1 and values:
        rows = rows[0]
        row_names = list(dict.fromkeys(item[rows] for item in raw_data))
    else:
        row_names = [labels.get(y, y.title()) for y in rows]
    data = regroup_data(
        raw_data, x_axis=columns, y_axis=rows, y_value=values, labels=labels, default=0, sort=columns
    )

    # Now build table based on the reorganized data
    table_data: list[list[Any]] = [
        [key] + [item.get(key, 0) for item in data]
        for key in [first_row_name] + row_names
    ]

    if total_row:
        table_data.append(
            ['Total'] + [sum([row[i] for row in table_data[1:]]) for i in range(1, num_columns + 1)]
        )

    if total_column:
        table_data[0].append('All')
        for row in table_data[1:]:
            row.append(sum(row[1:]))

    if force_strings:
        table_data = [
            [f'{item}' for item in row] for row in table_data
        ]

    if transpose:
        table_data = list(map(list, zip(*table_data)))

    if max_cols and len(table_data[0]) > max_cols:
        # Split the table into multiple parts if it exceeds max_cols
        data_parts = wrap_table(table_data, max_cols=max_cols)
    else:
        data_parts = [table_data]

    styles = entry.style or ""
    styles += " table-flip-headers" if flip_headers else ""
    styles += " table-nowrap-headers" if not wrap_headers else ""

    return {
        'title': entry.title,
        'kind': 'table',
        'data': data_parts,
        'style': styles,
        'header': "column row",
        'description': entry.description,
        'notes': entry.notes
    }


def generate_bars(entry, kind='bars', **kwargs):
    """
    Generate a bar or column chart from the data source
    :param entry: The report entry containing the configuration for the table
    :param kind: The type of chart to generate ('bars', 'columns', 'area', 'line')
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    labels = entry.source.get_labels()

    categories = entry.attrs.get('categories', '')
    values = entry.attrs.get('values', [])
    color_by = entry.attrs.get('color_by', None)
    grouped = entry.attrs.get('grouped', False)
    sort_by = entry.attrs.get('sort_by', None)
    sort_desc = entry.attrs.get('sort_desc', False)
    ticks_every = entry.attrs.get('ticks_every', 1)
    limit = entry.attrs.get('limit', None)
    scheme = entry.attrs.get('scheme', 'Live8')
    vertical = (kind == "columns")
    scale = entry.attrs.get('scale', 'linear')
    normalize = entry.attrs.get('normalize', False)
    facets = entry.attrs.get('facets', None)

    if not categories or not values:
        return {}

    category_name = labels.get(categories, categories)
    color_name = labels.get(color_by, color_by) if color_by else None
    sort_name = labels.get(sort_by, sort_by) if sort_by else None
    facet_name = labels.get(facets, facets) if facets else None

    category_axis = 'x' if vertical else 'y'
    value_axis = 'y' if vertical else 'x'
    data_fields = [categories] + values

    if color_name:
        data_fields.append(color_by)
    if sort_name:
        data_fields.append(sort_by)
    if facet_name:
        data_fields.append(facets)

    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    data = prepare_data(raw_data, select=data_fields, labels=labels, sort=sort_by, sort_desc=sort_desc)
    if limit:
        data = data[:limit]

    # If plotting multiple values, expand data to include all combinations of category and values
    if len(values) > 1:
        expanded_data = []
        value_keys = [labels.get(v, v) for v in values]
        for item in data:
            for key in value_keys:
                new_item = {k: v for k, v in item.items() if k not in value_keys}
                new_item['Value'] = item.get(key, 0)
                new_item['Variable'] = key
                expanded_data.append(new_item)
        data = expanded_data
        value_name = 'Value'
        color_axis = 'Variable'

    else:
        value_name = labels.get(values[0], values[0])
        color_axis = color_name

    features = {
        category_axis: category_name,
        value_axis: value_name,
        'grouped': grouped,
        **({'colors': color_axis} if color_axis else {}),
        **({'sort': f'-{sort_name}' if sort_desc else sort_name} if sort_by else {}),
        **({'facets': facet_name} if facets else {}),
    }

    info = {
        'title': entry.title,
        'description': entry.description,
        'kind': kind,
        **features,
        'normalize': normalize,
        'style': entry.style,
        'ticks-every': ticks_every,
        'scheme': scheme,
        'scale': scale,
        'notes': entry.notes,
        'data': data,
    }

    if data and isinstance(data[0].get(category_name), (int, float)):
        info["ticks-interval"] = 1

    return info


def generate_columns(entry, **kwargs):
    return generate_bars(entry, kind='columns', **kwargs)


def generate_area(entry, **kwargs):
    return generate_plot(entry, **kwargs)


def generate_line(entry, **kwargs):
    return generate_plot(entry, **kwargs)


def generate_list(entry, **kwargs):
    """
    Generate a list from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    columns = list(
        entry.source.fields.filter(name__in=entry.attrs.get('columns', [])).values_list('name', flat=True)
    )
    order_by = entry.attrs.get('order_by', None)
    order_desc = entry.attrs.get('order_desc', False)
    limit = entry.attrs.get('limit', None)

    if not columns:
        return {}

    data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    labels = entry.source.get_labels()

    if order_by:
        sort_key, reverse = (order_by[1:], True) if order_by.startswith('-') else (order_by, order_desc)
        data = list(sorted(data, key=lambda x: x.get(sort_key, 0), reverse=reverse))

    if limit:
        data = data[:limit]

    table_data = [
        [labels.get(field, field.title()) for field in columns]
    ] + [
        [item.get(field, '') for field in columns]
        for item in data
    ]

    return {
        'title': entry.title,
        'kind': 'table',
        'data': [table_data],
        'style': f"{entry.style} first-col-left",
        'header': "row",
        'description': entry.description,
        'notes': entry.notes
    }


def generate_plot(entry, **kwargs):
    """
    Generate an XY plot from the data source
    :param entry: The report entry containing the configuration for the table
    :param kind: The type of plot to generate ('scatter', 'area', 'line')
    returns: A dictionary containing the table data and metadata suitable for rendering
    """

    labels = entry.source.get_labels()
    groups = entry.attrs.get('groups', [])
    x_label = entry.attrs.get('x_label', '')
    y_label = entry.attrs.get('y_label', '')
    x_value = entry.attrs.get('x_value', '')
    x_scale = entry.attrs.get('x_scale', 'linear')
    y_scale = entry.attrs.get('y_scale', 'linear')
    group_by = entry.attrs.get('group_by', None)
    scheme = entry.attrs.get('scheme', 'Live8')

    if not (x_value and groups):
        return {}

    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    features = [
        {
            'type': group.pop('type', 'points'),
            'x': labels.get(x_value, x_value),                                      # All plots share the same x-value
            **{key: labels.get(field, field) for key, field in group.items()},      # Add y-values, z
            **{'colors': labels.get(group_by, group_by) for i in [1] if group_by},  # Add color channel
        }
        for group in groups if 'y' in group
    ]

    select_fields = {x_value} | ({group_by} if group_by else set())
    select_fields |= {group[k] for group in groups for k in ['y', 'z'] if k in group}
    data = prepare_data(raw_data, select=select_fields, labels=labels, sort=x_value, sort_desc=False)

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'xyplot',
        'style': entry.style,
        'scheme': scheme,
        'x-scale': x_scale,
        'y-scale': y_scale,
        'x-label': x_label,
        'y-label': y_label,
        'features': features,
        'data': data,
        'notes': entry.notes
    }


def generate_pie(entry, kind: Literal['pie', 'donut'] = 'pie', **kwargs):
    """
    Generate a pie or donut from the data source
    :param entry: The report entry containing the configuration for the table
    :param kind: The type of pie chart to generate ('pie' or 'donut')
    returns: A dictionary containing the table data and metadata suitable for rendering
    """

    colors = entry.attrs.get('colors', None)
    value_field = entry.attrs.get('value', '')
    label_field = entry.attrs.get('label', '')
    labels = entry.source.get_labels()

    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    data = defaultdict(int)
    for item in raw_data:
        data[item.get(label_field)] += item.get(value_field, 0)

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': kind,
        'style': entry.style,
        'scheme': colors,
        'data': [{'label': labels.get(label, label), 'value': value} for label, value in data.items()],
        'notes': entry.notes
    }


def generate_donut(entry, **kwargs):
    """
    Generate a donut chart from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    return generate_pie(entry, kind='donut', **kwargs)


def generate_histogram(entry, **kwargs):
    """
    Generate a histogram from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    labels = entry.source.get_labels()
    bins = entry.attrs.get('bins', None)
    values = entry.attrs.get('values', '')
    scheme = entry.attrs.get('scheme', None)
    group_by = entry.attrs.get('group_by', None)
    binning = entry.attrs.get('binning', 'auto')
    stack = entry.attrs.get('stack', True)
    scale = entry.attrs.get('scale', 'linear')

    if not values:
        return {}

    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    select_fields = [values, group_by]
    data = prepare_data(raw_data, select=select_fields, labels=labels)

    info = {
        'title': entry.title,
        'description': entry.description,
        'kind': 'histogram',
        'style': entry.style,
        'scheme': scheme,
        'scale': scale,
        'stack': stack,
        'values': labels.get(values, values),
        'data': data,
        'notes': entry.notes
    }
    if group_by:
        info['groups'] = labels.get(group_by, group_by)

    info['bins'] = bins if binning == 'manual' else binning
    return info


def generate_timeline(entry, **kwargs):
    """
    Generate a timeline from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """

    labels = entry.source.get_labels()
    start_value = entry.attrs.get('start_value', None)
    end_value = entry.attrs.get('end_value', None)
    label_value = entry.attrs.get('labels', None)
    color_by = entry.attrs.get('color_by', None)
    scheme = entry.attrs.get('scheme', 'Live8')

    if not start_value or not end_value:
        return {}

    select_fields = [field for field in [start_value, end_value, label_value, color_by] if field]
    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    data = prepare_data(raw_data, select=select_fields, labels=labels, sort=start_value, sort_desc=False)

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'timeline',
        'colors': labels.get(color_by, color_by),
        'labels': labels.get(label_value, label_value),
        'start': labels.get(start_value, start_value),
        'end': labels.get(end_value, end_value),
        'style': entry.style,
        'scheme': scheme,
        'notes': entry.notes,
        'data': data
    }


def generate_text(entry, **kwargs):
    """
    Generate a rich text entry from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    rich_text = entry.attrs.get('rich_text', '')
    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'richtext',
        'style': entry.style,
        'text': rich_text,
        'notes': entry.notes
    }


def generate_geochart(entry, **kwargs):
    """
    Generate a geo chart from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the data and metadata suitable for rendering
    """

    labels = entry.source.get_labels()
    groups = entry.attrs.get('groups', [])
    map_id = entry.attrs.get('map', '001')
    mode = entry.attrs.get('mode', 'area')
    location = entry.attrs.get('location', None)
    latitude = entry.attrs.get('latitude', None)
    longitude = entry.attrs.get('longitude', None)
    map_labels = entry.attrs.get('map_labels', None)
    scheme = entry.attrs.get('scheme', 'Live8')

    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    features = [
        {
            'type': group.get('type', 'area'),
            'value': labels.get(group['value'], group['value']),
        }
        for group in groups if 'value' in group
    ]

    select_fields = {field for field in [location, latitude, longitude] if field}
    select_fields |= {group['value'] for group in groups if 'value' in group}
    data = prepare_data(raw_data, select=select_fields, labels=labels)

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'geochart',
        'mode': mode,
        'map': map_id,
        'labels': map_labels,
        'latitude': labels.get(latitude, latitude),
        'longitude': labels.get(longitude, longitude),
        'location': labels.get(location, location),
        'scheme': scheme,
        'features': features,
        'style': entry.style,
        'notes': entry.notes,
        'data': data
    }


def generate_likert(entry, **kwargs):
    """
    Generate a liker scale Bar charts
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    labels = entry.source.get_labels()
    scheme = entry.attrs.get('scheme', 'Live8')

    settings = {
        key: entry.attrs.get(key, '')
        for key in ['questions', 'answers', 'counts', 'scores', 'facets']
    }
    raw_data = entry.source.get_data(select=entry.get_filters(), **kwargs)
    domain = sorted({
        (item.get(settings['answers']), item.get(settings['scores']))
        for item in raw_data}, key=lambda x: x[1]
    )
    data = prepare_data(raw_data, select=list(settings.values()), labels=labels)
    info = {
        'title': entry.title,
        'description': entry.description,
        'kind': 'likert',
        'style': entry.style,
        **{key: labels.get(value, value) for key, value in settings.items()},
        'domain': domain, #[(v[0], int(numpy.sign(v[1]))) for v in domain],
        'scheme': scheme,
        'notes': entry.notes,
        'data': data,
    }
    return info
