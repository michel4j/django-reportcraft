import re
from collections import defaultdict
from random import choices
from typing import Any

from crispy_forms.layout import Div, Field
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from crisp_modals.forms import (
    ModalModelForm, HalfWidth, FullWidth, Row, ThirdWidth, QuarterWidth, ThreeQuarterWidth, TwoThirdWidth, ModalForm
)

from . import models, utils
from .models import DataSource
from .utils import MAP_CHOICES, AXIS_CHOICES, COLOR_SCHEMES

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
        fields = ('title', 'section', 'slug', 'description', 'theme', 'notes')
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
                QuarterWidth('section'), HalfWidth('slug'), QuarterWidth('theme'),
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
        self.fields['model'].queryset = ContentType.objects.filter(
            app_label__in=settings.REPORTCRAFT_APPS
        ).order_by('app_label', 'model')

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


class ImportEntryForm(ModalModelForm):
    entry = forms.ModelChoiceField(label="Entry to Import", queryset=models.Entry.objects.none())

    class Meta:
        model = models.Entry
        fields = ('report',)
        widgets = {
            'report': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entry'].queryset = models.Entry.objects.all().order_by('report__title', 'title')
        self.body.append(
            Row(
                FullWidth('entry'),
            ),
            'report'
        )

    def clean(self):
        cleaned_data = super().clean()
        copy_fields = (
            'title', 'description', 'notes', 'style', 'kind', 'source', 'position',
            'filters', 'attrs'
        )
        entry = cleaned_data.pop('entry')
        for field in copy_fields:
            cleaned_data[field] = getattr(entry, field)
        return cleaned_data


class EntryForm(ModalModelForm):
    class Meta:
        model = models.Entry
        fields = (
            'title', 'description', 'notes', 'style', 'kind', 'source', 'report', 'position',
            'filters'
        )
        widgets = {
            'title': forms.TextInput(),
            'description': forms.TextInput(),
            'notes': forms.Textarea(attrs={'rows': "2"}),
            'filters': forms.Textarea(attrs={'rows': "2"}),
            'report': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                Div(Field('filters', css_class="font-monospace"), css_class='col-12'),
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

        filters = cleaned_data.get('filters')
        if filters.strip() and source:
            source_fields = set(source.fields.values_list('name', flat=True))
            print(source_fields)
            try:
                parser = utils.FilterParser(identifiers=source_fields)
                parser.parse(filters)
            except ValueError as e:
                self.add_error('filters', _(f"Invalid filter: {e}"))

        return cleaned_data


PLOT_SERIES = 4
PLOT_TYPES = [
    ('points', 'Points'),
    ('points-filled', 'Filled Points'),
    ('line', 'Line'),
    ('line-points', 'Line & Points'),
    ('area', 'Area')
]

SCALE_CHOICES = [
    ('linear', 'Linear'),
    ('inverse', 'Reciprocal'),
    ('log', 'Logarithmic'),
    ('log2', 'Base-2 Logarithmic'),
    ('symlog', 'Symmetric Logarithmic'),
    ('square', 'Square'),
    ('inv-square', 'Inverse Square'),
    ('sqrt', 'Square Root'),
    ('cube', 'Cube'),
    ('inv-cube', 'Inverse Cube'),
    ('cube-root', 'Cube Root'),
    ('time', 'Time'),

]


class EntryConfigForm(ModalModelForm):
    SINGLE_FIELDS = ()
    MULTI_FIELDS = ()
    OTHER_FIELDS = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._single_fields = [*self.SINGLE_FIELDS]
        self._multi_fields = [*self.MULTI_FIELDS]
        self._other_fields = [*self.OTHER_FIELDS]
        self.add_fields()
        self.update_initial()
        self.body.title = _(f"Configure {self.instance.get_kind_display()}")

    def add_fields(self):
        """
        Dynamically Add fields to the form.
        """
        pass

    def update_initial(self):
        """
        Update the initial values of the form fields based on the instance's attributes.
        This method should be overridden in subclasses to set specific field initial values.
        """
        attrs = self.instance.attrs
        if self.instance.source:
            field_names = {
                field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')
            }
            field_queryset = self.instance.source.fields.order_by('name').filter(pk__in=field_names.values())
        else:
            field_queryset = DataSource.objects.none()

        for field in self._multi_fields:
            self.fields[field].queryset = field_queryset
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name__in=attrs[field])

        for field in self._single_fields:
            self.fields[field].queryset = field_queryset
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()

        for field in self._other_fields:
            if field in attrs:
                self.fields[field].initial = attrs[field]

        return attrs, field_queryset

    def initialize_groups(self, attrs: dict, queryset: Any, fields: list = None, count: int = PLOT_SERIES):
        """
        Initialize a grouped fields
        """
        group_fields = [] if not fields else fields
        for i in range(count):
            for key in group_fields:
                self.fields[f'groups__{i}__{key}'].queryset = queryset

        flat_groups = {
            f'groups__{i}__{k}': (k, v)
            for i, g in enumerate(attrs.get('groups', []))
            for k, v in g.items()
        }
        for field, (key, value) in flat_groups.items():
            if field not in self.fields:
                continue
            if key in group_fields:
                self.fields[field].initial = queryset.filter(name=value).first()
            else:
                self.fields[field].initial = value

    @staticmethod
    def clean_groups(data, required: list = None) -> dict:
        """
        Extract and clean grouped fields from the form data.
        :param data: The cleaned form data.
        :param required: List of required keys in each group. If None, no keys are required. Groups without any of the
        required keys will be removed.
        """
        required = set() if not required else set(required)
        groups = defaultdict(dict)
        for field, value in data.items():
            match = re.match(r'groups__(\d+)__(\w+)', field)
            if match:
                index = int(match.group(1))
                key = match.group(2)
                if isinstance(value, models.DataField):
                    value = value.name
                if value:
                    groups[index][key] = value

        data['attrs']['groups'] = [g for g in groups.values() if set(g.keys()) & set(required)]  # Remove empty groups
        return data

    def clean(self):
        """
        Clean the form data and prepare the attributes for saving.
        This method should be overridden in subclasses to handle specific field logic.
        """
        cleaned_data = super().clean()
        new_attrs = {}

        for field in self._multi_fields:
            if field in cleaned_data and cleaned_data[field].exists():
                new_attrs[field] = [y.name for y in cleaned_data[field].order_by('position')]

        for field in self._single_fields:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in self._other_fields:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, '', [], {}]}
        return cleaned_data


class TableForm(EntryConfigForm):
    columns = forms.ModelChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    rows = forms.ModelMultipleChoiceField(label='Rows', required=True, queryset=models.DataField.objects.none())
    values = forms.ModelChoiceField(label='Values', required=False, queryset=models.DataField.objects.none())
    total_column = forms.BooleanField(label="Row Totals", required=False)
    total_row = forms.BooleanField(label="Column Totals", required=False)
    force_strings = forms.BooleanField(label="Force Strings", required=False)
    flip_headers = forms.BooleanField(label="Flip Headers", required=False)
    wrap_headers = forms.BooleanField(label="Wrap Headers", required=False)
    transpose = forms.BooleanField(label="Transpose", required=False)
    max_cols = forms.IntegerField(label="Max Columns", required=False)

    SINGLE_FIELDS = ['columns', 'values']
    MULTI_FIELDS = ['rows']
    OTHER_FIELDS = [
        'total_row', 'total_column', 'force_strings', 'transpose', 'flip_headers',
        'wrap_headers', 'max_cols'
    ]

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
        self.body.append(
            Row(
                FullWidth('rows'),
                ThirdWidth('columns'),
                ThirdWidth('values'),
                ThirdWidth('max_cols'),
            ),
            Row(
                ThirdWidth('total_row'),
                ThirdWidth('total_column'),
                ThirdWidth('force_strings'),
                ThirdWidth('flip_headers'),
                ThirdWidth('wrap_headers'),
                ThirdWidth('transpose'),
            ),
            Row(
                Field('attrs'),
            ),
        )


class BarsForm(EntryConfigForm):
    categories = forms.ModelChoiceField(label='Categories', required=True, queryset=models.DataField.objects.none())
    values = forms.ModelMultipleChoiceField(label='Values', required=True, queryset=models.DataField.objects.none())
    color_by = forms.ModelChoiceField(label='Color By', required=False, queryset=models.DataField.objects.none())
    sort_by = forms.ModelChoiceField(label='Sort By', required=False, queryset=models.DataField.objects.none())
    grouped = forms.BooleanField(
        label='Type', required=False, initial=False,
        widget=forms.Select(choices=((True, 'Grouped'), (False, 'Stacked'))),
    )
    facets = forms.ModelChoiceField(label='Facets', required=False, queryset=models.DataField.objects.none())
    scheme = forms.ChoiceField(label='Color Scheme', required=False, choices=utils.COLOR_SCHEMES, initial='Live8')
    ticks_every = forms.IntegerField(label='Ticks Every', required=False, initial=1)
    sort_desc = forms.BooleanField(
        label="Sort Order", required=False, widget=forms.Select(choices=((True, 'Descending'), (False, 'Ascending'))),
        initial=False
    )
    normalize = forms.BooleanField(
        label='Normalize', required=False, initial=False, widget=forms.Select(choices=((True, 'Yes'), (False, 'No'))),
    )
    scale = forms.ChoiceField(label='Value Scale', required=False, choices=SCALE_CHOICES, initial='linear')
    limit = forms.IntegerField(label="Limit", required=False)

    SINGLE_FIELDS = ['categories', 'color_by', 'sort_by', 'facets']
    MULTI_FIELDS = ['values']
    OTHER_FIELDS = [
        'grouped', 'scheme', 'ticks_every', 'sort_desc', 'limit', 'scale', 'normalize'
    ]

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
        self.body.append(
            Row(
                QuarterWidth('categories'),
                ThreeQuarterWidth('values'),
            ),
            Row(
                QuarterWidth('grouped'),
                QuarterWidth('color_by'),
                QuarterWidth('scheme'),
                QuarterWidth('facets'),
            ),
            Row(
                ThirdWidth('sort_by'),
                ThirdWidth('sort_desc'),
                ThirdWidth('limit'),
            ),
            Row(
                ThirdWidth('scale'),
                ThirdWidth('ticks_every'),
                ThirdWidth('normalize')
            ),
            Div(
                Field('attrs'),
            ),
        )


class PlotForm(EntryConfigForm):
    x_label = forms.CharField(label='X Label', required=False)
    y_label = forms.CharField(label='Y Label', required=False)
    x_value = forms.ModelChoiceField(label='X-Value', required=True, queryset=models.DataField.objects.none())
    scheme = forms.ChoiceField(label='Color Scheme', required=False, choices=utils.CATEGORICAL_SCHEMES, initial='Live8')
    group_by = forms.ModelChoiceField(label='Group By', required=False, queryset=models.DataField.objects.none())
    precision = forms.IntegerField(label="Precision", required=False)
    x_scale = forms.ChoiceField(label='X Scale', required=False, choices=SCALE_CHOICES, initial='linear')
    y_scale = forms.ChoiceField(label='Y Scale', required=False, choices=SCALE_CHOICES, initial='linear')

    SINGLE_FIELDS = ['group_by', 'x_value']
    OTHER_FIELDS = ['x_label', 'y_label', 'scheme', 'precision', 'x_scale', 'y_scale']

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
        self.body.append(
            Row(
                ThirdWidth('x_value'),
                ThirdWidth('x_label'),
                ThirdWidth('y_label'),
                style='g-3'
            ),
            Row(
                ThirdWidth('group_by'),
                ThirdWidth('scheme'),
                ThirdWidth('precision'),
                style='g-3'
            ),
            Row(
                HalfWidth('x_scale'),
                HalfWidth('y_scale'),
                style='g-2'
            ),
        )
        for i in range(PLOT_SERIES):
            self.body.append(
                Row(
                    ThirdWidth(f'groups__{i}__y'),
                    ThirdWidth(f'groups__{i}__z'),
                    ThirdWidth(f'groups__{i}__type'),
                    style='g-3'
                ),
            )

    def add_fields(self):
        for i in range(PLOT_SERIES):
            self.fields[f'groups__{i}__y'] = forms.ModelChoiceField(
                label=f'Y-Value', required=False, queryset=models.DataField.objects.none()
            )
            self.fields[f'groups__{i}__z'] = forms.ModelChoiceField(
                label=f'Z-Value', required=False, queryset=models.DataField.objects.none()
            )
            self.fields[f'groups__{i}__type'] = forms.ChoiceField(label="Type", required=False, choices=PLOT_TYPES)

    def update_initial(self):
        attrs, queryset = super().update_initial()
        return self.initialize_groups(attrs, queryset, fields=['y', 'z'], count=PLOT_SERIES)

    def clean(self):
        cleaned_data = super().clean()
        return self.clean_groups(cleaned_data, required=['y'])


class ListForm(EntryConfigForm):
    columns = forms.ModelMultipleChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    order_by = forms.ModelChoiceField(label='Order By', required=False, queryset=models.DataField.objects.none())
    order_desc = forms.BooleanField(label='Descending Order', required=False)
    limit = forms.IntegerField(label='Limit', required=False)

    SINGLE_FIELDS = ['order_by']
    MULTI_FIELDS = ['columns']
    OTHER_FIELDS = ['order_desc', 'limit']

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


class PieForm(ModalModelForm):
    value = forms.ModelChoiceField(label='Value', required=True, queryset=models.DataField.objects.none())
    label = forms.ModelChoiceField(label='Label', required=True, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=utils.CATEGORICAL_SCHEMES, initial='Live8')

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


class TimelineForm(EntryConfigForm):
    min_time = forms.DateTimeField(label='Start Time', required=False)
    max_time = forms.DateTimeField(label='End Time', required=False)
    start_value = forms.ModelChoiceField(label='Event Start', required=True, queryset=models.DataField.objects.none())
    end_value = forms.ModelChoiceField(label='Event End', required=True, queryset=models.DataField.objects.none())
    labels = forms.ModelChoiceField(label='Labels', required=False, queryset=models.DataField.objects.none())
    color_by = forms.ModelChoiceField(label='Color By', required=False, queryset=models.DataField.objects.none())
    scheme = forms.ChoiceField(label='Color Scheme', required=False, choices=utils.CATEGORICAL_SCHEMES, initial='Live8')

    SINGLE_FIELDS = ['start_value', 'end_value', 'labels', 'color_by',]
    OTHER_FIELDS = ['min_time', 'max_time', 'scheme']

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
        self.body.append(
            Row(
                HalfWidth('start_value'),
                HalfWidth('end_value'),
                HalfWidth('labels'),
                HalfWidth('color_by'),
            ),
            Row(
                ThirdWidth('min_time'),
                ThirdWidth('max_time'),
                ThirdWidth('scheme'),
            ),
        )


class RichTextForm(EntryConfigForm):
    rich_text = forms.CharField(
        label='Rich Text', required=True, widget=forms.Textarea(attrs={'rows': 15}),
        help_text=_("Use markdown syntax to format the text")
    )

    OTHER_FIELDS = ['rich_text']

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
        self.body.append(
            Row(
                FullWidth('rich_text'),
            ),
        )


class HistogramForm(EntryConfigForm):
    values = forms.ModelChoiceField(label='Values', required=True, queryset=models.DataField.objects.none())
    group_by = forms.ModelChoiceField(label='Group By', required=False, queryset=models.DataField.objects.none())
    stack = forms.BooleanField(
        label='Stack Groups', required=False, initial=True,
        widget=forms.Select(choices=((True, 'Yes'), (False, 'No'))),
    )
    scheme = forms.ChoiceField(label='Color Scheme', required=False, choices=utils.CATEGORICAL_SCHEMES, initial='Live8')
    bins = forms.IntegerField(label='Bins', required=False)
    scale = forms.ChoiceField(label='Y-Scale', required=False, choices=SCALE_CHOICES, initial='linear')
    binning = forms.ChoiceField(
        label='Binning', required=False, initial='auto',
        choices=(
            ('auto', 'Auto'),
            ('freedman-diaconis', 'Freedman-Diaconis'),
            ('scott', 'Scott'),
            ('sturges', 'Sturges'),
            ('manual', 'Manual'),
        ),
    )

    SINGLE_FIELDS = ['values', 'group_by']
    OTHER_FIELDS = ['bins', 'scheme', 'binning', 'stack', 'scale']

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
        self.body.append(
            Row(
                HalfWidth('values'),HalfWidth('scale'),
                ThirdWidth('group_by'), ThirdWidth('scheme'), ThirdWidth('stack'),
                HalfWidth('binning'), HalfWidth('bins'),
            ),
            Row(

                Field('attrs'),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        attrs = cleaned_data['attrs']
        bins = attrs.get('bins')
        binning = attrs.get('binning')
        if binning == 'manual' and not bins:
            self.add_error('bins', _("Bins is required when Binning is set to Manual"))
        return cleaned_data


MODE_CHOICES = (
    ('', 'Select...'),
    ('area', 'Area'),
    ('bubble', 'Bubbles'),
    ('density', 'Density'),
    ('markers', 'Markers'),
)

MAP_LABELS = (
    ('', 'None'),
    ('names', 'Names'),
    ('codes', 'Codes'),
    ('places', 'Places'),
)


class GeoCharForm(EntryConfigForm):
    latitude = forms.ModelChoiceField(label='Latitude', required=False, queryset=models.DataField.objects.none())
    longitude = forms.ModelChoiceField(label='Longitude', required=False, queryset=models.DataField.objects.none())
    location = forms.ModelChoiceField(label='Location', required=False, queryset=models.DataField.objects.none())
    map = forms.ChoiceField(label='Map', choices=MAP_CHOICES, initial='001')
    map_labels = forms.ChoiceField(label='Labels', choices=MAP_LABELS, initial='', required=False)
    scheme = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_SCHEMES, initial='Blues')

    SINGLE_FIELDS = ['latitude', 'longitude', 'location']
    OTHER_FIELDS = ['map', 'map_labels', 'scheme']

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
        self.body.append(
            Row(
                ThirdWidth(Field('map', css_class='selectize')),
                ThirdWidth('map_labels'),
                ThirdWidth('scheme'),
            ),
            Row(
                ThirdWidth('location'),
                ThirdWidth('latitude'),
                ThirdWidth('longitude'),
                style='g-3'
            ),
            Field('attrs'),
        )
        for i in range(PLOT_SERIES):
            self.body.append(
                Row(
                    HalfWidth(f'groups__{i}__type'),
                    HalfWidth(f'groups__{i}__value'),
                ),
            )

    def add_fields(self):
        for i in range(PLOT_SERIES):
            self.fields[f'groups__{i}__type'] = forms.ChoiceField(label="Type", required=False, choices=MODE_CHOICES)
            self.fields[f'groups__{i}__value'] = forms.ModelChoiceField(
                label=f'Value', required=False, queryset=models.DataField.objects.none()
            )

    def update_initial(self):
        attrs, queryset = super().update_initial()
        return self.initialize_groups(attrs, queryset, fields=['value'])

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data = self.clean_groups(cleaned_data, required=['type', 'value'])
        attrs = cleaned_data['attrs']
        groups = attrs.get('groups', [])
        location_defined = bool(attrs.get('location'))
        coordinates_defined = attrs.get('latitude') and attrs.get('longitude')
        coordinates_required = any(
            group.get('type') in ['bubble', 'hex-bin', 'density', 'markers']
            for group in groups
        )
        location_required = any(
            group.get('type') in ['area']
            for group in groups
        )
        if location_required and not location_defined:
            self.add_error('location', _("Location is required for the selected Area features"))

        if coordinates_required and not coordinates_defined:
            self.add_error('latitude', _("Latitude and Longitude are required for the selected feature types"))
            self.add_error('longitude', _("Latitude and Longitude are required for the selected feature types"))

        if not location_defined and not coordinates_defined:
            self.add_error('location', _("Either Location or Latitude and Longitude are required"))

        return cleaned_data


class LikertForm(EntryConfigForm):
    questions = forms.ModelChoiceField(label='Questions', required=True, queryset=models.DataField.objects.none())
    answers = forms.ModelChoiceField(label='Answers', required=True, queryset=models.DataField.objects.none())
    counts = forms.ModelChoiceField(label='Counts', required=False, queryset=models.DataField.objects.none())
    scores = forms.ModelChoiceField(label='Scores', required=False, queryset=models.DataField.objects.none())

    facets = forms.ModelChoiceField(label='Facets', required=False, queryset=models.DataField.objects.none())
    scheme = forms.ChoiceField(label='Color Scheme', required=False, choices=utils.DIVERGENT_SCHEMES, initial='RdBu')
    normalize = forms.BooleanField(
        label='Normalize', required=False, initial=False, widget=forms.Select(choices=((True, 'Yes'), (False, 'No'))),
    )

    SINGLE_FIELDS = ['questions', 'answers', 'counts', 'scores', 'facets']
    OTHER_FIELDS = [
        'scheme',
    ]

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
        self.body.append(
            Row(
                HalfWidth('questions'), HalfWidth('answers'),
                HalfWidth('counts'), HalfWidth('scores'),
            ),
            Row(

                ThirdWidth('facets'), ThirdWidth('scheme'), ThirdWidth('normalize'),
            ),
            Div(
                Field('attrs'),
            ),
        )