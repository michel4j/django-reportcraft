import re

from datetime import datetime
from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from crisp_modals.forms import (
    ModalModelForm, HalfWidth, FullWidth, Row, ThirdWidth, QuarterWidth,
)

from . import models
from .utils import COLOR_CHOICES


disabled_widget = forms.HiddenInput(attrs={'readonly': True})


class ThreeQuarterWidth(Div):
    def __init__(self, *args,  style="", **kwargs):
        super().__init__(*args, css_class=f"col-9 {style}", **kwargs)

class TwoThirdWidth(Div):
    def __init__(self, *args,  style="", **kwargs):
        super().__init__(*args, css_class=f"col-8 {style}", **kwargs)


class ReportForm(ModalModelForm):
    class Meta:
        model = models.Report
        fields = ('title', 'slug', 'description', 'style', 'notes')
        widgets = {
            'title': forms.TextInput,
            'description': forms.Textarea(attrs={'rows': "2"}),
            'notes': forms.Textarea(attrs={'rows': "4"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.body.form_action = reverse_lazy('edit-report', kwargs={"pk": self.instance.pk})
        else:
            self.body.form_action = reverse_lazy('new-report')

        self.body.append(
            Row(
                FullWidth('title'),
            ),
            Row(
                HalfWidth('slug'), HalfWidth('style'),
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
            self.body.title = _("Edit Field")
            self.body.form_action = reverse_lazy(
                'edit-source-field', kwargs={'pk': pk, 'source': self.instance.source.pk}
            )
            self.fields['model'].queryset = self.instance.source.models.all()
        else:
            self.body.title = _("Add Field")
            self.body.form_action = reverse_lazy(
                'add-source-field', kwargs={'source': self.initial['source']}
            )
            self.fields['model'].queryset = models.DataModel.objects.filter(source=self.initial['source'])

        self.footer.layout = Layout()
        self.body.layout = Layout(
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
                Div('expression', css_class='col-12'),
                Field('source'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )


class DataSourceForm(ModalModelForm):
    group_fields = forms.CharField(required=False, help_text=_("Comma separated list of field names to group by"))

    class Meta:
        model = models.DataSource
        fields = (
            'name', 'group_by', 'limit', 'group_fields'
        )
        widgets = {
            'group_by': forms.HiddenInput,
        }
        help_texts = {
            'limit': _("Maximum number of records"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pk = self.instance.pk

        if pk:
            self.body.title = u"Edit Data Source"
            self.body.form_action = reverse_lazy('edit-data-source', kwargs={'pk': pk})
            self.fields['group_fields'].initial = ', '.join(self.instance.group_by)
        else:
            self.body.title = u"Add Data Source"
            self.body.form_action = reverse_lazy('new-data-source')

        self.body.layout = Layout(
            Div(
                Div('name', css_class='col-12'),
                Div('group_fields', css_class='col-8'),
                Div('limit', css_class='col-4'),
                css_class='row'
            ),
        )

    def clean(self):
        data = super().clean()
        group_fields = data.pop('group_fields', "")
        data['group_by'] = re.split(r'\s*[,;|]\s*', group_fields) if group_fields else []
        return data


class DataModelForm(ModalModelForm):
    class Meta:
        model = models.DataModel
        fields = ('model', 'source', 'name')
        widgets = {
            'source': forms.HiddenInput,
            'name': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        self.source = kwargs.pop('source')
        super().__init__(*args, **kwargs)
        pk = self.instance.pk

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

        if pk:
            self.body.title = _("Edit Data Model")
            self.body.form_action = reverse_lazy('edit-source-model', kwargs={'pk': pk, 'source': self.source.pk})
        else:
            self.body.title = _("Add Data Model")
            self.body.form_action = reverse_lazy('add-source-model', kwargs={'source': self.source.pk})

        extra_div = Div(*[Div(field, css_class='col-12') for field in self.extra_fields.values()], css_class='row')
        self.body.layout = Layout(
            Div(
                Div('model', css_class='col-12'),
                css_class='row'
            ),
            extra_div,
            Field('source'),
            Field('name'),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
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

        if pk:
            self.body.title = _("Edit Entry")
            self.body.form_action = reverse_lazy(
                'edit-report-entry', kwargs={'pk': pk, 'report': self.instance.report.pk}
            )
        else:
            if 'report' in self.initial:
                self.body.title = _("Add Entry to {}".format(self.initial['report']))
                self.body.form_action = reverse_lazy(
                    'add-report-entry', kwargs={'report': self.initial['report']}
                )
            self.body.title = _("Add Entry")

        self.body.layout = Layout(
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
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
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
            'attrs', 'columns', 'rows', 'values', 'total_row', 'total_column', 'force_strings', 'transpose',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body.title = _("Configure Table")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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

    color_field = forms.ModelChoiceField(label='Color By', required=False, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')
    line = forms.ModelChoiceField(label='Line', required=False, queryset=models.DataField.objects.none())
    x_culling = forms.IntegerField(label="Culling", required=False)
    wrap_x_labels = forms.BooleanField(label="Wrap Labels", required=False)
    aspect_ratio = forms.FloatField(label="Aspect Ratio", required=False)
    vertical = forms.BooleanField(label="Vertical Bars", required=False)

    sort_by = forms.ModelChoiceField(label='Sort By', required=False, queryset=models.DataField.objects.none())
    sort_desc = forms.BooleanField(label="Sort Descending", required=False)
    limit = forms.IntegerField(label="Limit", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'x_axis', 'y_axis', 'y_value', 'stack_0', 'stack_1', 'stack_2', 'color_field', 'line',
            'x_culling', 'wrap_x_labels', 'aspect_ratio', 'sort_by', 'sort_desc', 'vertical', 'limit',
            'colors'
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body.title = _("Configure Barchart")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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
                Div('aspect_ratio', css_class='col-3'),
                Div('x_culling', css_class='col-3'),
                Div('limit', css_class='col-3'),
                Div(Field('line', css_class='select'), css_class='col-3'),
                css_class='row'
            ),
            Div(
                Div(Field('stack_0', css_class='select'), css_class='col-12'),
                Div(Field('stack_1', css_class='select'), css_class='col-12'),
                Div(Field('stack_2', css_class='select'), css_class='col-12'),
                css_class='row'
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
        for field in ['x_axis', 'y_axis', 'y_value', 'stack_0', 'stack_1', 'stack_2', 'color_field', 'line', 'sort_by']:
            self.fields[field].queryset = field_queryset

        for field in ['x_axis', 'y_value', 'line', 'color_field', 'sort_by']:
            if field in attrs:
                self.fields[field].initial = field_queryset.filter(name=attrs[field]).first()
        if 'y_axis' in attrs:
            self.fields['y_axis'].initial = field_queryset.filter(name__in=attrs['y_axis'])

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

        for field in ['x_axis', 'y_value', 'line', 'color_field', 'sort_by']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        if 'y_axis' in cleaned_data and cleaned_data['y_axis'].exists():
            new_attrs['y_axis'] = [y.name for y in cleaned_data['y_axis'].order_by('position')]

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


class PlotForm(ModalModelForm):
    x_axis = forms.ModelChoiceField(label='X-axis', required=True, queryset=models.DataField.objects.none())
    y1_axis = forms.ModelMultipleChoiceField(label='Y1-axis', required=True, queryset=models.DataField.objects.none())
    y2_axis = forms.ModelMultipleChoiceField(label='Y2-axis', required=False, queryset=models.DataField.objects.none())
    y1_label = forms.CharField(label='Y1 Label', required=False)
    y2_label = forms.CharField(label='Y2 Label', required=False)
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    tick_precision = forms.IntegerField(label="Precision", required=False)
    scatter = forms.BooleanField(label="Scatter Plot", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'x_axis', 'y1_axis', 'y1_axis', 'y2_axis', 'y2_label', 'tick_precision', 'scatter', 'colors'
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _("Configure Plot")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.append(
            Row(
                ThirdWidth(Field('x_axis', css_class='select')),
                ThirdWidth('tick_precision'),
                ThirdWidth(Field('colors', css_class='select')),
            ),
            Row(
                ThirdWidth('y1_label'),
                TwoThirdWidth(Field('y1_axis', css_class='select')),
            ),
            Row(
                ThirdWidth('y2_label'),
                TwoThirdWidth(Field('y2_axis', css_class='select')),
            ),
            Row(
                ThirdWidth('scatter'), Field('attrs'),
            ),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        field_ids = {field['name']: field['pk'] for field in self.instance.source.fields.values('name', 'pk')}
        field_queryset = self.instance.source.fields.filter(pk__in=field_ids.values())
        for field in ['x_axis', 'y1_axis', 'y2_axis']:
            self.fields[field].queryset = field_queryset

        if 'x_axis' in attrs:
            self.fields['x_axis'].initial = field_queryset.filter(name=attrs['x_axis']).first()

        if 'y_axis' in attrs:
            for i, y_group in enumerate(attrs['y_axis']):
                self.fields[f'y{i + 1}_axis'].initial = field_queryset.filter(name__in=y_group)

        for field in ['y1_label', 'y2_label', 'tick_precision', 'scatter', 'aspect_ratio', 'colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {
            'y_axis': []
        }

        for field in ['x_axis']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for i in range(2):
            if f'y{i + 1}_axis' in cleaned_data and cleaned_data[f'y{i + 1}_axis'].exists():
                new_attrs[f'y_axis'].append([y.name for y in cleaned_data[f'y{i + 1}_axis']])

        for field in ['y1_label', 'y2_label', 'tick_precision', 'scatter', 'colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class ListForm(ModalModelForm):
    columns = forms.ModelMultipleChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    order_by = forms.ModelChoiceField(label='Order By', required=False, queryset=models.DataField.objects.none())
    order_desc = forms.BooleanField(label='Descending Order', required=False)
    limit = forms.IntegerField(label='Limit', required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'columns', 'limit', 'order_by', 'order_desc'
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _("Configure List")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    class Meta:
        model = models.Entry
        fields = ('attrs', 'value', 'label', 'colors')
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body.title = _("Configure Pie")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'min_time', 'max_time', 'start_field', 'end_field', 'label_field', 'type_field', 'colors',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
            'min_time': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'}),
            'max_time': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _("Configure Timeline")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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
            'attrs', 'rich_text',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body.title = _("Configure Rich Text")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'values', 'bins', 'colors',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.title = _("Configure Histogram")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
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

