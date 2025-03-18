from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportcraft'

    def ready(self):
        from django.conf import settings
        settings = settings._wrapped.__dict__
        settings.setdefault('REPORTCRAFT_APPS', [])
        settings.setdefault('REPORTCRAFT_MIXINS', {
            'VIEW': [],
            'EDIT': ['django.contrib.auth.mixins.LoginRequiredMixin'],
        })
