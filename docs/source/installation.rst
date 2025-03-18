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
