from django.urls import path
from .views import AudioUploadView

urlpatterns = [
    path('upload-audio/', AudioUploadView.as_view(), name='upload-audio'),
]
