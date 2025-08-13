from collections import defaultdict

from django.conf import settings
from django.http import JsonResponse, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView, edit, ListView, TemplateView
from crisp_modals.views import ModalUpdateView, ModalCreateView, ModalDeleteView
from itemlist.views import ItemListView

from . import models, forms
from .utils import CsvResponse

VIEW_MIXINS = [import_string(mixin) for mixin in settings.REPORTCRAFT_MIXINS.get('VIEW',[])]
EDIT_MIXINS = [import_string(mixin) for mixin in settings.REPORTCRAFT_MIXINS.get('EDIT', [])]


class ReportView(DetailView):
    template_name = 'reportcraft/report.html'
    model = models.Report
    data_url = 'report-data'

    def get_data_url(self):
        """
        Get the URL for the report data endpoint.
        :return: URL for the report data
        """
        return reverse(self.data_url, kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
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

        queryset = self.get_queryset()
        report = queryset.filter(slug=slug).first()
        if not report:
            raise Http404('Report not found')

        filters = dict(self.request.GET.items())
        return {
            'report-title': report.title,
            'description': report.description,
            'style': f"row {report.style}",
            'content': [block.generate(filters=filters) for block in report.entries.all()],
            'notes': report.notes
        }

    def get(self, request, *args, **kwargs):
        info = self.get_report(*args, **kwargs)
        return JsonResponse({'details': [info]}, safe=False)


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
        content_type = request.GET.get('type', 'json')
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

    def get_link_url(self, obj):
        """
        Get the URL for the report view.
        :param obj: Report object
        :return: URL for the report view
        """
        return reverse(self.link_url, kwargs={self.link_kwarg: obj.slug})

    def get_limit_section(self):
        return self.limit_section

    def get_queryset(self):
        section = self.get_limit_section()
        if section:
            self.queryset = self.model.objects.filter(section=section)
        else:
            self.queryset = self.model.objects.all()
        return super().get_queryset()


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
    list_title = 'Data Sources'
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
        model.Types.AREA: forms.BarsForm,
        model.Types.LINE: forms.BarsForm,
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

