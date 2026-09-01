# 🌊 Inundação — WTH Motor + OSMNX → GeoJSON calculado

> O fluxo mais completo do sistema. **Não usa raster GEE** (endpoint GEE
> responde 400 por design): a camada é **calculada** por dois microsserviços
> e persistida no evento como GeoJSON. Fonte da verdade: `georisk/processors.py`,
> `georisk/models.py`, `GeoRisk.jsx`.

## 1. Bases de dados

| | |
|---|---|
| **Hidrologia** | Serviço **WTH Motor** (`:8001`) — `POST /api/v1/flood/calculate` |
| **Malha viária** | Serviço **OSMNX** (`:8002`) — `POST /api/v1/streets/extract` (OpenStreetMap) |
| **Entrada** | lat/lon do evento + **cota** derivada da severidade |
| **Saída** | 2 GeoJSONs salvos no `GeoEvent` (campos `flood_geojson`, `streets_geojson`) |

Mapeamento severidade → cota (`processors.py:25-30`):

| Severidade | Cota |
|---|---|
| Baixa | 0.5 m |
| Media | 1.0 m |
| Critica | 2.0 m |

## 2. Tratamento no backend (pipeline assíncrono Celery)

`POST /api/georisk/` (tipo `Inundacao`) enfileira task → `EventProcessorFactory`
retorna `FloodEventProcessor` (`processors.py:15-99`):

```
1. POST WTH /calculate {lat, lon, cota}        → task_id
2. Polling WTH /status/<task_id> a cada 2s
   ├── "Concluído" com error → SEM mancha: status=COMPLETED, return "No flood risk found"
   ├── "Concluído"          → flood_geojson salvo no evento (provisório)
   └── "Falha"              → exceção → ERROR
3. POST OSMNX /extract {flood_geojson}         → task_id
4. Polling OSMNX /status/<task_id> a cada 2s
   ├── timeout 300 s          → status=COMPLETED_PARTIAL (só a mancha)
   ├── "Concluído"            → streets_geojson salvo, status=COMPLETED
   └── "Falha"                → exceção → ERROR
```

Demais tipos passam pelo `DefaultEventProcessor` (só marca `COMPLETED`).

**Área segura:** resposta sem `flood_geojson` — a UI mostra "Área segura
(sem risco de inundação detectado no local)".

## 3. Plotagem no mapa

Os GeoJSONs são renderizados **fora** do `MarkerClusterGroup` (limitação da
lib com polígonos dentro de cluster — `GeoRisk.jsx:534-559`):

- `flood_geojson` → polígonos de alagamento **azuis** (`#3b82f6`, fillOpacity 0.4)
- `streets_geojson` → trechos de rua afetados em **linhas vermelhas** (`#ef4444`, weight 3)
- Pin do evento + popup ficam no cluster; os polígonos desenham por cima do basemap

**Status no ar:** `PENDING` pulsa laranja (divIcon com `animation: pulse`)
até o polling do frontend (`GET /api/georisk/<id>/` a cada 2s) ver
`COMPLETED` / `COMPLETED_PARTIAL` / `ERROR`.

## 4. Interação do usuário — clicar num evento de outro usuário

Fluxo ao clicar num marcador de Inundação já processado (`GeoRisk.jsx:501-511`):

1. **Popup** do autor original (avatar/inicial, `@username`, tipo, severidade,
   status, data, descrição)
2. `triggerEvent({...evt, _ts, source: 'marker'})` → evento ativo
3. **flyTo** até a coordenada (zoom 12)
4. **VFX 3D:** efeito de água (`GEE_TRIGGER_DELAY.Inundacao = 800 ms`);
   ao fim, `onGEETileRequest('Inundacao')` é chamado — mas como
   `TYPE_TO_GEE` **não** tem `Inundacao`, `geeReady` nunca vira true e
   **nenhum fetch GEE é feito** (por design — a camada já é GeoJSON próprio)
5. **Camada:** os GeoJSONs de mancha e vias **já estão no evento** — são
   renderizados de forma permanente enquanto o evento estiver no filtro
   ativo, **independente de clique** (clique dá flyTo + popup + VFX; os
   polígonos já estavam desenhados)
6. Evento de outro usuário **não é reprocessado** — o clique só visualiza;
   o processamento pesado (WTH + OSMNX) aconteceu uma única vez no submit
   do autor original

**Nuances honestas:**
- Eventos `COMPLETED_PARTIAL` de outro usuário mostram só a mancha (vias
  expiraram no processamento original)
- Sem checagem de posse; popup de evento alheio é idêntico ao próprio

## 5. Arquivos relacionados

| Arquivo | Papel |
|---|---|
| `georisk/processors.py:15-99` | `FloodEventProcessor` — WTH → OSMNX → GeoJSONs |
| `georisk/processors.py:109-115` | `EventProcessorFactory` |
| `georisk/tasks.py` | Task Celery que roda o processor |
| `georisk/models.py` | `GeoEvent.flood_geojson` / `.streets_geojson` |
| `georisk/urls.py:6-7` | Rotas de list/create e retrieve |
| `risk_network_frontend/src/pages/GeoRisk.jsx:151-189` | `startPolling` — status a cada 2s |
| `risk_network_frontend/src/pages/GeoRisk.jsx:534-559` | Renderização dos GeoJSONs fora do cluster |
| Repos externos | `risk-network-wth-motor/`, `risk-network-osmnx-streets/` (irmãos deste repo) |