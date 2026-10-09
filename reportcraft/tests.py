import json
from django.test import TestCase, Client, RequestFactory, override_settings
from django.template.loader import render_to_string
from django.urls import path, include, reverse
from django.db.models import *
from django.db.models.functions import *

from reportcraft.models import Report
from reportcraft.registry import ReportRegistry, site, CatalogItem
from reportcraft.utils import ExpressionParser, FilterParser, merge_data, apply_defaults
from reportcraft.views import DictReportView, CodeReportView, ReportIndexView
from reportcraft.code import (
    BarChartEntry,
    CodeReport,
    QuerySetDataset,
    RichTextEntry,
    StaticDataset,
    TableEntry,
)


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
    "Count(Journal, filter=(Journal.Metrics.ImpactFactor > 5))": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5)),
    "Count(Journal, filter=(Journal.Metrics.ImpactFactor > 5) & (Journal.Publisher = 'Springer'))": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5) & Q(journal__publisher='Springer')),
    "Count(Journal, filters=(Journal.Metrics.ImpactFactor > 5))": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5)),
    "Count(Journal, filters=(Journal.Metrics.ImpactFactor > 5) & (Journal.Publisher = 'Springer'))": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5) & Q(journal__publisher='Springer')),
    "Count(Journal, filters='Journal.Metrics.ImpactFactor > 5')": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5)),
    "Count(Journal, filters=\"Journal.Metrics.ImpactFactor > 5 and Journal.Publisher = 'Springer'\")": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5) & Q(journal__publisher='Springer')),
    "Count(Journal, filter='Journal.Metrics.ImpactFactor > 5')": Count('journal', filter=Q(journal__metrics__impact_factor__gt=5)),
    "Avg(Journal.Metrics.ImpactFactor, filter=(Journal.Metrics.Year = 2000))": Avg('journal__metrics__impact_factor', filter=Q(journal__metrics__year=2000)),
    "Avg(Journal.Metrics.ImpactFactor, filters=(Journal.Metrics.Year = 2000))": Avg('journal__metrics__impact_factor', filter=Q(journal__metrics__year=2000)),
    "Avg(Journal.Metrics.ImpactFactor, filter=(Journal.Metrics.Year = Published.Year))": Avg('journal__metrics__impact_factor', filter=Q(journal__metrics__year=F('published__year'))),
    "Avg(Journal.Metrics.ImpactFactor, filters=(Journal.Metrics.Year = Published.Year))": Avg('journal__metrics__impact_factor', filter=Q(journal__metrics__year=F('published__year'))),
}

FILTERS = {
    "Journal.Metrics.Year = Published.Year": Q(journal__metrics__year__exact=F('published__year')),
    "Journal.Metrics.Year = Published.Year + 1": Q(journal__metrics__year__exact=F('published__year') + 1),
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


def _normalize_q(q):
    if not isinstance(q, Q):
        return q
    new_q = Q()
    new_q.connector = q.connector
    new_q.negated = q.negated
    new_children = []
    for child in q.children:
        if isinstance(child, tuple) and len(child) == 2:
            k, v = child
            if k.endswith('__exact'):
                k = k[:-7]
            new_children.append((k, v))
        elif isinstance(child, Q):
            new_children.append(_normalize_q(child))
        else:
            new_children.append(child)
    new_q.children = new_children
    return new_q


def compare_expressions(expr1, expr2):
    """
    Compare two expressions for equality, ignoring whitespace and case.
    """
    for key in ['distinct', 'filter', 'default', 'source_expression', 'extra']:
        val1 = expr1.__dict__.get(key)
        val2 = expr2.__dict__.get(key)
        if key == 'filter' and val1 is not None and val2 is not None:
            q1 = val1.source_expressions[0] if hasattr(val1, 'source_expressions') and val1.source_expressions else val1
            q2 = val2.source_expressions[0] if hasattr(val2, 'source_expressions') and val2.source_expressions else val2
            if _normalize_q(q1) == _normalize_q(q2):
                continue
        if val1 != val2:
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

    def test_datafield_get_expression_with_filters(self):
        from reportcraft.models import DataField
        expected = Count('journal', filter=Q(journal__metrics__impact_factor__gt=5))

        field = DataField(expression="Count(Journal, filters=(Journal.Metrics.ImpactFactor > 5))")
        expr = field.get_expression()
        self.assertTrue(compare_expressions(expr, expected), f"Failed for DataField expr: {expr!r}")

        field_str = DataField(expression="Count(Journal, filters='Journal.Metrics.ImpactFactor > 5')")
        expr_str = field_str.get_expression()
        self.assertTrue(compare_expressions(expr_str, expected), f"Failed for DataField string expr: {expr_str!r}")

        field_filter = DataField(expression="Count(Journal, filter=(Journal.Metrics.ImpactFactor > 5))")
        expr_filter = field_filter.get_expression()
        self.assertTrue(compare_expressions(expr_filter, expected), f"Failed for DataField filter expr: {expr_filter!r}")

    def test_current_temporal_functions(self):
        from django.utils import timezone
        from reportcraft.functions import ThisYear, ThisMonth, ThisQuarter, ThisDay, ThisWeek, Today, Now
        parser = ExpressionParser()

        active_date = timezone.localdate()

        res_year = parser.parse("ThisYear()")
        self.assertIsInstance(res_year, ThisYear)
        self.assertEqual(res_year.value, active_date.year)

        res_month = parser.parse("ThisMonth()")
        self.assertIsInstance(res_month, ThisMonth)
        self.assertEqual(res_month.value, active_date.month)

        res_quarter = parser.parse("ThisQuarter()")
        self.assertIsInstance(res_quarter, ThisQuarter)
        self.assertEqual(res_quarter.value, (active_date.month - 1) // 3 + 1)

        res_day = parser.parse("ThisDay()")
        self.assertIsInstance(res_day, ThisDay)
        self.assertEqual(res_day.value, active_date.day)

        res_week = parser.parse("ThisWeek()")
        self.assertIsInstance(res_week, ThisWeek)
        self.assertEqual(res_week.value, active_date.isocalendar().week)

        res_today = parser.parse("Today()")
        self.assertIsInstance(res_today, Today)
        self.assertEqual(res_today.value, active_date)

        res_now = parser.parse("Now()")
        self.assertIsInstance(res_now, Now)

        # Compound expression
        res_compound = parser.parse("ThisYear() - 1")
        self.assertEqual(repr(res_compound), repr(ThisYear() - Value(1)))

        # ORM QuerySet execution
        from demo.example.models import Country
        c = Country.objects.create(name="TemporalTestCountry", code="TTC")
        annotated = Country.objects.filter(pk=c.pk).annotate(
            cur_year=ThisYear(),
            cur_month=ThisMonth(),
            cur_quarter=ThisQuarter(),
            cur_day=ThisDay(),
            cur_week=ThisWeek(),
            cur_today=Today(),
            cur_now=Now(),
        ).first()
        self.assertEqual(annotated.cur_year, active_date.year)
        self.assertEqual(annotated.cur_month, active_date.month)
        self.assertEqual(annotated.cur_quarter, (active_date.month - 1) // 3 + 1)
        self.assertEqual(annotated.cur_day, active_date.day)
        self.assertEqual(annotated.cur_week, active_date.isocalendar().week)
        self.assertEqual(annotated.cur_today, active_date)
        self.assertIsNotNone(annotated.cur_now)

    def test_year_bucket_functions(self):
        import datetime
        from demo.example.models import Journal, Publication, Metric
        from reportcraft.functions import (
            YearBucket, Decade, Lustrum, Quadrennial, Triennial, Biennial, Century
        )
        parser = ExpressionParser()

        # 1. Parser verification
        res_dec = parser.parse("Decade(Published)")
        self.assertIsInstance(res_dec, Decade)

        res_lus = parser.parse("Lustrum(Published)")
        self.assertIsInstance(res_lus, Lustrum)

        res_tri = parser.parse("Triennial(Published)")
        self.assertIsInstance(res_tri, Triennial)

        res_bie = parser.parse("Biennial(Published)")
        self.assertIsInstance(res_bie, Biennial)

        res_qua = parser.parse("Quadrennial(Published)")
        self.assertIsInstance(res_qua, Quadrennial)

        res_cen = parser.parse("Century(Published)")
        self.assertIsInstance(res_cen, Century)

        res_yb = parser.parse("YearBucket(Published, size=5, anchor=2000)")
        self.assertIsInstance(res_yb, YearBucket)

        # 2. ORM execution with DateField (Polymorphic Date)
        j = Journal.objects.create(name="Bucketing Journal")
        p2026 = Publication.objects.create(journal=j, title="P2026", published=datetime.date(2026, 5, 15))
        p2023 = Publication.objects.create(journal=j, title="P2023", published=datetime.date(2023, 11, 1))
        p1995 = Publication.objects.create(journal=j, title="P1995", published=datetime.date(1995, 4, 20))
        p1999 = Publication.objects.create(journal=j, title="P1999", published=datetime.date(1999, 12, 31))

        qs = Publication.objects.filter(journal=j).annotate(
            decade=Decade('published'),
            lustrum=Lustrum('published'),
            triennial=Triennial('published'),
            biennial=Biennial('published'),
            quadrennial=Quadrennial('published'),
            century=Century('published'),
            custom_yb=YearBucket('published', size=7, anchor=2020),
            null_decade=Decade(Value(None, output_field=DateField())),
        )

        r2026 = qs.get(pk=p2026.pk)
        self.assertEqual(r2026.decade, "2020s")
        self.assertEqual(r2026.lustrum, "2025-2029")
        self.assertEqual(r2026.triennial, "2025-2027")
        self.assertEqual(r2026.biennial, "2026-2027")
        self.assertEqual(r2026.quadrennial, "2024-2027")
        self.assertEqual(r2026.century, "2000s")
        self.assertEqual(r2026.custom_yb, "2020-2026")
        self.assertIsNone(r2026.null_decade)

        r2023 = qs.get(pk=p2023.pk)
        self.assertEqual(r2023.decade, "2020s")
        self.assertEqual(r2023.lustrum, "2020-2024")
        self.assertEqual(r2023.triennial, "2022-2024")
        self.assertEqual(r2023.biennial, "2022-2023")
        self.assertEqual(r2023.quadrennial, "2020-2023")
        self.assertEqual(r2023.century, "2000s")

        # Historical dates before anchor 2000 (Floored division verification)
        r1995 = qs.get(pk=p1995.pk)
        self.assertEqual(r1995.decade, "1990s")
        self.assertEqual(r1995.lustrum, "1995-1999")
        self.assertEqual(r1995.triennial, "1995-1997")
        self.assertEqual(r1995.biennial, "1994-1995")
        self.assertEqual(r1995.quadrennial, "1992-1995")
        self.assertEqual(r1995.century, "1900s")

        r1999 = qs.get(pk=p1999.pk)
        self.assertEqual(r1999.decade, "1990s")
        self.assertEqual(r1999.lustrum, "1995-1999")
        self.assertEqual(r1999.triennial, "1998-2000")
        self.assertEqual(r1999.biennial, "1998-1999")
        self.assertEqual(r1999.quadrennial, "1996-1999")
        self.assertEqual(r1999.century, "1900s")

        # 3. ORM execution with IntegerField (Polymorphic Integer Year)
        m = Metric.objects.create(journal=j, year=2024, impact_factor=4.5)
        m_res = Metric.objects.filter(pk=m.pk).annotate(
            decade=Decade('year'),
            lustrum=Lustrum('year'),
            triennial=Triennial('year'),
        ).first()
        self.assertEqual(m_res.decade, "2020s")
        self.assertEqual(m_res.lustrum, "2020-2024")
        self.assertEqual(m_res.triennial, "2022-2024")



    def test_filter_parser_dotted_and_operators(self):
        parser = FilterParser()
        res1 = parser.parse("Journal.Metrics.ImpactFactor > 5")
        self.assertEqual(res1, Q(journal__metrics__impact_factor__gt=5))

        res2 = parser.parse("(Journal.Metrics.ImpactFactor > 5) & (Journal.Publisher = 'Springer')")
        self.assertEqual(res2, Q(journal__metrics__impact_factor__gt=5) & Q(journal__publisher__exact='Springer'))

        res3 = parser.parse("(Journal.Metrics.ImpactFactor > 5) | (Journal.Publisher = 'Springer')")
        self.assertEqual(res3, Q(journal__metrics__impact_factor__gt=5) | Q(journal__publisher__exact='Springer'))



TEST_REPORT_DICT = {
    'title': 'Executive Leadership KPI Overview',
    'description': 'A preformed dictionary report rendered directly at a custom URL endpoint.',
    'theme': 'default',
    'notes': 'Rendered via inline JSON embedding.',
    'sections': [
        {
            'title': 'High-Level Metrics',
            'style': 'row',
            'theme': 'default',
            'notes': 'Section notes.',
            'content': [
                {
                    'title': 'Active Projects',
                    'kind': 'richtext',
                    'style': 'col-md-4',
                    'text': '## 142',
                    'description': 'Active grants',
                },
                {
                    'title': 'Category Output',
                    'kind': 'bars',
                    'style': 'col-md-8',
                    'scheme': 'Live8',
                    'categories': 'Domain',
                    'values': ['Outputs'],
                    'data': [
                        {'Domain': 'Computer Science', 'Outputs': 225},
                        {'Domain': 'Biomedical Sciences', 'Outputs': 184},
                    ],
                }
            ]
        }
    ]
}


class SampleDictReportView(DictReportView):
    report_dict = TEST_REPORT_DICT


class CallableDictReportView(DictReportView):
    def get_report_dict(self, request=None):
        user = request.GET.get('user', 'Guest') if request else 'Guest'
        return {
            'title': f'Dynamic Report for {user}',
            'description': 'Generated on demand',
            'theme': 'default',
            'sections': [],
        }


class FunctionDictReportView(DictReportView):
    report_dict = staticmethod(lambda request=None: {'title': 'Staticmethod Report', 'sections': []})


class EmptyDictReportView(DictReportView):
    pass


SAMPLE_CODE_REPORT_DATASET = StaticDataset(
    data=[
        {"item": "Widget A", "count": 10, "category": "Hardware"},
        {"item": "Widget B", "count": 20, "category": "Hardware"},
        {"item": "Gadget X", "count": 15, "category": "Electronics"},
    ],
    labels={"item": "Item", "count": "Count", "category": "Category"}
)

SAMPLE_CODE_REPORT = CodeReport(
    title="Inventory Status Report",
    description="Live warehouse inventory tracking",
    theme="neutral",
    entries=[
        RichTextEntry(title="Overview", text="Stock levels"),
        BarChartEntry(
            title="Items",
            dataset=SAMPLE_CODE_REPORT_DATASET,
            categories="item",
            values="count",
        ),
    ]
)


class SampleCodeReportView(CodeReportView):
    report = SAMPLE_CODE_REPORT


class DynamicSubclassCodeReportView(CodeReportView):
    def get_report(self, request=None):
        user = request.GET.get('user', 'Guest') if request else 'Guest'
        return CodeReport(
            title=f"Dynamic Code Report for {user}",
            description="Generated dynamically",
            entries=[
                RichTextEntry(title="Greeting", text=f"Welcome {user}"),
            ]
        )


class DynamicSubclassNoArgCodeReportView(CodeReportView):
    def get_report(self):
        return CodeReport(
            title="Dynamic Report Without Request Arg",
            entries=[RichTextEntry(title="Info", text="No request param")]
        )


class CallableCodeReportView(CodeReportView):
    report = staticmethod(lambda request=None: CodeReport(
        title="Callable Code Report",
        entries=[RichTextEntry(title="Static Text", text="Content")]
    ))


class EmptyCodeReportView(CodeReportView):
    pass


urlpatterns = [
    path('reports/', include('reportcraft.urls')),
    path('dict-report/', SampleDictReportView.as_view(), name='sample-dict-report'),
    path('callable-dict-report/', CallableDictReportView.as_view(), name='callable-dict-report'),
    path('function-dict-report/', FunctionDictReportView.as_view(), name='function-dict-report'),
    path('empty-dict-report/', EmptyDictReportView.as_view(), name='empty-dict-report'),
    path('code-report/', SampleCodeReportView.as_view(), name='sample-code-report'),
    path('dynamic-code-report/', DynamicSubclassCodeReportView.as_view(), name='dynamic-code-report'),
    path('dynamic-noarg-code-report/', DynamicSubclassNoArgCodeReportView.as_view(), name='dynamic-noarg-code-report'),
    path('callable-code-report/', CallableCodeReportView.as_view(), name='callable-code-report'),
    path('empty-code-report/', EmptyCodeReportView.as_view(), name='empty-code-report'),
]


@override_settings(ROOT_URLCONF='reportcraft.tests')
class DictReportViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dict_report_html_rendering_inline_payload(self):
        """Verify that DictReportView renders HTML containing inline json_script and no fetch requirement."""
        response = self.client.get(reverse('sample-dict-report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reportcraft/report.html')

        content = response.content.decode('utf-8')
        # Check inline script tag
        self.assertIn('<script id="rc-report-data" type="application/json">', content)
        self.assertIn('Executive Leadership KPI Overview', content)
        self.assertIn('id="report-entry"', content)
        self.assertIn('const inlineDataEl = document.getElementById("rc-report-data");', content)

        # Parse inline payload from the script tag
        start_marker = '<script id="rc-report-data" type="application/json">'
        end_marker = '</script>'
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        raw_json = content[start_idx:end_idx].strip()
        data = json.loads(raw_json)

        self.assertEqual(data['title'], TEST_REPORT_DICT['title'])
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(len(data['sections'][0]['content']), 2)

    def test_dict_report_json_format_param(self):
        """Verify that ?format=json returns direct JSON."""
        response = self.client.get(reverse('sample-dict-report') + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['title'], TEST_REPORT_DICT['title'])
        self.assertEqual(len(data['sections'][0]['content']), 2)

    def test_dict_report_accept_header(self):
        """Verify that Accept: application/json returns direct JSON."""
        response = self.client.get(reverse('sample-dict-report'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['title'], TEST_REPORT_DICT['title'])

    def test_dict_report_complex_accept_header(self):
        """Verify that compound Accept headers containing application/json return direct JSON."""
        response = self.client.get(
            reverse('sample-dict-report'),
            HTTP_ACCEPT='application/json, text/javascript, */*; q=0.01'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['title'], TEST_REPORT_DICT['title'])

    def test_callable_dict_report(self):
        """Verify that callable get_report_dict handles requests with query params."""
        # JSON mode
        response = self.client.get(reverse('callable-dict-report') + '?user=Alice&format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Dynamic Report for Alice')

        # HTML mode
        response = self.client.get(reverse('callable-dict-report') + '?user=Alice')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Dynamic Report for Alice', content)

    def test_function_dict_report(self):
        """Verify that staticmethod / function report_dict attribute works."""
        response = self.client.get(reverse('function-dict-report') + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Staticmethod Report')

    def test_empty_dict_report(self):
        """Verify default fallback when report_dict is None."""
        response = self.client.get(reverse('empty-dict-report'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<span id="report-title">Report</span>', content)

    def test_database_report_backwards_compatibility(self):
        """Verify that Ajax fetch is used when no payload is provided without errors."""
        report = Report.objects.create(
            slug='test-db-report',
            title='Database Report',
            description='Stored in SQLite'
        )
        response = self.client.get(reverse('report-view', kwargs={'slug': report.slug}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('fetch("/reports/api/reports/test-db-report/?")', content)

    def test_report_embed_inline_payload(self):
        """Verify that report-embed.html renders inline json_script when payload is provided."""
        rendered = render_to_string('reportcraft/report-embed.html', {
            'report': {'theme': 'default'},
            'payload': TEST_REPORT_DICT,
        })
        self.assertIn('<script id="rc-report-data" type="application/json">', rendered)
        self.assertIn('Executive Leadership KPI Overview', rendered)
        self.assertIn('const inlineDataEl = document.getElementById("rc-report-data");', rendered)

    def test_report_embed_fallback_to_ajax(self):
        """Verify that report-embed.html renders fetch call when payload is not provided."""
        rendered = render_to_string('reportcraft/report-embed.html', {
            'report': {'theme': 'default'},
            'data_url': '/reports/api/reports/test-embed/',
            'query': '?param=1',
        })
        self.assertNotIn('<script id="rc-report-data" type="application/json">', rendered)
        self.assertIn('fetch("/reports/api/reports/test-embed/?param=1")', rendered)


@override_settings(ROOT_URLCONF='reportcraft.tests')
class CodeReportViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_code_report_html_rendering_inline_payload(self):
        """Verify that CodeReportView renders HTML containing inline json_script and reportcraft JS."""
        response = self.client.get(reverse('sample-code-report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reportcraft/report.html')

        content = response.content.decode('utf-8')
        self.assertIn('<script id="rc-report-data" type="application/json">', content)
        self.assertIn('Inventory Status Report', content)
        self.assertIn('id="report-entry"', content)
        self.assertIn('const inlineDataEl = document.getElementById("rc-report-data");', content)

        # Parse inline payload from the script tag
        start_marker = '<script id="rc-report-data" type="application/json">'
        end_marker = '</script>'
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        raw_json = content[start_idx:end_idx].strip()
        data = json.loads(raw_json)

        self.assertEqual(data['title'], 'Inventory Status Report')
        self.assertEqual(data['description'], 'Live warehouse inventory tracking')
        self.assertEqual(data['theme'], 'neutral')
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(len(data['sections'][0]['content']), 2)
        self.assertEqual(data['sections'][0]['content'][0]['kind'], 'richtext')
        self.assertEqual(data['sections'][0]['content'][1]['kind'], 'bars')

    def test_code_report_json_format_param(self):
        """Verify that ?format=json returns direct JsonResponse."""
        response = self.client.get(reverse('sample-code-report') + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['title'], 'Inventory Status Report')
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(len(data['sections'][0]['content']), 2)

    def test_code_report_accept_header(self):
        """Verify that Accept: application/json returns direct JsonResponse."""
        response = self.client.get(reverse('sample-code-report'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['title'], 'Inventory Status Report')

    def test_code_report_complex_accept_header(self):
        """Verify that compound Accept headers return direct JsonResponse."""
        response = self.client.get(
            reverse('sample-code-report'),
            HTTP_ACCEPT='application/json, text/javascript, */*; q=0.01'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['title'], 'Inventory Status Report')

    def test_code_report_runtime_filter_propagation_json(self):
        """Verify that query parameters are propagated as filters in JSON mode."""
        response = self.client.get(reverse('sample-code-report') + '?item=Widget+A&format=json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        bars_data = data['sections'][0]['content'][1]['data']
        self.assertEqual(len(bars_data), 1)
        self.assertEqual(bars_data[0]['Item'], 'Widget A')

    def test_code_report_runtime_filter_propagation_html(self):
        """Verify that query parameters are propagated as filters in HTML inline mode."""
        response = self.client.get(reverse('sample-code-report') + '?category=Electronics')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        start_marker = '<script id="rc-report-data" type="application/json">'
        end_marker = '</script>'
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        raw_json = content[start_idx:end_idx].strip()
        data = json.loads(raw_json)
        bars_data = data['sections'][0]['content'][1]['data']
        self.assertEqual(len(bars_data), 1)
        self.assertEqual(bars_data[0]['Item'], 'Gadget X')

    def test_dynamic_subclass_override_get_report(self):
        """Verify dynamic subclass override of get_report(self, request)."""
        # JSON mode
        response = self.client.get(reverse('dynamic-code-report') + '?user=Alice&format=json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Dynamic Code Report for Alice')
        self.assertEqual(data['sections'][0]['content'][0]['text'], 'Welcome Alice')

        # HTML mode
        response = self.client.get(reverse('dynamic-code-report') + '?user=Bob')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Dynamic Code Report for Bob', content)
        self.assertIn('Welcome Bob', content)

    def test_dynamic_subclass_no_arg_get_report(self):
        """Verify dynamic subclass override of get_report(self) with no request arg."""
        response = self.client.get(reverse('dynamic-noarg-code-report') + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Dynamic Report Without Request Arg')

    def test_callable_report_attribute(self):
        """Verify callable report attribute."""
        response = self.client.get(reverse('callable-code-report') + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Callable Code Report')

    def test_empty_code_report_view(self):
        """Verify fallback when report is None."""
        response = self.client.get(reverse('empty-code-report'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<span id="report-title">Report</span>', content)

        json_response = self.client.get(reverse('empty-code-report') + '?format=json')
        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json_response.json(), {})

    def test_context_data_contains_code_report(self):
        """Verify context data includes code_report."""
        response = self.client.get(reverse('sample-code-report'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('code_report', response.context)
        self.assertIs(response.context['code_report'], SAMPLE_CODE_REPORT)

    def test_code_report_with_queryset_dataset(self):
        """Verify CodeReportView works with QuerySetDataset and propagates runtime filters."""
        Report.objects.create(title="Alpha Report", slug="alpha-report", theme="light")
        Report.objects.create(title="Beta Report", slug="beta-report", theme="dark")

        qs_ds = QuerySetDataset(Report.objects.all(), fields=["title", "slug", "theme"])
        orm_report = CodeReport(
            title="ORM Reports",
            entries=[
                BarChartEntry(title="All Reports", dataset=qs_ds, categories="title", values="slug")
            ]
        )

        class ORMCodeReportView(CodeReportView):
            report = orm_report

        request = RequestFactory().get('/fake-path/?theme=dark&format=json')
        view = ORMCodeReportView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        chart_data = data['sections'][0]['content'][0]['data']
        self.assertEqual(len(chart_data), 1)
        self.assertEqual(chart_data[0]['Title'], 'Beta Report')

    def test_direct_method_calls(self):
        """Verify get_report() and get_report_dict() work when called directly without request."""
        view = SampleCodeReportView()
        self.assertIs(view.get_report(), SAMPLE_CODE_REPORT)
        report_dict = view.get_report_dict()
        self.assertEqual(report_dict['title'], 'Inventory Status Report')
        self.assertEqual(len(report_dict['sections']), 1)


from demo.example.models import Country, Institution
from reportcraft.models import DataSource, Entry, Report
from reportcraft.protocols import (
    DatasetProtocol,
    EntryProtocol,
    FieldCollectionProtocol,
    FieldValuesListProtocol,
    ReportEntryProtocol,
)
from reportcraft.code import (
    BarChartEntry,
    CodeEntry,
    CodeReport,
    ColumnChartEntry,
    DonutChartEntry,
    GeoChartEntry,
    HistogramEntry,
    InMemFieldCollection,
    InMemFieldQuerySet,
    LayoutRow,
    LikertEntry,
    PieChartEntry,
    PlotEntry,
    QuerySetDataset,
    RichTextEntry,
    StaticDataset,
    TableEntry,
    TimelineEntry,
    Width,
)


class ProtocolsTestCase(TestCase):
    def test_field_protocols(self):
        qs = InMemFieldQuerySet(["col1", "col2"])
        self.assertIsInstance(qs, FieldValuesListProtocol)

        coll = InMemFieldCollection(["col1", "col2"])
        self.assertIsInstance(coll, FieldCollectionProtocol)

    def test_dataset_protocols(self):
        static_ds = StaticDataset(data=[{"a": 1, "b": 2}], labels={"a": "Alpha"})
        self.assertIsInstance(static_ds, DatasetProtocol)

        qs_ds = QuerySetDataset(Report.objects.all())
        self.assertIsInstance(qs_ds, DatasetProtocol)

        report = Report.objects.create(title="Prot Report", slug="prot-report")
        ds = DataSource.objects.create(name="Prot DS")
        self.assertIsInstance(ds, DatasetProtocol)

    def test_entry_protocols(self):
        code_entry = CodeEntry(title="Test", kind="table")
        self.assertIsInstance(code_entry, EntryProtocol)
        self.assertIsInstance(code_entry, ReportEntryProtocol)

        table_entry = TableEntry(title="Table")
        self.assertIsInstance(table_entry, EntryProtocol)
        self.assertIsInstance(table_entry, ReportEntryProtocol)

        report = Report.objects.create(title="E Report", slug="e-report")
        orm_entry = Entry.objects.create(report=report, title="ORM Entry", kind="table")
        self.assertIsInstance(orm_entry, EntryProtocol)
        self.assertIsInstance(orm_entry, ReportEntryProtocol)


class DatasetsTestCase(TestCase):
    def test_in_mem_field_collection_and_queryset(self):
        fields = InMemFieldCollection(["name", "age", "city"])
        self.assertEqual(list(fields.all()), ["name", "age", "city"])
        self.assertEqual(len(fields), 3)
        self.assertIn("age", fields)

        # values_list flat vs non-flat
        self.assertEqual(fields.values_list("name", flat=True), ["name", "age", "city"])
        self.assertEqual(fields.values_list("name", flat=False), [("name",), ("age",), ("city",)])

        # filter preserving requested order
        filtered = fields.filter(name__in=["city", "name", "missing"])
        self.assertEqual(list(filtered.values_list("name", flat=True)), ["city", "name"])

        # filter with empty or None
        self.assertEqual(list(fields.filter(name__in=[]).values_list("name", flat=True)), [])
        self.assertEqual(list(fields.filter(name__in=None).values_list("name", flat=True)), [])

    def test_static_dataset(self):
        raw_data = [
            {"region": "North", "sales": 100, "active": True},
            {"region": "South", "sales": 200, "active": False},
            {"region": "East", "sales": 150, "active": True},
        ]
        ds = StaticDataset(data=raw_data, labels={"region": "Territory"})
        labels = ds.get_labels()
        self.assertEqual(labels["region"], "Territory")
        self.assertEqual(labels["sales"], "Sales")

        # get_data with no filter
        self.assertEqual(len(ds.get_data()), 3)

        # get_data with callable select
        filtered = ds.get_data(select=lambda row: row["sales"] > 120)
        self.assertEqual(len(filtered), 2)

        # get_data with runtime filters
        filtered_runtime = ds.get_data(filters={"region": "South"})
        self.assertEqual(len(filtered_runtime), 1)
        self.assertEqual(filtered_runtime[0]["sales"], 200)

        # StaticDataset with empty data and custom fields
        empty_ds = StaticDataset(fields=["id", "name"])
        self.assertEqual(list(empty_ds.fields.all()), ["id", "name"])
        self.assertEqual(empty_ds.get_data(), [])

    def test_queryset_dataset(self):
        Country.objects.create(name="Canada", code="CAN", population=38000000, continent="Americas")
        Country.objects.create(name="France", code="FRA", population=67000000, continent="Europe")
        Country.objects.create(name="Japan", code="JPN", population=125000000, continent="Asia")

        qs = Country.objects.all()
        ds = QuerySetDataset(qs, labels={"name": "Country Name"})
        labels = ds.get_labels()
        self.assertEqual(labels["name"], "Country Name")
        self.assertIn("code", labels)
        self.assertIn("population", labels)

        data = ds.get_data()
        self.assertEqual(len(data), 3)

        pop_filter = ds.get_data(select=Q(population__gte=50000000))
        self.assertEqual(len(pop_filter), 2)

        asia = ds.get_data(filters={"continent": "Asia"})
        self.assertEqual(len(asia), 1)
        self.assertEqual(asia[0]["name"], "Japan")

        big = ds.get_data(filters={"population__gt": 100000000})
        self.assertEqual(len(big), 1)
        self.assertEqual(big[0]["name"], "Japan")

        cleaned = ds.clean_filters({"invalid_field": "123", "population": 38000000, "bad__nested__too__deep": 1})
        self.assertEqual(cleaned, {"population": 38000000})

        ordered = ds.get_data(order_by=["-population"], limit=2)
        self.assertEqual(len(ordered), 2)
        self.assertEqual(ordered[0]["name"], "Japan")

    def test_queryset_dataset_with_annotations(self):
        Country.objects.create(name="Brazil", code="BRA", population=210000000, area=8515767.0)
        qs = Country.objects.filter(code="BRA").annotate(density=F("population") / F("area"))
        ds = QuerySetDataset(qs)
        self.assertIn("density", ds.fields.all())
        labels = ds.get_labels()
        self.assertEqual(labels["density"], "Density")
        data = ds.get_data()
        self.assertEqual(len(data), 1)
        self.assertIn("density", data[0])

    def test_queryset_dataset_relation_fields(self):
        c = Country.objects.create(name="Canada", code="CAN")
        Institution.objects.create(name="UofT", city="Toronto", country=c)

        # Relation field requested via select (list of strings)
        ds1 = QuerySetDataset(Institution.objects.all())
        data1 = ds1.get_data(select=["name", "country__name"])
        self.assertEqual(len(data1), 1)
        self.assertIn("country__name", data1[0])
        self.assertEqual(data1[0]["country__name"], "Canada")

        # Relation field requested via select (single string)
        data1_single = ds1.get_data(select="country__name")
        self.assertEqual(len(data1_single), 1)
        self.assertIn("country__name", data1_single[0])
        self.assertEqual(data1_single[0]["country__name"], "Canada")

        # Relation field declared in self.fields
        ds2 = QuerySetDataset(Institution.objects.all(), fields=["name", "country__name"])
        data2 = ds2.get_data()
        self.assertEqual(len(data2), 1)
        self.assertIn("country__name", data2[0])
        self.assertEqual(data2[0]["country__name"], "Canada")

        # Relation field preserved even when invalid field triggers fallback logic
        ds3 = QuerySetDataset(Institution.objects.all(), fields=["name", "country__name", "non_existent_field"])
        data3 = ds3.get_data()
        self.assertEqual(len(data3), 1)
        self.assertIn("country__name", data3[0])
        self.assertEqual(data3[0]["country__name"], "Canada")


class WidthTestCase(TestCase):
    def test_width_enum_and_resolve(self):
        self.assertEqual(Width.FULL, "col-md-12")
        self.assertEqual(Width.HALF, "col-md-6")
        self.assertEqual(Width.THIRD, "col-md-4")
        self.assertEqual(Width.QUARTER, "col-md-3")

        # integer resolve
        self.assertEqual(Width.resolve(1), "col-md-1")
        self.assertEqual(Width.resolve(6), "col-md-6")
        self.assertEqual(Width.resolve(12), "col-md-12")
        with self.assertRaises(ValueError):
            Width.resolve(0)
        with self.assertRaises(ValueError):
            Width.resolve(13)

        # string integer resolve
        self.assertEqual(Width.resolve("6"), "col-md-6")
        with self.assertRaises(ValueError):
            Width.resolve("15")

        # string name resolve
        self.assertEqual(Width.resolve("half"), "col-md-6")
        self.assertEqual(Width.resolve("HALF"), "col-md-6")

        # custom CSS classes preserved
        self.assertEqual(Width.resolve("col-lg-8"), "col-lg-8")

        # None defaults to FULL
        self.assertEqual(Width.resolve(None), "col-md-12")

        # Width constructor lookup
        self.assertEqual(Width(6), Width.HALF)
        self.assertEqual(Width("col-md-6"), Width.HALF)
        self.assertEqual(Width("half"), Width.HALF)


class EntriesTestCase(TestCase):
    def setUp(self):
        self.sample_data = [
            {"product": "Apples", "category": "Fruit", "sales": 100, "date": "2026-01-01"},
            {"product": "Bananas", "category": "Fruit", "sales": 200, "date": "2026-01-02"},
            {"product": "Carrots", "category": "Vegetable", "sales": 150, "date": "2026-01-03"},
        ]
        self.dataset = StaticDataset(
            data=self.sample_data,
            labels={"product": "Product", "category": "Category", "sales": "Sales", "date": "Date"}
        )

    def test_code_entry_base(self):
        entry = CodeEntry(
            title="My Entry",
            kind="table",
            width=6,
            description="Entry desc",
            notes="Entry notes",
            filters="sales > 100",
        )
        self.assertEqual(entry.style, "col-md-6")
        q_filter = entry.get_filters()
        self.assertIsInstance(q_filter, Q)
        self.assertEqual(q_filter, Q(sales__gt=100))

    def test_table_entry(self):
        table = TableEntry(
            title="Sales Table",
            dataset=self.dataset,
            rows=["product"],
            columns="category",
            values="sales",
            total_row=True,
            total_column=True,
            width=Width.HALF,
        )
        self.assertEqual(table.style, "col-md-6")
        self.assertEqual(table.kind, "table")
        payload = table.generate()
        self.assertEqual(payload["title"], "Sales Table")
        self.assertEqual(payload["kind"], "table")
        self.assertIn("data", payload)

    def test_bar_and_column_chart_entry(self):
        bar = BarChartEntry(
            title="Sales Bars",
            dataset=self.dataset,
            categories="product",
            values=["sales"],
            scheme="Tableau10",
            sort_by="sales",
            width=Width.FULL,
        )
        self.assertEqual(bar.kind, "bars")
        payload = bar.generate()
        self.assertEqual(payload["title"], "Sales Bars")
        self.assertEqual(payload["kind"], "bars")

        col = ColumnChartEntry(
            title="Sales Columns",
            dataset=self.dataset,
            categories="product",
            values="sales",
            scheme="Tableau10",
        )
        self.assertEqual(col.kind, "columns")
        col_payload = col.generate()
        self.assertEqual(col_payload["kind"], "columns")

    def test_pie_and_donut_chart_entry(self):
        pie = PieChartEntry(
            title="Sales Pie",
            dataset=self.dataset,
            categories="category",
            values="sales",
        )
        self.assertEqual(pie.kind, "pie")
        pie_payload = pie.generate()
        self.assertEqual(pie_payload["kind"], "pie")
        self.assertIn("data", pie_payload)

        donut = DonutChartEntry(
            title="Sales Donut",
            dataset=self.dataset,
            categories="category",
            values="sales",
        )
        self.assertEqual(donut.kind, "donut")
        donut_payload = donut.generate()
        self.assertEqual(donut_payload["kind"], "donut")

    def test_plot_entry(self):
        plot = PlotEntry(
            title="Sales Plot",
            dataset=self.dataset,
            x="date",
            y="sales",
            color_by="category",
        )
        self.assertEqual(plot.kind, "plot")
        payload = plot.generate()
        self.assertEqual(payload["kind"], "xyplot")
        self.assertIn("features", payload)

    def test_histogram_entry(self):
        hist = HistogramEntry(
            title="Sales Dist",
            dataset=self.dataset,
            values="sales",
            bins=5,
        )
        self.assertEqual(hist.kind, "histogram")
        payload = hist.generate()
        self.assertEqual(payload["kind"], "histogram")

    def test_timeline_entry(self):
        tl_ds = StaticDataset(
            data=[
                {"event": "Alpha", "start": "2026-01-01", "end": "2026-01-05"},
                {"event": "Beta", "start": "2026-01-06", "end": "2026-01-10"},
            ],
            labels={"event": "Event", "start": "Start", "end": "End"}
        )
        tl = TimelineEntry(
            title="Project Timeline",
            dataset=tl_ds,
            start="start",
            end="end",
            label="event",
        )
        self.assertEqual(tl.kind, "timeline")
        payload = tl.generate()
        self.assertEqual(payload["kind"], "timeline")

    def test_richtext_entry(self):
        rt = RichTextEntry(
            title="Notes",
            text="### Summary\nAll operations nominal.",
            width=Width.FULL,
        )
        self.assertEqual(rt.kind, "text")
        payload = rt.generate()
        self.assertEqual(payload["kind"], "richtext")
        self.assertEqual(payload["text"], "### Summary\nAll operations nominal.")

    def test_geochart_entry(self):
        geo_ds = StaticDataset(
            data=[{"country": "US", "cases": 1200}, {"country": "CA", "cases": 400}],
            labels={"country": "Country", "cases": "Cases"}
        )
        geo = GeoChartEntry(
            title="Global Map",
            dataset=geo_ds,
            locations="country",
            values="cases",
        )
        self.assertEqual(geo.kind, "map")
        payload = geo.generate()
        self.assertEqual(payload["kind"], "geochart")

    def test_likert_entry(self):
        likert_ds = StaticDataset(
            data=[
                {"q": "Q1", "ans": "Agree", "cnt": 10, "score": 1},
                {"q": "Q1", "ans": "Disagree", "cnt": 2, "score": -1},
            ],
            labels={"q": "Question", "ans": "Answer", "cnt": "Count", "score": "Score"}
        )
        likert = LikertEntry(
            title="Survey",
            dataset=likert_ds,
            questions="q",
            answers="ans",
            counts="cnt",
            scores="score",
        )
        self.assertEqual(likert.kind, "likert")
        payload = likert.generate()
        self.assertEqual(payload["kind"], "likert")


class CodeReportTestCase(TestCase):
    def setUp(self):
        self.dataset = StaticDataset(
            data=[
                {"item": "Widget A", "count": 10},
                {"item": "Widget B", "count": 20},
            ],
            labels={"item": "Item", "count": "Count"}
        )

    def test_code_report_declarative(self):
        report = CodeReport(
            title="Warehouse Inventory",
            slug="warehouse-inventory",
            theme="neutral",
            description="Daily stock count",
            notes="Generated automatically",
            entries=[
                RichTextEntry(title="Intro", text="Stock report"),
                BarChartEntry(title="Item Counts", dataset=self.dataset, categories="item", values="count"),
            ]
        )
        self.assertEqual(report.title, "Warehouse Inventory")
        self.assertEqual(len(report.entries), 2)

        payload = report.generate()
        self.assertEqual(payload["title"], "Warehouse Inventory")
        self.assertEqual(payload["description"], "Daily stock count")
        self.assertEqual(payload["theme"], "neutral")
        self.assertEqual(len(payload["sections"]), 1)
        self.assertEqual(len(payload["sections"][0]["content"]), 2)
        self.assertEqual(payload["sections"][0]["content"][0]["kind"], "richtext")
        self.assertEqual(payload["sections"][0]["content"][1]["kind"], "bars")

    def test_code_report_builder_methods(self):
        report = CodeReport(title="Modular Report")
        report.add_entry(RichTextEntry(title="Overview", text="Overview text"))
        self.assertEqual(len(report.entries), 1)

        report.add_section(
            title="Deep Dive",
            entries=[
                BarChartEntry(title="Bars", dataset=self.dataset, categories="item", values="count"),
            ],
            style="two-col",
            theme="dark",
            notes="Section notes"
        )
        self.assertEqual(len(report.entries), 2)
        self.assertEqual(len(report.sections), 1)

        payload = report.generate()
        self.assertEqual(len(payload["sections"]), 2)
        self.assertEqual(payload["sections"][0]["title"], "Deep Dive")
        self.assertEqual(payload["sections"][0]["theme"], "dark")
        self.assertEqual(len(payload["sections"][0]["content"]), 1)
        self.assertEqual(payload["sections"][1]["content"][0]["title"], "Overview")

    def test_code_report_runtime_filter_propagation(self):
        report = CodeReport(
            title="Filtered Report",
            entries=[
                BarChartEntry(title="Bars", dataset=self.dataset, categories="item", values="count"),
            ]
        )
        payload = report.generate(filters={"item": "Widget A"})
        bars_data = payload["sections"][0]["content"][0]["data"]
        # Should only contain Widget A
        self.assertEqual(len(bars_data), 1)
        self.assertEqual(bars_data[0]["Item"], "Widget A")

    def test_code_report_layout_row_and_standalone_entries(self):
        report = CodeReport(title="Layout Test", theme="neutral", notes="Base notes")
        e1 = RichTextEntry(title="Stand 1", text="Standalone 1")
        e2 = BarChartEntry(title="Row Entry", dataset=self.dataset, categories="item", values="count")
        e3 = RichTextEntry(title="Stand 2", text="Standalone 2")

        report.add_entry(e1)
        row = LayoutRow(title="First Row", entries=[e2], style="two-col", theme="dark", notes="Row notes")
        report.add_row(row)
        report.add_entry(e3)

        payload = report.generate()
        self.assertEqual(len(payload["sections"]), 2)
        # First section is the explicit LayoutRow
        self.assertEqual(payload["sections"][0]["title"], "First Row")
        self.assertEqual(payload["sections"][0]["theme"], "dark")
        self.assertEqual(len(payload["sections"][0]["content"]), 1)
        self.assertEqual(payload["sections"][0]["content"][0]["title"], "Row Entry")
        # Second section is the default LayoutRow combining standalone entries
        self.assertEqual(payload["sections"][1]["theme"], "neutral")
        self.assertEqual(len(payload["sections"][1]["content"]), 2)
        self.assertEqual(payload["sections"][1]["content"][0]["title"], "Stand 1")
        self.assertEqual(payload["sections"][1]["content"][1]["title"], "Stand 2")

    def test_categorical_chart_entry_hierarchy(self):
        from reportcraft.code.entries import _CategoricalChartEntry
        self.assertTrue(issubclass(BarChartEntry, _CategoricalChartEntry))
        self.assertTrue(issubclass(ColumnChartEntry, _CategoricalChartEntry))


class ReportRegistryTestCase(TestCase):
    def setUp(self):
        self.registry = ReportRegistry()
        self.report1 = CodeReport(
            title="Sales Report",
            slug="sales-report",
            description="Q1 Sales Overview",
        )
        self.report2 = CodeReport(
            title="Ops Report",
            slug="ops-report",
            description="Operations Metrics",
        )

    def tearDown(self):
        site.clear()

    def test_package_exports(self):
        from reportcraft import ReportRegistry as RootReportRegistry, site as root_site
        from reportcraft.code import ReportRegistry as CodePkgReportRegistry, site as code_pkg_site
        self.assertIs(RootReportRegistry, ReportRegistry)
        self.assertIs(root_site, site)
        self.assertIs(CodePkgReportRegistry, ReportRegistry)
        self.assertIs(code_pkg_site, site)

    def test_register_and_get_report(self):
        self.registry.register(self.report1)
        retrieved = self.registry.get_report("sales-report")
        self.assertEqual(retrieved, self.report1)
        self.assertIsNone(self.registry.get_report("non-existent"))

    def test_register_without_slug_raises_error(self):
        invalid_report = CodeReport(title="No Slug Report")
        with self.assertRaises(ValueError):
            self.registry.register(invalid_report)

    def test_register_decorator(self):
        rep = CodeReport(title="Deco Report", slug="deco-report")
        self.registry.register()(rep)
        self.assertEqual(self.registry.get_report("deco-report"), rep)

    def test_unregister_by_slug_and_object(self):
        self.registry.register(self.report1)
        self.registry.register(self.report2)
        self.assertEqual(self.registry.get_report("sales-report"), self.report1)

        # Unregister by slug
        self.registry.unregister("sales-report")
        self.assertIsNone(self.registry.get_report("sales-report"))

        # Unregister by object
        self.registry.unregister(self.report2)
        self.assertIsNone(self.registry.get_report("ops-report"))

        # Idempotent unregister of non-existent slug
        self.registry.unregister("non-existent")

    def test_catalog_items_and_in_catalog_flag(self):
        # report1 is in catalog, report2 is NOT
        self.registry.register(self.report1, in_catalog=True, section="finance")
        self.registry.register(self.report2, in_catalog=False, section="ops")

        items = self.registry.get_catalog_items()
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["slug"], "sales-report")
        self.assertEqual(item["title"], "Sales Report")
        self.assertEqual(item["description"], "Q1 Sales Overview")
        self.assertEqual(item["section"], "finance")
        self.assertTrue(item["in_catalog"])
        # Test attribute access on CatalogItem
        self.assertEqual(item.slug, "sales-report")
        self.assertEqual(item.title, "Sales Report")
        self.assertEqual(item.description, "Q1 Sales Overview")
        self.assertEqual(item.section, "finance")

        # report2 is still retrievable via get_report
        self.assertEqual(self.registry.get_report("ops-report"), self.report2)

    def test_section_filtering_in_registry(self):
        rep_fin = CodeReport(title="Finance Report", slug="fin-rep")
        rep_ops = CodeReport(title="Operations Report", slug="ops-rep")
        rep_gen = CodeReport(title="General Report", slug="gen-rep")

        self.registry.register(rep_fin, section="finance")
        self.registry.register(rep_ops, section="operations")
        self.registry.register(rep_gen)  # section is None

        all_items = self.registry.get_catalog_items()
        self.assertEqual(len(all_items), 3)

        fin_items = self.registry.get_catalog_items(section="finance")
        self.assertEqual(len(fin_items), 1)
        self.assertEqual(fin_items[0]["slug"], "fin-rep")

        ops_items = self.registry.get_catalog_items(section="operations")
        self.assertEqual(len(ops_items), 1)
        self.assertEqual(ops_items[0]["slug"], "ops-rep")


@override_settings(ROOT_URLCONF='reportcraft.tests')
class ReportIndexViewTestCase(TestCase):
    def setUp(self):
        site.clear()
        self.client = Client()
        self.factory = RequestFactory()
        self.orm_report1 = Report.objects.create(
            title="Database Report 1",
            slug="db-report-1",
            description="DB Report description",
            section="finance",
        )
        self.orm_report2 = Report.objects.create(
            title="Database Report 2",
            slug="db-report-2",
            description="Another DB report",
            section="operations",
        )
        self.code_report1 = CodeReport(
            title="Code Analytics",
            slug="code-analytics",
            description="Live code report",
        )
        self.code_report2 = CodeReport(
            title="Code Finance",
            slug="code-finance",
            description="Live finance metrics",
        )

    def tearDown(self):
        site.clear()

    def test_get_link_url_orm_report(self):
        view = ReportIndexView()
        url = view.get_link_url(self.orm_report1)
        self.assertEqual(url, reverse('report-view', kwargs={'slug': 'db-report-1'}))

    def test_get_link_url_dict_with_url(self):
        view = ReportIndexView()
        item = {"slug": "custom-rep", "url": "/custom/path/to/report/"}
        self.assertEqual(view.get_link_url(item), "/custom/path/to/report/")

    def test_get_link_url_dict_without_url(self):
        view = ReportIndexView()
        item = {"slug": "code-analytics"}
        self.assertEqual(view.get_link_url(item), reverse('report-view', kwargs={'slug': 'code-analytics'}))

    def test_get_link_url_object_with_url(self):
        view = ReportIndexView()
        rep = CodeReport(title="Custom URL Rep", slug="custom-url-rep")
        rep.url = "/custom/url/endpoint/"
        self.assertEqual(view.get_link_url(rep), "/custom/url/endpoint/")

    def test_get_link_url_object_without_url(self):
        view = ReportIndexView()
        rep = CodeReport(title="No URL Rep", slug="no-url-rep")
        self.assertEqual(view.get_link_url(rep), reverse('report-view', kwargs={'slug': 'no-url-rep'}))

    def test_index_view_combines_orm_and_code_reports(self):
        site.register(self.code_report1, in_catalog=True)
        site.register(self.code_report2, in_catalog=True, section="finance")

        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)

        # Context object_list should contain both ORM reports and registered code reports
        object_list = list(response.context['object_list'])
        slugs = [
            obj.slug if hasattr(obj, 'slug') else obj['slug']
            for obj in object_list
        ]
        self.assertIn("db-report-1", slugs)
        self.assertIn("db-report-2", slugs)
        self.assertIn("code-analytics", slugs)
        self.assertIn("code-finance", slugs)

        # Ensure rendered HTML displays links for both
        content = response.content.decode('utf-8')
        self.assertIn("Database Report 1", content)
        self.assertIn("Code Analytics", content)
        self.assertIn(reverse('report-view', kwargs={'slug': 'code-analytics'}), content)

    def test_index_view_section_filtering(self):
        site.register(self.code_report1, in_catalog=True, section="operations")
        site.register(self.code_report2, in_catalog=True, section="finance")

        class FinanceIndexView(ReportIndexView):
            limit_section = "finance"

        request = self.factory.get('/reports/view/')
        view = FinanceIndexView()
        view.setup(request)
        object_list = list(view.get_queryset())
        slugs = [
            obj.slug if hasattr(obj, 'slug') else obj['slug']
            for obj in object_list
        ]
        self.assertIn("db-report-1", slugs)
        self.assertIn("code-finance", slugs)
        self.assertNotIn("db-report-2", slugs)
        self.assertNotIn("code-analytics", slugs)

    def test_index_view_search_filtering(self):
        searchable_code_report = CodeReport(
            title="Quarterly Review",
            slug="quarterly-review",
            description="Comprehensive Q3 breakdown",
            notes="Quarterly finance analysis",
        )
        site.register(searchable_code_report, in_catalog=True)
        site.register(self.code_report1, in_catalog=True)

        response = self.client.get(reverse('report-list') + '?search=Quarterly')
        self.assertEqual(response.status_code, 200)
        object_list = list(response.context['object_list'])
        slugs = [
            obj.slug if hasattr(obj, 'slug') else obj['slug']
            for obj in object_list
        ]
        self.assertIn("quarterly-review", slugs)
        self.assertNotIn("code-analytics", slugs)

    def test_index_view_in_catalog_false_excluded(self):
        hidden_report = CodeReport(
            title="Secret Internal",
            slug="secret-internal",
        )
        site.register(hidden_report, in_catalog=False)

        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)
        slugs = [
            obj.slug if hasattr(obj, 'slug') else obj['slug']
            for obj in response.context['object_list']
        ]
        self.assertNotIn("secret-internal", slugs)

    def test_index_view_include_code_reports_disabled(self):
        site.register(self.code_report1, in_catalog=True)

        class PureORMIndexView(ReportIndexView):
            include_code_reports = False

        request = self.factory.get('/reports/view/')
        view = PureORMIndexView()
        view.setup(request)
        object_list = list(view.get_queryset())
        slugs = [obj.slug for obj in object_list]
        self.assertNotIn("code-analytics", slugs)
        self.assertIn("db-report-1", slugs)

    def test_index_view_deduplication(self):
        # Code report with same slug as existing ORM report
        duplicate_code_report = CodeReport(
            title="Duplicate Report",
            slug="db-report-1",
        )
        site.register(duplicate_code_report, in_catalog=True)

        request = self.factory.get('/reports/view/')
        view = ReportIndexView()
        view.setup(request)
        object_list = list(view.get_queryset())
        slug_counts = [
            obj.slug if hasattr(obj, 'slug') else obj['slug']
            for obj in object_list
        ].count("db-report-1")
        self.assertEqual(slug_counts, 1)

    def test_registered_code_report_view_routing(self):
        site.clear()
        code_report = CodeReport(
            title="Registered Code Report",
            slug="registered-code-report",
            theme="neutral",
            description="A code report available via ReportView",
            entries=[
                RichTextEntry(title="Intro", text="Welcome"),
            ],
        )
        site.register(code_report)

        # 1. ReportView HTML rendering with inline payload
        response = self.client.get(reverse('report-view', kwargs={'slug': 'registered-code-report'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reportcraft/report.html')
        self.assertIn('code_report', response.context)
        self.assertEqual(response.context['code_report'], code_report)
        self.assertIn('payload', response.context)
        self.assertEqual(response.context['payload']['title'], "Registered Code Report")
        content = response.content.decode('utf-8')
        self.assertIn('<script id="rc-report-data" type="application/json">', content)
        self.assertIn("Registered Code Report", content)

        # 2. DataView JSON API endpoint
        api_response = self.client.get(reverse('report-data', kwargs={'slug': 'registered-code-report'}))
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response['Content-Type'], 'application/json')
        data = api_response.json()
        self.assertEqual(data['title'], "Registered Code Report")
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(data['sections'][0]['content'][0]['title'], "Intro")

        # 3. 404 for unknown slug
        resp_404 = self.client.get(reverse('report-view', kwargs={'slug': 'non-existent-report-slug'}))
        self.assertEqual(resp_404.status_code, 404)
        api_resp_404 = self.client.get(reverse('report-data', kwargs={'slug': 'non-existent-report-slug'}))
        self.assertEqual(api_resp_404.status_code, 404)

    def test_catalog_item_matches_search(self):
        code_report = CodeReport(
            title="Finance Report Q3",
            slug="fin-q3",
            description="Third quarter financial metrics",
            notes="Audit approved",
            entries=[RichTextEntry(title="Revenue Breakdown", text="Details")],
        )
        item = CatalogItem(
            slug="fin-q3",
            title="Finance Report Q3",
            description="Third quarter financial metrics",
            report=code_report,
        )
        self.assertTrue(item.matches_search("finance"))
        self.assertTrue(item.matches_search("revenue"))
        self.assertTrue(item.matches_search("audit"))
        self.assertTrue(item.matches_search("fin-q3"))
        self.assertFalse(item.matches_search("nonexistent"))


class MergeDataTestCase(TestCase):
    def test_merge_data_missing_fields_populated_with_defaults(self):
        data = [
            {'category': 'A', 'metric_1': 10},
            {'category': 'B', 'metric_2': 20},
        ]
        result = merge_data(data, unique=['category'], defaults={'metric_1': 0, 'metric_2': 0})
        self.assertEqual(result, [
            {'category': 'A', 'metric_1': 10, 'metric_2': 0},
            {'category': 'B', 'metric_1': 0, 'metric_2': 20},
        ])

        # Same key merged across disparate sources with partial fields
        data_composite = [
            {'category': 'A', 'metric_1': 10},
            {'category': 'A', 'metric_2': 20},
        ]
        result_composite = merge_data(
            data_composite, unique=['category'], defaults={'metric_1': 0, 'metric_2': 0, 'metric_3': -1}
        )
        self.assertEqual(result_composite, [
            {'category': 'A', 'metric_1': 10, 'metric_2': 20, 'metric_3': -1},
        ])

    def test_merge_data_explicit_none_replaced_by_defaults(self):
        data = [
            {'category': 'A', 'metric_1': None, 'metric_2': 15},
        ]
        result = merge_data(data, unique=['category'], defaults={'metric_1': 100})
        self.assertEqual(result, [
            {'category': 'A', 'metric_1': 100, 'metric_2': 15},
        ])

    def test_merge_data_non_none_precedence_over_none(self):
        # Case 1: None first, non-None second
        data_first_none = [
            {'category': 'A', 'metric_1': None},
            {'category': 'A', 'metric_1': 42},
        ]
        result1 = merge_data(data_first_none, unique=['category'], defaults={'metric_1': 0})
        self.assertEqual(result1, [{'category': 'A', 'metric_1': 42}])

        # Case 2: Non-None first, None second
        data_second_none = [
            {'category': 'A', 'metric_1': 42},
            {'category': 'A', 'metric_1': None},
        ]
        result2 = merge_data(data_second_none, unique=['category'], defaults={'metric_1': 0})
        self.assertEqual(result2, [{'category': 'A', 'metric_1': 42}])

    def test_merge_data_preserves_falsy_values(self):
        data = [
            {'category': 'A', 'count': 0, 'flag': False, 'note': ''},
        ]
        result = merge_data(data, unique=['category'], defaults={'count': 99, 'flag': True, 'note': 'N/A'})
        self.assertEqual(result, [
            {'category': 'A', 'count': 0, 'flag': False, 'note': ''},
        ])

    def test_merge_data_without_defaults_backward_compatibility(self):
        data = [
            {'category': 'A', 'v1': 1},
            {'category': 'A', 'v2': 2},
        ]
        result = merge_data(data, unique=['category'])
        self.assertEqual(result, [{'category': 'A', 'v1': 1, 'v2': 2}])

    def test_datasource_get_source_data_applies_field_defaults(self):
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Country
        from reportcraft.models import DataSource, DataModel, DataField

        Country.objects.create(name="Canada", code="CAN", continent="North America", capital=None)
        Country.objects.create(name="France", code="FRA", continent="Europe", capital="Paris")

        ds = DataSource.objects.create(name="Country Composite DS", group_by=["continent"])
        ct = ContentType.objects.get_for_model(Country)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Country")

        DataField.objects.create(source=ds, model=dm, name="continent", label="Continent")
        DataField.objects.create(source=ds, model=dm, name="capital", label="Capital", default="Unknown Capital")

        data = ds.get_source_data()
        self.assertEqual(len(data), 2)
        by_continent = {item["continent"]: item["capital"] for item in data}
        self.assertEqual(by_continent["North America"], "Unknown Capital")
        self.assertEqual(by_continent["Europe"], "Paris")

    def test_apply_defaults_missing_and_none_values(self):
        data = [
            {'name': 'Canada', 'capital': None},
            {'name': 'France', 'capital': 'Paris'},
            {'name': 'Unknown'},
        ]
        result = apply_defaults(data, defaults={'capital': 'Unknown Capital', 'population': 0})
        self.assertEqual(result, [
            {'name': 'Canada', 'capital': 'Unknown Capital', 'population': 0},
            {'name': 'France', 'capital': 'Paris', 'population': 0},
            {'name': 'Unknown', 'capital': 'Unknown Capital', 'population': 0},
        ])

    def test_apply_defaults_preserves_falsy_values(self):
        data = [
            {'id': 1, 'count': 0, 'active': False, 'label': ''},
        ]
        result = apply_defaults(data, defaults={'count': 10, 'active': True, 'label': 'N/A'})
        self.assertEqual(result, [
            {'id': 1, 'count': 0, 'active': False, 'label': ''},
        ])

    def test_apply_defaults_empty_defaults_or_data(self):
        data = [{'a': 1}]
        self.assertEqual(apply_defaults(data, defaults=None), [{'a': 1}])
        self.assertEqual(apply_defaults(data, defaults={}), [{'a': 1}])
        self.assertEqual(apply_defaults([], defaults={'a': 1}), [])

    def test_datasource_get_source_data_non_grouped_applies_defaults(self):
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Country
        from reportcraft.models import DataSource, DataModel, DataField

        Country.objects.create(name="Iceland", code="ISL", capital=None)
        Country.objects.create(name="Japan", code="JPN", capital="Tokyo")

        # Non-grouped data source (group_by is empty/None)
        ds = DataSource.objects.create(name="Country Non-Grouped DS", group_by=None)
        ct = ContentType.objects.get_for_model(Country)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Country")

        DataField.objects.create(source=ds, model=dm, name="name", label="Name")
        DataField.objects.create(source=ds, model=dm, name="capital", label="Capital", default="Default Capital")

        data = ds.get_source_data()
        self.assertEqual(len(data), 2)
        by_name = {item["name"]: item["capital"] for item in data}
        self.assertEqual(by_name["Iceland"], "Default Capital")
        self.assertEqual(by_name["Japan"], "Tokyo")

    def test_datasource_get_source_data_with_filtered_datafield(self):
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Country
        from reportcraft.models import DataSource, DataModel, DataField

        Country.objects.create(name="Country Alpha", code="CAL", continent="Region 1")
        Country.objects.create(name="Country Beta", code="CBE", continent="Region 1")
        Country.objects.create(name="Country Gamma", code="CGA", continent="Region 1")
        Country.objects.create(name="Country Delta", code="CDE", continent="Region 2")
        Country.objects.create(name="Country Epsilon", code="CEP", continent="Region 2")

        ds = DataSource.objects.create(name="Filtered DataField DS", group_by=["continent"])
        ct = ContentType.objects.get_for_model(Country)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Country")

        DataField.objects.create(source=ds, model=dm, name="continent", label="Continent")
        DataField.objects.create(source=ds, model=dm, name="total", label="Total", expression="Count(id)")
        DataField.objects.create(
            source=ds, model=dm, name="alpha_count", label="Alpha Count",
            expression="Count(id, filters=\"name = 'Country Alpha'\")"
        )
        DataField.objects.create(
            source=ds, model=dm, name="alpha_or_beta", label="Alpha or Beta Count",
            expression="Count(id, filters=(name = 'Country Alpha' or name = 'Country Beta'))"
        )
        DataField.objects.create(
            source=ds, model=dm, name="not_alpha", label="Not Alpha Count",
            expression="Count(id, filter=(name != 'Country Alpha'))"
        )

        data = ds.get_source_data()
        by_continent = {item["continent"]: item for item in data}

        self.assertIn("Region 1", by_continent)
        self.assertEqual(by_continent["Region 1"]["total"], 3)
        self.assertEqual(by_continent["Region 1"]["alpha_count"], 1)
        self.assertEqual(by_continent["Region 1"]["alpha_or_beta"], 2)
        self.assertEqual(by_continent["Region 1"]["not_alpha"], 2)

        self.assertIn("Region 2", by_continent)
        self.assertEqual(by_continent["Region 2"]["total"], 2)
        self.assertEqual(by_continent["Region 2"]["alpha_count"], 0)
        self.assertEqual(by_continent["Region 2"]["alpha_or_beta"], 0)
        self.assertEqual(by_continent["Region 2"]["not_alpha"], 2)

    def test_datasource_get_queryset_static_filter_multi_model(self):
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Country, Journal
        from reportcraft.models import DataSource, DataModel, DataField

        Country.objects.create(name="AlphaCountry", code="ALC", continent="Region 1", population=50)
        Country.objects.create(name="BetaCountry", code="BEC", continent="Region 1", population=500)
        Journal.objects.create(name="AlphaJournal")
        Journal.objects.create(name="BetaJournal")

        ds = DataSource.objects.create(name="Multi-Model Static Filter DS", filters="population > 100")
        ct_country = ContentType.objects.get_for_model(Country)
        ct_journal = ContentType.objects.get_for_model(Journal)
        dm_country = DataModel.objects.create(source=ds, model=ct_country, name="example.Country")
        dm_journal = DataModel.objects.create(source=ds, model=ct_journal, name="example.Journal")

        DataField.objects.create(source=ds, model=dm_country, name="name", label="Name")
        DataField.objects.create(source=ds, model=dm_country, name="population", label="Population")
        DataField.objects.create(source=ds, model=dm_journal, name="name", label="Name")

        # get_queryset on Country should filter by population > 100
        country_qs = ds.get_queryset("example.Country")
        self.assertEqual(country_qs.count(), 1)
        self.assertEqual(country_qs.first()["name"], "BetaCountry")

        # get_queryset on Journal should not raise FieldError, even though Journal has no 'population' field
        journal_qs = ds.get_queryset("example.Journal")
        self.assertEqual(journal_qs.count(), 2)

        # get_source_data should succeed and merge records
        data = ds.get_source_data()
        names = {item["name"] for item in data}
        self.assertIn("BetaCountry", names)
        self.assertNotIn("AlphaCountry", names)
        self.assertIn("AlphaJournal", names)
        self.assertIn("BetaJournal", names)

        # Compound static filter: AND condition where one field is shared and one is not
        ds.filters = "name = 'BetaJournal' and population > 100"
        ds.save()
        # For Country: name == 'BetaJournal' and population > 100 -> 0 rows
        self.assertEqual(ds.get_queryset("example.Country").count(), 0)
        # For Journal: population > 100 is pruned, name == 'BetaJournal' is applied -> 1 row
        journal_and_qs = ds.get_queryset("example.Journal")
        self.assertEqual(journal_and_qs.count(), 1)
        self.assertEqual(journal_and_qs.first()["name"], "BetaJournal")

        # Compound static filter: OR condition where one field is shared and one is not
        ds.filters = "name = 'AlphaJournal' or population > 100"
        ds.save()
        # For Country: BetaCountry has population > 100 -> 1 row
        self.assertEqual(ds.get_queryset("example.Country").count(), 1)
        # For Journal: population > 100 is pruned, name == 'AlphaJournal' -> 1 row
        journal_or_qs = ds.get_queryset("example.Journal")
        self.assertEqual(journal_or_qs.count(), 1)
        self.assertEqual(journal_or_qs.first()["name"], "AlphaJournal")

        # Static filter with negation (!=) on field not in Journal
        ds.filters = "population != 500"
        ds.save()
        # Country: AlphaCountry has population 50 -> 1 row
        self.assertEqual(ds.get_queryset("example.Country").count(), 1)
        self.assertEqual(ds.get_queryset("example.Country").first()["name"], "AlphaCountry")
        # Journal: population != 500 pruned -> 2 rows
        self.assertEqual(ds.get_queryset("example.Journal").count(), 2)

    def test_datasource_filtered_avg_expression(self):
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Institution, Person, Country
        from reportcraft.models import DataSource, DataModel, DataField

        c = Country.objects.create(name="AvgTestCountry", code="ATC")
        inst1 = Institution.objects.create(name="Institute Alpha", city="City A", country=c)
        inst2 = Institution.objects.create(name="Institute Beta", city="City B", country=c)

        # Institute Alpha has two people: age 30 and age 50 (avg: 40.0)
        Person.objects.create(first_name="Alice", last_name="A", gender="female", age=30, institution=inst1)
        Person.objects.create(first_name="Bob", last_name="B", gender="male", age=50, institution=inst1)
        # Institute Beta has one person: age 20 (avg: 20.0)
        Person.objects.create(first_name="Charlie", last_name="C", gender="male", age=20, institution=inst2)

        ds = DataSource.objects.create(name="Filtered Avg DS", group_by=["name"])
        ct = ContentType.objects.get_for_model(Institution)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Institution")

        DataField.objects.create(source=ds, model=dm, name="name", label="Name")
        df_unfiltered = DataField.objects.create(
            source=ds, model=dm, name="avg_age", label="Avg Age",
            expression="Avg(People.Age)"
        )
        df_match = DataField.objects.create(
            source=ds, model=dm, name="avg_age_filtered_match", label="Filtered Match",
            expression="Avg(People.Age, filter=(People.Age = 30))"
        )
        df_nomatch = DataField.objects.create(
            source=ds, model=dm, name="avg_age_filtered_nomatch", label="Filtered No Match",
            expression="Avg(People.Age, filter=(People.Age = 2000))"
        )
        df_filters_nomatch = DataField.objects.create(
            source=ds, model=dm, name="avg_age_filters_nomatch", label="Filters No Match",
            expression="Avg(People.Age, filters=(People.Age = 2000))"
        )

        # 1. Verify direct ORM evaluation via aggregate()
        agg_res = Institution.objects.filter(name="Institute Alpha").aggregate(
            unfiltered=df_unfiltered.get_expression(),
            filtered_match=df_match.get_expression(),
            filtered_nomatch=df_nomatch.get_expression(),
            filters_nomatch=df_filters_nomatch.get_expression(),
        )
        self.assertEqual(agg_res["unfiltered"], 40.0)
        self.assertEqual(agg_res["filtered_match"], 30.0)
        self.assertIsNone(agg_res["filtered_nomatch"])
        self.assertIsNone(agg_res["filters_nomatch"])
        self.assertNotEqual(agg_res["filtered_nomatch"], agg_res["unfiltered"])

        # 2. Verify via ds.get_source_data() with grouping
        data = ds.get_source_data()
        by_name = {item["name"]: item for item in data}

        self.assertIn("Institute Alpha", by_name)
        alpha = by_name["Institute Alpha"]
        self.assertEqual(alpha["avg_age"], 40.0)
        self.assertEqual(alpha["avg_age_filtered_match"], 30.0)
        self.assertIsNone(alpha["avg_age_filtered_nomatch"])
        self.assertIsNone(alpha["avg_age_filters_nomatch"])
        self.assertNotEqual(alpha["avg_age_filtered_nomatch"], alpha["avg_age"])

        self.assertIn("Institute Beta", by_name)
        beta = by_name["Institute Beta"]
        self.assertEqual(beta["avg_age"], 20.0)
        self.assertIsNone(beta["avg_age_filtered_match"])
        self.assertIsNone(beta["avg_age_filtered_nomatch"])
        self.assertIsNone(beta["avg_age_filters_nomatch"])

    def test_publication_filtered_metric_impact_factor(self):
        import datetime
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Journal, Metric, Publication
        from reportcraft.models import DataSource, DataModel, DataField

        # Setup Journal and Metrics
        j = Journal.objects.create(name="Journal of Examples")
        Metric.objects.create(journal=j, year=2020, impact_factor=2.0)
        Metric.objects.create(journal=j, year=2021, impact_factor=4.0)

        # Setup Publications: 1 in 2020 (IF: 2.0), 3 in 2021 (IF: 4.0)
        Publication.objects.create(title="Paper 2020", journal=j, published=datetime.date(2020, 5, 1))
        Publication.objects.create(title="Paper 2021 A", journal=j, published=datetime.date(2021, 2, 1))
        Publication.objects.create(title="Paper 2021 B", journal=j, published=datetime.date(2021, 6, 1))
        Publication.objects.create(title="Paper 2021 C", journal=j, published=datetime.date(2021, 9, 1))

        # Setup DataSource and DataFields on Publication
        ds = DataSource.objects.create(name="Publication Impact DS")
        ct = ContentType.objects.get_for_model(Publication)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Publication")

        df_title = DataField.objects.create(source=ds, model=dm, name="title", label="Title")
        df_filters = DataField.objects.create(
            source=ds, model=dm, name="impact_factor_filters", label="Impact Factor (filters)",
            expression="Avg(Journal.Metrics.ImpactFactor, filters=(Journal.Metrics.Year = Published.Year))"
        )
        df_filter = DataField.objects.create(
            source=ds, model=dm, name="impact_factor_filter", label="Impact Factor (filter)",
            expression="Avg(Journal.Metrics.ImpactFactor, filter=(Journal.Metrics.Year = Published.Year))"
        )

        # 1. Direct ORM aggregate evaluation over Publication:
        # Expected weighted average: (2.0*1 + 4.0*3) / 4 = 14.0 / 4 = 3.5
        agg_res = Publication.objects.aggregate(
            avg_filters=df_filters.get_expression(),
            avg_filter=df_filter.get_expression(),
        )
        self.assertEqual(agg_res["avg_filters"], 3.5)
        self.assertEqual(agg_res["avg_filter"], 3.5)

        # 2. Evaluate per-publication via DataSource
        data = ds.get_source_data()
        by_title = {item["title"]: item for item in data}
        self.assertEqual(by_title["Paper 2020"]["impact_factor_filters"], 2.0)
        self.assertEqual(by_title["Paper 2020"]["impact_factor_filter"], 2.0)
        self.assertEqual(by_title["Paper 2021 A"]["impact_factor_filters"], 4.0)
        self.assertEqual(by_title["Paper 2021 B"]["impact_factor_filters"], 4.0)
        self.assertEqual(by_title["Paper 2021 C"]["impact_factor_filters"], 4.0)

        # 3. Evaluate grouped DataSource (group by journal__name)
        ds_grouped = DataSource.objects.create(name="Grouped Publication Impact DS", group_by=["journal__name"])
        dm_grouped = DataModel.objects.create(source=ds_grouped, model=ct, name="example.Publication")
        DataField.objects.create(source=ds_grouped, model=dm_grouped, name="journal__name", label="Journal")
        DataField.objects.create(
            source=ds_grouped, model=dm_grouped, name="avg_impact", label="Avg Impact",
            expression="Avg(Journal.Metrics.ImpactFactor, filters=(Journal.Metrics.Year = Published.Year))"
        )
        grouped_data = ds_grouped.get_source_data()
        self.assertEqual(len(grouped_data), 1)
        self.assertEqual(grouped_data[0]["journal__name"], "Journal of Examples")
        self.assertEqual(grouped_data[0]["avg_impact"], 3.5)


class TemporalAndBucketingTestCase(TestCase):
    def test_datasource_grouped_by_decade_and_lustrum(self):
        from django.contrib.contenttypes.models import ContentType
        from demo.example.models import Journal, Publication
        from reportcraft.models import DataSource, DataModel, DataField
        import datetime

        j = Journal.objects.create(name="Temporal Test Journal")
        Publication.objects.create(journal=j, title="P1", published=datetime.date(1995, 1, 1))
        Publication.objects.create(journal=j, title="P2", published=datetime.date(1998, 6, 1))
        Publication.objects.create(journal=j, title="P3", published=datetime.date(2021, 3, 1))
        Publication.objects.create(journal=j, title="P4", published=datetime.date(2024, 9, 1))
        Publication.objects.create(journal=j, title="P5", published=datetime.date(2026, 2, 1))

        ds = DataSource.objects.create(name="Decade Grouped DS", group_by=["decade"])
        ct = ContentType.objects.get_for_model(Publication)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Publication")
        DataField.objects.create(source=ds, model=dm, name="decade", label="Decade", expression="Decade(published)")
        DataField.objects.create(source=ds, model=dm, name="count", label="Count", expression="Count(id)")

        data = ds.get_source_data()
        by_decade = {item["decade"]: item["count"] for item in data}
        self.assertEqual(by_decade["1990s"], 2)
        self.assertEqual(by_decade["2020s"], 3)

    def test_datasource_with_current_temporal_expressions(self):
        from django.contrib.contenttypes.models import ContentType
        from django.utils import timezone
        from demo.example.models import Journal, Publication
        from reportcraft.models import DataSource, DataModel, DataField
        import datetime

        j = Journal.objects.create(name="Current Temporal Journal")
        Publication.objects.create(journal=j, title="Paper Recent", published=datetime.date(2026, 1, 1))
        Publication.objects.create(journal=j, title="Paper Old", published=datetime.date(2010, 1, 1))

        ds = DataSource.objects.create(name="Recent Papers DS")
        ct = ContentType.objects.get_for_model(Publication)
        dm = DataModel.objects.create(source=ds, model=ct, name="example.Publication")
        DataField.objects.create(source=ds, model=dm, name="title", label="Title")
        DataField.objects.create(
            source=ds, model=dm, name="years_ago", label="Years Ago",
            expression="ThisYear() - ExtractYear(published)"
        )

        data = ds.get_source_data()
        by_title = {item["title"]: item["years_ago"] for item in data}
        self.assertEqual(by_title["Paper Recent"], timezone.localdate().year - 2026)
        self.assertEqual(by_title["Paper Old"], timezone.localdate().year - 2010)

    def test_explicit_value_injection_and_constructor_args(self):
        from reportcraft.functions import ThisYear, ThisMonth, ThisQuarter, ThisDay, ThisWeek, Today, Now
        import datetime

        custom_date = datetime.date(2030, 8, 15)
        custom_dt = datetime.datetime(2030, 8, 15, 10, 30, 0)

        ty = ThisYear(2030)
        self.assertEqual(ty.value, 2030)
        self.assertEqual(repr(ty), "ThisYear(2030)")

        tm = ThisMonth(8)
        self.assertEqual(tm.value, 8)
        self.assertEqual(repr(tm), "ThisMonth(8)")

        tq = ThisQuarter(3)
        self.assertEqual(tq.value, 3)

        td = ThisDay(15)
        self.assertEqual(td.value, 15)

        tw = ThisWeek(33)
        self.assertEqual(tw.value, 33)

        today = Today(custom_date)
        self.assertEqual(today.value, custom_date)

        now = Now(custom_dt)
        self.assertEqual(now.value, custom_dt)

    def test_timezone_activation_affects_defaults(self):
        from zoneinfo import ZoneInfo
        from django.utils import timezone
        from reportcraft.functions import ThisYear, ThisMonth, Today

        current_tz = timezone.get_current_timezone()
        try:
            timezone.activate(ZoneInfo('Pacific/Auckland'))
            auckland_date = timezone.localdate()
            self.assertEqual(ThisYear().value, auckland_date.year)
            self.assertEqual(ThisMonth().value, auckland_date.month)
            self.assertEqual(Today().value, auckland_date)
        finally:
            timezone.activate(current_tz)

    def test_cross_database_compilation_templates(self):
        from reportcraft.functions import Decade, Lustrum

        class MockCompiler:
            def compile(self, expr):
                return '"published"', ()

        compiler = MockCompiler()

        # Decade PostgreSQL
        dec = Decade('published')
        sql_pg, params_pg = dec.as_postgresql(compiler, None)
        self.assertIn('::text', sql_pg)
        self.assertIn('FLOOR', sql_pg)
        self.assertIn('::numeric', sql_pg)
        self.assertIn("'s'", sql_pg)
        self.assertEqual(params_pg, ())

        # Lustrum PostgreSQL
        lus = Lustrum('published')
        sql_pg_lus, params_pg_lus = lus.as_postgresql(compiler, None)
        self.assertIn("'-'", sql_pg_lus)
        self.assertEqual(params_pg_lus, ())

        # Decade MySQL
        sql_my, params_my = dec.as_mysql(compiler, None)
        self.assertIn('CONCAT', sql_my)
        self.assertIn('CHAR', sql_my)
        self.assertIn("'s'", sql_my)
        self.assertEqual(params_my, ())

        # Lustrum MySQL
        sql_my_lus, params_my_lus = lus.as_mysql(compiler, None)
        self.assertIn('CONCAT', sql_my_lus)
        self.assertIn("'-'", sql_my_lus)
        self.assertEqual(params_my_lus, ())

        # ANSI Fallback as_sql
        sql_ansi, params_ansi = dec.as_sql(compiler, None)
        self.assertIn('VARCHAR(20)', sql_ansi)
        self.assertIn("'s'", sql_ansi)
        self.assertEqual(params_ansi, ())

    def test_custom_anchor_and_size_bucketing(self):
        from demo.example.models import Journal, Publication
        from reportcraft.functions import YearBucket
        import datetime

        j = Journal.objects.create(name="Custom Bucket Journal")
        p1 = Publication.objects.create(journal=j, title="P2025", published=datetime.date(2025, 1, 1))
        p2 = Publication.objects.create(journal=j, title="P2018", published=datetime.date(2018, 1, 1))

        qs = Publication.objects.filter(journal=j).annotate(
            b6=YearBucket('published', size=6, anchor=2001)
        )
        self.assertEqual(qs.get(pk=p1.pk).b6, "2025-2030")
        self.assertEqual(qs.get(pk=p2.pk).b6, "2013-2018")

    def test_year_month_func(self):
        from demo.example.models import Journal, Publication
        from reportcraft.functions import YearMonth
        import datetime

        j = Journal.objects.create(name="YearMonth Journal")
        p1 = Publication.objects.create(journal=j, title="P2025-07", published=datetime.date(2025, 7, 15))
        p2 = Publication.objects.create(journal=j, title="P2023-12", published=datetime.date(2023, 12, 1))

        qs = Publication.objects.filter(journal=j).annotate(
            ym=YearMonth('published')
        )
        self.assertEqual(qs.get(pk=p1.pk).ym, "2025-07")
        self.assertEqual(qs.get(pk=p2.pk).ym, "2023-12")

    def test_year_quarter_func(self):
        from demo.example.models import Journal, Publication
        from reportcraft.functions import YearQuarter
        import datetime

        j = Journal.objects.create(name="YearQuarter Journal")
        p1 = Publication.objects.create(journal=j, title="P2025-Q3", published=datetime.date(2025, 8, 10))
        p2 = Publication.objects.create(journal=j, title="P2024-Q1", published=datetime.date(2024, 2, 20))

        qs = Publication.objects.filter(journal=j).annotate(
            yq=YearQuarter('published')
        )
        self.assertEqual(qs.get(pk=p1.pk).yq, "2025-Q3")
        self.assertEqual(qs.get(pk=p2.pk).yq, "2024-Q1")


    def test_age_funcs(self):
        from demo.example.models import Institution, Country, Person
        from reportcraft.functions import Age, AgeInYears, AgeInMonths, AgeInDays
        import datetime
        from django.utils import timezone

        c = Country.objects.create(name="Age Country", code="AC")
        inst = Institution.objects.create(name="Age Inst", city="City", country=c)
        now = timezone.now()
        delta = datetime.timedelta(days=365*30 + 90)  # 30 years and ~3 months
        created_dt = now - delta
        Institution.objects.filter(pk=inst.pk).update(created=created_dt)

        qs = Institution.objects.filter(pk=inst.pk).annotate(
            age=Age('created'),
            age_years=AgeInYears('created'),
            age_months=AgeInMonths('created'),
            age_days=AgeInDays('created')
        ).first()
        self.assertIsInstance(qs.age, datetime.timedelta)
        self.assertEqual(qs.age.days, delta.days)
        self.assertEqual(qs.age_years, 30)
        self.assertTrue(30 <= qs.age_months // 12 <= 31)  # Allow for month rounding
        self.assertTrue(10950 <= qs.age_days <= 11100)  # Allow for leap years

        # Also verify with Person model using created
        p = Person.objects.create(first_name="Test", last_name="Person", gender="female", age=30, bio="Test", institution=inst)
        Person.objects.filter(pk=p.pk).update(created=created_dt)
        qs_person = Person.objects.filter(pk=p.pk).annotate(
            age_delta=Age('created'),
            age_years=AgeInYears('created'),
            age_months=AgeInMonths('created'),
            age_days=AgeInDays('created')
        ).first()
        self.assertIsInstance(qs_person.age_delta, datetime.timedelta)
        self.assertEqual(qs_person.age_delta.days, delta.days)
        self.assertEqual(qs_person.age_years, 30)

    def test_age_and_formatting_cross_database_compilation(self):
        from reportcraft.functions import Age, AgeInYears, AgeInMonths, AgeInDays, YearQuarter, YearMonth
        from django.db import connection

        class MockCompiler:
            def compile(self, expr):
                return '"created"', ()

        compiler = MockCompiler()

        # Age
        age = Age('created')
        self.assertIn('AGE("created")', age.as_postgresql(compiler, connection)[0])
        self.assertIn('TIMEDIFF(NOW(), "created")', age.as_mysql(compiler, connection)[0])
        self.assertIn("julianday('now')", age.as_sqlite(compiler, connection)[0])
        self.assertIn('NUMTODSINTERVAL', age.as_oracle(compiler, connection)[0])

        # AgeInYears
        aiy = AgeInYears('created')
        self.assertIn('EXTRACT(YEAR FROM AGE("created"))', aiy.as_postgresql(compiler, connection)[0])
        self.assertIn('TIMESTAMPDIFF(YEAR, "created", CURDATE())', aiy.as_mysql(compiler, connection)[0])
        self.assertIn("strftime", aiy.as_sqlite(compiler, connection)[0])
        self.assertIn('MONTHS_BETWEEN', aiy.as_oracle(compiler, connection)[0])

        # AgeInMonths
        aim = AgeInMonths('created')
        self.assertIn('EXTRACT(MONTH FROM AGE("created"))', aim.as_postgresql(compiler, connection)[0])
        self.assertIn('TIMESTAMPDIFF(MONTH, "created", CURDATE())', aim.as_mysql(compiler, connection)[0])
        self.assertIn("strftime", aim.as_sqlite(compiler, connection)[0])
        self.assertIn('TRUNC(MONTHS_BETWEEN', aim.as_oracle(compiler, connection)[0])

        # AgeInDays
        aid = AgeInDays('created')
        self.assertIn('CURRENT_DATE - ("created")::date', aid.as_postgresql(compiler, connection)[0])
        self.assertIn('DATEDIFF(CURDATE(), "created")', aid.as_mysql(compiler, connection)[0])
        self.assertIn("julianday('now') - julianday(\"created\")", aid.as_sqlite(compiler, connection)[0])
        self.assertIn('TRUNC(SYSDATE - "created")', aid.as_oracle(compiler, connection)[0])

        # YearQuarter
        yq = YearQuarter('created')
        self.assertIn("TO_CHAR(\"created\", 'YYYY')", yq.as_postgresql(compiler, connection)[0])
        self.assertIn("DATE_FORMAT(\"created\"", yq.as_mysql(compiler, connection)[0])
        self.assertIn("strftime", yq.as_sqlite(compiler, connection)[0])
        self.assertIn("TO_CHAR(\"created\", 'YYYY-\"Q\"Q')", yq.as_oracle(compiler, connection)[0])

        # YearMonth
        ym = YearMonth('created')
        self.assertIn("TO_CHAR(\"created\", 'YYYY-MM')", ym.as_postgresql(compiler, connection)[0])
        self.assertIn("DATE_FORMAT(\"created\"", ym.as_mysql(compiler, connection)[0])
        self.assertIn("strftime", ym.as_sqlite(compiler, connection)[0])
        self.assertIn("TO_CHAR(\"created\", 'YYYY-MM')", ym.as_oracle(compiler, connection)[0])

    def test_expression_parser_with_age_and_formatting_funcs(self):
        from reportcraft.utils import ExpressionParser
        from reportcraft.functions import Age, AgeInYears, AgeInMonths, AgeInDays, YearQuarter, YearMonth

        parser = ExpressionParser()
        self.assertIsInstance(parser.parse("Age(Created)"), Age)
        self.assertIsInstance(parser.parse("AgeInYears(Created)"), AgeInYears)
        self.assertIsInstance(parser.parse("AgeInMonths(Created)"), AgeInMonths)
        self.assertIsInstance(parser.parse("AgeInDays(Created)"), AgeInDays)
        self.assertIsInstance(parser.parse("YearQuarter(Created)"), YearQuarter)
        self.assertIsInstance(parser.parse("YearMonth(Created)"), YearMonth)
