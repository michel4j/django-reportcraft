from collections import defaultdict
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, edit
from crisp_modals.views import ModalUpdateView, ModalCreateView, ModalDeleteView
from itemlist.views import ItemListView

from . import models, forms
    

class ReportView(DetailView):
    template_name = 'reportcraft/report.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['data_url'] = reverse('report-data', kwargs={'slug': self.object.slug})
        return context


class ReportData(View):
    @staticmethod
    def get_report(*args, slug='', **kwargs):
        report = models.Report.objects.filter(slug=slug).first()
        if not report:
            raise Http404('Report not found')

        return {
            'title': report.title,
            'description': report.description,
            'style': f"row {report.style}",
            'content': [block.generate(*args, **kwargs) for block in report.entries.all()],
            'notes': report.notes
        }

    def get(self, request, *args, **kwargs):
        info = self.get_report(*args, **kwargs)
        return JsonResponse({'details': [info]}, safe=False)


class ReportList(ItemListView):
    model = models.Report
    list_filters = ['created', 'modified']
    list_columns = ['title', 'slug', 'description']
    list_search = ['slug', 'title', 'description', 'entries__title', 'notes']
    ordering = ['-created']
    paginate_by = 15
    template_name = 'reportcraft/index.html'
    link_url = 'report-view'
    link_kwarg = 'slug'


class DataSourceList(ItemListView):
    model = models.DataSource
    list_filters = ['created', 'modified']
    list_columns = ['name', 'limit']
    list_search = ['fields__name', 'entries__title']
    ordering = ['-created']
    paginate_by = 25
    template_name = 'reportcraft/list.html'
    tool_template = 'reportcraft/source-list-tools.html'
    link_url = 'source-editor'
    list_title = 'Data Sources'


class SourceEditor(DetailView):
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


class ReportEditor(DetailView):
    template_name = 'reportcraft/report-editor.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['entries'] = self.object.entries.all()
        context['sources'] = models.DataSource.objects.all()
        context['used_sources'] = models.DataSource.objects.filter(entries__report=self.object).distinct()
        return context


class EditReport(ModalUpdateView):
    form_class = forms.ReportForm
    model = models.Report

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.pk})


class CreateReport(ModalCreateView):
    form_class = forms.ReportForm
    model = models.Report

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.pk})


class CreateDataSource(ModalCreateView):
    form_class = forms.DataSourceForm
    model = models.DataSource

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.pk})


class EditDataSource(ModalUpdateView):
    form_class = forms.DataSourceForm
    model = models.DataSource

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.pk})


class EditSourceField(ModalUpdateView):
    form_class = forms.DataFieldForm
    model = models.DataField

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})


class AddSourceField(ModalCreateView):
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


class AddSourceModel(ModalCreateView):
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


class EditSourceModel(ModalUpdateView):
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


class EditEntry(ModalUpdateView):
    form_class = forms.EntryForm
    model = models.Entry

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['report'] = self.kwargs.get('report')
        return initial


class DeleteSourceModel(ModalDeleteView):
    model = models.DataModel


class DeleteReport(ModalDeleteView):
    model = models.Report


class DeleteDataSource(ModalDeleteView):
    model = models.DataSource


class DeleteEntry(ModalDeleteView):
    model = models.Entry


class DeleteSourceField(ModalDeleteView):
    model = models.DataField


class ConfigureEntry(ModalUpdateView):
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
        }.get(self.object.kind, forms.EntryForm)

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})


class CreateEntry(ModalCreateView):
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

