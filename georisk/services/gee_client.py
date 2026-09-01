"""
GEE Client — Integração com o Google Earth Engine (SRP & OCP).

Responsabilidade Única (SRP): toda a lógica de autenticação e obtenção de
MapIDs do Earth Engine vive aqui, longe das views.
Aberto/Fechado (OCP): novos provedores/camadas (ex: `get_flood_tiles`) são
adicionados como novos métodos sem modificar os existentes.

Credenciais (Segurança):
- A Service Account NUNCA deve ficar versionada no repositório.
- A leitura ocorre via variável de ambiente `GEE_SERVICE_ACCOUNT_FILE`
  (caminho do arquivo json) ou, alternativamente, `GEE_SERVICE_ACCOUNT_JSON`
  (conteúdo json inline, p/ nuvem). Sem credencial, o provider fica em estado
  "não inicializado" e responde com erro controlado.
"""
import json
import logging
import os
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

GEE_SCOPE = 'https://www.googleapis.com/auth/earthengine'

# Import no nível do módulo p/ testabilidade (patch em gee_client.ee).
# Mantemos fallback controlado: sem o pacote, o provider reporta erro de domínio.
try:
    import ee
except ImportError:  # pragma: no cover - ambiente sem earthengine-api
    ee = None


class GEEProviderError(Exception):
    """Erro de domínio do GEEProvider (auth, inicialização, processamento)."""


class GEEProvider:
    """
    Provedor de camadas do Google Earth Engine.

    Implementado como Singleton thread-safe: `ee.Initialize` só pode ocorrer
    uma vez por processo e as credenciais são resolvidas sob demanda.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    # ------------------------------------------------------------------ #
    # Autenticação
    # ------------------------------------------------------------------ #
    def _resolve_credentials(self):
        """
        Resolve as credenciais a partir do ambiente (sem hardcode).
        Ordem: GEE_SERVICE_ACCOUNT_JSON (conteúdo) -> GEE_SERVICE_ACCOUNT_FILE (path).
        """
        from google.oauth2 import service_account

        inline_json = os.environ.get('GEE_SERVICE_ACCOUNT_JSON')
        if inline_json:
            try:
                info = json.loads(inline_json)
                return service_account.Credentials.from_service_account_info(
                    info, scopes=[GEE_SCOPE]
                )
            except (json.JSONDecodeError, ValueError) as e:
                raise GEEProviderError(f"GEE_SERVICE_ACCOUNT_JSON inválido: {e}")

        file_path = os.environ.get('GEE_SERVICE_ACCOUNT_FILE')
        if file_path:
            if not os.path.exists(file_path):
                raise GEEProviderError(
                    f"service_account.json não encontrado em: {file_path}"
                )
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                raise GEEProviderError(f"Falha ao ler {file_path}: {e}")

            if data.get('private_key') in (None, '', 'COLE_O_CONTEUDO_DO_JSON_AQUI'):
                raise GEEProviderError(
                    "service_account.json é um placeholder (privkey vazia)."
                )

            return service_account.Credentials.from_service_account_file(
                file_path, scopes=[GEE_SCOPE]
            )

        raise GEEProviderError(
            "Credenciais GEE ausentes: defina GEE_SERVICE_ACCOUNT_FILE "
            "(caminho) ou GEE_SERVICE_ACCOUNT_JSON (conteúdo)."
        )

    def initialize(self, project_id=None):
        """Autentica e inicializa o Earth Engine (idempotente)."""
        if self._initialized:
            return True
        if ee is None:
            raise GEEProviderError("Pacote 'earthengine-api' não instalado no backend.")

        project = project_id or os.environ.get(
            'GEE_PROJECT_ID', getattr(settings, 'GEE_PROJECT_ID', None)
        )
        credentials = self._resolve_credentials()
        try:
            ee.Initialize(credentials, project=project)
            self._initialized = True
            logger.info("Earth Engine inicializado com sucesso (project=%s).", project)
            return True
        except Exception as e:
            self._initialized = False
            raise GEEProviderError(f"Falha ao inicializar o Earth Engine: {e}")

    @property
    def is_initialized(self):
        return self._initialized

    def reset(self):
        """Usado em testes: força nova autenticação na próxima chamada."""
        with self._lock:
            self._initialized = False

    # ------------------------------------------------------------------ #
    # Camadas (cada tipo de evento = um método novo — OCP)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_tile_payload(map_id_dict, visualization=None):
        payload = {
            'mapid': map_id_dict['mapid'],
            'token': map_id_dict['token'],
            'tile_fetcher': map_id_dict['tile_fetcher'].url_format,
        }
        if visualization is not None:
            payload['visualization'] = visualization
        return payload

    def get_fire_tiles(self, start_date=None, end_date=None):
        """
        Camada de focos de calor (Queimada) — coleção FIRMS/T21.
        Retorna dict com mapid/token/tile_fetcher p/ uso em L.tileLayer().
        """
        import datetime

        self.initialize()

        end = datetime.date.fromisoformat(end_date) if end_date else datetime.date.today()
        start = (
            datetime.date.fromisoformat(start_date)
            if start_date
            else end - datetime.timedelta(days=25)
        )
        if start > end:
            raise GEEProviderError("start_date não pode ser maior que end_date.")

        try:
            firms = (
                ee.ImageCollection('FIRMS')
                .filterDate(start.isoformat(), end.isoformat())
                .select('T21')
            )
            visualization = {
                'min': 300,
                'max': 400,
                'palette': ['orange', 'red', 'yellow'],
            }
            map_id_dict = ee.Image(firms.mosaic()).getMapId(visualization)
            return self._build_tile_payload(map_id_dict, visualization)
        except GEEProviderError:
            raise
        except Exception as e:
            raise GEEProviderError(f"Erro ao processar imagem no GEE: {e}")

    def get_frost_tiles(self, start_date=None, end_date=None):
        """
        Camada de Geada — temperatura de superfície MODIS/Terra 8 dias
        (MOD11A2, banda LST_Day_1km, escala 0.02 → Kelvin).
        Paleta do frio: branco/azul-claro = congelante (~≤273 K),
        escuro = ameno. Janela padrão de 16 dias (2 ciclos de 8 dias).
        """
        import datetime

        self.initialize()

        end = datetime.date.fromisoformat(end_date) if end_date else datetime.date.today()
        start = (
            datetime.date.fromisoformat(start_date)
            if start_date
            else end - datetime.timedelta(days=16)
        )
        if start > end:
            raise GEEProviderError("start_date não pode ser maior que end_date.")

        try:
            lst = (
                ee.ImageCollection('MODIS/061/MOD11A2')
                .filterDate(start.isoformat(), end.isoformat())
                .select('LST_Day_1km')
                .mean()
                .multiply(0.02)  # raw → Kelvin
            )
            visualization = {
                'min': 240,
                'max': 310,
                'palette': ['ffffff', '93c5fd', '3b82f6', '1e3a8a', '1f2937'],
            }
            map_id_dict = ee.Image(lst).getMapId(visualization)
            return self._build_tile_payload(map_id_dict, visualization)
        except GEEProviderError:
            raise
        except Exception as e:
            raise GEEProviderError(f"Erro ao processar imagem no GEE: {e}")

    def get_storm_tiles(self, start_date=None, end_date=None):
        """
        Camada de Tempestade — precipitação GPM IMERG V07 (Early Run, 30 min).
        Banda `precipitation`: mm/h × 0.1 → mm/h reais. Agregada em média
        simples na janela (padrão 3 dias). Paleta de chuva: escuro=seco →
        ciano → azul → roxo → vermelho (chuva extrema).
        """
        import datetime

        self.initialize()

        end = datetime.date.fromisoformat(end_date) if end_date else datetime.date.today()
        start = (
            datetime.date.fromisoformat(start_date)
            if start_date
            else end - datetime.timedelta(days=3)
        )
        if start > end:
            raise GEEProviderError("start_date não pode ser maior que end_date.")

        try:
            precip = (
                ee.ImageCollection('NASA/GPM_L3/IMERG_V07')
                .filterDate(start.isoformat(), end.isoformat())
                .select('precipitation')
                .mean()
                .multiply(0.1)  # raw × 0.1 → mm/h
            )
            visualization = {
                'min': 0.0,
                'max': 12.0,
                'palette': ['1e293b', '22d3ee', '3b82f6', 'a855f7', 'ef4444'],
            }
            map_id_dict = ee.Image(precip).getMapId(visualization)
            return self._build_tile_payload(map_id_dict, visualization)
        except GEEProviderError:
            raise
        except Exception as e:
            raise GEEProviderError(f"Erro ao processar imagem no GEE: {e}")


def get_gee_provider():
    """Ponto de injeção do provider (facilita mock nos testes)."""
    return GEEProvider()