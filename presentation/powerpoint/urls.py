from django.urls import path

from . import views

app_name = 'powerpoint'

urlpatterns = [
    path('', views.index, name='index'),

    path('documents/', views.document, name='document'),
    path('documents/preview/<int:document_id>/', views.document_preview, name='document_preview'),
    path('documents/edit/<int:document_id>/', views.document_edit, name='document_edit'),
    path('documents/download/<int:document_id>/', views.document_download, name='document_download'),
    path('documents/delete/<int:document_id>/', views.document_delete, name='document_delete'),

    path('maindocuments/', views.merge, name='merge'),
    path('maindocuments/preview/<int:document_id>/', views.merge_preview, name='merge_preview'),
    path('maindocuments/download/<int:document_id>/', views.merge_download, name='merge_download'),
    path('maindocuments/delete/<int:document_id>/', views.merge_delete, name='merge_delete'),

    path('samples/', views.sample, name='sample'),
    path('samples/preview/<int:document_id>/', views.sample_preview, name='sample_preview'),
    path('samples/edit/<int:document_id>/', views.sample_edit, name='sample_edit'),
    path('samples/download/<int:document_id>/', views.sample_download, name='sample_download'),

    path('media/<path:path>', views.protected_media_view, name='protected_media_view'),
]
