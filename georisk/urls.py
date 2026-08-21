from django.urls import path
from .views import GeoEventListCreateView, GeoEventRetrieveView

urlpatterns = [
    path('', GeoEventListCreateView.as_view(), name='geoevent-list-create'),
    path('<int:pk>/', GeoEventRetrieveView.as_view(), name='geoevent-detail'),
]
