from django.urls import path
from .views import GeoEventListCreateView, GeoEventRetrieveView, StormProxyView
from .views_gee import GEETileView

urlpatterns = [
    path('', GeoEventListCreateView.as_view(), name='geoevent-list-create'),
    path('<int:pk>/', GeoEventRetrieveView.as_view(), name='geoevent-detail'),
    path('storm/plot/', StormProxyView.as_view(), name='storm-plot'),
    # Google Earth Engine tiles: /api/georisk/gee/queimada/, /api/georisk/gee/tempestade/
    path('gee/<str:event_type>/', GEETileView.as_view(), name='gee-tiles'),
]