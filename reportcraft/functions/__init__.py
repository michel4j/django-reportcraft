from __future__ import annotations

import datetime
import itertools

import numpy
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Window, Sum, F, Case, When, Value as V, TextField, CharField, Count
from django.db.models.expressions import RowRange
from django.utils import timezone

SHIFT = 8
SHIFT_DURATION = '{:d} hour'.format(SHIFT)
OFFSET = -timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone()).utcoffset().total_seconds()


def _get_active_datetime() -> datetime.datetime:
    """Returns the current aware datetime in Django's active timezone."""
    return timezone.localtime() if getattr(settings, 'USE_TZ', False) else timezone.now()


def _get_active_date() -> datetime.date:
    """Returns the current calendar date in Django's active timezone."""
    return timezone.localdate() if getattr(settings, 'USE_TZ', False) else datetime.date.today()


class ThisYear(models.Value):
    """Current calendar year in Django's active timezone as an IntegerField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = _get_active_date().year
        if output_field is None:
            output_field = models.IntegerField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class ThisMonth(models.Value):
    """Current calendar month (1-12) in Django's active timezone as an IntegerField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = _get_active_date().month
        if output_field is None:
            output_field = models.IntegerField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class ThisQuarter(models.Value):
    """Current calendar quarter (1-4) in Django's active timezone as an IntegerField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = (_get_active_date().month - 1) // 3 + 1
        if output_field is None:
            output_field = models.IntegerField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class ThisDay(models.Value):
    """Current day of the month (1-31) in Django's active timezone as an IntegerField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = _get_active_date().day
        if output_field is None:
            output_field = models.IntegerField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class ThisWeek(models.Value):
    """Current ISO week number (1-53) in Django's active timezone as an IntegerField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = _get_active_date().isocalendar().week
        if output_field is None:
            output_field = models.IntegerField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class Today(models.Value):
    """Current calendar date in Django's active timezone as a DateField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = _get_active_date()
        if output_field is None:
            output_field = models.DateField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class Now(models.Value):
    """Current datetime in Django's active timezone as a DateTimeField Value."""
    def __init__(self, value=None, output_field=None, **extra):
        if value is None:
            value = _get_active_datetime()
        if output_field is None:
            output_field = models.DateTimeField()
        super().__init__(value, output_field=output_field, **extra)
        self._constructor_args = ((value,), {'output_field': self.output_field, **extra})


class Age(models.Func):
    """Calculates interval/duration from field to now."""
    output_field = models.DurationField()

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="AGE(%(expressions)s)", **extra_context)

    def as_mysql(self, compiler, connection, **extra_context):
        # TIMEDIFF returns a time/duration interval up to ~838 hours
        return self.as_sql(compiler, connection, template="TIMEDIFF(NOW(), %(expressions)s)", **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        # SQLite stores epoch differences; in microseconds to match Django DurationField conventions
        return self.as_sql(
            compiler,
            connection,
            template="CAST((julianday('now') - julianday(%(expressions)s)) * 86400000000 AS INTEGER)",
            **extra_context,
        )

    def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="NUMTODSINTERVAL(SYSDATE - %(expressions)s, 'DAY')", **extra_context)


class AgeInYears(models.Func):
    """Calculates full years between field and current date."""
    output_field = models.IntegerField()

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="EXTRACT(YEAR FROM AGE(%(expressions)s))::integer", **extra_context)

    def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="TIMESTAMPDIFF(YEAR, %(expressions)s, CURDATE())", **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template=(
                "CAST(strftime('%%%%Y', 'now', 'localtime') AS INTEGER) - CAST(strftime('%%%%Y', %(expressions)s) AS INTEGER) - "
                "(strftime('%%%%m-%%%%d', 'now', 'localtime') < strftime('%%%%m-%%%%d', %(expressions)s))"
            ),
            **extra_context,
        )

    def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="TRUNC(MONTHS_BETWEEN(TRUNC(SYSDATE), %(expressions)s) / 12)",
            **extra_context,
        )


class AgeInMonths(models.Func):
    """Calculates full months between field and current date."""
    output_field = models.IntegerField()

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="(EXTRACT(YEAR FROM AGE(%(expressions)s)) * 12 + EXTRACT(MONTH FROM AGE(%(expressions)s)))::integer",
            **extra_context,
        )

    def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="TIMESTAMPDIFF(MONTH, %(expressions)s, CURDATE())", **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template=(
                "(CAST(strftime('%%%%Y', 'now', 'localtime') AS INTEGER) - CAST(strftime('%%%%Y', %(expressions)s) AS INTEGER)) * 12 + "
                "CAST(strftime('%%%%m', 'now', 'localtime') AS INTEGER) - CAST(strftime('%%%%m', %(expressions)s) AS INTEGER) - "
                "(strftime('%%%%d', 'now', 'localtime') < strftime('%%%%d', %(expressions)s))"
            ),
            **extra_context,
        )

    def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="TRUNC(MONTHS_BETWEEN(TRUNC(SYSDATE), %(expressions)s))",
            **extra_context,
        )


class AgeInDays(models.Func):
    """Calculates total days between field and current date."""
    output_field = models.IntegerField()

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="(CURRENT_DATE - (%(expressions)s)::date)", **extra_context)

    def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="DATEDIFF(CURDATE(), %(expressions)s)", **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="CAST(julianday('now') - julianday(%(expressions)s) AS INTEGER)",
            **extra_context,
        )

    def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="TRUNC(SYSDATE - %(expressions)s)", **extra_context)


class YearQuarter(models.Func):
    """Formats date/datetime into 'YYYY-QX' string."""
    output_field = models.CharField(max_length=7)

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="CONCAT(TO_CHAR(%(expressions)s, 'YYYY'), '-Q', TO_CHAR(%(expressions)s, 'Q'))",
            **extra_context,
        )

    def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="CONCAT(DATE_FORMAT(%(expressions)s, '%%%%Y-Q'), QUARTER(%(expressions)s))",
            **extra_context,
        )

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template=(
                "strftime('%%%%Y-Q', %(expressions)s) || "
                "((CAST(strftime('%%%%m', %(expressions)s) AS INTEGER) + 2) / 3)"
            ),
            **extra_context,
        )

    def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="TO_CHAR(%(expressions)s, 'YYYY-\"Q\"Q')", **extra_context)


class YearMonth(models.Func):
    """Formats date/datetime into 'YYYY-MM' string."""
    output_field = models.CharField(max_length=7)

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="TO_CHAR(%(expressions)s, 'YYYY-MM')", **extra_context)

    def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="DATE_FORMAT(%(expressions)s, '%%%%Y-%%%%m')", **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="strftime('%%%%Y-%%%%m', %(expressions)s)", **extra_context)

    def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, template="TO_CHAR(%(expressions)s, 'YYYY-MM')", **extra_context)


class CumSum(Window):
    """
    A custom Django database expression that calculates a cumulative sum.

    This expression uses a window function to sum a given field over a set of
    rows defined by an ordering.
    """

    def __init__(self, expression, ordering, **extra):
        """
        :param expression: The field or expression to sum.
        :param ordering: The field or expression to order the window by.
        :param extra: Additional keyword arguments to pass to the Window expression,
                     such as `partition_by`.
        """
        # The window frame starts at the beginning of the partition (None)
        # and ends at the current row (0).
        frame = RowRange(start=None, end=0)
        if isinstance(ordering, F):
            ordering = ordering.asc()
        elif isinstance(ordering, str):
            ordering = F(ordering).asc()

        super().__init__(
            expression=Sum(expression),
            order_by=ordering,
            frame=frame,
            **extra
        )


class CumCount(Window):
    """
    A custom Django database expression that calculates a cumulative Count.

    This expression uses a window function to count a given field over a set of
    rows defined by an ordering.
    """

    def __init__(self, expression, ordering, **extra):
        """
        :param expression: The field or expression to sum.
        :param ordering: The field or expression to order the window by.
        :param extra: Additional keyword arguments to pass to the Window expression,
                     such as `partition_by`.
        """
        # The window frame starts at the beginning of the partition (None)
        # and ends at the current row (0).
        frame = RowRange(start=None, end=0)
        if isinstance(ordering, F):
            ordering = ordering.asc()
        elif isinstance(ordering, str):
            ordering = F(ordering).asc()

        super().__init__(
            expression=Count(expression),
            order_by=ordering,
            frame=frame,
            **extra
        )


class DisplayName(F):
    """
    Display Name Placeholder for a field that is used to display a human-readable name
    """

    def __init__(self, field_spec):
        if isinstance(field_spec, F):
            super().__init__(field_spec.name)
        else:
            super().__init__(field_spec)


class ChoiceName(Case):
    """
    Queries display names for a Django choices field
    """

    def __init__(self, model_name: str, field_ref: str | F, **extra):
        if isinstance(field_ref, F):
            field_ref = field_ref.name

        app_label, model_class = model_name.split('.')
        model = apps.get_model(app_label, model_class)

        field_name = field_ref.split('__')[-1]
        field = model._meta.get_field(field_name)

        # the next piece must be exactly like this to work on SQLite also, for some reason
        # directly referencing the name like V(name) does not work
        whens = [
            When(**{f"{field_ref}__exact": value, 'then': V(f"{name}")})
            for value, name in field.get_choices(include_blank=False)
        ]

        super().__init__(*whens, output_field=TextField(), default=V(''), **extra)


class Hours(models.Func):
    function = 'HOUR'
    template = '%(function)s(%(expressions)s)'
    output_field = models.FloatField()

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="EXTRACT",
            template="%(function)s(epoch FROM %(expressions)s)/3600"
        )

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(
            compiler, connection, function="TIMESTAMPDIFF",
            template="-%(function)s(HOUR,%(expressions)s)"
        )

    def as_sqlite(self, compiler, connection, **kwargs):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(
            compiler, connection, function="strftime",
            template="%(function)s(%%%%H,%(expressions)s)"
        )


class Minutes(models.Func):
    function = 'MINUTE'
    template = '%(function)s(%(expressions)s)'
    output_field = models.FloatField()

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="EXTRACT", template="%(function)s(epoch FROM %(expressions)s)/60"
        )

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(
            compiler, connection, function="TIMESTAMPDIFF",
            template="-%(function)s(MINUTE,%(expressions)s)"
        )

    def as_sqlite(self, compiler, connection, **kwargs):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(
            compiler, connection, function="strftime", template="%(function)s(%%%%M,%(expressions)s)"
        )


class ShiftStart(models.Func):
    function = 'to_timestamp'
    template = '%(function)s(%(expressions)s)'
    output_field = models.DateTimeField()

    def __init__(self, *expressions, size=SHIFT, **extra):
        super().__init__(*expressions, **extra)
        self.size = size

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="to_timestamp",
            template=(
                "%(function)s("
                "   floor((EXTRACT(epoch FROM %(expressions)s)) / EXTRACT(epoch FROM interval '{shift}'))"
                "   * EXTRACT(epoch FROM interval '{shift}') {offset:+}"
                ")"
            ).format(shift=self.size, offset=OFFSET)
        )


class ShiftEnd(models.Func):
    function = 'to_timestamp'
    template = '%(function)s(%(expressions)s)'
    output_field = models.DateTimeField()

    def __init__(self, *expressions, size=SHIFT, **extra):
        super().__init__(*expressions, **extra)
        self.size = size

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="to_timestamp",
            template=(
                "%(function)s("
                "   ceil((EXTRACT(epoch FROM %(expressions)s)) / EXTRACT(epoch FROM interval '{shift}'))"
                "   * EXTRACT(epoch FROM interval '{shift}') {offset:+}"
                ")"
            ).format(shift=self.size, offset=OFFSET)
        )


class Interval(Case):
    """
    A Django database function to categorize a numeric field's value into
    dynamically generated intervals.

    This function generates a series of SQL CASE WHEN statements to label
    a value based on where it falls within a defined range.

    Args:
        expression (str): The name of the field to evaluate.
        lo (int or float): The lower bound of the main interval range.
        hi (int or float): The upper bound of the main interval range.
        size (int): The total number of categories to create. This includes
                    the outer bounds ('<lo' and '>hi'), so it must be at
                    least 3 to have one middle interval.

    Usage Example:
        from django.contrib.auth.models import User
        from .db_functions import Interval

        # Annotate users with an age group based on a 'age' field.
        # This will create 4 categories: '<18', '18-40', '41-65', '>65'
        annotated_users = User.objects.annotate(
            age_group=Interval('age', lo=18, hi=65, size=4)
        )

        for user in annotated_users:
            print(f"{user.username}: {user.age_group}")
    """

    def __init__(self, field, *, lo, hi, size=3, floats=False, **extra):
        lo = lo if not isinstance(lo, V) else lo.value
        hi = hi if not isinstance(hi, V) else hi.value
        size = size if not isinstance(size, V) else size.value

        # --- Input Validation ---
        if isinstance(field, F):
            field = field.name
        elif not isinstance(field, str):
            raise TypeError("First argument must be a field name string.")

        if not isinstance(size, int):
            raise ValueError("The 'size' argument must be an integer of at least 3.")
        if not isinstance(lo, (int, float)):
            raise TypeError("The 'lo' argument must be an integer or float.")
        if not isinstance(hi, (int, float)):
            raise TypeError("The 'hi' argument must be an integer or float.")
        if not lo < hi:
            raise ValueError("The 'lo' argument must be less than 'hi'.")

        num_intervals = max(size - 2, 1)

        # --- Condition 1: Lower Bound ---
        whens = [
            When(**{f'{field}__lt': lo}, then=V(f' <{lo:g} ')),     # Add spaces to allow sorting to work
            When(**{f'{field}__gt': hi}, then=V(f'>{hi:g}')),
        ]
        if num_intervals == 1:
            whens.append(
                When(**{f'{field}__gte': lo, f'{field}__lte': hi},  then=V(f'{lo:g}-{hi:g}'))
            )
        else:
            # split by step size.
            for pair in itertools.pairwise(numpy.linspace(lo, hi, num_intervals + 1)):
                if floats:
                    start, end = float(pair[0]), float(pair[1])
                else:
                    start, end = int(numpy.ceil(pair[0])), int(numpy.floor(pair[1]))

                whens.append(
                    When(**{f'{field}__gte': start, f'{field}__lte': end}, then=V(f'{start:g}-{end:g}'))
                )

        super().__init__(*whens, output_field=CharField(), default=V(""), **extra)


class YearBucket(models.Func):
    """
    A Django database function to bucket dates or integer years into
    discrete multi-year intervals with closed discrete label formatting.

    Args:
        expression: A field name, F expression, or date/datetime/integer expression.
        size (int): The span of years in each bucket (default: 10).
        anchor (int): The base reference year for cycle alignment (default: 2000).
        fmt (str): Formatting motif ('decade' for e.g. '2020s', 'range' for '2020-2024').
    """
    output_field = models.CharField()

    def __init__(self, expression, size=10, anchor=2000, fmt=None, **extra):
        if isinstance(expression, str):
            expression = models.F(expression)

        if isinstance(size, models.Value):
            size = size.value
        if isinstance(anchor, models.Value):
            anchor = anchor.value

        self.size = int(size)
        self.anchor = int(anchor)

        if fmt is None:
            self.fmt = 'decade' if self.size in (10, 100) else 'range'
        else:
            self.fmt = fmt

        super().__init__(expression, **extra)

    def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
        c = super().resolve_expression(query, allow_joins, reuse, summarize, for_save)
        source = c.source_expressions[0]
        output_field = getattr(source, 'output_field', None)

        if isinstance(output_field, (models.DateField, models.DateTimeField)):
            from django.db.models.functions import ExtractYear
            extracted = ExtractYear(source).resolve_expression(
                query, allow_joins, reuse, summarize, for_save
            )
            c.set_source_expressions([extracted])

        return c

    def as_sqlite(self, compiler, connection, **extra_context):
        sql, params = compiler.compile(self.source_expressions[0])
        a, s = self.anchor, self.size
        start_sql = f'CAST({a} + CAST(FLOOR(({sql} - {a}) * 1.0 / {s}) AS INTEGER) * {s} AS TEXT)'
        if self.fmt == 'decade':
            return f"({start_sql} || 's')", params
        else:
            end_sql = f'CAST({a} + CAST(FLOOR(({sql} - {a}) * 1.0 / {s}) AS INTEGER) * {s} + {s - 1} AS TEXT)'
            return f"({start_sql} || '-' || {end_sql})", (*params, *params)

    def as_postgresql(self, compiler, connection, **extra_context):
        sql, params = compiler.compile(self.source_expressions[0])
        a, s = self.anchor, self.size
        start_sql = f'({a} + FLOOR(({sql} - {a})::numeric / {s})::int * {s})::text'
        if self.fmt == 'decade':
            return f"({start_sql} || 's')", params
        else:
            end_sql = f'({a} + FLOOR(({sql} - {a})::numeric / {s})::int * {s} + {s - 1})::text'
            return f"({start_sql} || '-' || {end_sql})", (*params, *params)

    def as_mysql(self, compiler, connection, **extra_context):
        sql, params = compiler.compile(self.source_expressions[0])
        a, s = self.anchor, self.size
        start_sql = f'CAST({a} + FLOOR(({sql} - {a}) / {s}) * {s} AS CHAR)'
        if self.fmt == 'decade':
            return f"CONCAT({start_sql}, 's')", params
        else:
            end_sql = f'CAST({a} + FLOOR(({sql} - {a}) / {s}) * {s} + {s - 1} AS CHAR)'
            return f"CONCAT({start_sql}, '-', {end_sql})", (*params, *params)

    def as_sql(self, compiler, connection, **extra_context):
        sql, params = compiler.compile(self.source_expressions[0])
        a, s = self.anchor, self.size
        start_sql = f'CAST({a} + CAST(FLOOR(({sql} - {a}) * 1.0 / {s}) AS INTEGER) * {s} AS VARCHAR(20))'
        if self.fmt == 'decade':
            return f"({start_sql} || 's')", params
        else:
            end_sql = f'CAST({a} + CAST(FLOOR(({sql} - {a}) * 1.0 / {s}) AS INTEGER) * {s} + {s - 1} AS VARCHAR(20))'
            return f"({start_sql} || '-' || {end_sql})", (*params, *params)


class Decade(YearBucket):
    """Bucket years into 10-year intervals formatted as e.g. '2020s'."""
    def __init__(self, expression, anchor=2000, **extra):
        super().__init__(expression, size=10, anchor=anchor, fmt='decade', **extra)


class Lustrum(YearBucket):
    """Bucket years into 5-year intervals formatted as closed ranges e.g. '2020-2024'."""
    def __init__(self, expression, anchor=2000, **extra):
        super().__init__(expression, size=5, anchor=anchor, fmt='range', **extra)


class Quadrennial(YearBucket):
    """Bucket years into 4-year intervals formatted as closed ranges e.g. '2020-2023'."""
    def __init__(self, expression, anchor=2000, **extra):
        super().__init__(expression, size=4, anchor=anchor, fmt='range', **extra)


class Triennial(YearBucket):
    """Bucket years into 3-year intervals formatted as closed ranges e.g. '2022-2024'."""
    def __init__(self, expression, anchor=2022, **extra):
        super().__init__(expression, size=3, anchor=anchor, fmt='range', **extra)


class Biennial(YearBucket):
    """Bucket years into 2-year intervals formatted as closed ranges e.g. '2022-2023'."""
    def __init__(self, expression, anchor=2022, **extra):
        super().__init__(expression, size=2, anchor=anchor, fmt='range', **extra)


class Century(YearBucket):
    """Bucket years into 100-year intervals formatted as e.g. '2000s'."""
    def __init__(self, expression, anchor=2000, **extra):
        super().__init__(expression, size=100, anchor=anchor, fmt='decade', **extra)

