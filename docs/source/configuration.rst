Configuration
=============

Django ReportCraft can be configured using the following settings:

- `REPORTCRAFT_APPS`: A list of strings representing the apps that contain the models to be used in reports. Only
  models from these apps will be available for use in reports. Default is `[]`.
- `REPORTCRAFT_MIXINS`: A dictionary mapping strings 'VIEW' and 'EDIT' to lists of strings representing the full
  class name of mixin classes for ReportCraft views. This can be used to customize the behavior of the ReportCraft views
  and provide additional authentication requirements.  By default, access edit reports is open to all logged-in users.

  For example:

    .. code-block:: python

         REPORTCRAFT_MIXINS = {
             'VIEW': ['django.contrib.auth.mixins.LoginRequiredMixin'],
             'EDIT': [
                'django.contrib.auth.mixins.LoginRequiredMixin',
                'myapp.mixins.MySecurityMixin'
             ],
         }
