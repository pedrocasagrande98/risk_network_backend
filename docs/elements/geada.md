# ❄️ Geada — MODIS LST (proxy físico de geadas)

> Base de dados, tratamento, plotagem e interação do usuário para o elemento
> **Geada**. Fonte da verdade: `georisk/services/gee_client.py` (get_frost_tiles),
> `georisk/views_gee.py`.

## 1. Base de dados

| | |
|---|---|
| **Coleção GEE** | `MODIS/061/MOD11A2` (Terra, collection 061) |
| **Banda** | `LST_Day_1km` — Land Surface Temperature diurna, ~1 km |
| **Escala** | valores crus × **0.02 = Kelvin** |
| **Por que LST?** | Não existe sensor direto de "gelo por pixel"; a LST diurna perto de/abaixo de 273 K indica condição de geada |
| **Janela padrão** | **16 dias** (2 ciclos de 8 dias do produto) terminando hoje (`?start=&end=` sobrescreve) |
| **Agregação** | `mean()` das capturas |

## 2. Tratamento no backend

```
get_frost_tiles(start, end)                    gee_client.py:182
  → ee.ImageCollection('MODIS/061/MOD11A2').filterDate(...).select('LST_Day_1km')
  → .mean().multiply(0.02)   # raw → Kelvin
  → visualization = {min: 240, max: 310, palette: [ffffff, 93c5fd, 3b82f6, 1e3a8a, 1f2937]}
  → ee.Image(lst).getMapId(visualization)
  ← {mapid, token, tile_fetcher, visualization}
```

- Semântica: **claro (branco/azul-claro) = congelante** (geada provável),
  escuro = ameno; cinza-escuro fecha a rampa
- Mesmo "termômetro" do FIRMS (sensor MODIS), mas como média climática de
  8 dias em vez de detecções pontuais

## 3. Plotagem no mapa

1. Frontend (após o **maior** delay — 2000 ms): `useGEELayer('geada')` →
   `GET /api/georisk/gee/geada/`
2. `GEETileLayer` → `L.tileLayer(tile_fetcher)` sobre o basemap
3. Cientificamente idêntico ao pipeline da Queimada (tiles GEE), mudando
   coleção, escala e paleta

## 4. Interação do usuário — clicar num evento de outro usuário

Fluxo ao clicar num marcador de Geada já existente (`GeoRisk.jsx:501-511`):

1. **Popup** do autor original (avatar/inicial + `@username`, tipo, severidade,
   status, data, descrição)
2. `triggerEvent` → evento ativo no `EventContext` (com `_ts` de re-disparo)
3. **flyTo** até a coordenada (zoom 12)
4. **VFX 3D:** efeito de congelamento da terra (`vfx/earthFrost.js` — solo
   "cristalizando"); após `GEE_TRIGGER_DELAY.Geada = 2000 ms`, habilita o fetch GEE
5. **Camada GEE:** tiles de LST cobrem a região visível — o usuário vê a
   temperatura de superfície *atual* sobre o basemap
6. "✕ Limpar efeito 3D" desmonta tudo

**Nuances honestas:** mesmas da Queimada — sem checagem de posse (qualquer
evento listado dispara a experiência) e o fetch GEE ignora a `event_date`
(janela sempre relativa a hoje: 16 dias).

## 5. Arquivos relacionados

| Arquivo | Papel |
|---|---|
| `georisk/services/gee_client.py:182-220` | `get_frost_tiles` — MOD11A2, escala 0.02, paleta frio |
| `georisk/views_gee.py:41-52` | Branch `geada` do `GEETileView` |
| `risk_network_frontend/src/pages/GeoRisk.jsx:501-511` | Handler de clique do marcador |
| `risk_network_frontend/src/components/Map/useGEELayer.js` | Fetch/cache do MapID |
| `risk_network_frontend/src/components/Map/vfx/earthFrost.js` | VFX 3D de congelamento |
| `risk_network_frontend/src/components/Map/ThreeVFXOverlay.jsx:41-47` | Delay 2000 ms |