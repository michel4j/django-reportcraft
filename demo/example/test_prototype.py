import json
from django.test import TestCase, Client
from django.urls import reverse
from reportcraft.models import Report, Entry
from demo.example.prototype_views import PROTOTYPE_REPORT_DICT


class DictReportPrototypeTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dict_report_html_rendering_inline_payload(self):
        """Verify that DictReportView renders HTML containing inline json_script and no fetch requirement."""
        response = self.client.get(reverse('prototype-dict-report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reportcraft/report.html')

        # Check inline script tag
        content = response.content.decode('utf-8')
        self.assertIn('<script id="rc-report-data" type="application/json">', content)
        self.assertIn('Executive Leadership KPI Overview', content)
        self.assertIn('id="report-entry"', content)

        # Parse inline payload from the script tag
        start_marker = '<script id="rc-report-data" type="application/json">'
        end_marker = '</script>'
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        raw_json = content[start_idx:end_idx].strip()
        data = json.loads(raw_json)

        self.assertEqual(data['title'], PROTOTYPE_REPORT_DICT['title'])
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(len(data['sections'][0]['content']), 5)

    def test_dict_report_json_format_param(self):
        """Verify that ?format=json returns direct JSON."""
        response = self.client.get(reverse('prototype-dict-report') + '?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['title'], PROTOTYPE_REPORT_DICT['title'])
        self.assertEqual(len(data['sections'][0]['content']), 5)

    def test_dict_report_accept_header(self):
        """Verify that Accept: application/json returns direct JSON."""
        response = self.client.get(reverse('prototype-dict-report'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['title'], PROTOTYPE_REPORT_DICT['title'])

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
        self.assertIn('fetch("/reports/api/reports/test-db-report/', content)
