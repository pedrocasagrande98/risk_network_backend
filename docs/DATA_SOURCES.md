# DATA_SOURCES.md — Fontes de Dados por Tipo de Evento

> Referência técnica das camadas de dados de cada elemento do GeoRisk:
> de onde vêm os dados, como são processados no backend e como são plotados
> no frontend. Complementa `gee_impacts.md` (testes) e `GEE_INTEGRATION_LOG.md`.

---

## Visão geral — matriz dos 5 elementos

| Elemento | Fonte de dados | Endpoint | Formato no mapa | Delay pós-VFX |
|---|---|---|---|---|
| **Queimada** | FIRMS (satélite NASA) via Google Earth Engine | `GET /api/georisk/gee/queimada/` | Raster (tiles PNG) | 1500 ms |
| **Geada** | MODIS/Terra MOD11A2 — temperatura de superfície | `GET /api/georisk/gee/geada/` | Raster (tiles PNG) | 2000 ms |
| **Tempestade** | GPM IMERG V07 (precipitação) via GEE + GFS (NOAA) via `risk-network-storm` (:8005) | `GET /api/georisk/gee/tempestade/` + `POST /api/georisk/storm/plot/` | Raster de chuva (tiles PNG) **+** malha vetorial animada (leaflet-velocity) | 400 ms |
| **Inundação** | Serviços WTH (:8001) + OSMNX (:8002) → GeoJSON | `POST /api/georisk/` (processor Celery) | Polígonos/linhas GeoJSON | 800 ms |
| **Desmoronamento** | — (somente registro do evento + VFX 3D) | `POST /api/georisk/` | Pin + popup | 800 ms |

Contratos de status do endpoint GEE: tipo implementado → **200**
(`{mapid, token, tile_fetcher, visualization}`); tempestade → **501**
(reservada); inundação/desmoronamento → **400**; falha de credencial GEE →
**503**; tipo desconhecido → **400**. O frontend só dispara fetch para quem
tem camada definida (`TYPE_TO_GEE` em `GeoRisk.jsx`).

---

## 1. Queimada — focos de calor do FIRMS

**Fonte:** coleção `FIRMS` (Fire Information for Resource Management System)
no Google Earth Engine, banda `T21` (temperatura de brilho do canal 21 do
instrumento MODIS/VIRS, em Kelvin). O FIRMS agrega detecções de queimada dos
satélites NASA (Terra/Aqua/Suomi NPP, ~1 km de resolução, várias passagens/dia).

**Janela temporal:** últimos 25 dias por padrão (`?start=&end=` sobrescreve).
Intervalo invertido é rejeitado com erro de domínio (`GEEProviderError`).

**Visualização:** `min 300 / max 400` (Temperatura de Brilho, Kelvin) com
paleta `orange → red → yellow` — pixels ~300 K são queimada fraca (laranja),
≥400 K são focos intensos (amarelo).

**Como plotamos:**
1. `GEEProvider.get_fire_tiles()` monta a `ee.ImageCollection('FIRMS')` →
   `filterDate` → `select('T21')` → `mosaic()` e pede o `getMapId(visualization)`.
2. O backend devolve `{mapid, token, tile_fetcher}` — o `tile_fetcher` é a URL
   de tiles do Earth Engine (`https://earthengine.googleapis.com/v1/.../{z}/{x}/{y}`).
3. No frontend, `useGEELayer` busca o payload e o `GEETileLayer` monta um
   `L.tileLayer(tile_fetcher)` por cima do basemap. A imagem é semi-transparente:
   só os pixels quentes (focos) aparecem; o resto é transparente.

---

## Geada — MODIS LST (temperatura de superfície)

Em vez de uma camada de "gelo por pixel" (não existe sensor direto de geada),
usamos **temperatura de superfície terrestre (LST)** do MODIS como proxy físico:
onde a LST diurna está perto de/abaixo de 273 K, há condição de geadas.

**Fonte:** `MODIS/061/MOD11A2` — produto de 8 dias, banda `LST_Day_1km`,
~1 km de resolução. Valores crus × 0.02 = Kelvin.

**Janela temporal:** 16 dias (2 ciclos de 8 dias) terminando hoje, `mean()`
das capturas. `?start=&end=` sobrescreve (mesmo contrato da Queimada).

**Visualização:** `min 240 / max 310 K` com paleta
`branco → azul-claro (#93c5fd) → azul (#3b82f6) → azul-escuro (#1e3a8a) → cinza-escuro`.
Ou seja: **claro = congelante** (geada provável), escuro = ameno.

**Como plotamos:** idêntico à Queimada — `getMapId()` no backend, tiles PNG
do earthengine.googleausercontent no Leaflet. Cientificamente é o mesmo
"termômetro" do FIRMS (MOD11A2 usa o mesmo sensor MODIS), só que a média
climática de 8 dias em vez de detecções pontuais.

---

## Tempestade — GPM IMERG (satélite) + GFS (vento) — as duas camadas

Tempestade agora tem **duas fontes complementares**, ambas reais:

### A) Camada GEE — precipitação GPM IMERG

**Fonte:** `NASA/GPM_L3/IMERG_V07` — Integrated Multi-satellitE Retrievals
for GPM (Early Run, ~30 min de latência, 0.1° global). Banda `precipitation`
(mm/h × 0.1 = mm/h reais — só um fator de escala).

**Janela temporal:** 3 dias por padrão (IMerg é granular de 30 min; 3 dias dá
uma "climatologia de chuva recente" legível), `mean()` das passagens.
`?start=&end=` sobrescreve (mesmo contrato das demais camadas).

**Visualização:** `min 0 / max 12 mm/h`, paleta
`cinza-escuro (seco) → ciano → azul → roxo → vermelho (chuva extrema)`.

**Como plotamos:** igual à Queimada/Geada — `getMapId()` no backend,
tiles do earthengine no Leaflet via `GEETileLayer`. Chuvas fracas pintam de
ciano, tempestades severas de roxo/vermelho.

### B) Vento — GFS (NOAA) sem GEE

1. Frontend: `POST /api/georisk/storm/plot/` com `{latitude, longitude, date}`.
2. `StormProxyView` (Django) repassa para `http://localhost:8005/api/wind/plot`
   (FastAPI do `risk-network-storm`).
3. O `WindEngine` baixa/recorta dados **GFS** (Global Forecast System, NOAA —
   0.25°, ventos U e V a 10 m) e devolve a malha no formato do
   **leaflet-velocity** (`[{header:{la1,la2,lo1,lo2,nx,ny,parameterUnit...},
   data:[u,v,u,v...]}]`).
4. O frontend injeta essa malha no `WindLayer` (`L.velocityLayer`) — partículas
   animadas cuja direção/velocidade seguem o vento real do dia no recorte
   9°×9° ao redor da coordenada. Estilo por severidade (`levelStyles`):
   Baixa 1.5px, Media 2px, Critica 3px (linhas brancas/cinza).

O 3D fica por conta do `bolt` (raio ramificado com flicker, roxo) + shake de
câmera; chuva de satélite + vento GFS dão o "mapa vivo" sobre o basemap.

---

## Inundação — GeoJSON calculado (WTH + OSMNX)

A Inundação é o fluxo mais completo e **não usa raster GEE** (o endpoint GEE
responde 400 por design — a camada dela é calculada):

1. `POST /api/georisk/` com tipo `Inundacao` enfileira tarefa no Celery.
2. O processor busca hidrologia do serviço WTH (:8001) e a malha viária do
   **OSMNX** (:8002) — ruas dentro do raio do ponto.
3. O resultado vira dois GeoJSONs salvos no evento:
   - `flood_geojson` — polígonos de alagamento (desenhados em azul #3b82f6,
     fillOpacity 0.4);
   - `streets_geojson` — trechos de rua afetados (linhas vermelhas, weight 3).
4. No mapa, esses GeoJSON são renderizados **fora** do cluster de marcadores
   (`<GeoJSON>` do react-leaflet), com popup do evento + pin.
5. Status processado por polling `GET /api/georisk/<id>/` a cada 2s até
   `COMPLETED` / `COMPLETED_PARTIAL` / `ERROR`.

Estruturas de "área segura" (sem risco) respondem sem `flood_geojson` e a UI
mostra "Área segura".

---

## Desmoronamento — somente evento

Sem dados geoespaciais de terceiros hoje: registra o evento (pin no mapa
com ícone marrom + VFX de rachadura/pedras/poeira). O endpoint GEE responde
**400** proposital (sem camada definida) e o frontend não faz fetch.

**Extensão futura (OCP):** basta um `get_landslide_tiles()` no GEEProvider
(p.ex. suscetibilidade de encosta) para ativar — nada mais precisa mudar:
uma nova entrada em `TYPE_TO_GEE` no frontend e uma nova rota no backend.

---

## Pipeline comum a Queimada e Geada (GEE)

```
Frontend (após delay do VFX)
  → GET /api/georisk/gee/<tipo>/?start=&end=
    → GEETileView (AllowAny, stateless)
      → GEEProvider.<get_X_tiles>(start, end)
        → ee.Initialize (Service Account via env; singleton thread-safe)
        → ee.ImageCollection(...).filterDate(...).select(banda).<agg>()
        → ee.Image(img).getMapId({min, max, palette})
      ← {mapid, token, tile_fetcher, visualization}
  ← 200 JSON
GEETileLayer → L.tileLayer(tile_fetcher) → tiles PNG do earthengine.googleapis.com
```

- **Credencial:** `GEE_SERVICE_ACCOUNT_FILE` (path do JSON) ou
  `GEE_SERVICE_ACCOUNT_JSON` (conteúdo); `GEE_PROJECT_ID` seleciona o projeto.
  Placeholder é detectado e rejeitado. Nada versionado no repo.
- **Cache de MapID:** o GEE expira mapids; cada chamada gera um novo. O hook
  descarta respostas obsoletas (`requestSeq`) quando o evento muda.
- **Falha de auth/processamento** → 503 com mensagem no badge GEE do mapa.

---

## Cores e ordem visual

- VFX 3D primeiro (flash + partículas), depois a camada de dados "chega" —
  coreografia fiel ao lab: Tempestade 400ms · Desmoronamento/Inundação 800ms ·
  Queimada 1500ms · Geada 2000ms.
- Badge GEE canto inferior esquerdo: carregando / erro (`⚠️ GEE: ...`).
- Marcadores: Inundação azul, Queimada vermelho, Desmoronamento marrom,
  Geada azul-claro, Tempestade roxo; PENDING pulsa laranja.