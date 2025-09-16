import yaml
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import YamlLexer, PythonLexer

from reportcraft.utils import CATEGORICAL_COLORS

register = template.Library()


def str_presenter(dumper, data):
    lines = data.splitlines()
    if len(lines) > 1:  # check for multiline string
        data = '\n'.join(lines)
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


@register.filter
def entry_html(entry):
    data = {
        'Type': entry.get_kind_display(),
        'Data Source': f"{entry.source}",
        'Attributes': entry.attrs
    }

    yaml_data = yaml.dump(data, sort_keys=False, allow_unicode=True, width=60)
    formatter = HtmlFormatter(nobackground=True, full=True)
    highlighted_data = highlight(yaml_data, YamlLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def yaml_html(data):
    yaml_data = yaml.dump(data, sort_keys=True, allow_unicode=True, width=65)
    formatter = HtmlFormatter(nobackground=True, full=True)
    highlighted_data = highlight(yaml_data, YamlLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def human_title(text):
    return text.replace('_', ' ').title()


@register.simple_tag
def data_snippet(source):

    data, count = source.snippet()
    labels = source.get_labels()
    if not data:
        return mark_safe('<p>No data</p>')

    if isinstance(data, str):
        return mark_safe(f"<pre>{data}</pre>")

    headers = data[0].keys()
    table_html = '<table class="table table-sm rc-snippet-table"><thead><tr>'
    for header in headers:
        name = labels.get(header, header)
        table_html += f'<th scope="col">{name}</th>'
    table_html += '</tr></thead><tbody>'

    for row in data:
        table_html += '<tr>'
        for header in headers:
            table_html += f'<td class="text-nowrap">{row.get(header, "")}</td>'
        table_html += '</tr>'

    table_html += f'</tbody></table><code>... of {count} items</code>'
    return mark_safe(table_html)


@register.filter
def expression_html(text):
    formatter = HtmlFormatter(nobackground=True)
    highlighted_data = highlight(text, PythonLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def boolean_check(value):
    text = '<i class="bi-check-circle-fill text-primary"></i>' if value else ''
    return mark_safe(text)


@register.simple_tag(takes_context=False)
def pigments_css(style='friendly'):
    formatter = HtmlFormatter(style=style, nobackground=True)
    return mark_safe(formatter.get_style_defs('.highlight'))


@register.inclusion_tag('reportcraft/tool-icon.html')
def tool_icon(**kwargs):
    return kwargs


@register.simple_tag(takes_context=True)
def report_url(context, report, **kwargs):
    """
    Returns the URL for a report with the given context and report object.
    """
    view = context.get('view')
    return view.get_link_url(report)


ICONS = {
    # General Tool icons
    'list-details': (
        '<path d="M13 5h8" /><path d="M13 9h5" />'
        '<path d="M13 15h8" /><path d="M13 19h5" /><path d="M3 4m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1'
        ' 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" /><path d="M3 14m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 '
        '0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
    ),
    'database': (
        '<path d="M12 6m-8 0a8 3 0 1 0 16 0a8 3 0 1 0 -16 0" />'
        '<path d="M4 6v6a8 3 0 0 0 16 0v-6" /><path d="M4 12v6a8 3 0 0 0 16 0v-6" />'
    ),
    'live-view': (
        '<path d="M4 8v-2a2 2 0 0 1 2 -2h2" />'
        '<path d="M4 16v2a2 2 0 0 0 2 2h2" /><path d="M16 4h2a2 2 0 0 1 2 2v2" />'
        '<path d="M16 20h2a2 2 0 0 0 2 -2v-2" /><path d="M12 11l0 .01" />'
        '<path d="M12 18l-3.5 -5a4 4 0 1 1 7 0l-3.5 5" />'
    ),
    'trash-x': (
        '<path d="M4 7h16" />'
        '<path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />'
        '<path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /><path d="M10 12l4 4m0 -4l-4 4" />'
    ),
    'photo-plus': (
        '<path d="M15 8h.01" />'
        '<path d="M12.5 21h-6.5a3 3 0 0 1 -3 -3v-12a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v6.5" />'
        '<path d="M3 16l5 -5c.928 -.893 2.072 -.893 3 0l4 4" /><path d="M14 14l1 -1c.67 -.644 1.45 -.824 2.182 -.54" />'
        '<path d="M16 19h6" /><path d="M19 16v6" />'
    ),
    'photo-down': (
        '<path d="M15 8h.01" /><path d="M12.5 21h-6.5a3 3 0 0 1 -3 -3v-12a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v6.5" />'
        '<path d="M3 16l5 -5c.928 -.893 2.072 -.893 3 0l4 4" />'
        '<path d="M14 14l1 -1c.653 -.629 1.413 -.815 2.13 -.559" />'
        '<path d="M19 16v6" /><path d="M22 19l-3 3l-3 -3" />'
    ),
    'copy': (
        '<path d="M7 7m0 2.667a2.667 2.667 0 0 1 2.667 -2.667h8.666a2.667 2.667 0 0 1 2.667 2.667v8.666a2.667 '
        '2.667 0 0 1 -2.667 2.667h-8.666a2.667 2.667 0 0 1 -2.667 -2.667z" />'
        '<path d="M4.012 16.737a2.005 2.005 0 0 1 -1.012 -1.737v-10c0 -1.1 .9 -2 2 -2h10c.75 0 1.158 .385 1.5 1" />'
    ),
    'adjustments-horizontal': (
        '<path d="M14 6m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M4 6l8 0" /><path d="M16 6l4 0" /><path d="M8 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M4 12l2 0" /><path d="M10 12l10 0" /><path d="M17 18m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M4 18l11 0" /><path d="M19 18l1 0" />'
    ),
    'pencil': (
        '<path d="M4 20h4l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4" />'
        '<path d="M13.5 6.5l4 4" />'
    ),
    'square-plus': (
        '<path d="M9 12h6" /><path d="M12 9v6" />'
        '<path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14z" />'
    ),
    'plus': (
        '<path d="M12 5l0 14" /><path d="M5 12l14 0" />'
    ),
    'database-plus': (
        '<path d="M4 6c0 1.657 3.582 3 8 3s8 -1.343 8 -3s-3.582 -3 -8 -3s-8 1.343 -8 3" />'
        '<path d="M4 6v6c0 1.657 3.582 3 8 3c1.075 0 2.1 -.08 3.037 -.224" /><path d="M20 12v-6" />'
        '<path d="M4 12v6c0 1.657 3.582 3 8 3c.166 0 .331 -.002 .495 -.006" />'
        '<path d="M16 19h6" /><path d="M19 16v6" />'
    ),
    'table-plus': (
        '<path d="M12.5 21h-7.5a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v7.5" /><path d="M3 10h18" />'
        '<path d="M10 3v18" /><path d="M16 19h6" /><path d="M19 16v6" />'
    ),
    'x': '<path d="M18 6l-12 12" /><path d="M6 6l12 12" />',
    'report': (
        '<path d="M8 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h5.697" />'
        '<path d="M18 14v4h4" /><path d="M18 11v-4a2 2 0 0 0 -2 -2h-2" />'
        '<path d="M8 3m0 2a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v0a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2z" />'
        '<path d="M18 18m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M8 11h4" /><path d="M8 15h3" />'
    ),
    'people': (
        '<path d="M9 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" />'
        '<path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />'
        '<path d="M21 21v-2a4 4 0 0 0 -3 -3.85" />'
    ),
    'buildings': (
        '<path d="M4 21v-15c0 -1 1 -2 2 -2h5c1 0 2 1 2 2v15" />'
        '<path d="M16 8h2c1 0 2 1 2 2v11" /><path d="M3 21h18" /><path d="M10 12v0" /><path d="M10 16v0" />'
        '<path d="M10 8v0" /><path d="M7 12v0" /><path d="M7 16v0" /><path d="M7 8v0" /><path d="M17 12v0" />'
        '<path d="M17 16v0" />'
    ),
    'notebook': (
        '<path d="M6 4h11a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-11a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1m3 0v18" />'
        '<path d="M13 8l2 0" /><path d="M13 12l2 0" />'
    ),
    'download': (
        '<path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2" />'
        '<path d="M7 11l5 5l5 -5" /><path d="M12 4l0 12" />'
    ),
    'file-type-csv': (
        '<path d="M14 3v4a1 1 0 0 0 1 1h4" />'
        '<path d="M5 12v-7a2 2 0 0 1 2 -2h7l5 5v4" /><path d="M7 16.5a1.5 1.5 0 0 0 -3 0v3a1.5 1.5 0 0 0 3 0" />'
        '<path d="M10 20.25c0 .414 .336 .75 .75 .75h1.25a1 1 0 0 0 1 -1v-1a1 1 0 0 0 -1 -1h-1a1 1 0 0 1 -1 -1v-1a1 '
        '1 0 0 1 1 -1h1.25a.75 .75 0 0 1 .75 .75" /><path d="M16 15l2 6l2 -6" />'
    ),
    'file-type-js': (
        '<path d="M14 3v4a1 1 0 0 0 1 1h4" />'
        '<path d="M3 15h3v4.5a1.5 1.5 0 0 1 -3 0" />'
        '<path d="M9 20.25c0 .414 .336 .75 .75 .75h1.25a1 1 0 0 0 1 -1v-1a1 1 0 0 0 -1 -1h-1a1 1 0 0 1 -1 -1v-1a1 '
        '1 0 0 1 1 -1h1.25a.75 .75 0 0 1 .75 .75" /><path d="M5 12v-7a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2h-1" />'
    ),

    # Entry Type Icons
    'pie': (
        '<path d="M10 3.2a9 9 0 1 0 10.8 10.8a1 1 0 0 0 -1 -1h-6.8a2 2 0 0 1 -2 -2v-7a.9 .9 0 0 0 -1 -.8" />'
        '<path d="M15 3.5a9 9 0 0 1 5.5 5.5h-4.5a1 1 0 0 1 -1 -1v-4.5" />'
    ),
    'columns': (
        '<path d="M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
        '<path d="M9 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
        '<path d="M15 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
        '<path d="M4 20h14" />'
    ),
    'bars': (
        '<path d="m11 3a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-6a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z"/>'
        '<path d="m15 15a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z"/>'
        '<path d="m19 9a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-14a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z"/>'
        '<path d="m4 4v14"/>'
    ),
    'likert': (
        '<path d="M3 18l14 0" /><path d="M9 9l3 3l-3 3" /><path d="M14 15l3 3l-3 3" /><path d="M3 3l0 18" />'
        '<path d="M3 12l9 0" /><path d="M18 3l3 3l-3 3" /><path d="M3 6l18 0" />'
    ),
    'grip': (
        '<path d="M9 5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />'
        '<path d="M9 12m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />'
        '<path d="M9 19m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />'
        '<path d="M15 5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />'
        '<path d="M15 12m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />'
        '<path d="M15 19m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" />'
    ),
    'bubble': (
        '<path d="M6 16m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0" />'
        '<path d="M16 19m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M14.5 7.5m-4.5 0a4.5 4.5 0 1 0 9 0a4.5 4.5 0 1 0 -9 0" />'
    ),
    'table': (
        '<path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14z" />'
        '<path d="M3 10h18" /><path d="M10 3v18" />'
    ),
    'list': (
        '<path d="M11 6h9" /><path d="M11 12h9" />'
        '<path d="M11 18h9" /><path d="M4 10v-4.5a1.5 1.5 0 0 1 3 0v4.5" /><path d="M4 8h3" />'
        '<path d="M4 20h1.5a1.5 1.5 0 0 0 0 -3h-1.5h1.5a1.5 1.5 0 0 0 0 -3h-1.5v6z" />'
    ),
    'plot': (
        '<path d="M3 3v18h18" />'
        '<path d="M9 9m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M19 7m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M14 15m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M10.16 10.62l2.34 2.88" />'
        '<path d="M15.088 13.328l2.837 -4.586" />'
    ),
    'histogram': (
        '<path d="M3 3v18h18" /><path d="M20 18v3" />'
        '<path d="M16 16v5" /><path d="M12 13v8" /><path d="M8 16v5" /><path d="M3 11c6 0 5 -5 9 -5s3 5 9 5" />'
    ),
    'timeline': (
        '<path d="M20 12v-6a2 2 0 0 0 -2 -2h-12a2 2 0 0 0 -2 2v8" />'
        '<path d="M4 18h17" /><path d="M18 15l3 3l-3 3" />'
    ),

    # Field type icons
    'TEXT': (
        '<path d="M6 15h15" /><path d="M21 19h-15" />'
        '<path d="M15 11h6" /><path d="M21 7h-6" /><path d="M9 9h1a1 1 0 1 1 -1 1v-2.5a2 2 0 0 1 2 -2" />'
        '<path d="M3 9h1a1 1 0 1 1 -1 1v-2.5a2 2 0 0 1 2 -2" />'
    ),
    'DATETIME': (
        '<path d="M11.795 21h-6.795a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v4" />'
        '<path d="M18 18m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M15 3v4" /><path d="M7 3v4" />'
        '<path d="M3 11h16" /><path d="M18 16.496v1.504l1 1" />'
    ),
    'DATE': (
        '<path d="M4 7a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12z" />'
        '<path d="M16 3v4" /><path d="M8 3v4" /><path d="M4 11h16" /><path d="M11 15h1" /><path d="M12 15v3" />'
    ),
    'INTEGER': (
        '<path d="M4 17v-10l7 10v-10" /><path d="M15 17h5" />'
        '<path d="M17.5 10m-2.5 0a2.5 3 0 1 0 5 0a2.5 3 0 1 0 -5 0" />'
    ),
    'BOOLEAN': (
        '<path d="M16 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M2 6m0 6a6 6 0 0 1 6 -6h8a6 6 0 0 1 6 6v0a6 6 0 0 1 -6 6h-8a6 6 0 0 1 -6 -6z" />'
    ),
    'STRING': (
        '<path d="M3 16v-6a2 2 0 1 1 4 0v6" />'
        '<path d="M3 13h4" /><path d="M10 8v6a2 2 0 1 0 4 0v-1a2 2 0 1 0 -4 0v1" />'
        '<path d="M20.732 12a2 2 0 0 0 -3.732 1v1a2 2 0 0 0 3.726 1.01" />'
    ),
    'FLOAT': (
        '<path d="M17 8a2 2 0 0 1 2 2v4a2 2 0 1 1 -4 0v-4a2 2 0 0 1 2 -2z" />'
        '<path d="M10 8a2 2 0 0 1 2 2v4a2 2 0 1 1 -4 0v-4a2 2 0 0 1 2 -2z" /><path d="M5 16h.01" />'
    ),
    'ARRAY': (
        '<path d="M15 12h.01" /><path d="M12 12h.01" /><path d="M9 12h.01" />'
        '<path d="M6 19a2 2 0 0 1 -2 -2v-4l-1 -1l1 -1v-4a2 2 0 0 1 2 -2" />'
        '<path d="M18 19a2 2 0 0 0 2 -2v-4l1 -1l-1 -1v-4a2 2 0 0 0 -2 -2" />'
    ),
    'JSON': (
        '<path d="M6 19a2 2 0 0 1 -2 -2v-4l-1 -1l1 -1v-4a2 2 0 0 1 2 -2" />'
        '<path d="M12 11.875l3 -1.687" /><path d="M12 11.875v3.375" /><path d="M12 11.875l-3 -1.687" />'
        '<path d="M12 11.875l3 1.688" /><path d="M12 8.5v3.375" /><path d="M12 11.875l-3 1.688" />'
        '<path d="M18 19a2 2 0 0 0 2 -2v-4l1 -1l-1 -1v-4a2 2 0 0 0 -2 -2" />'
    ),

    'map': (
        '<path d="M12 18.5l-3 -1.5l-6 3v-13l6 -3l6 3l6 -3v7.5" />'
        '<path d="M9 4v13" /><path d="M15 7v5.5" />'
        '<path d="M21.121 20.121a3 3 0 1 0 -4.242 0c.418 .419 1.125 1.045 2.121 1.879c1.051 -.89 1.759 '
        '-1.516 2.121 -1.879z" /><path d="M19 18v.01" />'
    ),
    'donut': (
        '<path d="M10 3.2a9 9 0 1 0 10.8 10.8a1 1 0 0 0 -1 '
        '-1h-3.8a4.1 4.1 0 1 1 -5 -5v-4a.9 .9 0 0 0 -1 -.8" /><path d="M15 3.5a9 9 0 0 1 5.5 5.5h-4.5a9 9 0 0 0 '
        '-1 -1v-4.5" />'
    ),
    'mixed': (
        '<path d="M4 19l4 -6l4 2l4 -5l4 4l0 5l-16 0" />'
        '<path d="M4 12l3 -4l4 2l5 -6l4 4" />'
    ),
    'line': (
        '<path d="M4 19l16 0" />'
        '<path d="M4 15l4 -6l4 2l4 -5l4 4" />'
    ),
    'area': (
        '<path d="M4 19l16 0" />'
        '<path d="M4 15l4 -6l4 2l4 -5l4 4l0 5l-16 0" />'
    ),
    'text': (
        '<path d="M6 15h15" /><path d="M21 19h-15" />'
        '<path d="M15 11h6" /><path d="M21 7h-6" /><path d="M9 9h1a1 1 0 1 1 -1 1v-2.5a2 2 0 0 1 2 -2" />'
        '<path d="M3 9h1a1 1 0 1 1 -1 1v-2.5a2 2 0 0 1 2 -2" />'
    ),

}
DEFAULT_ICON = (
    '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />'
    '<path d="M11 16l4 -1.5" /><path d="M10 10c-.5 -1 -2.5 -1 -3 0" /><path d="M17 10c-.5 -1 -2.5 -1 -3 0" />'
)
SVG_TEMPLATE = (
    '<svg  xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  '
    'stroke-width="{stroke}" stroke-linecap="round"  stroke-linejoin="round" class="{css_class}">{drawing}</svg>'
)


@register.simple_tag
def svg_icon(name, size=None, stroke=None):
    size = 'md' if not size else size
    stroke = 1.25 if not stroke else stroke
    svg = SVG_TEMPLATE.format(stroke=stroke, drawing=ICONS.get(name, DEFAULT_ICON), css_class=f"icon-{size}")
    return mark_safe(svg)


@register.simple_tag
def font_icon(name, size=None):
    size = 'md' if not size else size
    return mark_safe(f'<i class="ti-{name} icon-{size}"></i>')


@register.simple_tag
def swatches():
    swatches_template = (
        '<div class="swatches">'
        '   <div class="swatches-name">&emsp;{name}</div>'
        '   <div class="swatches-colors">{colors}</div>'
        '</div>'
    )
    all_swatches = []
    for name, colors in CATEGORICAL_COLORS.items():
        swatches_entry = ''.join([f'<div class="swatch" style="background-color: {color};"></div>' for color in colors])
        all_swatches.append(swatches_template.format(name=name, colors=swatches_entry))

    return mark_safe(''.join(all_swatches))


@register.simple_tag(takes_context=True)
def item_url(context, item):
    """
    Returns the URL for a given item based on context.
    """
    view = context.get('view')
    slug_field = getattr(view, 'slug_field', 'pk')
    slug_kwarg = getattr(view, 'slug_kwarg', 'pk')
    url_name = getattr(view, 'link_url', None)
    kwargs = {slug_kwarg: getattr(item, slug_field, None)}

    if url_name:
        return reverse(url_name, kwargs=kwargs)
    elif hasattr(item, 'get_absolute_url'):
        return item.get_absolute_url()
    elif hasattr(item, 'url'):
        return item.url
    elif hasattr(item, 'get_url'):
        return item.get_url()
    else:
        return '#0'
