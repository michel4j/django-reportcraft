import yaml
from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import YamlLexer, PythonLexer

from reportcraft.utils import COLOR_SCHEMES

register = template.Library()


@register.filter
def entry_html(entry):
    data = {
        'Type': entry.get_kind_display(),
        'Data Source': f"{entry.source}",
        'Attributes': entry.attrs
    }
    if entry.kind == entry.Types.TEXT:
        flow_style = False
        style = None
    else:
        flow_style = None
        style = None

    yaml_data = yaml.dump(data, default_style=style, default_flow_style=flow_style, sort_keys=False)
    formatter = HtmlFormatter(nobackground=True)
    highlighted_data = highlight(yaml_data, YamlLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def yaml_html(data):
    yaml_data = yaml.dump(data, default_flow_style=None, sort_keys=False)
    formatter = HtmlFormatter(nobackground=True)
    highlighted_data = highlight(yaml_data, YamlLexer(), formatter)
    return mark_safe(highlighted_data)


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


ICONS = {
    # General Tool icons
    'list-details': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M13 5h8" /><path d="M13 9h5" />'
        '<path d="M13 15h8" /><path d="M13 19h5" /><path d="M3 4m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1'
        ' 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" /><path d="M3 14m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 '
        '0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
    ),
    'database': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 6m-8 0a8 3 0 1 0 16 0a8 3 0 1 0 -16 0" />'
        '<path d="M4 6v6a8 3 0 0 0 16 0v-6" /><path d="M4 12v6a8 3 0 0 0 16 0v-6" />'
    ),
    'live-view': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 8v-2a2 2 0 0 1 2 -2h2" />'
        '<path d="M4 16v2a2 2 0 0 0 2 2h2" /><path d="M16 4h2a2 2 0 0 1 2 2v2" />'
        '<path d="M16 20h2a2 2 0 0 0 2 -2v-2" /><path d="M12 11l0 .01" />'
        '<path d="M12 18l-3.5 -5a4 4 0 1 1 7 0l-3.5 5" />'
    ),
    'trash-x': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 7h16" />'
        '<path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />'
        '<path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /><path d="M10 12l4 4m0 -4l-4 4" />'
    ),
    'photo-plus': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M15 8h.01" />'
        '<path d="M12.5 21h-6.5a3 3 0 0 1 -3 -3v-12a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v6.5" />'
        '<path d="M3 16l5 -5c.928 -.893 2.072 -.893 3 0l4 4" /><path d="M14 14l1 -1c.67 -.644 1.45 -.824 2.182 -.54" />'
        '<path d="M16 19h6" /><path d="M19 16v6" />'
    ),
    'adjustments-horizontal': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14 6m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M4 6l8 0" /><path d="M16 6l4 0" /><path d="M8 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M4 12l2 0" /><path d="M10 12l10 0" /><path d="M17 18m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M4 18l11 0" /><path d="M19 18l1 0" />'
    ),
    'pencil': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M4 20h4l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4" />'
        '<path d="M13.5 6.5l4 4" />'
    ),
    'square-plus': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 12h6" /><path d="M12 9v6" />'
        '<path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14z" />'
    ),
    'database-plus': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M4 6c0 1.657 3.582 3 8 3s8 -1.343 8 -3s-3.582 -3 -8 -3s-8 1.343 -8 3" />'
        '<path d="M4 6v6c0 1.657 3.582 3 8 3c1.075 0 2.1 -.08 3.037 -.224" /><path d="M20 12v-6" />'
        '<path d="M4 12v6c0 1.657 3.582 3 8 3c.166 0 .331 -.002 .495 -.006" />'
        '<path d="M16 19h6" /><path d="M19 16v6" />'
    ),
    'table-plus': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M12.5 21h-7.5a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v7.5" /><path d="M3 10h18" />'
        '<path d="M10 3v18" /><path d="M16 19h6" /><path d="M19 16v6" />'
    ),
    'x': '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M18 6l-12 12" /><path d="M6 6l12 12" />',
    'report': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M8 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h5.697" />'
        '<path d="M18 14v4h4" /><path d="M18 11v-4a2 2 0 0 0 -2 -2h-2" />'
        '<path d="M8 3m0 2a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v0a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2z" />'
        '<path d="M18 18m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M8 11h4" /><path d="M8 15h3" />'
    ),
    'people': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" />'
        '<path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />'
        '<path d="M21 21v-2a4 4 0 0 0 -3 -3.85" />'
    ),
    'buildings': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 21v-15c0 -1 1 -2 2 -2h5c1 0 2 1 2 2v15" />'
        '<path d="M16 8h2c1 0 2 1 2 2v11" /><path d="M3 21h18" /><path d="M10 12v0" /><path d="M10 16v0" />'
        '<path d="M10 8v0" /><path d="M7 12v0" /><path d="M7 16v0" /><path d="M7 8v0" /><path d="M17 12v0" />'
        '<path d="M17 16v0" />'
    ),
    'notebook': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M6 4h11a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-11a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1m3 0v18" />'
        '<path d="M13 8l2 0" /><path d="M13 12l2 0" />'
    ),

    # Entry Type Icons
    'pie': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><'
        'path d="M10 3.2a9 9 0 1 0 10.8 10.8a1 1 0 0 0 -1 -1h-6.8a2 2 0 0 1 -2 -2v-7a.9 .9 0 0 0 -1 -.8" />'
        '<path d="M15 3.5a9 9 0 0 1 5.5 5.5h-4.5a1 1 0 0 1 -1 -1v-4.5" />'
    ),
    'bars': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
        '<path d="M15 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />'
        '<path d="M9 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" /><path d="M4 20h14" />'
    ),
    'table': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/>'
        '<path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14z" />'
        '<path d="M3 10h18" /><path d="M10 3v18" />'
    ),
    'list': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M11 6h9" /><path d="M11 12h9" />'
        '<path d="M11 18h9" /><path d="M4 10v-4.5a1.5 1.5 0 0 1 3 0v4.5" /><path d="M4 8h3" />'
        '<path d="M4 20h1.5a1.5 1.5 0 0 0 0 -3h-1.5h1.5a1.5 1.5 0 0 0 0 -3h-1.5v6z" />'
    ),
    'plot': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 3v18h18" />'
        '<path d="M9 9m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M19 7m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />'
        '<path d="M14 15m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M10.16 10.62l2.34 2.88" />'
        '<path d="M15.088 13.328l2.837 -4.586" />'
    ),
    'histogram': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 3v18h18" /><path d="M20 18v3" />'
        '<path d="M16 16v5" /><path d="M12 13v8" /><path d="M8 16v5" /><path d="M3 11c6 0 5 -5 9 -5s3 5 9 5" />'
    ),
    'timeline': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M20 12v-6a2 2 0 0 0 -2 -2h-12a2 2 0 0 0 -2 2v8" />'
        '<path d="M4 18h17" /><path d="M18 15l3 3l-3 3" />'
    ),
    'text': (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 15h15" /><path d="M21 19h-15" />'
        '<path d="M15 11h6" /><path d="M21 7h-6" /><path d="M9 9h1a1 1 0 1 1 -1 1v-2.5a2 2 0 0 1 2 -2" />'
        '<path d="M3 9h1a1 1 0 1 1 -1 1v-2.5a2 2 0 0 1 2 -2" />'
    ),
}
DEFAULT_ICON = (
    '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />'
    '<path d="M11 16l4 -1.5" /><path d="M10 10c-.5 -1 -2.5 -1 -3 0" /><path d="M17 10c-.5 -1 -2.5 -1 -3 0" />'
)
SVG_TEMPLATE = (
    '<svg  xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  '
    'stroke-width="{stroke}" stroke-linecap="round"  stroke-linejoin="round" class="{css_class}">{drawing}</svg>'
)


@register.simple_tag
def svg_icon(name, size=None, stroke=None):
    size = 'md' if not size else size
    stroke = 2 if not stroke else stroke
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
    for name, colors in COLOR_SCHEMES.items():
        swatches_entry = ''.join([f'<div class="swatch" style="background-color: {color};"></div>' for color in colors])
        all_swatches.append(swatches_template.format(name=name, colors=swatches_entry))

    return mark_safe(''.join(all_swatches))
