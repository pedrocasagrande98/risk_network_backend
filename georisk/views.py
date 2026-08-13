from rest_framework import generics, permissions
from .models import GeoEvent
from .serializers import GeoEventSerializer
from .tasks import process_new_geoevent

class GeoEventListCreateView(generics.ListCreateAPIView):
    queryset = GeoEvent.objects.all().order_by('-created_at')
    serializer_class = GeoEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        # Dispara a task assíncrona para não travar a requisição HTTP
        process_new_geoevent.delay(instance.id)
