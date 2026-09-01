# 🔥 Queimada — FIRMS via Google Earth Engine

> Base de dados, tratamento, plotagem e interação do usuário para o elemento
> **Queimada**. Fonte da verdade: `georisk/services/gee_client.py` (get_fire_tiles),
> `georisk/views_gee.py`, `storm/` não envolvido.

## 1. Base de dados

| | |
|---|---|
| **Coleção GEE** | `FIRMS` (Fire Information for Resource Management System) |
| **Banda** | `T21` — temperatura de brilho do canal 21 (MODIS/VIRS), em **Kelvin** |
| **Satélites** | NASA Terra / Aqua / Suomi NPP (~1 km de resolução, várias passagens/dia) |
| **Janela padrão** | Últimos **25 dias** (`?start=&end=` sobrescreve; intervalo invertido → erro de domínio) |
| **Agregação** | `mosaic()` das detecções da janela |

## 2. Tratamento no backend

```
get_fire_tiles(start, end)                     gee_client.py:146
  → ee.ImageCollection('FIRMS').filterDate(...).select('T21')
  → visualization = {min: 300, max: 400, palette: [orange, red, yellow]}
  → ee.Image(collection.mosaic()).getMapId(visualization)
  ← {mapid, token, tile_fetcher, visualization}
```

- Semântica da paleta: ~300 K = queimada fraca (laranja) → ≥400 K = foco intenso (amarelo)
- Falha de auth/processamento → `GEEProviderError` → HTTP 503 com mensagem

## 3. Plotagem no mapa

1. Frontend (após delay de 1500 ms do VFX): `useGEELayer('queimada')` faz
   `GET /api/georisk/gee/queimada/`
2. `GEETileLayer` monta `L.tileLayer(tile_fetcher)` sobre o basemap escuro (Esri)
3. A imagem é semi-transparente: só pixels quentes (focos) aparecem

## 4. Interação do usuário — clicar num evento de outro usuário

Fluxo completo ao clicar num marcador de Queimada já existente
(`GeoRisk.jsx:501-511`, `source: 'marker'`):

1. **Popup** mostra o autor original: avatar (ou inicial do `@username`),
   tipo, severidade, status, data e descrição
2. `triggerEvent({...evt, _ts})` → `EventContext` marca o evento como ativo
   (o `_ts: Date.now()` garante re-disparo mesmo clicando no mesmo marcador 2x)
3. **flyTo:** `FlyToMapCenter` anima a câmera até `[lat, lon]` do evento, zoom 12
4. **VFX 3D:** `ThreeVFXOverlay` monta o canvas Three.js e dispara o efeito de
   fogo; após o delay (`GEE_TRIGGER_DELAY.Queimada = 1500 ms`) chama
   `onGEETileRequest('Queimada')`
5. **Camada GEE:** `geeReady=true` → `useGEELayer` busca o MapID e os tiles
   PNG do FIRMS cobrem o mapa inteiro (não só o recorte do evento)
6. Botão **"✕ Limpar efeito 3D"** (`handleClearEvent`) desmonta VFX e camada

**Nuances honestas:**
- Não há checagem de posse: qualquer usuário autenticado vê o popup e dispara
  a experiência completa de qualquer evento listado (o filtro `include_mine`
  controla a listagem, não o clique)
- O fetch GEE **não** usa a `event_date` do evento — a janela é sempre
  "últimos 25 dias" do dia atual; um evento antigo mostra o fogo *recente*
  daquela região, não o do dia do report

## 5. Arquivos relacionados

| Arquivo | Papel |
|---|---|
| `georisk/services/gee_client.py:146-180` | `get_fire_tiles` — coleção, paleta, MapID |
| `georisk/views_gee.py:28-39` | Branch `queimada` do `GEETileView` |
| `risk_network_frontend/src/pages/GeoRisk.jsx:501-511` | Handler de clique do marcador |
| `risk_network_frontend/src/components/Map/useGEELayer.js` | Fetch do MapID + cache por `requestSeq` |
| `risk_network_frontend/src/components/Map/GEETileLayer.jsx` | `L.tileLayer(tile_fetcher)` |
| `risk_network_frontend/src/components/Map/vfx/fire.js` | VFX 3D de fogo |
| `risk_network_frontend/src/components/Map/ThreeVFXOverlay.jsx:41-47` | Delay 1500 ms |