Usage
=====

To use Django ReportCraft, Navigate to https://mysite/reports/ and create a new report entry by clicking the
`Add Report` button on the top-right corner. Make sure you are logged in otherwise the button will not be visible.

Once you have created a report, you can build the report using the graphical designer by creating Data Sources,
Data Fields, and Report Entries.


Data Sources
------------

A Data Source is a model that provides data for the report. You can create a new Data Source by clicking Add Data Source
button from the Sources list. To create a new Data Source, you need to provide the following information:

- Name: The name of the Data Source.
- Group Fields: A comma separate list of group fields to use for aggregating the data.
- Limit: The maximum number of records to return. This field is optional.

Data Source Models
------------------
After creating a Data Source, you can add Models to it. Models need to be added first, as all Data Fields are linked
to specific models defined within the Source. Models can be added by clicking the Add Model button from the Data Source
editor pages.  To add a new Model, you need to provide the following information:

- Model: The model to use for the data source. Select a model from the dropdown list. Only models that are part of
  applications whose `app_label` is included in the REPORTCRAFT_APPS setting list will be available.
- Group Expressions: For each group field, you can provide an expression to use for grouping the data. The expression
  should be a valid `Expression`. See the Expressions section below.

Data Fields
-----------
After adding a Model, you can add Fields to it. Fields can be added by clicking the Add Field from the Source Editor
page.  The following information is required to add a new Field:

- Name: The name of the field. This should be a valid identifier. We recommend using snake_case for the field name.
- Label: The label to use for the field in the report. This should be a human readable string.
- Model: The model to use for the field. Select a model from the dropdown list. Only models that have been added to the
  Source, are available.
- Ordering (optional): A signed integer to use for ordering by the values of the field. Larger magnitutes get precedence,
  and the sign determined the order (ascending or descending).
- Default (optional): The default value to use for the field if no entries are found.
- Precision (optional): The number of decimal places to use for the field. Values are rounded to the specified precision.
- Position: The position of the field relative to other fields in the report. While the `Ordering` field is used for
  ordering the data, the `Position` field is used for ordering the fields in the report.
- Expression: The expression to use for the field. The expression should be a valid `Expression`. See the Expressions
  section below.

Expressions
-----------
Expressions are used to define how to calculate the value of a field. Expressions can be simple field references or
Mathematical expressions. The following operators are supported:

- `+`: Addition
- `-`: Subtraction
- `*`: Multiplication
- `/`: Division
- `-`: Unary negation

Field names are referenced using CamelCase. For example, to reference a field named `total_amount`, you would use `TotalAmount`
in the expression.  You can also reference group fields using the same syntax. For example, to reference a group field named
`category`, you would use `Category` in the expression.  Related fields must be referenced using the `.` operator instead
of the `__` operator. For example, to reference a related field named `name` on a related model named `institution`, you would
use `Institution.Name` in the expression.

Any unquoted identifier that is not a function or a literal is assumed to be a field name.  For example, `TotalAmount * 0.1`
would multiply the value of the `TotalAmount` field by the value 0.1.  You can also use parentheses to group expressions. For example,
`(TotalAmount + TaxAmount) * 0.1` would add the value of the `TotalAmount` field to the value of the `TaxAmount` field and
then multiply the result by 0.1.  String literals must be enclosed in single or double quotes. For example, `'Hello, World!'`.

Functions must use parentheses immediately after the identifier to enclose arguments. Nesting is supported.

The following functions are supported:

.. code-block:: python
    [Sum, Avg, Count, Max, Min, Concat, Greatest, Least,
    Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan, ATan2, Mod, Sign, Trunc,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek,
    Upper, Lower, Length, Substr, LPad, RPad, Trim, LTrim, RTrim,
    Radians, Degrees, Hours, Minutes, ShiftStart, ShiftEnd, Q, DisplayName]


For date based fields, you can use subfields to extract parts of the date. For example, instead of using a function to
extract the year from a date field like `ExtractYear(Date)` in the expression. It is valid and much easier to use
`Date.Year`.

Report Entries
--------------

A report is made up of a collection of entries. Each entry is a single component that can be displayed in a report. You
can create a new entry by clicking the Add Entry button from the Report Editor page. To create a new entry, you need to
provide initially the following information:

- Title (optional): The title of the entry. This will be displayed as either the heading of the entry or the caption of the table or
  chart.
- Position: The position of the entry relative to other entries in the report. The position is used to order the entries
  in the report.
- Description (optional): A description of the entry. This will be displayed as a paragraph of text at the top of the entry.
- Notes (optional): Notes to display at the bottom of the entry. Notes are often used to provide additional information
  about the entry.
- Data Source: The data source to use for the entry. Select a data source from the dropdown list. Only data sources that
  have been added to the report are available.
- Width: The width of the entry. The width is used to determine how much space the entry takes up in the report. The width
  is a fraction of the total width of the report.  The following widths are supported:

    - Full: The entry takes up the full width of the report.
    - Three Quarters: The entry takes up three quarters of the width of the report.
    - Two Thirds: The entry takes up two thirds of the width of the report.
    - Half: The entry takes up half of the width of the report.
    - Third: The entry takes up a third of the width of the report.
    - Quarter: The entry takes up a quarter of the width of the report.

- Type: The type of the entry. The type determines how the data is displayed. The following types are supported:

    - Table: A table that displays the data in a tabular format.
    - Bar Chart: A chart that displays the data in a bar chart format.
    - Pie Chart: A chart that displays the data in a pie chart format.
    - XY Plot: A chart that displays the data in a XY chart format with lines or points.
    - Chart: A chart that displays the data in a graphical format.
    - Histogram: A chart that displays the data in a histogram format.
    - Text: A text entry that displays the data as a paragraph of text.
    - List: A special type of table that displays a list of entries. Each row in a List is usually quite similar to the other rows unlike a Table.
    - Rich Text: A text entry that displays markdown formatted text.

Once you have created an entry, you can configure it using the toolbar icons on the entry.  The specific configuration
options depend on the type of the entry.


Table Entry
-----------
A Table Entry displays the data in a tabular format. The table entry has the following configuration options:

- Rows: One or more fields to display as the rows of the table. Select the fields to display as the rows from the dropdown list.
  Only fields that have been added to the data source are available.
- Columns:  The field to use as the columns of the table. For example, if the data is grouped by Year, the `Year`
  field would be an appropriate Column field.
- Values: The fields to use as the values of the table when a single field is specified under Rows. In this case, the
  Values of the Rows field will be used as the columns and the table cells will contain corresponding values from the
  Values field.
- Column Totals: Toggle to add a row at the bottom of the table that contains the totals for each column.
- Row Totals: Toggle to add a column at the right of the table that contains the totals for each row.
- Transpose:  Flip the rows and columns of the table. This is useful when the data is more naturally displayed with the
  rows as columns and the columns as rows.
- Force Strings: Convert all values to formatted strings.


Bar Chart Entry
---------------
A Bar Chart Entry displays the data in a bar chart format. The bar chart entry has the following configuration options:

- X Axis: The field to use as the x-axis of the chart. This field will be used to label the bars on the x-axis.
- Y Axis: One or more fields to use as the y-axis of the chart. This field will be used to determine the height of the bars on the
  y-axis. Enter multiple fields to represent multiple series of bars.
- Values: The field to use as the values of the chart. This field will be used to determine the height of the bars on the
  y-axis if a single field is specified under Y Axis. In this case, the
  Values of the Y-axis field will be used as the series.
- Sort By: The field to use for sorting the bars on the x-axis.
- Color By: The field to use for coloring the bars.
- Color Scheme: The color palette to use for coloring the bars. The following color schemes are supported:

    - Accent
    - Dark2
    - Live4
    - Live8
    - Live16
    - Paired
    - Pastel1
    - Pastel2
    - Set1
    - Set2
    - Set3
    - Tableau10
    - Category10
    - Observable10

- Aspect Ratio: The ratio of the width to the height of the bars.
- Culling: The maximum number of X-axis ticks to display.
- Stack: Specify the groups of fields to stack. Only fields already specified under Y-axis should be included
- Wrap Labels: Wrap the labels on the x-axis to multiple lines.
- Vertical bars: Display the bars vertically instead of horizontally.
- Sort Descending: Sort the bars in descending order.

Pie Chart Entry
---------------

A Pie Chart Entry displays the data in a pie chart format. The pie chart entry has the following configuration options:

- Value: The field to use as the values of the chart. This field will be used to determine the size of the slices in the
  pie chart.
- Label: The field to use as the labels of the chart. This field will be used to label the slices in the pie chart.
- Color By: The field to use for coloring the slices.
