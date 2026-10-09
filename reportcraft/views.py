from __future__ import annotations

import json
from collections import defaultdict

from django.conf import settings
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView, edit, ListView, TemplateView
from crisp_modals.views import ModalUpdateView, ModalCreateView, ModalDeleteView, ModalConfirmView
from itemlist.views import ItemListView

from typing import TYPE_CHECKING

from . import models, forms
from .utils import CsvResponse

if TYPE_CHECKING:
    from .code.report import CodeReport

VIEW_MIXINS = [import_string(mixin) for mixin in settings.REPORTCRAFT_MIXINS.get('VIEW',[])]
EDIT_MIXINS = [import_string(mixin) for mixin in settings.REPORTCRAFT_MIXINS.get('EDIT', [])]


class ReportView(DetailView):
    template_name = 'reportcraft/report.html'
    model = models.Report
    data_url = 'report-data'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg or 'slug')
        try:
            return super().get_object(queryset=queryset)
        except Http404:
            if slug:
                from reportcraft.registry import site
                code_report = site.get_report(slug)
                if code_report is not None:
                    return code_report
            raise

    def get_data_url(self):
        """
        Get the URL for the report data endpoint.
        :return: URL for the report data
        """
        slug = getattr(self.object, 'slug', None)
        if slug:
            return reverse(self.data_url, kwargs={'slug': slug})
        return ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from reportcraft.code.report import CodeReport
        if hasattr(self, 'request') and self.request and hasattr(self.request, 'GET'):
            filters = dict(self.request.GET.items())
        else:
            filters = {}

        if isinstance(self.object, CodeReport):
            payload = self.object.generate(filters=filters)
            context['code_report'] = self.object
            context['payload'] = payload
            context['report'] = {
                'title': payload.get('title', getattr(self.object, 'title', 'Report')),
                'description': payload.get('description', getattr(self.object, 'description', '')),
                'theme': payload.get('theme', getattr(self.object, 'theme', 'default')),
                'notes': payload.get('notes', getattr(self.object, 'notes', '')),
                'slug': getattr(self.object, 'slug', ''),
            }
        else:
            context['report'] = self.object
            context['payload'] = self.object.generate(filters=filters)
        context['data_url'] = self.get_data_url()
        context['query'] = self.get_query_string()
        return context

    def get_query_string(self):
        """
        Fetch the querystring
        :return: urlencoded querystring, including initial '?'
        """
        params = dict(self.request.GET.items())
        param_string = urlencode(sorted(params.items()), doseq=True)
        return mark_safe(f'?{param_string}')


class DictReportView(TemplateView):
    """
    Renders a preformed report dictionary at a URL endpoint.
    - Default GET: renders HTML embedding payload directly via json_script.
    - GET with ?format=json or Accept: application/json: returns pure JSON.
    - Integrators can supply report_dict directly or override get_report_dict(request).
    """
    template_name = 'reportcraft/report.html'
    report_dict = None

    def get_report_dict(self, request=None) -> dict:
        if request is None and hasattr(self, 'request'):
            request = self.request
        if callable(self.report_dict):
            try:
                return self.report_dict(request)
            except TypeError:
                return self.report_dict()
        elif self.report_dict is not None:
            return self.report_dict
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = self.get_report_dict(self.request)
        context['report'] = {
            'title': payload.get('title', 'Report'),
            'description': payload.get('description', ''),
            'theme': payload.get('theme', 'default'),
            'notes': payload.get('notes', ''),
        }
        context['payload'] = payload
        context['query'] = ''
        return context

    def get(self, request, *args, **kwargs):
        format_param = request.GET.get('format', '').lower()
        accept_header = request.headers.get('Accept', '')
        if format_param == 'json' or 'application/json' in accept_header:
            return JsonResponse(self.get_report_dict(request), safe=False)
        return super().get(request, *args, **kwargs)


class CodeReportView(DictReportView):
    """
    Renders a CodeReport at a URL endpoint.
    Inherits from DictReportView for dual HTML and JSON content negotiation.
    Extracts runtime URL query parameters and forwards them as filters to report.generate().
    """
    report: CodeReport | None = None

    def get_report(self, request=None) -> CodeReport | None:
        if request is None and hasattr(self, 'request'):
            request = self.request
        if callable(self.report):
            try:
                return self.report(request)
            except TypeError:
                return self.report()
        return self.report

    def get_report_dict(self, request=None) -> dict:
        if request is None and hasattr(self, 'request'):
            request = self.request
        try:
            report = self.get_report(request)
        except TypeError:
            report = self.get_report()

        if report is None:
            return {}

        filters = dict(request.GET.items()) if request and hasattr(request, 'GET') else {}
        return report.generate(filters=filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['code_report'] = self.get_report(self.request)
        return context


class DataView(View):
    """
    Base class for report data views.
    This class is used to fetch and return report data in JSON format.
    """
    model = models.Report

    def get_queryset(self):
        """
        Get the queryset for the report model.
        :return: QuerySet of Report objects
        """
        if self.kwargs.get('section'):
            return self.model.objects.filter(section=self.kwargs.get('section'))
        else:
            return self.model.objects.all()

    def get_report(self, *args, slug='', **kwargs):
        """
        Fetch the report by slug and return its data.
        :param args: positional arguments
        :param slug: slug of the report
        :param kwargs: keyword arguments
        :return: dictionary with report data
        """
        slug = slug or kwargs.get('slug', '')
        queryset = self.get_queryset()
        report = queryset.filter(slug=slug).first()
        if not report:
            from reportcraft.registry import site
            code_report = site.get_report(slug)
            if code_report is not None:
                filters = dict(self.request.GET.items()) if hasattr(self, 'request') and self.request and hasattr(self.request, 'GET') else {}
                return code_report.generate(filters=filters)
            raise Http404('Report not found')

        filters = dict(self.request.GET.items())
        return report.generate(filters=filters)

    def get(self, request, *args, **kwargs):
        info = self.get_report(*args, **kwargs)
        return JsonResponse(info, safe=False)


class MainReportView(*VIEW_MIXINS, ReportView):
    pass


class ReportData(*VIEW_MIXINS, DataView):
    pass


class SourceData(*VIEW_MIXINS, View):
    model = models.DataSource

    def get(self, request, *args, **kwargs):

        source = self.model.objects.filter(pk=kwargs.get('pk')).first()
        if not source:
            raise Http404('Source not found')

        params = dict(request.GET.items())
        try:
            data = source.get_data(filters=params)
        except Exception:
            data = []
        content_type = self.kwargs.get('format', 'json').lower()
        if content_type == 'csv':
            return CsvResponse(data, headers=source.get_labels().keys())
        else:
            return JsonResponse(data, safe=False)


class ReportIndexView(ItemListView):
    model = models.Report
    list_filters = ['created', 'modified']
    list_columns = ['title', 'slug', 'description']
    list_search = ['slug', 'title', 'description', 'entries__title', 'notes']
    ordering = ['-created']
    paginate_by = 20
    template_name = 'reportcraft/index.html'
    link_url = 'report-view'
    link_kwarg = 'slug'
    limit_section = None
    include_code_reports = True
    registry = None

    def get_registry(self):
        if self.registry is not None:
            return self.registry
        from reportcraft.registry import site
        return site

    def get_link_url(self, obj):
        """
        Get the URL for the report view.
        Supports both ORM Report instances (using slug) and registered code report
        dictionary representations or objects (using obj.url or reverse('report-view', kwargs={'slug': obj.slug})).
        :param obj: Report object, dictionary representation, or CodeReport instance
        :return: URL string for the report
        """
        url = obj.get('url') if isinstance(obj, dict) else getattr(obj, 'url', None)
        if url:
            return url
        slug = obj.get('slug') if isinstance(obj, dict) else getattr(obj, 'slug', None)
        if not slug:
            return ''
        link_url = self.link_url or 'report-view'
        link_kwarg = self.link_kwarg or 'slug'
        return reverse(link_url, kwargs={link_kwarg: slug})

    def get_limit_section(self):
        return self.limit_section

    def filter_code_reports_by_search(self, items, search_text):
        if not search_text:
            return items
        from reportcraft.registry import CatalogItem
        matched = []
        for item in items:
            if hasattr(item, 'matches_search'):
                if item.matches_search(search_text):
                    matched.append(item)
            elif isinstance(item, dict):
                if CatalogItem(item).matches_search(search_text):
                    matched.append(item)
        return matched

    def get_code_reports(self):
        if not getattr(self, 'include_code_reports', True):
            return []
        registry = self.get_registry()
        section = self.get_limit_section()
        if section:
            items = registry.get_catalog_items(section=section)
        else:
            items = registry.get_catalog_items()

        search_query = ''
        if hasattr(self, 'request') and self.request and hasattr(self.request, 'GET'):
            search_query = self.request.GET.get('search', '').strip()
        if search_query:
            items = self.filter_code_reports_by_search(items, search_query)
        return items

    def get_queryset(self):
        section = self.get_limit_section()
        if section:
            self.queryset = self.model.objects.filter(section=section)
        else:
            self.queryset = self.model.objects.all()
        qs = super().get_queryset()

        code_reports = self.get_code_reports()
        if not code_reports:
            return qs

        orm_slugs = {r.slug for r in qs}
        unique_code_reports = [
            r for r in code_reports
            if (r.get('slug') if isinstance(r, dict) else getattr(r, 'slug', None)) not in orm_slugs
        ]
        return list(qs) + unique_code_reports

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'section' not in context:
            section = self.get_limit_section()
            if section:
                context['section'] = section
        return context


class ReportIndex(*VIEW_MIXINS, ReportIndexView):
    pass


class EditorReportList(*EDIT_MIXINS, ListView):
    model = models.Report
    template_name = 'reportcraft/off-canvas-list.html'
    context_object_name = 'items'
    link_url = 'report-editor'
    list_title = 'Reports'
    add_url = 'new-report'

    def get_queryset(self):
        return self.model.objects.all().order_by('-modified')


class DataSourceList(*EDIT_MIXINS, ListView):
    model = models.DataSource
    template_name = 'reportcraft/off-canvas-list.html'
    context_object_name = 'items'
    link_url = 'source-editor'
    list_title = 'Datasets'
    add_url = 'new-data-source'

    def get_queryset(self):
        return self.model.objects.all().order_by('-modified')


class SourceEditor(*EDIT_MIXINS, DetailView):
    template_name = 'reportcraft/source-editor.html'
    model = models.DataSource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        field_info = defaultdict(list)
        for field in self.object.fields.all().order_by('position'):
            field_info[field.model].append(field)
        context['source'] = self.object
        context['fields'] = dict(field_info)
        return context


class ReportEditorRoot(*EDIT_MIXINS, TemplateView):
    template_name = 'reportcraft/report-editor.html'
    link_url = 'report-editor'
    list_title = 'Reports'
    add_url = 'new-report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = models.Report.objects.all().order_by('-modified')
        context['show_sidebar'] = True
        return context


class ReportEditor(*EDIT_MIXINS, DetailView):
    template_name = 'reportcraft/report-editor.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['entries'] = self.object.entries.all()
        context['sources'] = models.DataSource.objects.all()
        context['used_sources'] = models.DataSource.objects.filter(entries__report=self.object).distinct()
        return context


class ReorderEntries(*EDIT_MIXINS, View):
    model = models.Report

    def post(self, request, *args, **kwargs):
        order = json.loads(request.body)
        report = models.Report.objects.filter(pk=self.kwargs['report']).first()
        if not report:
            return JsonResponse({'status': 'error', 'message': 'Report not found'}, status=404)

        positions = {pk: i for i, pk in enumerate(order)}
        to_update = report.entries.filter(pk__in=order)
        for entry in to_update:
            entry.position = positions[entry.pk]
            entry.modified = timezone.now()
        report.entries.bulk_update(to_update, ['position', 'modified'])

        return JsonResponse({'status': 'ok'})


class EditReport(*EDIT_MIXINS, ModalUpdateView):
    form_class = forms.ReportForm
    model = models.Report

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.pk})


class CreateReport(ModalCreateView):
    form_class = forms.ReportForm
    model = models.Report

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.pk})


class CreateDataSource(*EDIT_MIXINS, ModalCreateView):
    form_class = forms.DataSourceForm
    model = models.DataSource

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.pk})


class EditDataSource(*EDIT_MIXINS, ModalUpdateView):
    form_class = forms.DataSourceForm
    model = models.DataSource

    def get_initial(self):
        initial = super().get_initial()
        initial['group_fields'] = ', '.join(self.object.group_by or [])
        return initial

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        data = form.cleaned_data
        self.object.group_by = data.get('group_by', [])
        self.object.save()
        return super().form_valid(form)


class EditSourceField(*EDIT_MIXINS, ModalUpdateView):
    form_class = forms.DataFieldForm
    model = models.DataField

    def get_delete_url(self):
        return reverse('delete-source-field', kwargs={'source': self.object.source.pk, 'pk': self.object.pk})

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})


class AddSourceField(*EDIT_MIXINS, ModalCreateView):
    form_class = forms.DataFieldForm
    model = models.DataField

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['source'] = self.kwargs.get('source')
        if 'group' in self.kwargs:
            initial['name'] = self.kwargs.get('group')
            initial['label'] = initial['name'].title()
        initial['position'] = models.DataField.objects.filter(source=initial['source']).count()
        return initial


def update_model_fields(data, view):
    groups = data.pop('groups')
    for i, (name, expression) in enumerate(groups.items()):
        group, created = models.DataField.objects.get_or_create(
            name=name, model=view.object, source=view.object.source
        )
        models.DataField.objects.filter(pk=group.pk).update(
            expression=expression,
            source=view.object.source,
            label=name.title(),
            position=i,
            modified=timezone.now(),
        )


class AddSourceModel(*EDIT_MIXINS, ModalCreateView):
    form_class = forms.DataModelForm
    model = models.DataField

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['source'] = models.DataSource.objects.filter(pk=self.kwargs.get('source')).first()
        return kwargs

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['source'] = self.kwargs.get('source')
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        response = super().form_valid(form)
        update_model_fields(data, self)
        return response


class EditSourceModel(*EDIT_MIXINS, ModalUpdateView):
    form_class = forms.DataModelForm
    model = models.DataModel

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['source'] = models.DataSource.objects.filter(pk=self.kwargs.get('source')).first()
        return kwargs

    def get_delete_url(self):
        return reverse('delete-source-model', kwargs={'source': self.object.source.pk, 'pk': self.object.pk})

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})

    def form_valid(self, form):
        data = form.cleaned_data
        update_model_fields(data, self)
        return super().form_valid(form)


class EditEntry(*EDIT_MIXINS, ModalUpdateView):
    form_class = forms.EntryForm
    model = models.Entry

    def get_success_url(self):
        return reverse_lazy('report-editor', kwargs={'pk': self.object.report.pk})

    def get_delete_url(self):
        return reverse_lazy('delete-report-entry', kwargs={'report': self.object.report.pk, 'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['report'] = self.kwargs.get('report')
        return initial


class DeleteSourceModel(*EDIT_MIXINS, ModalDeleteView):
    model = models.DataModel


class DeleteReport(*EDIT_MIXINS, ModalDeleteView):
    model = models.Report
    success_url = reverse_lazy('report-editor-root')


class DeleteDataSource(*EDIT_MIXINS, ModalDeleteView):
    model = models.DataSource
    success_url = reverse_lazy('report-editor-root')


class DeleteEntry(*EDIT_MIXINS, ModalDeleteView):
    model = models.Entry


class DeleteSourceField(*EDIT_MIXINS, ModalDeleteView):
    model = models.DataField


class ConfigureEntry(*EDIT_MIXINS, ModalUpdateView):
    model = models.Entry
    FORM_CLASSES = {
        model.Types.TABLE: forms.TableForm,
        model.Types.BARS: forms.BarsForm,
        model.Types.COLUMNS: forms.BarsForm,
        model.Types.PIE: forms.PieForm,
        model.Types.PLOT: forms.PlotForm,
        model.Types.LIST: forms.ListForm,
        model.Types.TIMELINE: forms.TimelineForm,
        model.Types.TEXT: forms.RichTextForm,
        model.Types.HISTOGRAM: forms.HistogramForm,
        model.Types.MAP: forms.GeoCharForm,
        model.Types.DONUT: forms.PieForm,
        model.Types.LIKERT: forms.LikertForm,
    }

    def get_form_class(self):
        return self.FORM_CLASSES.get(self.object.kind, forms.EntryForm)

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})


class CreateEntry(*EDIT_MIXINS, ModalCreateView):
    form_class = forms.EntryForm
    model = models.Entry

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})

    def get_initial(self):
        report = models.Report.objects.filter(pk=self.kwargs.get('report')).first()
        if not report:
            raise Http404('Report not found')
        initial = super().get_initial()
        initial['report'] = self.kwargs.get('report')
        initial['position'] = report.entries.count()
        return initial

    def form_valid(self, form):
        super().form_valid(form)
        return HttpResponseRedirect(
            reverse('configure-report-entry', kwargs={'pk': self.object.pk, 'report': self.object.report.pk})
        )


class ImportEntry(*EDIT_MIXINS, ModalCreateView):
    form_class = forms.ImportEntryForm
    model = models.Entry

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})

    def get_initial(self):
        report = models.Report.objects.filter(pk=self.kwargs.get('pk')).first()
        if not report:
            raise Http404('Report not found')
        initial = super().get_initial()
        initial['report'] = report
        return initial

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        entry = models.Entry(**cleaned_data)
        entry.save()
        return JsonResponse({'url': ''})


class CloneEntry(*EDIT_MIXINS, ModalConfirmView):
    model = models.Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Clone Entry"
        context['message'] = "Are you sure you want to clone this entry?"
        return context

    def confirmed(self, *args, **kwargs):
        entry = self.get_object()
        obj = entry.clone()
        return JsonResponse({
            'url': ""
        })


class CloneDataSource(*EDIT_MIXINS, ModalConfirmView):
    model = models.DataSource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Clone Dataset"
        context['message'] = (
            "Are you sure you want to clone this dataset? "
            "This will also clone all associated models and fields."
        )
        return context

    def confirmed(self, *args, **kwargs):
        source = self.get_object()
        obj = source.clone()
        return JsonResponse({
            'url': reverse('source-editor', kwargs={'pk': obj.pk})
        })


class CloneReport(*EDIT_MIXINS, ModalConfirmView):
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Clone Report"
        context['message'] = (
            "Are you sure you want to clone this report? "
            "This will also clone all associated entries."
            "Datasets will not be cloned."
        )
        return context

    def confirmed(self, *args, **kwargs):
        report = self.get_object()
        obj = report.clone()
        return JsonResponse({
            'url': reverse('report-editor', kwargs={'pk': obj.pk})
        })