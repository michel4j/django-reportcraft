from django.urls import reverse
from django.views.generic import ListView, TemplateView
from crisp_modals.views import ModalUpdateView, ModalCreateView, ModalDeleteView
from demo.example.forms import PersonForm, InstitutionForm, SubjectForm
from demo.example.models import Person, Institution, Subject
from itemlist.views import ItemListView
from itemlist.filters import YearLimitFilterFactory, MonthFilterFactory, QuarterFilterFactory


# Create your views here.
class FancyPersonList(ItemListView):
    model = Person
    template_name = 'list.html'
    list_columns = ['first_name', 'last_name', 'age', 'type', 'institution']
    list_search = ['first_name', 'last_name', 'age', 'type', 'bio', 'institution__name']
    list_filters = [
        'type',
        YearLimitFilterFactory.new('created', 'since'),
        YearLimitFilterFactory.new('created', 'until'),
    ]
    list_title = 'Fancy People'
    link_url = 'person-edit'
    link_attr = 'data-modal-url'
    tool_template = 'example/people-tools.html'
    paginate_by = 15


class FancyInstitutionList(ItemListView):
    model = Institution
    template_name = 'list.html'
    list_columns = ['id', 'name', 'city', 'province', 'country__name', 'parent']
    list_search = ['name', 'city', 'parent__name', 'subjects__name']
    list_filters = ['parent', 'created']
    list_title = 'Fancy Institutions'
    link_url = 'institution-edit'
    link_attr = 'data-modal-url'
    link_field = 'name'
    tool_template = 'example/institutions-tools.html'
    paginate_by = 15


class FancySubjectList(ItemListView):
    model = Subject
    template_name = 'list.html'
    list_columns = ['name', 'description']
    list_search = ['name', 'description', 'institutions__name']
    list_title = 'Fancy Subjects'
    link_url = 'subject-edit'
    link_attr = 'data-modal-url'
    tool_template = 'example/subjects-tools.html'
    paginate_by = 15


class EditPerson(ModalUpdateView):
    model = Person
    form_class = PersonForm


class AddPerson(ModalCreateView):
    model = Person
    form_class = PersonForm


class EditInstitution(ModalUpdateView):
    model = Institution
    form_class = InstitutionForm


class AddInstitution(ModalCreateView):
    model = Institution
    form_class = InstitutionForm


class EditSubject(ModalUpdateView):
    model = Subject
    form_class = SubjectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['delete_url'] = reverse('subject-delete', kwargs={'pk': self.object.pk})
        return kwargs


class AddSubject(ModalCreateView):
    model = Subject
    form_class = SubjectForm


class DeletePerson(ModalDeleteView):
    model = Person


class DeleteInstitution(ModalDeleteView):
    model = Institution


class DeleteSubject(ModalDeleteView):
    model = Subject


class HomeView(TemplateView):
    template_name = "example/home.html"

