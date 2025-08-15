import re

from datetime import datetime
from crispy_forms.bootstrap import Tab, TabHolder
from crispy_forms.layout import Div, Field, Layout, HTML
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from crisp_modals.forms import (
    ModalModelForm, HalfWidth, FullWidth, Row, ThirdWidth, QuarterWidth, ThreeQuarterWidth, TwoThirdWidth
)

from . import models, utils
from .utils import CATEGORICAL_COLORS, SEQUENTIAL_COLORS, REGION_CHOICES, AXIS_CHOICES

disabled_widget = forms.HiddenInput(attrs={'readonly': True})


class AutoPopulatedSlugField(forms.TextInput):
    """
    A SlugField that automatically populates the slug based on the title field.
    If the slug is already set, it will not change it.
    """
    def __init__(self, *args, **kwargs):
        self.src_field = kwargs.pop('src_field', 'title')
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        output = super().render(name, value, final_attrs, renderer)
        js_code = render_to_string('reportcraft/auto-slug-field.html', {
            'slug_field': name,
            'src_field': self.src_field,
        })
        return output + js_code


class ReportForm(ModalModelForm):
    class Meta:
        model = models.Report
        fields = ('title', 'section', 'slug', 'description', 'style', 'notes')
        widgets = {
            'title': forms.TextInput,
            'description': forms.Textarea(attrs={'rows': "2"}),
            'notes': forms.Textarea(attrs={'rows': "4"}),
            'slug': AutoPopulatedSlugField(src_field='title'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.append(
            Row(
                FullWidth('title'),
            ),
            Row(
                QuarterWidth('section'), HalfWidth('slug'), QuarterWidth('style'),
            ),
            Row(
                FullWidth('description'),
            ),
            Row(
                FullWidth('notes'),
            ),
        )


class DataFieldForm(ModalModelForm):
    class Meta:
        model = models.DataField
        fields = (
            'name', 'model', 'label', 'default', 'expression', 'precision',
            'source', 'position', 'ordering',
        )
        widgets = {
            'default': forms.TextInput(),
            'expression': forms.Textarea(attrs={'rows': "2"}),
            'source': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pk = self.instance.pk
        self.fields['source'].widget = forms.HiddenInput()
        if pk:
            self.fields['model'].queryset = self.instance.source.models.all()
        else:
            self.fields['model'].queryset = models.DataModel.objects.filter(source=self.initial['source'])

        self.body.append(
            Div(
                Div('name', css_class='col-6'),
                Div('label', css_class="col-6"),
                css_class='row'
            ),
            Div(
                Div(Field('model', css_class='select'), css_class="col-8"),
                Div('ordering', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Div('default', css_class='col-4'),
                Div('precision', css_class='col-4'),
                Div('position', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Div(Field('expression', css_class='font-monospace'), css_class='col-12'),
                Field('source'),
                css_class='row'
            ),
        )

    def clean(self):
        data = super().clean()
        data['name'] = data.get('name', '').strip().lower()
        model = data.get('model')
        name = data['name']
        expression = data.get('expression')
        if not model.has_field(name) and not expression:
            self.add_error('expression', _(f"Required since `{model}` does not have a field named `{name}`"))
        return data


class DataSourceForm(ModalModelForm):
    group_fields = forms.CharField(required=False, help_text=_("Comma separated list of field names to group by"))

    class Meta:
        model = models.DataSource
        fields = (
            'name', 'group_by', 'limit', 'group_fields', 'description', 'filters'
        )
        widgets = {
            'group_by': forms.HiddenInput,
            'description': forms.Textarea(attrs={'rows': "2"}),
            'filters': forms.Textarea(attrs={'rows': "2"}),
        }
        help_texts = {
            'limit': _("Maximum number of records"),
            'filters': _("Use only field names from the source. ")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.append(
            Div(
                Div('name', css_class='col-12'),
                Div('group_fields', css_class='col-sm-8'),
                Div('limit', css_class='col-sm-4'),
                Div('description', css_class='col-12'),
                Div(Field('filters', css_class='font-monospace'), css_class='col-12'),
                css_class='row'
            )
        )

    def clean(self):
        data = super().clean()
        group_fields = data.pop('group_fields', "")
        data['group_by'] = re.split(r'\s*[,;|]\s*', group_fields) if group_fields else []
        filters = data.get('filters')
        if filters.strip():
            source_fields = set(self.instance.fields.values_list('name', flat=True))
            try:
                parser = utils.FilterParser(identifiers=source_fields)
                parser.parse(filters)
            except ValueError as e:
                self.add_error('filters', _(f"Invalid filter: {e}"))
        return data


class DataModelForm(ModalModelForm):
    class Meta:
        model = models.DataModel
        fields = ('model', 'source', 'name')
        widgets = {
            'source': forms.HiddenInput,
            'name': forms.HiddenInput,
        }

    def __init__(self, *args, source=None, **kwargs):
        self.source = source
        super().__init__(*args, **kwargs)

        self.fields['model'].queryset = ContentType.objects.filter(app_label__in=settings.REPORTCRAFT_APPS)

        self.extra_fields = {}
        if self.instance.model:
            group_fields = self.instance.get_group_fields()
            for field_name, field in group_fields.items():
                group_name = f'{field_name}__group'
                self.fields[group_name] = forms.CharField(label=_(f'{field_name.title()} Group'), required=True)
                self.fields[group_name].help_text = f'Enter expression for {field_name} grouping'
                if field:
                    self.fields[group_name].initial = field.expression
                self.extra_fields[field_name] = group_name
        else:
            for field_name in self.source.group_by:
                group_name = f'{field_name}__group'
                self.fields[group_name] = forms.CharField(label=_(f'{field_name.title()} Group'), required=True)
                self.fields[group_name].help_text = f'Enter expression for {field_name} grouping'
                self.extra_fields[field_name] = group_name

        extra_div = Div(*[Div(field, css_class='col-12') for field in self.extra_fields.values()], css_class='row')
        self.body.append(
            Div(
                Div('model', css_class='col-12'),
                css_class='row'
            ),
            extra_div,
            Field('source'),
            Field('name'),
        )

    def clean(self):
        data = super().clean()

        data['name'] = f'{data["model"].app_label}.{data["model"].model.title()}'
        data['groups'] = {
            field: data[group] for field, group in self.extra_fields.items()
        }
        return data


class EntryForm(ModalModelForm):
    class Meta:
        model = models.Entry
        fields = (
            'title', 'description', 'notes', 'style', 'kind', 'source', 'report', 'position'
        )
        widgets = {
            'title': forms.TextInput(),
            'description': forms.TextInput(),
            'notes': forms.Textarea(attrs={'rows': "4"}),
            'report': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pk = self.instance.pk

        self.body.append(
            Div(
                Div('title', css_class='col-10'),
                Div('position', css_class='col-2'),
                css_class='row'
            ),
            Div(
                Div('description', css_class='col-12'),
                css_class='row'
            ),
            Div(
                Div('kind', css_class='col-4'),
                Div('source', css_class='col-4'),
                Div('style', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Div('notes', css_class='col-12'),
                Field('report'),
                css_class='row'
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        kind = cleaned_data.get('kind')
        source = cleaned_data.get('source')
        if kind != models.Entry.Types.TEXT and not source:
            self.add_error('source', _("This field is required for the selected entry type"))
        return cleaned_data


class TableForm(ModalModelForm):
    columns = forms.ModelChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    rows = forms.ModelMultipleChoiceField(label='Rows', required=True, queryset=models.DataField.objects.none())
    values = forms.ModelChoiceField(label='Values', required=False, queryset=models.DataField.objects.none())
    total_column = forms.BooleanField(label="Row Totals", required=False)
    total_row = forms.BooleanField(label="Column Totals", required=False)
    force_strings = forms.BooleanField(label="Force Strings", required=False)
    transpose = forms.BooleanField(label="Transpose", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Div(
                Div(Field('rows', css_class='select'), css_class='col-12'),
                Div(Field('columns', css_class='select'), css_class='col-6'),
                Div(Field('values', css_class='select'), css_class='col-6'),
                css_class='row'
            ),
            Div(
                Div('total_row', css_class='col-6'),
                Div('total_column', css_class='col-6'),
                Div('force_strings', css_class='col-6'),
                Div('transpose', css_class='col-6'),
                css_class='row'
            ),
            Div(

                Field('attrs'),
                css_class='row'
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['columns', 'values', 'rows']:
            self.fields[field].queryset = field_queryset

        for field in ['columns', 'values']:
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()
        if 'rows' in attrs:
            self.fields['rows'].initial = field_queryset.filter(name__in=attrs['rows'])

        for field in ['total_row', 'total_column', 'force_strings', 'transpose']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}
        for field in ['columns', 'values']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        if 'rows' in cleaned_data:
            new_attrs['rows'] = [y.name for y in cleaned_data['rows'].order_by('position')]

        for field in ['total_row', 'total_column', 'force_strings', 'transpose']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class BarsForm(ModalModelForm):
    x_axis = forms.ModelChoiceField(label='X-axis', required=True, queryset=models.DataField.objects.none())
    y_axis = forms.ModelMultipleChoiceField(label='Y-axis', required=True, queryset=models.DataField.objects.none())
    y_value = forms.ModelChoiceField(label='Values', required=False, queryset=models.DataField.objects.none())

    stack_0 = forms.ModelMultipleChoiceField(label='Stack', required=False, queryset=models.DataField.objects.none())
    stack_1 = forms.ModelMultipleChoiceField(label='Stack', required=False, queryset=models.DataField.objects.none())
    stack_2 = forms.ModelMultipleChoiceField(label='Stack', required=False, queryset=models.DataField.objects.none())

    areas = forms.ModelMultipleChoiceField(label='Areas', required=False, queryset=models.DataField.objects.none())
    bars = forms.ModelMultipleChoiceField(label='Bars', required=False, queryset=models.DataField.objects.none())
    lines = forms.ModelMultipleChoiceField(label='Lines', required=False, queryset=models.DataField.objects.none())

    color_field = forms.ModelChoiceField(label='Color By', required=False, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=CATEGORICAL_COLORS, initial='Live8')
    x_culling = forms.IntegerField(label="Culling", required=False)
    wrap_x_labels = forms.BooleanField(label="Wrap Labels", required=False)
    aspect_ratio = forms.FloatField(label="Aspect Ratio", required=False)
    vertical = forms.BooleanField(label="Rotate", required=False)

    sort_by = forms.ModelChoiceField(label='Sort By', required=False, queryset=models.DataField.objects.none())
    sort_desc = forms.BooleanField(label="Sort Descending", required=False)
    limit = forms.IntegerField(label="Limit", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Div(
                Div(Field('x_axis', css_class='select'), css_class='col-4'),
                Div(Field('y_axis', css_class='select'), css_class='col-8'),
                css_class='row'
            ),
            Div(
                Div(Field('y_value', css_class='select'), css_class='col-3'),
                Div(Field('sort_by', css_class='select'), css_class='col-3'),
                Div(Field('color_field', css_class='select'), css_class='col-3'),
                Div(Field('colors', css_class='select'), css_class='col-3'),
                css_class='row'
            ),
            Div(
                Div('aspect_ratio', css_class='col-4'),
                Div('x_culling', css_class='col-4'),
                Div('limit', css_class='col-4'),
                css_class='row'
            ),
            TabHolder(
                Tab(
                    'Stacks',
                    Div(
                        Div(Field('stack_0', css_class='select'), css_class='col-12'),
                        Div(Field('stack_1', css_class='select'), css_class='col-12'),
                        Div(Field('stack_2', css_class='select'), css_class='col-12'),
                        css_class='row'
                    ),
                ),
                Tab(
                    'Mixed Types',
                    Div(
                        Div(Field('areas', css_class='select'), css_class='col-12'),
                        Div(Field('bars', css_class='select'), css_class='col-12'),
                        Div(Field('lines', css_class='select'), css_class='col-12'),
                        css_class='row'
                    ),
                ),
                css_class='nav-tabs-sm my-2'
            ),
            Div(
                Div(
                    Div('wrap_x_labels', css_class='col-4'),
                    Div('vertical', css_class='col-4'),
                    Div('sort_desc', css_class='col-4'),
                    css_class='row'
                ),
                Field('attrs'),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        field_fields = [
            'x_axis', 'y_axis', 'y_value', 'stack_0', 'stack_1', 'stack_2', 'color_field',  'sort_by',
            'areas', 'bars', 'lines'
        ]
        for field in field_fields:
            self.fields[field].queryset = field_queryset

        for field in ['x_axis', 'y_value', 'color_field', 'sort_by']:
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()

        for field in ['y_axis', 'areas', 'lines', 'bars']:
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name__in=attrs[field])

        if 'stack' in attrs:
            for i, stack in enumerate(attrs['stack']):
                self.fields[f'stack_{i}'].initial = field_queryset.filter(name__in=stack)

        for field in ['x_culling', 'wrap_x_labels', 'aspect_ratio', 'sort_desc', 'limit', 'colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

        self.fields['vertical'].initial = attrs.get('vertical', True)

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['x_axis', 'y_value', 'color_field', 'sort_by']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in ['y_axis', 'areas', 'lines', 'bars']:
            if field in cleaned_data and cleaned_data[field].exists():
                new_attrs[field] = [y.name for y in cleaned_data[field].order_by('position')]
                mixed = True

        stack = []
        for i in range(3):
            if f'stack_{i}' in cleaned_data and cleaned_data[f'stack_{i}'].exists():
                stack.append([y.name for y in cleaned_data[f'stack_{i}'].order_by('position')])

        if stack:
            new_attrs['stack'] = stack

        for field in ['x_culling', 'wrap_x_labels', 'aspect_ratio', 'vertical', 'sort_desc', 'limit', 'colors']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


PLOT_SERIES = 4
XY_MARKERS = [('scatter', 'Points'), ('line', 'Lines'), ('', 'Lines & Points')]


class PlotForm(ModalModelForm):
    x_label = forms.CharField(label='X Label', required=False)
    y_label = forms.CharField(label='Y Label', required=False)
    x_value = forms.ModelChoiceField(label='X-Value', required=True, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=CATEGORICAL_COLORS, initial='Live8')
    group_by = forms.ModelChoiceField(label='Group By', required=False, queryset=models.DataField.objects.none())
    precision = forms.IntegerField(label="Precision", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        for i in range(PLOT_SERIES):
            self.fields[f'y__{i}'] = forms.ModelChoiceField(
                label=f'Y-Value', required=False, queryset=models.DataField.objects.none()
            )
            self.fields[f'z__{i}'] = forms.ModelChoiceField(
                label=f'Z-Value', required=False, queryset=models.DataField.objects.none()
            )
            self.fields[f'type__{i}'] = forms.ChoiceField(label="Type", required=False, choices=XY_MARKERS)

        self.update_initial()
        self.body.append(
            Row(
                ThirdWidth('x_value'),
                ThirdWidth('x_label'),
                ThirdWidth('y_label'),
                style='g-3'
            ),
            Row(
                ThirdWidth('group_by'),
                ThirdWidth('colors'),
                ThirdWidth('precision'),
                style='g-3'
            ),
        )
        for i in range(PLOT_SERIES):
            self.body.append(
                Row(
                    ThirdWidth(f'y__{i}'),
                    ThirdWidth(f'z__{i}'),
                    ThirdWidth(f'type__{i}'),
                    style='g-3'
                ),
            )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())

        for field in ['x_value', 'group_by']:
            self.fields[field].queryset = field_queryset

        for i in range(PLOT_SERIES):
            for f in ['y', 'z']:
                self.fields[f'{f}__{i}'].queryset = field_queryset

        for field in ['x_value', 'group_by']:
            self.fields[field].queryset = field_queryset
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()

        for i, group in enumerate(attrs.get('groups', [])):
            for f in ['y', 'z']:
                if f in group:
                    self.fields[f'{f}__{i}'].initial = field_queryset.filter(name=group[f]).first()
            self.fields[f'type__{i}'].initial = group.get('type', '')

        for field in ['x_label', 'y_label', 'precision', 'colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {
            'groups': []
        }

        for i in range(PLOT_SERIES):
            group = {}
            for f in ['y', 'z']:
                if f'{f}__{i}' in cleaned_data and cleaned_data[f'{f}__{i}']:
                    group[f] = cleaned_data[f'{f}__{i}'].name

            if f'type__{i}' in cleaned_data and cleaned_data[f'type__{i}']:
                group['type'] = cleaned_data[f'type__{i}']
            if 'y' in group.keys():
                new_attrs['groups'].append(group)

        for field in ['x_value', 'group_by']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in ['x_label', 'y_label', 'precision', 'colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, '', [], {}]}
        return cleaned_data


class ListForm(ModalModelForm):
    columns = forms.ModelMultipleChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    order_by = forms.ModelChoiceField(label='Order By', required=False, queryset=models.DataField.objects.none())
    order_desc = forms.BooleanField(label='Descending Order', required=False)
    limit = forms.IntegerField(label='Limit', required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Row(
                FullWidth(Field('columns', css_class='select')),
            ),
            Row(
                HalfWidth(Field('order_by', css_class='select')), HalfWidth('limit'),
            ),
            Row(
                ThirdWidth('order_desc'), Field('attrs'),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['columns', 'order_by']:
            self.fields[field].queryset = field_queryset

        if 'columns' in attrs:
            self.fields['columns'].initial = field_queryset.filter(name__in=attrs['columns'])

        if 'order_by' in attrs:
            order_by, order_desc = (attrs['order_by'][1:], True) if attrs['order_by'][0] == '-' else (attrs['order_by'], False)
            self.fields['order_by'].initial = field_queryset.filter(name=order_by).first()
            self.fields['order_desc'].initial = order_desc

        if 'limit' in attrs:
            self.fields['limit'].initial = attrs['limit']

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        if 'columns' in cleaned_data and cleaned_data['columns'].exists():
            new_attrs['columns'] = [
                y.name for y in cleaned_data['columns'].order_by('position')
            ]
        if 'order_by' in cleaned_data and cleaned_data['order_by'] is not None:
            prefix = '-' if cleaned_data.get('order_desc') else ''
            new_attrs['order_by'] = f"{prefix}{cleaned_data['order_by'].name}"

        for field in ['limit']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class PieForm(ModalModelForm):
    value = forms.ModelChoiceField(label='Value', required=True, queryset=models.DataField.objects.none())
    label = forms.ModelChoiceField(label='Label', required=True, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=CATEGORICAL_COLORS, initial='Live8')

    class Meta:
        model = models.Entry
        fields = ('attrs', 'value', 'label', 'colors')
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Row(
                ThirdWidth(Field('value', css_class='select')),
                ThirdWidth(Field('label', css_class='select')),
                ThirdWidth(Field('colors', css_class='select')),
            ),
            Div(
                Field('attrs'),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['value', 'label']:
            self.fields[field].queryset = field_queryset

        for field in ['value', 'label']:
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()
        for field in ['colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['value', 'label']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name
        for field in ['colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class TimelineForm(ModalModelForm):
    min_time = forms.DateTimeField(label='Start Time', required=False)
    max_time = forms.DateTimeField(label='End Time', required=False)
    start_field = forms.ModelChoiceField(label='Event Start', required=True, queryset=models.DataField.objects.none())
    end_field = forms.ModelChoiceField(label='Event End', required=True, queryset=models.DataField.objects.none())
    label_field = forms.ModelChoiceField(label='Event Label', required=False, queryset=models.DataField.objects.none())
    type_field = forms.ModelChoiceField(label='Event Type', required=False, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=CATEGORICAL_COLORS, initial='Live8')

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
            'min_time': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'}),
            'max_time': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Row(
                QuarterWidth(Field('start_field', css_class='select')),
                QuarterWidth(Field('end_field', css_class='select')),
                QuarterWidth(Field('label_field', css_class='select')),
                QuarterWidth(Field('type_field', css_class='select')),
            ),
            Row(
                ThirdWidth(Field('min_time', css_class='datetime')),
                ThirdWidth(Field('max_time', css_class='datetime')),
                ThirdWidth(Field('colors', css_class='select')),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['start_field', 'end_field', 'label_field', 'type_field']:
            self.fields[field].queryset = field_queryset

        for field in ['start_field', 'end_field', 'label_field', 'type_field']:
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()
        for field in ['colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]
        for field in ['min_time', 'max_time']:
            if field in attrs:
                self.fields[field].initial = datetime.fromtimestamp(attrs[field]/1000)

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['start_field', 'end_field', 'label_field', 'type_field']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in ['min_time', 'max_time']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = int(cleaned_data[field].timestamp()*1000)

        for field in ['colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class RichTextForm(ModalModelForm):
    rich_text = forms.CharField(
        label='Rich Text', required=True, widget=forms.Textarea(attrs={'rows': 15}),
        help_text=_("Use markdown syntax to format the text")
    )

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Row(
                FullWidth('rich_text'),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['rich_text']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['rich_text']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class HistogramForm(ModalModelForm):
    values = forms.ModelChoiceField(label='Values', required=True, queryset=models.DataField.objects.none())
    bins = forms.IntegerField(label='Bins', required=False)
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=CATEGORICAL_COLORS, initial='Live8')

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Row(
                ThirdWidth(Field('values', css_class='select')),
                ThirdWidth('bins'),
                ThirdWidth(Field('colors', css_class='select')),
            ),
            Row(

                Field('attrs'),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['values']:
            self.fields[field].queryset = field_queryset
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()

        for field in ['bins', 'colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['values']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in ['bins', 'colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


MODE_CHOICES = (
    ('regions', 'Area'),
    ('markers', 'Bubbles'),
)

RESOLUTION_CHOICES = (
    ('countries', 'Countries'),
    ('provinces', 'Provinces'),
    ('metros', 'Metropolitan'),
)


class GeoCharForm(ModalModelForm):
    latitude = forms.ModelChoiceField(label='Latitude', required=False, queryset=models.DataField.objects.none())
    longitude = forms.ModelChoiceField(label='Longitude', required=False, queryset=models.DataField.objects.none())
    name = forms.ModelChoiceField(label='Name', required=False, queryset=models.DataField.objects.none())
    location = forms.ModelChoiceField(label='Location', required=False, queryset=models.DataField.objects.none())
    value = forms.ModelChoiceField(label='Values', required=True, queryset=models.DataField.objects.none())
    region = forms.ChoiceField(label='Map', choices=REGION_CHOICES, initial='world')
    resolution = forms.ChoiceField(label='Resolution', choices=RESOLUTION_CHOICES, required=True, initial='countries')
    mode = forms.ChoiceField(label='Mode', choices=MODE_CHOICES, required=True)
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=SEQUENTIAL_COLORS, initial='Blues')

    class Meta:
        model = models.Entry
        fields = (
            'attrs',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")
        self.update_initial()
        self.body.append(
            Row(
                ThirdWidth('latitude'),
                ThirdWidth('longitude'),
                ThirdWidth('name'),
            ),
            Row(
                ThirdWidth('location'),
                ThirdWidth('value'),
                ThirdWidth('colors'),
            ),
            Row(
                FullWidth(Field('region', css_class='selectize')),
                HalfWidth(Field('resolution', css_class='select')),
                HalfWidth(Field('mode', css_class='select')),
            ),
            Field('attrs'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['location', 'value', 'name', 'latitude', 'longitude']:
            self.fields[field].queryset = field_queryset

            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()

        for field in ['colors', 'region', 'resolution', 'mode']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        mode = cleaned_data.get('mode')
        invalid_markers = (
            mode == 'markers' and not
            all(cleaned_data.get(field) for field in ['latitude', 'longitude', 'name', 'value'])
        )
        invalid_regions = (
            mode == 'regions' and not
            all(cleaned_data.get(field) for field in ['location', 'value'])
        )
        if invalid_markers:
            raise forms.ValidationError(_("Latitude, Longitude, Name, and Value fields are required for Markers mode"))
        elif invalid_regions:
            raise forms.ValidationError(_("Location and Value fields are required for Area mode"))

        for field in ['location', 'value', 'name', 'latitude', 'longitude']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in ['colors', 'region', 'resolution', 'mode']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data

