from django.urls import path
from .views import UploadCSVView, LatestSummary, History, GeneratePDF

urlpatterns = [
    path("upload/", UploadCSVView.as_view()),
    path("summary/latest/", LatestSummary.as_view()),
    path("history/", History.as_view()),
    path("report/<int:pk>/", GeneratePDF.as_view()),
]

