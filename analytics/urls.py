from django.urls import path
from .views import SearchHistoryView

urlpatterns = [
    path('history/', SearchHistoryView.as_view(), name='search-history'),
]
