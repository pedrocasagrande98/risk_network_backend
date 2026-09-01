# Elements — Bases de dados, tratamento e plotagem por elemento

> Documentação detalhada de cada elemento do GeoRisk: **de onde vêm os dados**,
> **como são tratados** no backend e **como são plotados** no mapa.
> Fonte da verdade: o código (referências de arquivo:linha incluídas em cada doc).

## Índice

| Doc | Elemento | Base de dados | Endpoint principal | Formato no mapa |
|---|---|---|---|---|
| [queimada.md](queimada.md) | 🔥 Queimada | FIRMS (NASA) via Google Earth Engine — banda `T21` | `GET /api/georisk/gee/queimada/` | Raster (tiles PNG) |
| [geada.md](geada.md) | ❄️ Geada | MODIS/Terra MOD11A2 — LST como proxy físico | `GET /api/georisk/gee/geada/` | Raster (tiles PNG) |
| [tempestade.md](tempestade.md) | ⛈️ Tempestade | GPM IMERG V07 (chuva, via GEE) **+** GFS/NOAA (vento, via storm :8005) | `GET /api/georisk/gee/tempestade/` + `POST /api/georisk/storm/plot/` | Raster de chuva **+** malha vetorial animada |
| [inundacao.md](inundacao.md) | 🌊 Inundação | Serviços WTH (:8001) + OSMNX (:8002) → GeoJSON calculado | `POST /api/georisk/` (Celery) | Polígonos + linhas GeoJSON |
| [desmoronamento.md](desmoronamento.md) | 🪨 Desmoronamento | — (somente registro do evento) | `POST /api/georisk/` | Pin + popup |

## Matriz técnica comparada

| | Queimada | Geada | Tempestade (chuva) | Tempestade (vento) | Inundação | Desmoronamento |
|---|---|---|---|---|---|---|
| **Coleção/Fonte** | `FIRMS` | `MODIS/061/MOD11A2` | `NASA/GPM_L3/IMERG_V07` | GFS 0.25° (COGs locais) | WTH + OSMNX | — |
| **Banda/Grandeza** | `T21` (K brilho) | `LST_Day_1km` (K) | `precipitation` (mm/h) | U/V a 10 m (m/s) | cota de alagamento (m) | — |
| **Fator de escala** | 1 | ×0.02 | ×0.1 | 1 | — | — |
| **Resolução** | ~1 km | ~1 km (8 dias) | 0.1° (30 min) | 0.25° (mensal/COG) | — | — |
| **Janela padrão** | 25 dias | 16 dias | 3 dias | mês da data | sob demanda | — |
| **Agregação** | `mosaic()` | `mean()` | `mean()` | recorte janela 500 km | — | — |
| **Visualização** | 300–400 K | 240–310 K | 0–12 mm/h | partículas | polígonos | pin |
| **Delay VFX** | 1500 ms | 2000 ms | 400 ms | 400 ms | 800 ms | 800 ms |
| **Clique em evento alheio busca dados novos?** | Sim — GEE (janela de hoje) | Sim — GEE (janela de hoje) | Sim — GEE (janela de hoje) | Sim — usa a **data do evento** | Não — GeoJSON já salvo | Não — só VFX |

## Interação do usuário — clicar num evento feito por outro usuário

Pipeline compartilhado por todos os 5 elementos (`GeoRisk.jsx:501-511`,
`EventContext.jsx`, `FlyToMapCenter.jsx`, `ThreeVFXOverlay.jsx`):

```
click no Marker (evento de qualquer usuário)
  → triggerEvent({id, type, latitude, longitude, severity, event_date,
                  source: 'marker', _ts: Date.now()})     ← EventContext
  → Popup do autor original (avatar/@username, tipo, severidade, status, data)
  → FlyToMapCenter: map.flyTo([lat, lon], 12)             ← câmera anima
  → ThreeVFXOverlay: canvas Three.js monta e dispara o VFX do elemento
      → após GEE_TRIGGER_DELAY[type]: onGEETileRequest(type)
          ├── tipo tem camada GEE (queimada/geada/tempestade)
          │     → useGEELayer fetch GET /api/georisk/gee/<tipo>/
          │     → tiles PNG do Earth Engine sobre o mapa
          └── tipo sem camada (inundacao/desmoronamento)
                → corretamente ignorado (nenhum request)
  → (só Tempestade) useEffect do activeEvent também dispara
      POST /api/georisk/storm/plot/ com a event_date do evento
  → "✕ Limpar efeito 3D" desmonta VFX, camada GEE e malha de vento
```

**Garantias do mecanismo:**
- `_ts: Date.now()` força re-disparo mesmo clicando 2x no mesmo marcador
- Dedupe do vento por chave `lat,lon,event_date,_ts` (sem request duplicado
  em voo; troca de evento cancela o fetch anterior)
- **Sem checagem de posse:** a experiência de clique é idêntica para evento
  próprio ou de outro usuário — o filtro `include_mine` controla a *listagem*,
  não o clique
- **Frescor dos dados varia por elemento:** camadas GEE mostram sempre a
  janela relativa a *hoje* (não a data do report); o vento usa a *data do
  evento* (COG mensal, fallback 2025-10); Inundação/Desmoronamento não
  buscam nada novo (GeoJSON persistido / só VFX)

Detalhes por elemento na seção 4 de cada doc abaixo.

## Contratos de status do endpoint GEE (`/api/georisk/gee/<tipo>/`)

| Situação | HTTP |
|---|---|
| Tipo com camada implementada (queimada, geada, tempestade) | **200** `{mapid, token, tile_fetcher, visualization}` |
| Tipo conhecido mas sem camada (inundacao, desmoronamento) | **400** |
| Falha de credencial/processamento GEE | **503** `{'error': ...}` |
| Tipo desconhecido | **400** |
| Intervalo `start > end` | exceção de domínio (`GEEProviderError`) → 503 |

## Infra comum às camadas GEE (Queimada, Geada, chuva da Tempestade)

- **Autenticação:** Service Account do Google via env — `GEE_SERVICE_ACCOUNT_FILE`
  (caminho do JSON) ou `GEE_SERVICE_ACCOUNT_JSON` (conteúdo inline);
  `GEE_PROJECT_ID` seleciona o projeto. Placeholder é detectado e rejeitado.
  **Nada de credencial versionada no repo.**
- **Provider:** `GEEProvider` é Singleton thread-safe (`georisk/services/gee_client.py`);
  `ee.Initialize` idempotente por processo.
- **Payload:** `{mapid, token, tile_fetcher, visualization}` — o `tile_fetcher`
  é a URL de tiles do Earth Engine (`https://earthengine.googleapis.com/v1/.../{z}/{x}/{y}`).
- **Cache de MapID:** o GEE expira mapids; cada chamada gera um novo. O hook do
  frontend descarta respostas obsoletas (`requestSeq`) quando o evento muda.
- **Frontend:** só dispara fetch para quem tem camada definida (`TYPE_TO_GEE`
  em `GeoRisk.jsx` do repo `risk-network-frontend`).

## Pipeline comum (GEE → mapa)

```
Frontend (após delay do VFX)
  → GET /api/georisk/gee/<tipo>/?start=&end=
    → GEETileView (AllowAny, stateless)          georisk/views_gee.py
      → GEEProvider.<get_X_tiles>(start, end)    georisk/services/gee_client.py
        → ee.Initialize (Service Account, singleton)
        → ee.ImageCollection(...).filterDate(...).select(banda).<agg>()
        → ee.Image(img).getMapId({min, max, palette})
      ← {mapid, token, tile_fetcher, visualization}
  ← 200 JSON
GEETileLayer → L.tileLayer(tile_fetcher) → tiles PNG do earthengine
```

## Arquivos transversais

| Arquivo | Papel |
|---|---|
| `georisk/services/gee_client.py` | Provider GEE: auth, singleton, 3 camadas (fire/frost/storm) |
| `georisk/views_gee.py` | `GEETileView` — rota fina de apresentação |
| `georisk/urls.py` | Rotas `/api/georisk/…` (eventos, storm/plot, gee/<tipo>) |
| `georisk/processors.py` | `FloodEventProcessor` (Inundação) + factory |
| `georisk/tasks.py` | Tarefas Celery que invocam os processors |
| `georisk/models.py` | Modelo `GeoEvent` (incl. `flood_geojson`, `streets_geojson`) |
| `storm/main.py` | FastAPI do serviço de vento (:8005) |
| `storm/wind_engine.py` | Recorte dos COGs GFS → formato leaflet-velocity |
| `storm/Dockerfile` | Imagem do storm (python:3.11-slim + libexpat1 + smoke test) |
| `storm/data/*.tif` | 12 COGs mensais de vento (2025-01 … 2025-12) |
| `docker-compose.yml` | 5 serviços com `restart: unless-stopped` |