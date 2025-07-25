from django.test import TestCase
from reportcraft.utils import ExpressionParser, FilterParser
from django.db.models import *
from django.db.models.functions import *


EXPRESSIONS = {
    "Published.Year": F('published__year'),
    "-Count(this)": -Count('id'),
    "Sum(Metrics.Citations) + Avg(Metrics.Mentions)": Sum('metrics__citations') + Avg('metrics__mentions'),
    "Sum(Metrics.Citations - Metrics.Mentions)": Sum(F('metrics__citations') - F('metrics__mentions')),
    "Avg(Metrics.Citations + Metrics.Mentions)": Avg(F('metrics__citations') + F('metrics__mentions')),
    "Count(Journal, distinct=True)": Count('journal', distinct=True),
    "Concat(Journal.Title, ' (', Journal.Issn, ')')": Concat(F('journal__title'), ' (', F('journal__issn'), ')'),
    "Avg(Journal.Metrics.ImpactFactor)": Avg('journal__metrics__impact_factor'),
    "Avg(Metrics.Citations) / Avg(Metrics.Mentions)": Avg('metrics__citations') / Avg('metrics__mentions'),
}

FILTERS = {
    "journal isnull True": Q(journal__isnull=True),
    "counts = 10": Q(counts__exact=10),
    "counts == 10.5": Q(counts__exact=10.5),
    "counts != 10": ~Q(counts__exact=10),
    "Citations has '100'": Q(citations__contains='100'),
    "Mentions < 50": Q(mentions__lt=50),
    "Name ~has 'chel'": Q(name__icontains='chel'),
    "Name ^= 'chel'": Q(name__startswith='chel'),
    "Name $= 'chel'": Q(name__endswith='chel'),
    "Name ^~ 'chel'": Q(name__istartswith='chel'),
    "Name $~ 'chel'": Q(name__iendswith='chel'),
    "Name ~= 'chel'": Q(name__iexact='chel'),
    "Citations !has '100'": ~Q(citations__contains='100'),
    "Mentions !< 50": ~Q(mentions__lt=50),
    "Name !~has 'chel'": ~Q(name__icontains='chel'),
    "Name !^= 'chel'": ~Q(name__startswith='chel'),
    "Name !$= 'chel'": ~Q(name__endswith='chel'),
    "Name !^~ 'chel'": ~Q(name__istartswith='chel'),
    "Name !$~ 'chel'": ~Q(name__iendswith='chel'),
    "Name !~= 'chel'": ~Q(name__iexact='chel'),
    "Citations >= 100": Q(citations__gte=100),
    "Mentions <= 50": Q(mentions__lte=50),
    "Citations > 100 and Mentions < 50": Q(citations__gt=100) & Q(mentions__lt=50),
    "Citations !> 100 and Mentions < 50": ~Q(citations__gt=100) & Q(mentions__lt=50),
    "Citations > 100 or Mentions < 50": Q(citations__gt=100) | Q(mentions__lt=50),
    "Citations > 100 and (Mentions < 50 or Size > 10)": Q(citations__gt=100) & (Q(mentions__lt=50) | Q(size__gt=10)),
}


def compare_expressions(expr1, expr2):
    """
    Compare two expressions for equality, ignoring whitespace and case.
    """
    for key in ['distinct', 'filter', 'default', 'source_expression', 'extra']:
        if expr1.__dict__.get(key) != expr2.__dict__.get(key):
            print(expr1.__dict__)
            print(expr2.__dict__)
            return False
    return True


class UtilsTestCase(TestCase):
    def test_expression_parser(self):
        parser = ExpressionParser()
        for expression, expected in EXPRESSIONS.items():
            result = parser.parse(expression)
            self.assertTrue(
                compare_expressions(result, expected),
                f"Failed for expression:`{expression}`,  {result!r} != {expected!r}"
            )

    def test_filter_parser(self):
        parser = FilterParser()
        for expression, expected in FILTERS.items():
            result = parser.parse(expression)
            self.assertEqual(result, expected, f"Failed for filter:`{expression}`, {result!r} != {expected!r}")

    def test_filter_valid_identifier(self):
        expr1 = 'Citations has "100"'
        parser = FilterParser(identifiers=['citations'])
        result1 = parser.parse(expr1)
        self.assertEqual(result1, Q(citations__contains='100'), f"Failed for valid identifier :`{expr1}`, {result1!r}")
        expr2 = 'Mentions <  50'
        try:
            result1 = parser.parse(expr2)
        except ValueError:
            pass
        else:
            self.fail(f"Expected ValueError for invalid identifier in expression: `{expr2}`")

    def test_silent_failure(self):
        expr1 = 'Citations + 100'
        parser = FilterParser()
        try:
            result1 = parser.parse(expr1, silent=True)
        except ValueError:
            self.fail(f"Unexpected ValueError for silent parsing: `{expr1}`")
        else:
            self.assertEqual(result1, Q(), f"Invalid return value:`{expr1}`, {result1!r}")