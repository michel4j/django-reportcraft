from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import threading
from datetime import datetime, timedelta
from functools import wraps, reduce
from importlib import import_module
from inspect import getframeinfo, stack
from operator import or_
from typing import Any, Sequence

import pyparsing as pp
import yaml
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Count, Avg, Sum, Max, Min, F, Value as V, Q, Case, When, CharField
from django.db.models.functions import (
    Greatest, Least, Concat, Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan,
    ATan2, Mod, Sign, Trunc, Radians, Degrees, Upper, Lower, Length, Substr, LPad, RPad, Trim, LTrim, RTrim,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek
)
from django.http import HttpResponse
from django.utils import timezone
from pyparsing.exceptions import ParseException


def load_object(import_path):
    """
    Loads an object from an 'import_path', like in MIDDLEWARE_CLASSES and the
    likes.

    Import paths should be: "mypackage.mymodule.MyObject". It then imports the
    module up until the last dot and tries to get the attribute after that dot
    from the imported module.

    If the import path does not contain any dots, a TypeError is raised.

    If the module cannot be imported, an ImportError is raised.

    If the attribute does not exist in the module, a AttributeError is raised.
    """
    if '.' not in import_path:
        raise TypeError(
            "'import_path' argument to 'misc.utils.load_object' must "
            "contain at least one dot."
        )
    module_name, object_name = import_path.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, object_name)


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

    def __init__(self, model_name: str, field_ref: str | F, condition=None, then=None, **lookups):
        if isinstance(field_ref, F):
            field_ref = field_ref.name

        model = apps.get_model(model_name)
        field_name = field_ref.split('__')[-1]
        choices = dict(model._meta.get_field(field_name).flatchoices)
        whens = [
            When(**{field_ref: k, 'then': V(v)})
            for k, v in choices.items()
        ]
        super().__init__(*whens, output_field=CharField(), default=V(''), condition=condition, then=then, **lookups)


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


SHIFT = 8
SHIFT_DURATION = '{:d} hour'.format(SHIFT)
OFFSET = -timezone.make_aware(datetime.now(), timezone.get_default_timezone()).utcoffset().total_seconds()


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


OPERATOR_FUNCTIONS = {
    '+': 'ADD()',
    '-': 'SUB()',
    '*': 'MUL()',
    '/': 'DIV()',
}

ALLOWED_FUNCTIONS = {
    Sum, Avg, Count, Max, Min, Concat, Greatest, Least,
    Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan, ATan2, Mod, Sign, Trunc,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek,
    Upper, Lower, Length, Substr, LPad, RPad, Trim, LTrim, RTrim,
    Radians, Degrees, Hours, Minutes, ShiftStart, ShiftEnd, Q, DisplayName
}

REPORTCRAFT_FUNCTIONS = getattr(settings, 'REPORTCRAFT_FUNCTIONS', [])  # list of string paths to importable functions
for func_path in REPORTCRAFT_FUNCTIONS:
    try:
        func = load_object(func_path)
        if callable(func):
            ALLOWED_FUNCTIONS.add(func)
    except (ImportError, AttributeError) as e:
        print(f"Error importing function {func_path}: {e}")

FUNCTIONS = {
    func.__name__: func for func in ALLOWED_FUNCTIONS
}


def get_histogram_points(data: list[float], bins: Any = None) -> list[dict]:
    """
    Generate histogram points
    """
    import numpy as np
    bins = 'doane' if bins is None else int(bins)
    hist, edges = np.histogram(data, bins=bins)
    centers = edges[:-1] + np.diff(edges) / 2
    return [{'x': float(x), 'y': float(y)} for x, y in zip(centers, hist)]


class Parser:
    @staticmethod
    def parse_float(tokens):
        """
        Parse a floating point number
        """
        return float(tokens[0])

    @staticmethod
    def parse_func_name(tokens):
        """
        Parse a function name
        """
        return f'{tokens[0]}()'

    @staticmethod
    def parse_int(tokens):
        """
        Parse an integer
        """
        return int(tokens[0])

    @staticmethod
    def parse_bool(tokens):
        """
        Parse a boolean
        """
        return {
            'True': True,
            'False': False,
            'true': True,
            'false': False,
        }.get(tokens[0], False)

    @staticmethod
    def parse_kwargs(self, tokens):
        """
        Parse keyword arguments for a function
        """
        return {k: v for k, v in tokens}

    @staticmethod
    def parse_var(tokens):
        """
        Parse a variable
        """
        return f'${tokens[0]}'

    @staticmethod
    def parse_negate(tokens):
        """
        Parse the negation operator
        """
        return ['NEG()', tokens[0][1]]

    @staticmethod
    def parse_operator(tokens):
        parts = tokens[0]
        if len(parts) == 3 and parts[1] in ['+', '-', '*', '/', '=']:
            return [OPERATOR_FUNCTIONS[parts[1]], parts[0], parts[2]]
        return tokens

    @staticmethod
    def clean_variable(name):
        """
        Clean the parsed variable into a proper Django database field name.
        :param name: The name of the variable, as a string. The special variable $this is converted to 'id'. Names
        separated by '.' are converted to '__' for Django field lookup.
        :return: A Django F object representing the field
        """
        var_names = name.strip('$').split('.')
        var_name = '__'.join(re.sub(r'(?<!^)(?=[A-Z])', '_', name) for name in var_names).lower()
        if var_name == 'this':
            var_name = 'id'
        return F(var_name)

    @staticmethod
    def clean_function(name, *args):
        """
        Clean the parsed function and arguments into a proper Django database function call
        :param name: The name of the function, as a string, must be in ALLOWED_FUNCTIONS
        :param args: The arguments to the function
        """

        if name == 'NEG' and len(args) == 1:
            return - args[0]
        elif name == 'ADD' and len(args) == 2:
            return args[0] + args[1]
        elif name == 'SUB' and len(args) == 2:
            return args[0] - args[1]
        elif name == 'MUL' and len(args) == 2:
            return args[0] * args[1]
        elif name == 'DIV':
            return args[0] / args[1]
        elif name == 'Q' and len(args) == 1:
            return Q(**args[0])
        elif name in FUNCTIONS:
            ordered_args = [a for a in args if not isinstance(a, dict)]
            kwargs = {k: v for a in args if isinstance(a, dict) for k, v in a.items()}
            return FUNCTIONS[name](*ordered_args, **kwargs)
        else:
            raise ParseException(f'Unknown function: {name}')


class ExpressionParser(Parser):
    def __init__(self):
        self.expr = pp.Forward()
        self.double = pp.Combine(pp.Optional('-') + pp.Word(pp.nums) + '.' + pp.Word(pp.nums)).setParseAction(
            self.parse_float
        )
        self.integer = pp.Combine(pp.Optional('-') + pp.Word(pp.nums)).setParseAction(self.parse_int)
        self.boolean = pp.oneOf('True False true false').setParseAction(self.parse_bool)
        self.variable = pp.Word(pp.alphas + '.').setParseAction(self.parse_var)
        self.string = pp.quotedString.setParseAction(pp.removeQuotes)

        # Define the function call
        self.left_par = pp.Literal('(').suppress()
        self.right_par = pp.Literal(')').suppress()
        self.equal = pp.Literal('=').suppress()
        self.comma = pp.Literal(',').suppress()
        self.func_name = pp.Word(pp.alphas).setParseAction(self.parse_func_name)
        self.func_kwargs = pp.Group(pp.Word(pp.alphas + '_') + self.equal + self.expr).setParseAction(self.parse_kwargs)
        self.func_call = pp.Group(
            self.func_name + self.left_par + pp.Group(pp.Optional(pp.delimitedList(self.expr))) + self.right_par
        )

        self.operand = (
                self.double | self.integer | self.boolean | self.func_kwargs | self.func_call
                | self.string | self.variable
        )

        self.negate = pp.Literal('-')
        self.expr << pp.infixNotation(
            self.operand, [
                (self.negate, 1, pp.opAssoc.RIGHT, self.parse_negate),
                (pp.oneOf('* /'), 2, pp.opAssoc.LEFT, self.parse_operator),
                (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT, self.parse_operator),
            ]
        )

    def clean(self, expression, wrap_value=True):
        """
        Clean the parsed expression into a Django expression
        :param expression: The parsed expression as a nested list
        :param wrap_value: Whether to wrap values in a Value function
        :return: A Django expression suitable for use in a QuerySet
        """

        if isinstance(expression, str) and expression.startswith('$'):
            return self.clean_variable(expression)
        elif isinstance(expression, bool):
            return expression
        elif isinstance(expression, (int, float, str)):
            return V(expression) if wrap_value else expression
        elif isinstance(expression, pp.ParseResults):
            return self.clean(expression.asList())
        elif isinstance(expression, dict):
            return {
                k: self.clean(v) for k, v in expression.items()
            }
        elif isinstance(expression, list) and len(expression) == 1:
            return self.clean(expression[0])
        elif not isinstance(expression, list):
            return V(expression) if wrap_value else expression
        elif len(expression) > 1 and isinstance(expression[0], str) and expression[0].endswith('()'):
            func_name = expression[0].strip()[:-2]
            args = self.clean(expression[1:])
            if not isinstance(args, list):
                args = [args]
            return self.clean_function(func_name, *args)
        else:
            return [self.clean(sub_expr) for sub_expr in expression]

    def parse(self, text):
        """
        Parse an expression string into a Django expression
        :param text: The expression string to parse
        :return: A Django expression suitable for use in a QuerySet
        """
        try:
            expression = self.expr.parse_string(text, parseAll=True).as_list()
            result = self.clean(expression)
        except (ParseException, KeyError) as err:
            result = V(0)
            print(f'Error parsing expression: {err}')
        return result


class FilterParser:
    """
    A parser for boolean filter expressions that generates Django Q objects.

    This class uses the pyparsing library to define a grammar for filter
    expressions and translates them into Django's Q objects for database querying.
    """

    def __init__(self, identifiers: Sequence[str] = None):
        """
        Initializes the FilterParser with a set of identifiers.
        :param identifiers: A list of variable names that can be used in the filter expressions. Accepts all by default
        """
        self.identifiers = identifiers or []
        self.q_expression = self._define_grammar()

    def _define_grammar(self):
        """
        Defines the pyparsing grammar for the filter expressions.
        """
        # Define the basic elements of the grammar
        if self.identifiers:
            identifier = pp.oneOf(self.identifiers, caseless=True).setParseAction(self._to_lowercase)
        else:
            identifier = pp.Word(pp.alphas, pp.alphanums + "_").setParseAction(self._to_lowercase)
        extr_operators = {
            '==': 'exact',  # alias for equality
            '=': 'exact',
            '~=': 'iexact',
            '>=': 'gte',
            '<=': 'lte',
            '>': 'gt',
            '<': 'lt',
            '^=': 'startswith',
            '^~': 'istartswith',  # Using '^~' for case-insensitive startswith
            '$=': 'endswith',
            '$~': 'iendswith',  # Using '$~' for case-insensitive endswith
            'has': 'contains',
            '~has': 'icontains',
            'regex': 'regex',
            'isnull': 'isnull',
        }
        # Operators
        operator = reduce(
            or_, [
                pp.Literal(f'{op_prefix}{op}').setParseAction(pp.replace_with(f'{lookup_prefix}{lookup}'))
                for op_prefix, lookup_prefix in [('!', 'not_'), ('', '')]
                for op, lookup in extr_operators.items()

            ]
        )

        # Values
        number = pp.pyparsing_common.number
        quoted_string = pp.QuotedString("'") | pp.QuotedString('"')
        boolean = pp.oneOf('True False', caseless=True).setParseAction(self._parse_bool)
        value = number | quoted_string | boolean

        # A single condition (e.g., "Citations > 100")
        condition = pp.Group(identifier + operator + value)
        condition.setParseAction(self._make_q_object)

        # Define the boolean logic using an operator precedence parser
        q_expression = pp.infixNotation(
            condition, [
                (pp.CaselessLiteral("and"), 2, pp.opAssoc.LEFT, self._process_and),
                (pp.CaselessLiteral("or"), 2, pp.opAssoc.LEFT, self._process_or),
            ]
        )

        return q_expression

    @staticmethod
    def _parse_bool(tokens):
        """
        Parse action to convert boolean strings to Python booleans.
        """
        return {
            'true': True,
            'false': False,
        }.get(tokens[0].lower(), False)

    @staticmethod
    def _to_lowercase(tokens):
        """Parse action to convert field names to lowercase."""
        return tokens[0].lower()

    @staticmethod
    def _make_q_object(tokens):
        """
        Parse action to convert a parsed condition into a Q object.
        e.g., from ['citations', 'gt', 100] to Q(citations__gt=100)
        """
        field, op, val = tokens[0]
        if op.startswith('not_'):
            # Handle the 'not' operator by negating the Q object
            q_key = f"{field}__{op[4:]}"
            return ~Q(**{q_key: val})

        q_key = f"{field}__{op}"
        return Q(**{q_key: val})

    @staticmethod
    def _process_and(tokens):
        """Parse action to handle AND logical operations."""
        # The tokens are nested, e.g., [[Q(citations__gt=100), Q(mentions__lt=50)]]
        q_obj = tokens[0][0]
        for i in range(2, len(tokens[0]), 2):
            q_obj &= tokens[0][i]
        return q_obj

    @staticmethod
    def _process_or(tokens):
        """Parse action to handle OR logical operations."""
        # The tokens are nested, e.g., [[Q(citations__gt=100), Q(mentions__lt=50)]]
        q_obj = tokens[0][0]
        for i in range(2, len(tokens[0]), 2):
            q_obj |= tokens[0][i]
        return q_obj

    def parse(self, filter_string, silent: bool = False):
        """
        Parses a filter string and returns the corresponding Q object.
        """
        try:
            # The result is in a list, so we extract the first element
            return self.q_expression.parseString(filter_string, parseAll=True)[0]
        except pp.ParseException as e:
            if not silent:
                raise ValueError(f"Expression `{filter_string}` is not valid.") from e
            return Q()  # Return an empty Q object if parsing fails and silent mode is on


def regroup_data(
        data: list[dict],
        x_axis: str = '',
        y_axis: list[str] | str = '',
        y_value: str = '',
        others: list[str] = None,
        labels: dict = None,
        default: Any = None,
        sort: str = '',
        sort_desc: bool = False
) -> list[dict]:
    """
    Regroup data into neat key-value pairs translating keys to labels according to labels dictionary

    :param data: list of dictionaries
    :param x_axis: Name of the x-axis field
    :param y_axis: List of y-axis field names or a single field name to group by
    :param y_value: Field name for y-axis if a single field is used for y-axis
    :param others: List of other fields to include in the output if any
    :param labels: Field labels
    :param default: Default value for missing fields
    :param sort: Name of field to sort by or empty string to disable sorting
    :param sort_desc: Sort in descending order
    """
    labels = labels or {}
    others = others or []
    x_label = labels.get(x_axis, x_axis)
    x_values = list(dict.fromkeys(filter(None, [item[x_axis] for item in data])))
    if isinstance(y_axis, str):
        y_labels = list(filter(None, dict.fromkeys(item[y_axis] for item in data)))
    else:
        y_labels = [labels.get(y, y) for y in y_axis]

    defaults = {
        y: default
        for y in y_labels
    }

    raw_data = {value: {x_label: value, **defaults} for value in x_values}
    # reorganize data into dictionary of dictionaries with appropriate fields
    for item in data:
        x_value = item[x_axis]
        if x_value not in x_values:
            continue
        if isinstance(y_axis, str):
            if item.get(y_axis) is not None:
                raw_data[x_value][item[y_axis]] = item.get(y_value, 0)
        elif isinstance(y_axis, list):
            for y_field in y_axis:
                y_label = labels.get(y_field, y_field)
                if y_label is None:
                    continue
                if y_field in item:
                    raw_data[x_value][y_label] = item.get(y_field, 0)
                elif y_label not in raw_data[x_value]:
                    raw_data[x_value][y_label] = default
        # Add other fields to the raw data
        for other in others:
            if other in item:
                raw_data[x_value][labels.get(other, other)] = item[other]

    data_list = list(raw_data.values())

    if sort:
        sort_key = labels.get(sort, sort)
        data_list.sort(key=lambda item: item.get(sort_key, 0), reverse=sort_desc)

    return data_list


def split_data(
        data: list[dict],
        group_by: str,
        default_group: str = 'Unknown',
) -> dict:
    """
    Split data into a dictionary of lists keyed by the values of a field

    :param data: list of dictionaries
    :param group_by: Name of the field to split by
    :param default_group: Name of the default group if the field is missing or empty
    """
    grouped_data = {}
    for item in data:
        group_value = item.get(group_by, default_group)
        if group_value in ['', None]:
            group_value = default_group
        if group_value not in grouped_data:
            grouped_data[group_value] = []
        grouped_data[group_value].append(item)
    return grouped_data


CACHE_TIMEOUT = 86400


def cached_model_method(duration: int = 30):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate a cache key using method name and arguments
            key_data = {
                'id': self.id,
                'class': self.__class__.__name__,
                'method': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key_string = json.dumps(key_data, sort_keys=True)
            cache_key = f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
            cache_expiry_key = f"{cache_key}:expiry"
            try:
                results = cache.get_many((cache_key, cache_expiry_key))
                cached_result = results.get(cache_key)
                now = datetime.now()
                expiry = results.get(cache_expiry_key, now)
                if cached_result is not None:
                    if now - expiry > timedelta(seconds=duration):
                        # Asynchronously replace cache value if it is about to expire, next request will get the fresh value
                        threading.Thread(
                            target=_update_cache, args=(self, func, cache_key, args, kwargs, duration)
                        ).start()
                    return cached_result

                # Compute and store the fresh result
                return _update_cache(self, func, cache_key, args, kwargs, duration)
            except Exception as e:
                print(f"Cache error: {e}")
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


def _update_cache(self, func, cache_key, args, kwargs, duration):
    """Updates the cache value asynchronously."""
    result = func(self, *args, **kwargs)
    cache_expiry_key = f"{cache_key}:expiry"
    cache.set_many(
        {
            cache_key: result,
            cache_expiry_key: datetime.now() + timedelta(seconds=duration)
        }, timeout=CACHE_TIMEOUT
    )
    return result


def epoch(dt: datetime = None) -> int:
    """
    Convert a datetime object to an epoch timestamp for Javascript
    :param dt: The datetime object to convert
    :return: The epoch timestamp as integer
    """
    timestamp = dt.timestamp() if dt else datetime.now().timestamp()
    return int(timestamp) * 1000


def list_colors(specifier):
    return [
        f'#{specifier[i:i + 6]}' for i in range(0, len(specifier), 6)
    ]


CATEGORICAL_SCHEMES = {
    "Accent": list_colors("7fc97fbeaed4fdc086ffff99386cb0f0027fbf5b17666666"),
    "Dark2": list_colors("1b9e77d95f027570b3e7298a66a61ee6ab02a6761d666666"),
    "Live4": list_colors("8f9f9ac560529f6dbfa0b552"),
    "Live8": list_colors("073b4c06d6a0ffd166ef476f118ab27f7effafc76578c5e7"),
    "Live16": list_colors(
        "67aec1c45a81cdc339ae8e6b6dc758a084b6667ccdcd4f55805cd6cf622da69e4c9b97956db586c255b6073b4cffd166"
    ),
    "Paired": list_colors("a6cee31f78b4b2df8a33a02cfb9a99e31a1cfdbf6fff7f00cab2d66a3d9affff99b15928"),
    "Pastel1": list_colors("fbb4aeb3cde3ccebc5decbe4fed9a6ffffcce5d8bdfddaecf2f2f2"),
    "Pastel2": list_colors("b3e2cdfdcdaccbd5e8f4cae4e6f5c9fff2aef1e2cccccccc"),
    "Set1": list_colors("e41a1c377eb84daf4a984ea3ff7f00ffff33a65628f781bf999999"),
    "Set2": list_colors("66c2a5fc8d628da0cbe78ac3a6d854ffd92fe5c494b3b3b3"),
    "Set3": list_colors("8dd3c7ffffb3bebadafb807280b1d3fdb462b3de69fccde5d9d9d9bc80bdccebc5ffed6f"),
    "Tableau10": list_colors("4e79a7f28e2ce1575976b7b259a14fedc949af7aa1ff9da79c755fbab0ab"),
    "Category10": list_colors("1f77b4ff7f0e2ca02cd627289467bd8c564be377c27f7f7fbcbd2217becf"),
    "Observable10": list_colors("4269d0efb118ff725c6cc5b03ca951ff8ab7a463f297bbf59c6b4e9498a0")
}

SEQUENTIAL_SCHEMES = {
    "Blues": ["#f7fbff", "#08306b"],
    "Greens": ["#f7fcf5", "#00441b"],
    "Greys": ["#fbfbfb", "#252525"],
    "Oranges": ["#fff5eb", "#7f2704"],
    "Purples": ["#fcfbfd", "#49006a"],
    "Reds": ["#fff5f0", "#67000d"],
    "BuGn": ["#e5f5f9", "#2ca25f"],
    "BuPu": ["#e0ecf4", "#8856a7"],
    "GnBu": ["#edf8fb", "#2ca25f"],
    "OrRd": ["#fee8c8", "#e34a33"],
    "PuBu": ["#ece7f2", "#2b8cbe"],
    # "PuBuGn": ["#ece2f0", "#1c9099"],
    "PuRd": ["#e7e1ef", "#dd1c77"],
    "RdPu": ["#fde0dd", "#c51b8a"],
    "YlGn": ["#f7fcb9", "#31a354"],
    # "YlGnBu": ["#edf8b1", "#2c7fb8"],
    # "YlOrBr": ["#fff7bc", "#8c2d04"],
    # "YlOrRd": ["#ffeda0", "#b30000"],

}

CATEGORICAL_COLORS = [(scheme, scheme) for scheme in CATEGORICAL_SCHEMES.keys()]
SEQUENTIAL_COLORS = [(scheme, scheme) for scheme in SEQUENTIAL_SCHEMES.keys()]
AXIS_CHOICES = [('', 'Choose...'), ('y', 'Y1-Axis'), ('y2', 'Y2-Axis')]


def map_colors(data, scheme='Live16'):
    """
    Map colors to data wrapping around the color list.
    :param data: List of data items
    :param scheme: List of colors
    :return: Dictionary of data items mapped to colors
    """
    colors = CATEGORICAL_SCHEMES.get(scheme, CATEGORICAL_SCHEMES['Live16'])
    return {item: colors[i % len(colors)] for i, item in enumerate(data)}


def get_model_name(model: type(models.Model)) -> str:
    """
    Get the name of a model of the form "app_name.model_name"
    :param model: The model class
    :return string representing the model name
    """
    return f'{model._meta.app_label}.{model.__name__}'


def get_models(exclude: Sequence = ('django', 'rest_framework')) -> dict:
    """
    Get all models from an app
    :param exclude: List or tuple of app names to exclude
    :return: A nested dictionary of app_name -> model_name -> field_name -> field_type
    The field_type is the internal type of the field, e.g. Char, Integer, etc. For related fields, it is the full related model name.
    """
    info = {}
    for app in apps.get_app_configs():
        app_name = app.name.split('.')[-1]
        if app_name in exclude:
            continue
        info[app_name] = {}
        for model in app.get_models():
            info[app_name][model.__name__] = {
                field.name: re.sub(r'Field$', '', field.get_internal_type()) for field in model._meta.get_fields() if
                not field.is_relation
            }
            info[app_name][model.__name__].update(
                {field.name: f"{get_model_name(field.related_model)}" for field in model._meta.get_fields() if
                 field.is_relation and field.related_model}
            )
        if not info[app_name]:
            del info[app_name]
    return info


class MinMax:
    """
    A class to find the minimum and maximum values in comprehensions
    """

    def __init__(self):
        self.min = None
        self.max = None

    def check(self, value):
        if self.min is None or value < self.min:
            self.min = value
        if self.max is None or value > self.max:
            self.max = value
        return value

    def __str__(self):
        return f"Min: {self.min}, Max: {self.max}"


class CsvResponse(HttpResponse):
    """
    An HTTP response class that consumes data to be serialized to CSV.

    :param data: Data to be dumped into csv. Should be alist of dicts.
    """

    def __init__(self, data: list[dict], headers: list[str], **kwargs):
        kwargs.setdefault("content_type", "text/csv")
        content = ''
        if data:
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            content = stream.getvalue()
            stream.close()
        super().__init__(content=content, **kwargs)


REGION_DATA = [
    {
        "002 - Africa": [
            {
                "015 - Northern Africa": [
                    "DZ - Algeria",
                    "EG - Egypt",
                    "EH - Western Sahara",
                    "LY - Libya",
                    "MA - Morocco",
                    "SD - Sudan",
                    "SS - South Sudan",
                    "TN - Tunisia"
                ]
            },
            {
                "011 - Western Africa": [
                    "BF - Burkina Faso",
                    "BJ - Benin",
                    "CI - Côte d'Ivoire",
                    "CV - Cabo Verde",
                    "GH - Ghana",
                    "GM - Gambia",
                    "GN - Guinea",
                    "GW - Guinea-Bissau",
                    "LR - Liberia",
                    "ML - Mali",
                    "MR - Mauritania",
                    "NE - Niger",
                    "NG - Nigeria",
                    "SH - Saint Helena, Ascension and Tristan da Cunha",
                    "SL - Sierra Leone",
                    "SN - Senegal",
                    "TG - Togo"
                ]
            },
            {
                "017 - Middle Africa": [
                    "AO - Angola",
                    "CD - Congo, Democratic Republic of the",
                    "CF - Central African Republic",
                    "CG - Congo",
                    "CM - Cameroon",
                    "GA - Gabon",
                    "GQ - Equatorial Guinea",
                    "ST - Sao Tome and Principe",
                    "TD - Chad"
                ]
            },
            {
                "014 - Eastern Africa": [
                    "BI - Burundi",
                    "DJ - Djibouti",
                    "ER - Eritrea",
                    "ET - Ethiopia",
                    "KE - Kenya",
                    "KM - Comoros",
                    "MG - Madagascar",
                    "MU - Mauritius",
                    "MW - Malawi",
                    "MZ - Mozambique",
                    "RE - Réunion",
                    "RW - Rwanda",
                    "SC - Seychelles",
                    "SO - Somalia",
                    "TZ - Tanzania, United Republic of",
                    "UG - Uganda",
                    "YT - Mayotte",
                    "ZM - Zambia",
                    "ZW - Zimbabwe"
                ]
            },
            {
                "018 - Southern Africa": [
                    "BW - Botswana",
                    "LS - Lesotho",
                    "NA - Namibia",
                    "SZ - Eswatini",
                    "ZA - South Africa"
                ]
            }
        ]
    },
    {
        "150 - Europe": [
            {
                "154 - Northern Europe": [
                    "GG - Guernsey",
                    "JE - Jersey",
                    "AX - Åland Islands",
                    "DK - Denmark",
                    "EE - Estonia",
                    "FI - Finland",
                    "FO - Faroe Islands",
                    "GB - United Kingdom of Great Britain and Northern Ireland",
                    "IE - Ireland",
                    "IM - Isle of Man",
                    "IS - Iceland",
                    "LT - Lithuania",
                    "LV - Latvia",
                    "NO - Norway",
                    "SE - Sweden",
                    "SJ - Svalbard and Jan Mayen"
                ]
            },
            {
                "155 - Western Europe": [
                    "AT - Austria",
                    "BE - Belgium",
                    "CH - Switzerland",
                    "DE - Germany",
                    "FR - France",
                    "LI - Liechtenstein",
                    "LU - Luxembourg",
                    "MC - Monaco",
                    "NL - Netherlands"
                ]
            },
            {
                "151 - Eastern Europe": [
                    "BG - Bulgaria",
                    "BY - Belarus",
                    "CZ - Czechia",
                    "HU - Hungary",
                    "MD - Moldova",
                    "PL - Poland",
                    "RO - Romania",
                    "RU - Russian Federation",
                    "SK - Slovakia",
                    "UA - Ukraine"
                ]
            },
            {
                "039 - Southern Europe": [
                    "AD - Andorra",
                    "AL - Albania",
                    "BA - Bosnia and Herzegovina",
                    "ES - Spain",
                    "GI - Gibraltar",
                    "GR - Greece",
                    "HR - Croatia",
                    "IT - Italy",
                    "ME - Montenegro",
                    "MK - North Macedonia",
                    "MT - Malta",
                    "RS - Serbia",
                    "PT - Portugal",
                    "SI - Slovenia",
                    "SM - San Marino",
                    "VA - Holy See",
                    "YU - Yugoslavia"
                ]
            }
        ]
    },
    {
        "019 - Americas": [
            {
                "021 - Northern America": [
                    "BM - Bermuda",
                    "CA - Canada",
                    "GL - Greenland",
                    "PM - Saint Pierre and Miquelon",
                    "US - United States of America"
                ]
            },
            {
                "029 - Caribbean": [
                    "AG - Antigua and Barbuda",
                    "AI - Anguilla",
                    "AN - Netherlands Antilles",
                    "AW - Aruba",
                    "BB - Barbados",
                    "BL - Saint Barthélemy",
                    "BS - Bahamas",
                    "CU - Cuba",
                    "DM - Dominica",
                    "DO - Dominican Republic",
                    "GD - Grenada",
                    "GP - Guadeloupe",
                    "HT - Haiti",
                    "JM - Jamaica",
                    "KN - Saint Kitts and Nevis",
                    "KY - Cayman Islands",
                    "LC - Saint Lucia",
                    "MF - Saint Martin (French part)",
                    "MQ - Martinique",
                    "MS - Montserrat",
                    "PR - Puerto Rico",
                    "TC - Turks and Caicos Islands",
                    "TT - Trinidad and Tobago",
                    "VC - Saint Vincent and the Grenadines",
                    "VG - Virgin Islands (British)",
                    "VI - Virgin Islands (U.S.)"
                ]
            },
            {
                "013 - Central America": [
                    "BZ - Belize",
                    "CR - Costa Rica",
                    "GT - Guatemala",
                    "HN - Honduras",
                    "MX - Mexico",
                    "NI - Nicaragua",
                    "PA - Panama",
                    "SV - El Salvador"
                ]
            },
            {
                "005 - South America": [
                    "AR - Argentina",
                    "BO - Bolivia",
                    "BR - Brazil",
                    "CL - Chile",
                    "CO - Colombia",
                    "EC - Ecuador",
                    "FK - Falkland Islands",
                    "GF - French Guiana",
                    "GY - Guyana",
                    "PE - Peru",
                    "PY - Paraguay",
                    "SR - Suriname",
                    "UY - Uruguay",
                    "VE - Venezuela"
                ]
            }
        ]
    },
    {
        "142 - Asia": [
            {
                "143 - Central Asia": [
                    "TM - Turkmenistan",
                    "TJ - Tajikistan",
                    "KG - Kyrgyzstan",
                    "KZ - Kazakhstan",
                    "UZ - Uzbekistan"
                ]
            },
            {
                "030 - Eastern Asia": [
                    "CN - China",
                    "HK - Hong Kong",
                    "JP - Japan",
                    "KP - North Korea",
                    "KR - South Korea",
                    "MN - Mongolia",
                    "MO - Macao",
                    "TW - Taiwan"
                ]
            },
            {
                "034 - Southern Asia": [
                    "AF - Afghanistan",
                    "BD - Bangladesh",
                    "BT - Bhutan",
                    "IN - India",
                    "IR - Iran",
                    "LK - Sri Lanka",
                    "MV - Maldives",
                    "NP - Nepal",
                    "PK - Pakistan"
                ]
            },
            {
                "035 - South-Eastern Asia": [
                    "BN - Brunei Darussalam",
                    "ID - Indonesia",
                    "KH - Cambodia",
                    "LA - Lao People's Democratic Republic",
                    "MM - Myanmar",
                    "MY - Malaysia",
                    "BU - Burma",
                    "PH - Philippines",
                    "SG - Singapore",
                    "TH - Thailand",
                    "TL - Timor-Leste",
                    "VN - Viet Nam",
                    "TP - East Timor"
                ]
            },
            {
                "145 - Western Asia": [
                    "AE - United Arab Emirates",
                    "AM - Armenia",
                    "AZ - Azerbaijan",
                    "BH - Bahrain",
                    "CY - Cyprus",
                    "GE - Georgia",
                    "IL - Israel",
                    "IQ - Iraq",
                    "JO - Jordan",
                    "KW - Kuwait",
                    "LB - Lebanon",
                    "OM - Oman",
                    "PS - Palestine, State of",
                    "QA - Qatar",
                    "SA - Saudi Arabia",
                    "SY - Syrian Arab Republic",
                    "TR - Turkey",
                    "YE - Yemen",
                ]
            }
        ]
    },
    {
        "009 - Oceania": [
            {
                "053 - Australia and New Zealand": [
                    "AU - Australia",
                    "NF - Norfolk Island",
                    "NZ - New Zealand"
                ]
            },
            {
                "054 - Melanesia": [
                    "FJ - Fiji",
                    "NC - New Caledonia",
                    "PG - Papua New Guinea",
                    "SB - Solomon Islands",
                    "VU - Vanuatu"
                ]
            },
            {
                "057 - Micronesia": [
                    "FM - Micronesia",
                    "GU - Guam",
                    "KI - Kiribati",
                    "MH - Marshall Islands",
                    "MP - Northern Mariana Islands",
                    "NR - Nauru",
                    "PW - Palau"
                ]
            },
            {
                "061 - Polynesia": [
                    "AS - American Samoa",
                    "CK - Cook Islands",
                    "NU - Niue",
                    "PF - French Polynesia",
                    "PN - Pitcairn",
                    "TK - Tokelau",
                    "TO - Tonga",
                    "TV - Tuvalu",
                    "WF - Wallis and Futuna",
                    "WS - Samoa"
                ]
            }
        ]
    }
]


def region_choices(data):
    if isinstance(data, list):
        for v in data:
            yield from region_choices(v)
    elif isinstance(data, dict):
        for k, v in data.items():
            code, name = re.split(r'\s+-\s+', k, maxsplit=1)
            yield code, f'{code} - {name}'
            yield from region_choices(v)
    else:
        code, name = re.split(r'\s+-\s+', data, maxsplit=1)
        yield code, f'{code} - {name}'


REGION_CHOICES = sorted([('world', '001 - World')] + list(region_choices(REGION_DATA)), key=lambda x: x[1])


def camel_case(snake_str: str) -> str:
    """
    Convert a snake_case string to CamelCase.
    :param snake_str: The snake_case string to convert.
    :return: The CamelCase version of the string.
    """
    return ''.join(x.capitalize() for x in snake_str.split('_'))


def sanitize_field(field_spec: str) -> str:
    """
    Prepare a django database field lookup for display.
    :param field_spec: The field lookup as a string. Related fields with a '__' lookup separator are
    converted to '.' for display. snake case is converted to CamelCase.
    :return: Sanitized field lookup string.
    """

    return '.'.join([camel_case(name) for name in field_spec.split('__')])


def debug_value(value, name=None):
    """
    Returns a string representation of the value for debugging purposes.
    If 'name' is provided, it will be included in the output.
    """
    caller = getframeinfo(stack()[1][0])
    print('=' * 80)
    print(f'Name: {name}\nType: {type(value)}\nFile: {caller.filename}\nLine #: {caller.lineno}')
    print('-' * 80)
    print(yaml.dump(value))
    print('=' * 80)
    print('\n')
