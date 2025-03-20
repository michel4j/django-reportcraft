# Django ReportCraft
A Django reusable App for dynamically designing and generating data visualization and 
business intelligence reports

## Summary of Features

### Report Creation
- Create and manage reports through a graphical designer.
- Easily add new report entries using the intuitive interface.

### Data Sources & Models
- **Data Sources:** Configure models that provide data for reports.  
  - Define the data source name, grouping fields, and record limit.
- **Data Source Models:**  
  - Add models to a data source.
  - Specify group expressions for data aggregation.

### Data Fields & Expressions
- Configure fields with attributes such as name, label, default value, and precision.
- **Expressions:**  
  - Use arithmetic operators (`+`, `-`, `*`, `/`, unary negation).
  - Reference Django field names using CamelCase and related fields with the `.` operator.
  - Group and nest expressions using parentheses.
  - Use string literals enclosed in quotes.
- **Supported Functions:**  
  - Django database functions (e.g., `Sum`, `Avg`, `Count`, etc.)
  - Custom functions (e.g., `ShiftStart`, `ShiftEnd`, `Hours`, `Minutes`, `DisplayName`).

### Report Entry Types & Configurations
- **Table Entry:**  
  - Configure rows, columns, values, column totals, row totals, and transpose option.
- **Bar Chart Entry:**  
  - Set the X-axis and one or more Y-axis fields.
  - Options for sorting, color schemes, stacking, label wrapping, and orientation.
- **Pie Chart Entry:**  
  - Define value and label fields for pie slices with color customization.
- **XY Plot Entry:**  
  - Configure dual Y-axes for left (Y1) and right (Y2).
  - Supports both line and scatter plot options.
- **List Entry:**  
  - Define multiple columns with sorting and ordering features.
- **Histogram Entry:**  
  - Choose a numeric field, configure the number of bins, and select a color scheme.
- **Text & Rich Text Entries:**  
  - Display plain text or markdown formatted rich text.

### Demo Application
A demo site showcasing an example configuration of various features is available in the repository. After cloning
the repository,

    poetry install
    ./manage.py migrate
    ./manage.py loaddata initial-data
    ./manage.py createsuperuser
    ./manage.py runserver
 
 Open the browser to http://localhost:8000/admin and log in with the superuser credentials created in the previous step.
 Click the "View Site" link in the top right corner of the page to access the main page, also accessible 
 from http://localhost:8000.
 
### Documentation
Detailed documentation and screenshots are available at https://michel4j.github.io/django-reportcraft/. 