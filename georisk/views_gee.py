"""
Camada fina de apresentação (SRP): a view apenas valida a entrada e delega
a obtenção do MapID ao GEEProvider.
"""
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.gee_client import GEEProviderError, get_gee_provider

logger = logging.getLogger(__name__)


class GEETileView(APIView):
    """
    GET /api/georisk/gee/<event_type>/  → MapID/token/tile_fetcher do Earth Engine.

    Frontend consome: L.tileLayer(payload.tile_fetcher).
    """
    permission_classes = [AllowAny]  # Requisição é stateless; tiles são públicos

    def get(self, request, event_type=None):
        provider = get_gee_provider()

        if event_type == 'queimada':
            params = getattr(request, 'query_params', request.GET)
            start_date = params.get('start') or None
            end_date = params.get('end') or None
            try:
                payload = provider.get_fire_tiles(
                    start_date=start_date, end_date=end_date
                )
            except GEEProviderError as e:
                logger.warning("GEE (queimada) falhou: %s", e)
                return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response(payload)

        if event_type == 'geada':
            params = getattr(request, 'query_params', request.GET)
            start_date = params.get('start') or None
            end_date = params.get('end') or None
            try:
                payload = provider.get_frost_tiles(
                    start_date=start_date, end_date=end_date
                )
            except GEEProviderError as e:
                logger.warning("GEE (geada) falhou: %s", e)
                return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response(payload)

        if event_type == 'tempestade':
            params = getattr(request, 'query_params', request.GET)
            start_date = params.get('start') or None
            end_date = params.get('end') or None
            try:
                payload = provider.get_storm_tiles(
                    start_date=start_date, end_date=end_date
                )
            except GEEProviderError as e:
                logger.warning("GEE (tempestade) falhou: %s", e)
                return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response(payload)

        return Response(
            {'error': f"Tipo de camada GEE desconhecido: '{event_type}'. "
                      "Use 'queimada' ou 'tempestade'."},
            status=status.HTTP_400_BAD_REQUEST,
        )