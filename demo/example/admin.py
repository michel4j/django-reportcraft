from django.contrib import admin
from .models import Journal, Metric, Publication, Subject, Institution, Person, Country


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('journal', 'year', 'impact_factor')
    list_filter = ('journal', 'year')


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'journal', 'published')
    list_filter = ('journal', 'published')
    search_fields = ('title',)
