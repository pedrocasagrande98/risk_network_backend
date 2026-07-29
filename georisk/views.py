from rest_framework import generics, permissions
from .models import GeoEvent
from .serializers import GeoEventSerializer

class GeoEventListCreateView(generics.ListCreateAPIView):
    queryset = GeoEvent.objects.all().order_by('-created_at')
    serializer_class = GeoEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
