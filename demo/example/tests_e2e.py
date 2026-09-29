import json
from django.test import TestCase, Client
from django.urls import reverse

from demo.example.models import Country, Institution, Person, Subject


class EndToEndReportDemoTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Seed data for Person, Institution, Subject
        self.country = Country.objects.create(name="Canada", code="CAN", population=38000000)
        self.inst1 = Institution.objects.create(
            name="Polytechnique Montreal",
            city="Montreal",
            province="Quebec",
            country=self.country,
        )
        self.inst2 = Institution.objects.create(
            name="University of Toronto",
            city="Toronto",
            province="Ontario",
            country=self.country,
        )
        self.subj1 = Subject.objects.create(name="Computer Science", description="CS studies")
        self.subj2 = Subject.objects.create(name="Physics", description="Physics studies")
        self.subj3 = Subject.objects.create(name="Mathematics", description="Math studies")

        self.inst1.subjects.add(self.subj1, self.subj2)
        self.inst2.subjects.add(self.subj1, self.subj3)

        # People
        Person.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            gender="female",
            age=36,
            type="admin",
            institution=self.inst1,
        )
        Person.objects.create(
            first_name="Grace",
            last_name="Hopper",
            gender="female",
            age=85,
            type="user",
            institution=self.inst1,
        )
        Person.objects.create(
            first_name="Alan",
            last_name="Turing",
            gender="male",
            age=41,
            type="user",
            institution=self.inst2,
        )
        Person.objects.create(
            first_name="Dennis",
            last_name="Ritchie",
            gender="male",
            age=70,
            type="guest",
            institution=self.inst2,
        )

    def _extract_inline_json(self, response):
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        start_marker = '<script id="rc-report-data" type="application/json">'
        end_marker = '</script>'
        self.assertIn(start_marker, content)
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        raw_json = content[start_idx:end_idx].strip()
        return json.loads(raw_json)

    def test_home_page_contains_demo_navigation_links(self):
        """Verify home page contains links to both demo reports."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn(reverse("code-report-demo"), content)
        self.assertIn(reverse("dict-report-demo"), content)
        self.assertIn("Code-First Report Demo", content)
        self.assertIn("Preformed Dict Report Demo", content)

    def test_code_report_demo_html_get(self):
        """GET /reports/code-demo/ returns 200 with inline json_script and reportcraft assets."""
        response = self.client.get(reverse("code-report-demo"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reportcraft/report.html")

        content = response.content.decode("utf-8")
        self.assertIn('<script id="rc-report-data" type="application/json">', content)
        self.assertIn("Academic &amp; Personnel Directory", content)
        self.assertIn("const inlineDataEl = document.getElementById(\"rc-report-data\");", content)

        data = self._extract_inline_json(response)
        self.assertEqual(data["title"], "Academic & Personnel Directory")
        self.assertIn("sections", data)
        self.assertEqual(len(data["sections"]), 1)
        entries = data["sections"][0]["content"]
        self.assertEqual(len(entries), 4)

        # 1. RichText
        self.assertEqual(entries[0]["kind"], "richtext")
        self.assertEqual(entries[0]["title"], "Executive Overview")
        self.assertEqual(entries[0]["style"], "col-md-12")

        # 2. Table
        self.assertEqual(entries[1]["kind"], "table")
        self.assertEqual(entries[1]["title"], "Personnel by Role and Gender")
        self.assertEqual(entries[1]["style"], "col-md-6 table-nowrap-headers")

        # 3. ColumnChart: Subjects
        self.assertEqual(entries[2]["kind"], "columns")
        self.assertEqual(entries[2]["title"], "Institutions per Subject Area")

        # 4. ColumnChart: Cities
        self.assertEqual(entries[3]["kind"], "columns")
        self.assertEqual(entries[3]["title"], "Institutions by City")

    def test_code_report_demo_content_negotiation(self):
        """Verify ?format=json and Accept: application/json content negotiation on code demo."""
        # 1. Query parameter ?format=json
        response = self.client.get(reverse("code-report-demo") + "?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["title"], "Academic & Personnel Directory")
        self.assertEqual(len(data["sections"][0]["content"]), 4)

        # 2. Accept: application/json header
        response = self.client.get(reverse("code-report-demo"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["title"], "Academic & Personnel Directory")

        # 3. Compound Accept header
        response = self.client.get(
            reverse("code-report-demo"),
            HTTP_ACCEPT="application/json, text/javascript, */*; q=0.01",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["title"], "Academic & Personnel Directory")

    def test_code_report_demo_runtime_filtering(self):
        """Verify query parameter filtering dynamically constrains QuerySetDataset."""
        # Filter by gender=female in JSON mode
        response = self.client.get(reverse("code-report-demo") + "?gender=female&format=json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        table_entry = data["sections"][0]["content"][1]
        table_rows = table_entry["data"][0]
        # First header row contains Gender and the matching genders
        header_row = table_rows[0]
        self.assertIn("female", header_row)
        self.assertNotIn("male", header_row)

        # Filter by type=admin in HTML inline mode
        response = self.client.get(reverse("code-report-demo") + "?type=admin")
        self.assertEqual(response.status_code, 200)
        data = self._extract_inline_json(response)
        table_entry = data["sections"][0]["content"][1]
        table_rows = table_entry["data"][0]
        # Only admin role row should be present
        role_labels = [row[0] for row in table_rows[1:]]
        self.assertIn("admin", role_labels)
        self.assertNotIn("user", role_labels)
        self.assertNotIn("guest", role_labels)

        # Combined filters: gender=male and type=user
        response = self.client.get(reverse("code-report-demo") + "?gender=male&type=user&format=json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        table_entry = data["sections"][0]["content"][1]
        table_rows = table_entry["data"][0]
        self.assertIn("male", table_rows[0])
        role_labels = [row[0] for row in table_rows[1:]]
        self.assertIn("user", role_labels)
        self.assertNotIn("admin", role_labels)
        self.assertNotIn("guest", role_labels)

    def test_dict_report_demo_html_get(self):
        """GET /reports/dict-demo/ returns 200 with inline json_script and KPI payload."""
        response = self.client.get(reverse("dict-report-demo"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reportcraft/report.html")

        content = response.content.decode("utf-8")
        self.assertIn('<script id="rc-report-data" type="application/json">', content)
        self.assertIn("Executive KPI Dashboard", content)

        data = self._extract_inline_json(response)
        self.assertEqual(data["title"], "Executive KPI Dashboard")
        self.assertEqual(data["description"], "Real-time performance indicators and operational metrics")
        self.assertEqual(len(data["sections"]), 1)
        entries = data["sections"][0]["content"]
        self.assertEqual(len(entries), 3)

        self.assertEqual(entries[0]["kind"], "richtext")
        self.assertEqual(entries[0]["title"], "Operational Highlights")
        self.assertEqual(entries[1]["kind"], "bars")
        self.assertEqual(entries[1]["title"], "Quarterly Volume Trends")
        self.assertEqual(entries[2]["kind"], "columns")
        self.assertEqual(entries[2]["title"], "Regional Distribution")

    def test_dict_report_demo_content_negotiation(self):
        """Verify ?format=json and Accept: application/json content negotiation on dict demo."""
        # 1. Query parameter ?format=json
        response = self.client.get(reverse("dict-report-demo") + "?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["title"], "Executive KPI Dashboard")
        self.assertEqual(len(data["sections"][0]["content"]), 3)

        # 2. Accept: application/json header
        response = self.client.get(reverse("dict-report-demo"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["title"], "Executive KPI Dashboard")

        # 3. Compound Accept header
        response = self.client.get(
            reverse("dict-report-demo"),
            HTTP_ACCEPT="application/json, text/javascript, */*; q=0.01",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["title"], "Executive KPI Dashboard")

    def test_code_report_demo_context_data(self):
        """Verify view context contains code_report, report metadata, and payload."""
        response = self.client.get(reverse("code-report-demo"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("code_report", response.context)
        self.assertIn("payload", response.context)
        self.assertIn("report", response.context)
        self.assertEqual(response.context["report"]["title"], "Academic & Personnel Directory")

    def test_dict_report_demo_context_data(self):
        """Verify view context contains report metadata and payload for dict report."""
        response = self.client.get(reverse("dict-report-demo"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("payload", response.context)
        self.assertIn("report", response.context)
        self.assertEqual(response.context["report"]["title"], "Executive KPI Dashboard")

    def test_code_report_demo_unknown_filter_ignored(self):
        """Verify unrecognized URL parameters do not break report generation."""
        response = self.client.get(reverse("code-report-demo") + "?unrecognized_field=foo&format=json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Academic & Personnel Directory")
        self.assertEqual(len(data["sections"][0]["content"]), 4)
