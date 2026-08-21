from rest_framework import generics, permissions
from .models import GeoEvent
from .serializers import GeoEventSerializer
from .tasks import process_new_geoevent

from .filters import FilterStrategyFactory

class GeoEventListCreateView(generics.ListCreateAPIView):
    serializer_class = GeoEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        filter_type = self.request.query_params.get('type', 'global')
        strategy = FilterStrategyFactory.get_strategy(filter_type)
        queryset = strategy.filter(self.request.user)

        include_mine = self.request.query_params.get('include_mine', 'false').lower() == 'true'
        if include_mine and self.request.user.is_authenticated:
            my_events = GeoEvent.objects.filter(user=self.request.user).order_by('-created_at')
            queryset = (queryset | my_events).distinct().order_by('-created_at')

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        # Dispara a task assíncrona para não travar a requisição HTTP
        process_new_geoevent.delay(instance.id)

class GeoEventRetrieveView(generics.RetrieveAPIView):
    queryset = GeoEvent.objects.all()
    serializer_class = GeoEventSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
