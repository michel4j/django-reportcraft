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


from demo.example.models import Country
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
        self.assertEqual(len(payload["sections"]), 1)
        self.assertEqual(payload["sections"][0]["title"], "Deep Dive")
        self.assertEqual(payload["sections"][0]["theme"], "dark")
        self.assertEqual(len(payload["sections"][0]["content"]), 1)

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