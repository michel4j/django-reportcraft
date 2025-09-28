from __future__ import annotations

import itertools
import logging
import re
import traceback
import uuid
from typing import Any

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet, Q
from django.db.models.functions import Round, Abs, Sign
from django.utils.text import slugify, gettext_lazy as _

import reportcraft.functions
from . import utils, entries


logger = logging.getLogger('reportcraft')

VALUE_TYPES = {
    'STRING': str,
    'INTEGER': int,
    'FLOAT': float,
}


ENTRY_ERROR_TEMPLATE = """
### Error: {error_type}!

An error occurred while generating this entry.
Please check the configuration!

```Python
{error}
```
"""

DATA_ERROR_TEMPLATE = """
Error: {error_type}!

An error occurred while generating this data.
Please check the configuration!

-----------------------------------------
{error}

"""


class CodeManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)


class DataSource(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    code = models.SlugField(max_length=100, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    description = models.TextField(default='', blank=True)
    group_by = models.JSONField(_("Group Fields"), default=list, blank=True, null=True)
    filters = models.TextField(default="", blank=True)
    limit = models.IntegerField(null=True, blank=True)

    objects = CodeManager()

    class Meta:
        verbose_name = 'Data Source'

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.code,)

    def clone(self):
        """Make a copy of this data source, including all models and fields"""
        clone = DataSource.objects.get(pk=self.pk)
        clone.pk = None
        clone.code = None
        clone.name = f'{self.name} (copy)'
        clone.save()

        model_mapping = {}
        for model in self.models.all():
            model_clone = DataModel.objects.get(pk=model.pk)
            model_clone.pk = None
            model_clone.source = clone
            model_clone.save()
            model_mapping[model.pk] = model_clone

        for field in self.fields.all():
            field_clone = DataField.objects.get(pk=field.pk)
            field_clone.pk = None
            field_clone.source = clone
            field_clone.model = model_mapping.get(field.model.pk, None)
            field_clone.save()

        return clone

    def name_slug(self):
        return slugify(self.name)

    def reports(self):
        return Report.objects.filter(pk__in=self.entries.values_list('report__pk', flat=True)).order_by('-modified')

    def groups_fields(self):
        return self.fields.filter(name__in=self.group_by)

    def non_group_fields(self):
        return self.fields.exclude(name__in=self.group_by)

    def get_filters(self):
        parser = utils.FilterParser()
        if self.filters:
            return parser.parse(self.filters, silent=True)
        else:
            return Q()

    def get_labels(self):
        return {field.name: field.label for field in self.fields.all()}

    def clean_filters(self, filters: dict) -> dict:
        """
        Clean the filters to ensure they only contain valid field names defined in the data source
        :param filters: dictionary of filters
        :return: cleaned filters
        """
        valid_fields = set(self.fields.values_list('name', flat=True))
        return {
            k: v for k, v in filters.items()
            if k.split('__')[0] in valid_fields and k.count('__') < 2       # Only allow one level of lookups
        }

    def get_queryset(
            self,
            model_name,
            filters: dict = None,
            select: Q = None,
            order_by: list = None
    ) -> QuerySet:
        """
        Generate a queryset for the given model name with the specified filters and order by fields.
        :param model_name: the name of the model to query
        :param filters: dynamic filters to apply
        :param select: additional Q object to apply as filter to select a subset of data
        :param order_by: order by fields
        :return: a queryset for the specified model with applied annotations, filters and ordering
        """

        filters = {} if not filters else filters
        order_by = [] if not order_by else order_by

        model: Any = apps.get_model(model_name)
        field_names = [f.name for f in model._meta.get_fields()]

        # Add annotations
        group_by = list(self.group_by)
        annotate_filter = {'name__in': group_by} if group_by else {}
        annotations = {
            field.name: field.get_expression()
            for field in self.fields.exclude(name__in=field_names).filter(model__name=model_name, **annotate_filter)
        }

        # Add aggregations and handle grouping
        aggregations = {}
        if group_by:
            aggregations = {
                field.name: field.get_expression()
                for field in self.fields.exclude(name__in=field_names).exclude(name__in=group_by).filter(model__name=model_name)
            }

        # Ordering
        order_fields = self.fields.annotate(
            order_by=Abs('ordering')
        ).filter(ordering__isnull=False).order_by('order_by').values_list(Sign('ordering'), 'name', )
        order_by: list = order_by or [f'-{name}' if sign < 0 else name for sign, name in order_fields]

        # Apply static filters
        static_filters = self.get_filters()
        select_filters = (select if select else Q())
        dynamic_filters = Q(**self.clean_filters(filters))

        # generate the queryset
        queryset = model.objects.annotate(
            **annotations
        ).values(*group_by).annotate(
            **aggregations
        ).order_by(*order_by).filter(
            static_filters & dynamic_filters & select_filters
        )
        # Apply limit
        if self.limit:
            queryset = queryset[:self.limit]

        return queryset

    def get_source_data(self, filters=None, select=None, order_by=None) -> list[dict]:
        """
        Generate data for this data source
        :param filters: dynamic filters
        :param select: additional Q object to apply as filter to select a subset of data
        :param order_by: order by fields

        """

        data = []
        model_names = set(self.fields.values_list('model__name', flat=True))
        for model_name in model_names:
            queryset = self.get_queryset(model_name, filters=filters, select=select, order_by=order_by)
            field_names = [field.name for field in self.fields.filter(model__name=model_name).all()]
            data.extend(list(queryset.values(*field_names)))

        if self.group_by:
            data = utils.merge_data(data, unique=self.group_by)

        return data

    @utils.cached_model_method(duration=1)
    def get_data(self, filters=None, select=None, order_by=None) -> list[dict]:
        """
        Cached wrapper of get_source_data.
        :param filters: dynamic filters
        :param select: additional Q object to apply as filter to select a subset of data
        :param order_by: order by fields
        """
        return self.get_source_data(filters=filters, select=select, order_by=order_by)

    def get_precision(self, field_name: str) -> int:
        """
        Get the precision for a field in this data source
        :param field_name: the name of the field
        """
        try:
            field = self.fields.get(name=field_name)
            return field.precision if field.precision is not None else 0
        except DataField.DoesNotExist:
            return 0

    def snippet(self, filters=None, order_by=None, size=50) -> tuple[list[dict], int]:
        """
        Generate a snippet of data for this data source
        :param filters: dynamic filters to apply
        :param order_by: order by fields
        :param size: number of items to return
        :return: a tuple of (data snippet, total number of items)
        """
        try:

            data = self.get_source_data(filters=filters, order_by=order_by)
            total = len(data)
            result = data[:size]
        except Exception as e:
            logger.exception(e)
            result = DATA_ERROR_TEMPLATE.format(error=traceback.format_exc(), error_type=type(e).__name__)
            total = 0
        return result, total


class DataModel(models.Model):
    """
    Model definition for DataModel. This model is used to define allowed data models
    and corresponding fields for the reportcraft app.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    code = models.SlugField(max_length=100, unique=True, editable=False, default=uuid.uuid4)
    model = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='models')

    objects = CodeManager()

    class Meta:
        verbose_name = 'Data Model'

    def natural_key(self):
        return (self.code,)

    def get_group_fields(self):
        group_names = list(self.source.group_by)
        if group_names:
            fields = {
                field.name: field for field in self.fields.all()
            }
            return {name: fields.get(name, None) for name in group_names}
        return {}

    def has_field(self, field_name: str) -> bool:
        """
        Check if the underlying model has a field with the given name
        :param field_name: the name of the field
        """
        model = self.model.model_class()
        return any(f.name == field_name for f in model._meta.get_fields())

    def get_field_spec(self, field, parent: str = None, depth: int = 0) -> list[tuple]:
        """
        Get the field specification for a given field
        :param field: the field name
        :param parent: optional parent field name for nested fields
        :param depth: current recursion depth (used to prevent infinite recursion)
        :return: dictionary with field specifications
        """
        spec = '__'.join([parent, field.name] if parent else [field.name])
        field_type = field.get_internal_type()
        disallowed_types = [
            'AutoField', 'BigAutoField', 'UUIDField', 'BinaryField', 'FileField', 'ImageField', 'ForeignKey',
            'GenericForeignKey', 'GenericRelation', 'OneToOneRel', 'ManyToManyField', 'ManyToOneRel', 'OneToOneField'
        ]

        if isinstance(field, (models.OneToOneField, models.ForeignKey, models.ManyToManyField)):
            return self.get_model_specs(field.related_model, parent=spec, depth=depth + 1)
        elif field_type not in disallowed_types:
            return [(utils.sanitize_field(spec), utils.FIELD_TYPES.get(field_type, field_type.replace('Field', '')))]
        return []

    def get_model_specs(self, model=None, parent: str = None, depth: int = 0, max_depth: int = 3) -> list[tuple]:
        """
        Get the field specifications for this model
        :param model: optional model class to inspect
        :param parent: optional parent field name for nested fields
        :param depth: current recursion depth (used to prevent infinite recursion)
        :param max_depth: maximum recursion depth to prevent infinite loops
        :return: list of field names and types
        """
        starting_model = self.model.model_class()
        if model is None:
            model = starting_model
        if depth >= max_depth or model is None:
            return []
        return list(
            itertools.chain.from_iterable(
                (self.get_field_spec(sub_field, parent, depth) for sub_field in model._meta.get_fields())
            )
        )

    def __str__(self):
        app, name = self.name.split('.')
        return f'{app}.{name.title()}'


class DataField(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.SlugField(max_length=50)
    code = models.SlugField(max_length=100, unique=True, editable=False, default=uuid.uuid4)
    model = models.ForeignKey(DataModel, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=100, null=True)
    default = models.JSONField(null=True, blank=True)
    expression = models.TextField(default="", blank=True)
    precision = models.IntegerField(null=True, blank=True)
    position = models.IntegerField(default=0)
    ordering = models.IntegerField(null=True, blank=True)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='fields')

    objects = CodeManager()

    class Meta:
        verbose_name = 'Data Field'
        unique_together = ['name', 'source', 'model']
        ordering = ['source', 'position', 'pk']

    def natural_key(self):
        return (self.code,)

    def __str__(self):
        return self.label

    def get_expression(self):
        parser = utils.ExpressionParser()
        if self.expression:
            db_expression = parser.parse(self.expression)
            if isinstance(db_expression, reportcraft.functions.DisplayName):
                db_expression = reportcraft.functions.ChoiceName(self.model.name, db_expression.name)
            if self.precision is not None:
                db_expression = Round(db_expression, self.precision)
            return db_expression
        return None


class Report(models.Model):
    class Themes(models.TextChoices):
        DEFAULT = 'default', _('Default')
        SKETCH = 'sketch', _('Sketch')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=128, unique=True)
    code = models.SlugField(max_length=100, unique=True, editable=False, default=uuid.uuid4)
    title = models.TextField()
    description = models.TextField(default='', blank=True)
    theme = models.CharField(max_length=20, choices=Themes.choices, default=Themes.DEFAULT)
    notes = models.TextField(default='', blank=True)
    section = models.SlugField(max_length=100, default='', blank=True, null=True)

    objects = CodeManager()

    def __str__(self):
        return self.title if not self.section else f'{self.section.upper()} / {self.title}'

    def natural_key(self):
        return (self.code,)

    def clone(self):
        """Make a copy of this report, including all entries"""
        clone = Report.objects.get(pk=self.pk)
        clone.pk = None
        clone.code = None
        clone.title = f'{self.title} (copy)'
        if m := re.match(r'.+-(\d+)$', clone.slug):
            number = int(m.group(1)) + 1
            clone.slug = re.sub(r'-(\d+)$', f'-{number}', clone.slug)
        else:
            clone.slug = f'{clone.slug}-1'
        clone.save()
        for entry in self.entries.all():
            entry.clone(report=clone)
        return clone


class Entry(models.Model):
    class Types(models.TextChoices):
        BARS = 'bars', _('Bar Chart')
        COLUMNS = 'columns', _('Column Chart')
        DONUT = 'donut', _('Donut Chart')
        HISTOGRAM = 'histogram', _('Histogram')
        LIST = 'list', _('List')
        MAP = 'map', _('Map Chart')
        PIE = 'pie', _('Pie Chart')
        TEXT = 'text', _('Rich Text')
        TABLE = 'table', _('Table')
        TIMELINE = 'timeline', _('Timeline')
        PLOT = 'plot', _('XY Plot')
        LIKERT = 'likert', _('Likert Scale')

    class Widths(models.TextChoices):
        QUARTER = "col-md-3", _("One Quarter")
        THIRD = "col-md-4", _("One Third")
        HALF = "col-md-6", _("Half")
        TWO_THIRDS = "col-md-8", _("Two Thirds")
        THREE_QUARTERS = "col-md-9", _("Three Quarters")
        FULL = "col-md-12", _("Full Width")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    code = models.SlugField(max_length=100, unique=True, editable=False, default=uuid.uuid4)
    title = models.TextField(default='', blank=True)
    description = models.TextField(default='', blank=True)
    notes = models.TextField(default='', blank=True)
    style = models.CharField(_("Width"), max_length=100, choices=Widths.choices, default=Widths.FULL, blank=True)
    kind = models.CharField(_("Type"), max_length=50, choices=Types.choices, default=Types.TABLE)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='entries', null=True, blank=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='entries')
    position = models.IntegerField(default=0)
    filters = models.TextField(default="", blank=True)
    attrs = models.JSONField(default=dict, blank=True)

    objects = CodeManager()

    class Meta:
        verbose_name_plural = 'Entries'
        ordering = ['report', 'position']

    def natural_key(self):
        return (self.code,)

    def __str__(self):
        short_report_title = (self.report.title[:20] + '...') if len(self.report.title) > 20 else self.report.title
        kind = self.get_kind_display()
        return f'{short_report_title} - {self.title} ({kind[:2]})'

    GENERATORS = {
        Types.DONUT: entries.generate_donut,
        Types.PIE: entries.generate_pie,
        Types.BARS: entries.generate_bars,
        Types.TABLE: entries.generate_table,
        Types.LIST: entries.generate_list,
        Types.PLOT: entries.generate_plot,
        Types.HISTOGRAM: entries.generate_histogram,
        Types.TIMELINE: entries.generate_timeline,
        Types.TEXT: entries.generate_text,
        Types.MAP: entries.generate_geochart,
        Types.COLUMNS: entries.generate_columns,
        Types.LIKERT: entries.generate_likert,
    }

    def get_filters(self):
        parser = utils.FilterParser()
        if self.filters:
            return parser.parse(self.filters, silent=True)
        else:
            return Q()

    def generate(self, **kwargs):
        try:
            generator = self.GENERATORS.get(self.kind, None)
            if not generator:
                raise ValueError(f"Unsupported entry type: {self.kind}")
            return generator(self, **kwargs)
        except Exception as e:
            logger.exception(e)
            return {
                'title': self.title,
                'description': self.description,
                'kind': 'richtext',
                'style': self.style,
                'text': ENTRY_ERROR_TEMPLATE.format(error=traceback.format_exc(), error_type=type(e).__name__),
                'notes': self.notes
            }

    def clone(self, report: Report = None) -> Entry:
        """
        Clone this entry and associate it with a new report if provided, otherwise keep the same report
        :param report: the new report to associate the cloned entry with
        :return: the cloned entry
        """
        clone = Entry.objects.get(pk=self.pk)
        clone.pk = None
        if report:
            clone.report = report
        else:
            clone.title = f'{self.title} (copy)'
        clone.save()
        return clone


