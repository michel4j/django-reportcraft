from __future__ import annotations

from datetime import datetime

from django.apps import apps
from django.db import models
from django.db.models import Window, Sum, F, Case, When, Value as V, TextField, CharField, Count
from django.db.models.expressions import RowRange
from django.utils import timezone


SHIFT = 8
SHIFT_DURATION = '{:d} hour'.format(SHIFT)
OFFSET = -timezone.make_aware(datetime.now(), timezone.get_default_timezone()).utcoffset().total_seconds()


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
        # This will create 4 categories: '<18', '18-40', '40-65', '>65'
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
            When(**{f'{field}__lt': lo}, then=V(f'<{lo:g}')),
            When(**{f'{field}__gte': hi}, then=V(f'>{hi:g}')),
        ]
        if num_intervals == 1:
            whens.append(
                When(**{f'{field}__gte': lo, f'{field}__lte': hi},  then=V(f'{lo:g}-{hi:g}'))
            )
        else:
            # split by step size.
            step = (hi - lo) / num_intervals if floats else (hi - lo) // num_intervals
            for i in range(num_intervals):
                start = lo + i * step
                if i == num_intervals - 1:
                    whens.append(
                        When(**{f'{field}__gte': start, f'{field}__lte': hi}, then=V(f'{start:g}-{hi:g}'))
                    )
                else:
                    end = lo + (i + 1) * step
                    whens.append(
                        When(**{f'{field}__gte': start, f'{field}__lt': end},then=V(f'{start:g}-{end:g}'))
                    )

        super().__init__(*whens, output_field=CharField(), default=V(""), **extra)
