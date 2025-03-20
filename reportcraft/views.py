from collections import defaultdict
from django.conf import settings
from django.http import JsonResponse, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.module_loading import import_string
from django.views import View
from django.views.generic import DetailView, edit
from crisp_modals.views import ModalUpdateView, ModalCreateView, ModalDeleteView
from itemlist.views import ItemListView

from . import models, forms


VIEW_MIXINS = [import_string(mixin) for mixin in settings.REPORTCRAFT_MIXINS.get('VIEW',[])]
EDIT_MIXINS = [import_string(mixin) for mixin in settings.REPORTCRAFT_MIXINS.get('EDIT', [])]


class ReportView(*VIEW_MIXINS, DetailView):
    template_name = 'reportcraft/report.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['data_url'] = reverse('report-data', kwargs={'slug': self.object.slug})
        return context


class ReportData(*VIEW_MIXINS, View):
    @staticmethod
    def get_report(*args, slug='', **kwargs):
        report = models.Report.objects.filter(slug=slug).first()
        if not report:
            raise Http404('Report not found')

        return {
            'report-title': report.title,
            'description': report.description,
            'style': f"row {report.style}",
            'content': [block.generate(*args, **kwargs) for block in report.entries.all()],
            'notes': report.notes
        }

    def get(self, request, *args, **kwargs):
        info = self.get_report(*args, **kwargs)
        return JsonResponse({'details': [info]}, safe=False)


class SourceData(*VIEW_MIXINS, View):
    model = models.DataSource

    def get(self, request, *args, **kwargs):
        source = self.model.objects.filter(pk=kwargs.get('pk')).first()
        if not source:
            raise Http404('Source not found')
        data = source.get_data()
        return JsonResponse(data, safe=False)


class ReportList(*VIEW_MIXINS, ItemListView):
    model = models.Report
    list_filters = ['created', 'modified']
    list_columns = ['title', 'slug', 'description']
    list_search = ['slug', 'title', 'description', 'entries__title', 'notes']
    ordering = ['-created']
    paginate_by = 15
    template_name = 'reportcraft/index.html'
    link_url = 'report-view'
    link_kwarg = 'slug'


class DataSourceList(*EDIT_MIXINS, ItemListView):
    model = models.DataSource
    list_filters = ['created', 'modified']
    list_columns = ['name', 'limit', 'group_by']
    list_search = ['fields__name', 'entries__title']
    list_transforms = {
        'group_by': lambda x, y: ', '.join(x) or '-',
    }
    ordering = ['-created']
    paginate_by = 25
    template_name = 'reportcraft/list.html'
    tool_template = 'reportcraft/source-list-tools.html'
    link_url = 'source-editor'
    list_title = 'Data Sources'


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
    success_url = reverse_lazy('report-list')


class DeleteDataSource(*EDIT_MIXINS, ModalDeleteView):
    model = models.DataSource
    success_url = reverse_lazy('data-source-list')


class DeleteEntry(*EDIT_MIXINS, ModalDeleteView):
    model = models.Entry


class DeleteSourceField(*EDIT_MIXINS, ModalDeleteView):
    model = models.DataField


class ConfigureEntry(*EDIT_MIXINS, ModalUpdateView):
    model = models.Entry

    def get_form_class(self):
        return {
            models.Entry.Types.TABLE: forms.TableForm,
            models.Entry.Types.BARS: forms.BarsForm,
            models.Entry.Types.PIE: forms.PieForm,
            models.Entry.Types.PLOT: forms.PlotForm,
            models.Entry.Types.LIST: forms.ListForm,
            models.Entry.Types.TIMELINE: forms.TimelineForm,
            models.Entry.Types.TEXT: forms.RichTextForm,
            models.Entry.Types.HISTOGRAM: forms.HistogramForm,
        }.get(self.object.kind, forms.EntryForm)

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

