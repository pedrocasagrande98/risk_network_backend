from django.urls import path
from .views import GeoEventListCreateView

urlpatterns = [
    path('', GeoEventListCreateView.as_view(), name='geoevent-list-create'),
]
