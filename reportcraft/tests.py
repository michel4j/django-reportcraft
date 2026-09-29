import json
from django.test import TestCase, Client, override_settings
from django.template.loader import render_to_string
from django.urls import path, include, reverse
from django.db.models import *
from django.db.models.functions import *

from reportcraft.models import Report
from reportcraft.utils import ExpressionParser, FilterParser
from reportcraft.views import DictReportView


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


urlpatterns = [
    path('reports/', include('reportcraft.urls')),
    path('dict-report/', SampleDictReportView.as_view(), name='sample-dict-report'),
    path('callable-dict-report/', CallableDictReportView.as_view(), name='callable-dict-report'),
    path('function-dict-report/', FunctionDictReportView.as_view(), name='function-dict-report'),
    path('empty-dict-report/', EmptyDictReportView.as_view(), name='empty-dict-report'),
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
        """Verify that traditional database reports without inline payload fall back to AJAX fetch without errors."""
        report = Report.objects.create(
            slug='test-db-report',
            title='Database Report',
            description='Stored in SQLite'
        )
        response = self.client.get(reverse('report-view', kwargs={'slug': report.slug}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Does NOT have inline json_script
        self.assertNotIn('<script id="rc-report-data" type="application/json">', content)
        # Still has fetch call to data_url
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
