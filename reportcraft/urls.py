from django.urls import path

from . import views

urlpatterns = [
    path('editor/', views.ReportEditorRoot.as_view(), name='report-editor-root'),
    path('editor/list/', views.EditorReportList.as_view(), name='editor-report-list'),
    path('editor/add/', views.CreateReport.as_view(), name='new-report'),
    path('editor/<int:pk>/', views.ReportEditor.as_view(), name='report-editor'),
    path('editor/<int:pk>/edit/', views.EditReport.as_view(), name='edit-report'),
    path('editor/<int:pk>/delete/', views.DeleteReport.as_view(), name='delete-report'),

    path('editor/<int:report>/edit/<int:pk>/', views.EditEntry.as_view(), name='edit-report-entry'),
    path('editor/<int:report>/delete/<int:pk>/', views.DeleteEntry.as_view(), name='delete-report-entry'),
    path('editor/<int:report>/add/', views.CreateEntry.as_view(), name='add-report-entry'),
    path('editor/<int:report>/config/<int:pk>/', views.ConfigureEntry.as_view(), name='configure-report-entry'),

    path('editor/sources/', views.DataSourceList.as_view(), name='data-source-list'),
    path('editor/sources/add/', views.CreateDataSource.as_view(), name='new-data-source'),
    path('editor/sources/<int:pk>/', views.SourceEditor.as_view(), name='source-editor'),
    path('editor/sources/<int:pk>/edit/', views.EditDataSource.as_view(), name='edit-data-source'),
    path('editor/sources/<int:pk>/delete/', views.DeleteDataSource.as_view(), name='delete-data-source'),

    path('editor/sources/<int:source>/add-field/', views.AddSourceField.as_view(), name='add-source-field'),
    path('editor/sources/<int:source>/add-field/<slug:group>/', views.AddSourceField.as_view(), name='add-group-field'),
    path('editor/sources/<int:source>/edit-field/<int:pk>/', views.EditSourceField.as_view(), name='edit-source-field'),
    path('editor/sources/<int:source>/del-field/<int:pk>/', views.DeleteSourceField.as_view(), name='delete-source-field'),

    path('editor/sources/<int:source>/add-model/', views.AddSourceModel.as_view(), name='add-source-model'),
    path('editor/sources/<int:source>/edit-model/<int:pk>/', views.EditSourceModel.as_view(), name='edit-source-model'),
    path('editor/sources/<int:source>/del-model/<int:pk>/', views.DeleteSourceModel.as_view(), name='delete-source-model'),

    path('view/', views.ReportIndex.as_view(), name='report-list'),
    path('view/<slug:slug>/', views.MainReportView.as_view(), name='report-view'),
    path('api/reports/<slug:slug>/', views.ReportData.as_view(), name='report-data'),
    path('api/sources/<int:pk>/', views.SourceData.as_view(), name='source-data'),
 ]