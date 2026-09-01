"""
Testes do Inject GEE (backend).

Cobre:
- GEEProvider: resolução de credenciais via ambiente, placeholder detection,
  inicialização idempotente e geração de tiles FIRMS (mockada — sem rede).
- GEETileView: contrato HTTP dos novos endpoints /api/georisk/gee/<type>/.
"""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from georisk.services import gee_client
from georisk.services.gee_client import GEEProvider, GEEProviderError


def _fake_map_id(viz_key='T21'):
    return {
        'mapid': f'mapid-{viz_key}-123',
        'token': 'fake-token',
        'tile_fetcher': SimpleNamespace(
            url_format=f'https://earthengine.googleapis.com/v1/fake/{viz_key}/tiles'
        ),
    }


def _fake_map_id_full():
    # Formato idêntico ao retorno real de ee.Image.getMapId(...)
    fake = _fake_map_id()
    return {
        'mapid': fake['mapid'],
        'token': fake['token'],
        'tile_fetcher': fake['tile_fetcher'],
    }


class GEEProviderCredentialsTest(TestCase):
    def setUp(self):
        self.provider = GEEProvider()
        self.provider.reset()

    def test_missing_credentials_raises_domain_error(self):
        with self.settings(), patch.dict('os.environ', {}, clear=False):
            import os
            os.environ.pop('GEE_SERVICE_ACCOUNT_FILE', None)
            os.environ.pop('GEE_SERVICE_ACCOUNT_JSON', None)
            with self.assertRaises(GEEProviderError) as ctx:
                self.provider._resolve_credentials()
        self.assertIn('Credenciais GEE ausentes', str(ctx.exception))

    def test_missing_file_raises_domain_error(self):
        with patch.dict('os.environ', {'GEE_SERVICE_ACCOUNT_FILE': 'Z:/nao/existe.json'}):
            with self.assertRaises(GEEProviderError) as ctx:
                self.provider._resolve_credentials()
        self.assertIn('não encontrado', str(ctx.exception))

    def test_placeholder_file_is_rejected(self):
        import json
        import tempfile

        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        )
        json.dump({'private_key': 'COLE_O_CONTEUDO_DO_JSON_AQUI'}, tmp)
        tmp.close()

        with patch.dict('os.environ', {'GEE_SERVICE_ACCOUNT_FILE': tmp.name}):
            with self.assertRaises(GEEProviderError) as ctx:
                self.provider._resolve_credentials()
        self.assertIn('placeholder', str(ctx.exception))


class GEEProviderTilesTest(TestCase):
    def setUp(self):
        self.provider = GEEProvider()
        self.provider.reset()

    def test_initialize_is_idempotent(self):
        with patch('georisk.services.gee_client.ee') as mock_ee_mod, \
             patch.object(GEEProvider, '_resolve_credentials', return_value=object()):
            # primeira chamada inicializa...
            self.assertTrue(self.provider.initialize())
            self.assertTrue(self.provider.is_initialized)
            calls_after_first = mock_ee_mod.Initialize.call_count
            # ...segunda chamada NÃO re-inicializa
            self.assertTrue(self.provider.initialize())
            self.assertEqual(mock_ee_mod.Initialize.call_count, calls_after_first)

    def test_initialize_failure_raises_domain_error(self):
        with patch('georisk.services.gee_client.ee') as mock_ee_mod, \
             patch.object(GEEProvider, '_resolve_credentials', return_value=object()):
            mock_ee_mod.Initialize.side_effect = RuntimeError('quota')
            with self.assertRaises(GEEProviderError) as ctx:
                self.provider.initialize()
        self.assertIn('Falha ao inicializar', str(ctx.exception))
        self.assertFalse(self.provider.is_initialized)

    def test_get_fire_tiles_returns_payload(self):
        fake = _fake_map_id()
        with patch.object(GEEProvider, 'initialize', return_value=True), \
             patch('georisk.services.gee_client.ee') as mock_ee_mod:
            mock_ee_mod.Image.return_value.getMapId.return_value = fake
            payload = self.provider.get_fire_tiles(
                start_date='2026-08-01', end_date='2026-08-25'
            )

        self.assertEqual(payload['mapid'], 'mapid-T21-123')
        self.assertEqual(payload['token'], 'fake-token')
        self.assertIn('earthengine.googleapis.com', payload['tile_fetcher'])
        self.assertEqual(payload['visualization']['min'], 300)
        self.assertEqual(payload['visualization']['max'], 400)
        self.assertEqual(payload['visualization']['palette'][0], 'orange')
        mock_ee_mod.ImageCollection.assert_called_once_with('FIRMS')

    def test_get_fire_tiles_default_window_is_25_days(self):
        today = date.today()
        expected_start = (today - timedelta(days=25)).isoformat()
        expected_end = today.isoformat()

        fake = _fake_map_id()
        with patch.object(GEEProvider, 'initialize', return_value=True), \
             patch('georisk.services.gee_client.ee') as mock_ee_mod:
            collection = mock_ee_mod.ImageCollection.return_value
            collection.filterDate.assert_not_called()  # sanity: mock novo
            mock_ee_mod.Image.return_value.getMapId.return_value = fake
            self.provider.get_fire_tiles()

        collection.filterDate.assert_called_once_with(expected_start, expected_end)

    def test_get_fire_tiles_invalid_range_raises(self):
        with patch.object(GEEProvider, 'initialize', return_value=True):
            with self.assertRaises(GEEProviderError):
                self.provider.get_fire_tiles(
                    start_date='2026-08-25', end_date='2026-08-01'
                )

    def test_get_storm_tiles_payload(self):
        """Tempestade: payload IMERG correto (mesmo contrato da queimada)."""
        fake = _fake_map_id()
        with patch.object(GEEProvider, 'initialize', return_value=True), \
             patch('georisk.services.gee_client.ee') as mock_ee_mod:
            mock_ee_mod.Image.return_value.getMapId.return_value = fake
            payload = self.provider.get_storm_tiles(
                start_date='2026-08-01', end_date='2026-08-25'
            )

        self.assertEqual(payload['mapid'], 'mapid-T21-123')
        self.assertEqual(payload['token'], 'fake-token')
        self.assertIn('earthengine.googleapis.com', payload['tile_fetcher'])
        # Visualização de precipitação (paleta de chuva)
        self.assertEqual(payload['visualization']['min'], 0.0)
        self.assertEqual(payload['visualization']['max'], 12.0)
        mock_ee_mod.ImageCollection.assert_called_once_with('NASA/GPM_L3/IMERG_V07')


@override_settings(ROOT_URLCONF='core.urls')
class GEETileViewTest(TestCase):
    def setUp(self):
        # Provider singleton precisa ser resetado entre testes
        GEEProvider().reset()

    def test_unknown_event_type_returns_400(self):
        resp = self.client.get('/api/georisk/gee/meteorito/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('desconhecido', resp.json()['error'])

    def test_queimada_returns_mapid_payload(self):
        fake = SimpleNamespace(
            mapid='mapid-abc',
            token='tok',
            tile_fetcher='https://earthengine.googleapis.com/v1/fake/tiles',
        )
        with patch.object(
            GEEProvider, 'get_fire_tiles', return_value={
                'mapid': fake.mapid,
                'token': fake.token,
                'tile_fetcher': fake.tile_fetcher,
                'visualization': {'min': 300, 'max': 400},
            }
        ) as mock_fire:
            resp = self.client.get('/api/georisk/gee/queimada/?start=2026-08-01&end=2026-08-25')

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['mapid'], 'mapid-abc')
        self.assertEqual(data['token'], 'tok')
        self.assertIn('tile_fetcher', data)
        mock_fire.assert_called_once_with(
            start_date='2026-08-01', end_date='2026-08-25'
        )

    def test_queimada_provider_error_maps_to_503(self):
        with patch.object(
            GEEProvider,
            'get_fire_tiles',
            side_effect=GEEProviderError('Earth Engine não autenticado'),
        ):
            resp = self.client.get('/api/georisk/gee/queimada/')
        self.assertEqual(resp.status_code, 503)
        self.assertIn('não autenticado', resp.json()['error'])

    def test_tempestade_returns_mapid_payload(self):
        with patch.object(
            GEEProvider, 'get_storm_tiles', return_value={
                'mapid': 'm', 'token': 't', 'tile_fetcher': 'http://tiles',
            }
        ):
            resp = self.client.get('/api/georisk/gee/tempestade/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('tile_fetcher', resp.json())


# ===================================================================== #
# Matriz por tipo de evento (os 5 elementos) + orquestrador Celery
# ===================================================================== #
import contextlib

from django.contrib.auth import get_user_model

from georisk.models import GeoEvent
from georisk.processors import (
    DefaultEventProcessor,
    EventProcessorFactory,
    FloodEventProcessor,
)
from georisk.tasks import process_new_geoevent

User = get_user_model()


class GEEEventTypesMatrixTest(TestCase):
    """
    Matriz dos 5 tipos de evento do domínio × camada GEE:
      - queimada    → implementado (200, FIRMS)
      - tempestade  → implementado (200, GPM IMERG — precipitação)
      - geada       → implementado (200, MODIS LST)
      - inundacao / desmoronamento → sem camada GEE (400)
    """

    def _get(self, slug, patch_target=None, kwargs=None):
        GEEProvider().reset()
        if patch_target:
            ctx = patch.object(GEEProvider, patch_target, **(kwargs or {}))
        else:
            ctx = contextlib.nullcontext()
        with ctx:
            return self.client.get(f'/api/georisk/gee/{slug}/')

    def test_matrix_of_all_five_event_types(self):
        cases = [
            ('queimada', 200, dict(
                patch_target='get_fire_tiles',
                kwargs=dict(return_value={
                    'mapid': 'm', 'token': 't', 'tile_fetcher': 'http://tiles',
                }),
            )),
            ('tempestade', 200, dict(
                patch_target='get_storm_tiles',
                kwargs=dict(return_value={
                    'mapid': 'm', 'token': 't', 'tile_fetcher': 'http://tiles',
                }),
            )),
            ('inundacao', 400, {}),
            ('desmoronamento', 400, {}),
            ('geada', 200, dict(
                patch_target='get_frost_tiles',
                kwargs=dict(return_value={
                    'mapid': 'm', 'token': 't', 'tile_fetcher': 'http://tiles',
                }),
            )),
        ]
        for slug, expected, cfg in cases:
            with self.subTest(event_type=slug):
                resp = self._get(slug, cfg.get('patch_target'), cfg.get('kwargs'))
                self.assertEqual(resp.status_code, expected)


class EventTypeProcessorMatrixTest(TestCase):
    """Cada elemento tem a estratégia de processamento esperada."""

    def setUp(self):
        self.user = User.objects.create_user(username='matrix', password='x12345678')

    def _event(self, t):
        return GeoEvent.objects.create(
            user=self.user, type=t, severity='Media',
            latitude=-23.5, longitude=-46.6, event_date='2026-08-29',
        )

    def test_strategy_per_type(self):
        expected = {
            'Inundacao': FloodEventProcessor,      # IA externa (WTH/OSMNX)
            'Desmoronamento': DefaultEventProcessor,
            'Queimada': DefaultEventProcessor,
            'Geada': DefaultEventProcessor,
            'Tempestade': DefaultEventProcessor,
        }
        for t, cls in expected.items():
            with self.subTest(type=t):
                proc = EventProcessorFactory.get_processor(self._event(t))
                self.assertIsInstance(proc, cls)

    def test_non_flood_types_complete_via_orchestrator(self):
        for t in ['Queimada', 'Desmoronamento', 'Geada', 'Tempestade']:
            with self.subTest(type=t):
                ev = self._event(t)
                process_new_geoevent.run(ev.id)  # execução síncrona (.run)
                ev.refresh_from_db()
                self.assertEqual(ev.status, 'COMPLETED')