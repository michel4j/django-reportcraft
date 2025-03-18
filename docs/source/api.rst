API Reference
=============

Django ReportCraft provides an API to fetch the raw report JSON data used for reports.  The following endpoints
are available:

- `.../api/reports/<report-slug>/`: Fetch the raw JSON data for a specific report. The report slug is used to identify
  the report. This endpoint is used internally to generate the graphical reports. This is the best option if you want the
  data from the report exactly as is in a computer friendly format.

- `.../api/sources/<source-id>/`: Fetch the raw JSON data for a specific data source identified by it's ID.