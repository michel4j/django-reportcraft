Usage
=====

To use Django ReportCraft, follow these steps:

1. Navigate to https://mysite/reports/ and create a new report entry by clicking the `Add Report` button on the top-right
   corner of the window.

2. Configure the report fields and settings.
3. Generate the report.

Example:

.. code-block:: python

   from reportcraft.models import Report

   report = Report.objects.create(name='My Report')
   report.configure(fields=['field1', 'field2'], settings={'setting1': 'value1'})
   report.generate()