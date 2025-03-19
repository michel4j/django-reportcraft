Installation
============
To install Django ReportCraft, use pip:

.. code-block:: bash

   pip install django-reportcraft

Add `reportcraft` to your `INSTALLED_APPS` in your Django settings:

.. code-block:: python

   INSTALLED_APPS = [
       ...
       'reportcraft',
       ...
   ]

ReportCraft users the `django-crisp-modals` and `django-crispy-forms` packages to display modal forms. Therefore
Add `crispy_forms` and `crisp_modals` to your `INSTALLED_APPS` in your Django settings:

.. code-block:: python

   INSTALLED_APPS = [
       ...
       'crispy_forms',
       'crispy_bootstrap5',
       'crisp_modals',
       ...
   ]

   CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
   CRISPY_TEMPLATE_PACK = "bootstrap5"

Run the migrations to create all required database tables:

.. code-block:: bash

   python manage.py migrate

Add the ReportCraft URLs to your Django project's URL configuration:

.. code-block:: python

   urlpatterns = [
       ...
       path('reports/', include('reportcraft.urls')),
       ...
   ]


Django ReportCraft front-end requires Bootstrap 5 and above and jQuery. Therefore ensure that your project includes
the required assets in the `base.html` template. Additionally your base template should provide the following template
blocks into which ReportCraft will render it's content:

.. code-block:: django

   {% block page-pretitle %}{% endblock %}
   {% block page-title %}{% endblock %}
   {% block page-content %}{% endblock %}
   {% block page-tools %}{% endblock %}
   {% block page-scripts %}{% endblock %}


- `page-pretitle`: This optional block is used to render a small description above the title.
- `page-title`: This block is used to render the title of the page.
- `page-tools`: This block is used to render additional context-dependent tools for the page.
- `page-content`: This block is used to render the main content of the page.
- `page-scripts`: This block is used to render additional scripts required by the page,
  usually at the bottom of the body tag.

See the `base.html` template in the demo application for an example.

