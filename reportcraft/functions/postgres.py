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

