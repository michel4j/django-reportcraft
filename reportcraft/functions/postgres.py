from __future__ import annotations

from django.db import models
from django.contrib.postgres.aggregates import StringAgg


class Join(StringAgg):
    def __init__(self, expression, separator=', ', **extra):
        """
        A custom Django database function to join strings with a delimiter.
        :param expression: The field to join
        :param delimiter: The delimiter to use for joining
        :param extra: Additional arguments for the StringAgg function
        """
        if isinstance(separator, models.Value):
            delimiter = separator.value
        else:
            delimiter = separator
        super().__init__(expression, delimiter=delimiter, **extra)


class TitleCase(models.Func):
    function = 'INITCAP'  # PostgreSQL's function for title case
    template = '%(function)s(%(expressions)s)'


class String(models.Func):
    """
    Coerce an expression to a string.
    """
    function = 'CAST'
    template = '%(function)s(%(expressions)s AS varchar)'
    output_field = models.CharField()

    def as_postgresql(self, compiler, connection):
        # CAST would be valid too, but the :: shortcut syntax is more readable.
        return self.as_sql(compiler, connection, template='%(expressions)s::text')



