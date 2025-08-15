from collections import defaultdict
from typing import Any, Literal
from .utils import regroup_data, MinMax, epoch, map_colors, get_histogram_points, split_data, debug_value


def generate_table(entry, *args, **kwargs) -> dict:
    """
    Generate a table from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """

    rows = entry.attrs.get('rows', [])
    columns = entry.attrs.get('columns', [])
    values = entry.attrs.get('values', '')
    total_column = entry.attrs.get('total_column', False)
    total_row = entry.attrs.get('total_row', False)
    force_strings = entry.attrs.get('force_strings', False)
    transpose = entry.attrs.get('transpose', False)
    labels = entry.source.get_labels()

    if not columns or not rows:
        return {}

    if isinstance(rows, str) and isinstance(columns, list):
        rows, columns = columns, rows
        transpose = True
    first_row_name = labels.get(columns, columns)

    raw_data = entry.source.get_data(*args, **kwargs)
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

    return {
        'title': entry.title,
        'kind': 'table',
        'data': table_data,
        'style': entry.style,
        'header': "column row",
        'description': entry.description,
        'notes': entry.notes
    }


def generate_bars(entry, kind='bars', *args, **kwargs):
    """
    Generate a bar or column chart from the data source
    :param entry: The report entry containing the configuration for the table
    :param kind: The type of chart to generate ('bars', 'columns', 'area', 'line')
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    labels = entry.source.get_labels()
    vertical = entry.attrs.get('vertical', True)
    x_axis = entry.attrs.get('x_axis', '')
    y_axis = entry.attrs.get('y_axis', [])
    sort_by = entry.attrs.get('sort_by', None)
    sort_desc = entry.attrs.get('sort_desc', False)
    stack = entry.attrs.get('stack', [])
    y_value = entry.attrs.get('y_value', '')
    colors = entry.attrs.get('colors', 'Live16')
    color_field = entry.attrs.get('color_field', None)
    aspect_ratio = entry.attrs.get('aspect_ratio', None)
    wrap_x_labels = entry.attrs.get('wrap_x_labels', False)
    x_culling = entry.attrs.get('x_culling', 15)
    limit = entry.attrs.get('limit', None)

    # For compatibility with older reports, convert 'bars' to 'columns' and vice versa if vertical is True
    if vertical and kind == 'bars':
        kind = 'columns'
        vertical = False
    elif vertical and kind == 'columns':
        kind = 'bars'
        vertical = False

    areas = entry.attrs.get('areas', [])
    lines = entry.attrs.get('lines', [])
    bars = entry.attrs.get('bars', [])

    if not x_axis or not y_axis:
        return {}

    x_label = labels.get(x_axis, x_axis.title())
    raw_data = entry.source.get_data(*args, **kwargs)
    if len(y_axis) == 1 and y_value:
        y_axis = y_axis[0]
        y_labels = list(filter(None, dict.fromkeys(item[y_axis] for item in raw_data)))
        y_stack = [y_labels for group in stack for y in group if y == y_axis]
        types = {
            **{y: 'bar' for y in y_labels if kind in ['bars', 'columns']},
            **{y: 'line' for y in y_labels if kind == 'line'},
            **{y: 'area' for y in y_labels if kind == 'area'},
        }

    else:
        y_stack = [[labels.get(y, y.title()) for y in group] for group in stack]
        types = {
            **{labels.get(field, field.title()): 'area' for field in areas},
            **{labels.get(field, field.title()): 'line' for field in lines},
            **{labels.get(field, field.title()): 'bar' for field in bars},
        }
        if not types:
            types = {
                **{labels.get(y, y.title()): 'bar' for y in y_axis if kind in ['bars', 'columns']},
                **{labels.get(y, y.title()): 'line' for y in y_axis if kind == 'line'},
                **{labels.get(y, y.title()): 'area' for y in y_axis if kind == 'area'},
            }

    data = regroup_data(
        raw_data, x_axis=x_axis, y_axis=y_axis, y_value=y_value, labels=labels,
        sort=sort_by, sort_desc=sort_desc, default=0,
    )

    info = {
        'title': entry.title,
        'description': entry.description,
        'kind': kind,
        'types': types,
        'y-ticks': None if vertical else 5,
        'style': entry.style,
        'notes': entry.notes,
        'x-label': x_label,
    }

    if aspect_ratio:
        info['aspect-ratio'] = aspect_ratio
    if y_stack:
        info['stack'] = y_stack
    if color_field:
        color_key = labels.get(color_field)
        info['color-by'] = color_key
        color_keys = list(dict.fromkeys([item.get(color_field) for item in raw_data if color_field in item]))
        info['colors'] = map_colors(color_keys, colors)
    elif colors:
        info['colors'] = colors
    if x_culling:
        info['x-culling'] = x_culling
    if wrap_x_labels:
        info['wrap-x-labels'] = wrap_x_labels

    if limit:
        data = data[limit:] if limit < 0 else data[:limit]
    info['data'] = data
    return info


def generate_area(entry, *args, **kwargs):
    return generate_bars(entry, *args, kind='area', **kwargs)


def generate_line(entry, *args, **kwargs):
    return generate_bars(entry, *args, kind='line', **kwargs)


def generate_columns(entry, *args, **kwargs):
    return generate_bars(entry, *args, kind='columns', **kwargs)


def generate_list(entry, *args, **kwargs):
    """
    Generate a list from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    columns = entry.attrs.get('columns', [])
    order_by = entry.attrs.get('order_by', None)
    limit = entry.attrs.get('limit', None)

    if not columns:
        return {}

    data = entry.source.get_data(*args, **kwargs)
    labels = entry.source.get_labels()

    if order_by:
        sort_key, reverse = (order_by[1:], True) if order_by.startswith('-') else (order_by, False)
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
        'data': table_data,
        'style': f"{entry.style} first-col-left",
        'header': "row",
        'description': entry.description,
        'notes': entry.notes
    }


def generate_plot(entry, *args, **kwargs):
    """
    Generate an XY plot from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    labels = entry.source.get_labels()

    groups = entry.attrs.get('groups', [])
    x_label = entry.attrs.get('x_label', '')
    y_label = entry.attrs.get('y_label', '')
    x_value = entry.attrs.get('x_value', '')
    group_by = entry.attrs.get('group_by', None)
    colors = entry.attrs.get('colors', 'Live16')
    precision = entry.attrs.get('precision', 0)

    valid_groups = [
        {
            'x': x_value,       # All groups share the same x-value
            **group
        }
        for group in groups if 'y' in group
    ]

    if not valid_groups:
        return {}

    y_fields = [group['y'] for group in valid_groups]
    z_fields = [group.get('z') for group in valid_groups if 'z' in group]

    raw_data = entry.source.get_data(*args, **kwargs)

    if len(valid_groups) == 1 and group_by:
        internal_groups = True
        data = regroup_data(raw_data, x_axis=x_value, y_axis=y_fields, others=[group_by] + z_fields)
        grouped_data = split_data(data, group_by)
        internal_groups = list(grouped_data.keys())
    else:
        internal_groups = False
        grouped_data = {}
        data = regroup_data(raw_data, x_axis=x_value, y_axis=y_fields, others=z_fields)

    # sort data
    types = {group.get('type') for group in valid_groups}
    sort_keys = [x_value]
    reverse_sort = False
    if z_fields and types == {'scatter'}:
        sort_keys = z_fields
        reverse_sort = True

    data.sort(key=lambda x: tuple(x.get(f) for f in sort_keys), reverse=reverse_sort)

    # get data groups
    group_info = []
    report_data = {}
    if internal_groups:
        group = valid_groups[0]
        for group_name, group_data in grouped_data.items():
            x_name = f'{group_name}_{group["x"]}'
            z_name = f'{group_name}_{group.get("z", "")}' if "z" in group else ''
            y_name = group_name.title()
            new_group = {
                'x': x_name,
                'y': y_name,
                'z': z_name,
                'type': group.get('type', ''),
            }
            # sort to show bigger bubbles first
            if group.get('type') == 'scatter' and group.get('z'):
                group_data.sort(key=lambda x: x.get(group['z'], 0), reverse=True)

            group_info.append({k: v for k, v in new_group.items() if v})
            sub_data = {
                x_name: [item[group['x']] for item in group_data if group['x'] in item],
                y_name: [item[group['y']] for item in group_data if group['y'] in item],
            }
            if 'z' in group:
                sub_data[z_name] = [item[group['z']] for item in group_data if group['z'] in item]
            report_data.update(sub_data)
    else:
        for group in valid_groups:
            x_name = labels.get(group['x'], group['x'].title())
            y_name = labels.get(group['y'], group['y'].title())
            z_name = labels.get(group.get('z', ''), group.get('z', '').title())
            new_group = {
                'x': x_name,
                'y': y_name,
                'z': z_name,
                'type': group.get('type', ''),
            }
            group_info.append({k: v for k, v in new_group.items() if v})

        report_data.update({
            labels.get(field_name, field_name.title()): [item[field_name] for item in data if field_name in item]
            for field_name in [x_value] + y_fields + z_fields
        })

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'xyplot',
        'style': entry.style,
        'colors': colors,
        'max-radius': 20,
        'groups': group_info,
        'x-label': x_label,
        'y-label': y_label,
        'x-tick-precision': precision,
        'data': report_data,
        'notes': entry.notes
    }


def generate_pie(entry, kind: Literal['pie', 'donut'] = 'pie', *args, **kwargs):
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

    raw_data = entry.source.get_data(*args, **kwargs)
    data = defaultdict(int)
    for item in raw_data:
        data[item.get(label_field)] += item.get(value_field, 0)

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': kind,
        'style': entry.style,
        'colors': colors,
        'data': [{'label': labels.get(label, label.title()), 'value': value} for label, value in data.items()],
        'notes': entry.notes
    }


def generate_donut(entry, *args, **kwargs):
    """
    Generate a donut chart from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    return generate_pie(entry, kind='donut', *args, **kwargs)


def generate_histogram(entry, *args, **kwargs):
    """
    Generate a histogram from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    bins = entry.attrs.get('bins', None)
    value_field = entry.attrs.get('values', '')
    colors = entry.attrs.get('colors', None)
    if not value_field:
        return {}

    raw_data = entry.source.get_data(*args, **kwargs)
    labels = entry.source.get_labels()
    values = [float(item.get(value_field)) for item in raw_data if item.get(value_field) is not None]
    data = get_histogram_points(values, bins=bins)
    x_culling = min(len(data), 15)
    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'histogram',
        'style': entry.style,
        'colors': colors,
        'x-label': labels.get(value_field, value_field.title()),
        'x-culling': x_culling,
        'data': data,
        'notes': entry.notes
    }


def generate_timeline(entry, *args, **kwargs):
    """
    Generate a timeline from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """

    type_field = entry.attrs.get('type_field', '')
    start_field = entry.attrs.get('start_field', [])
    end_field = entry.attrs.get('end_field', '')
    label_field = entry.attrs.get('label_field', '')
    colors = entry.attrs.get('colors', None)

    if not type_field or not start_field or not end_field:
        return {}

    min_max = MinMax()
    raw_data = entry.source.get_data(*args, **kwargs)
    data = [
        {
            'type': item.get(type_field, ''),
            'start': min_max.check(epoch(item[start_field])),
            'end': min_max.check(epoch(item[end_field])),
            'label': item.get(label_field, '')
        } for item in raw_data if start_field in item and end_field in item
    ]

    min_time = entry.attrs.get('min_time', min_max.min)
    max_time = entry.attrs.get('max_time', min_max.max)

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'timeline',
        'colors': colors,
        'start': min_time,
        'end': max_time,
        'style': entry.style,
        'notes': entry.notes,
        'data': data
    }


def generate_text(entry, *args, **kwargs):
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


def generate_geochart(entry, *args, **kwargs):
    """
    Generate a geo chart from the data source
    :param entry: The report entry containing the configuration for the table
    returns: A dictionary containing the table data and metadata suitable for rendering
    """
    all_columns = {
        'Lat': entry.attrs.get('latitude'),
        'Lon': entry.attrs.get('longitude'),
        'Location': entry.attrs.get('location'),
        'Name': entry.attrs.get('name'),
        'Value': entry.attrs.get('value'),
        'Color': entry.attrs.get('color_by'),
    }
    columns = {key: value for key, value in all_columns.items() if value}

    region = entry.attrs.get('region', 'world')
    resolution = entry.attrs.get('resolution', 'countries')
    mode = entry.attrs.get('mode', 'regions')
    colors = entry.attrs.get('colors', 'YlOrRd')

    raw_data = entry.source.get_data(*args, **kwargs)
    data = [
        {k: item.get(v) for k, v in columns.items()}
        for item in raw_data
    ]

    return {
        'title': entry.title,
        'description': entry.description,
        'kind': 'geochart',
        'mode': mode,
        'region': region,
        'resolution': resolution,
        'colors': colors,
        'show-legend': False,
        'style': entry.style,
        'notes': entry.notes,
        'map': 'canada',
        'data': data
    }

