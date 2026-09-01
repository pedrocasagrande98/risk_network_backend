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

import urllib.request
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class StormProxyView(APIView):
    permission_classes = [permissions.AllowAny] # Pode ajustar conforme necessidade

    def post(self, request, *args, **kwargs):
        payload = request.data
        try:
            req = urllib.request.Request(
                'http://localhost:8005/api/wind/plot',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return Response(result, status=response.status)
        except urllib.error.HTTPError as e:
            return Response({'error': str(e)}, status=e.code)
        except Exception as e:
            return Response({'error': f'Failed to connect to storm service: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
