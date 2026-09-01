# ⛈️ Tempestade — GPM IMERG (chuva) + GFS (vento animado)

> O único elemento com **duas fontes complementares** e **duas camadas no mapa**:
> raster de precipitação de satélite (GEE) + malha vetorial animada de vento
> (serviço storm dedicado, FastAPI :8005). Fonte da verdade:
> `gee_client.py`, `storm/main.py`, `storm/wind_engine.py`, `GeoRisk.jsx`.

## 1. Bases de dados

### A) Chuva — GPM IMERG V07 via GEE

| | |
|---|---|
| **Coleção GEE** | `NASA/GPM_L3/IMERG_V07` (Early Run, ~30 min de latência) |
| **Banda** | `precipitation` — mm/h crus × **0.1 = mm/h reais** |
| **Resolução** | 0.1° global, granular de 30 min |
| **Janela padrão** | **3 dias** (`?start=&end=` sobrescreve) — "climatologia de chuva recente" |
| **Agregação** | `mean()` das passagens |

### B) Vento — GFS (NOAA) **sem GEE**, via COGs locais

| | |
|---|---|
| **Arquivos** | `storm/data/vento_brasil_YYYY-MM.tif` — **12 COGs mensais** (2025-01 … 2025-12), empacotados na imagem Docker |
| **Bands** | band 1 = **U** (leste-oeste), band 2 = **V** (norte-sul), m/s a 10 m |
| **Resolução** | 0.25° |
| **Seleção** | mês da `event_date` do evento; faltando o arquivo → fallback `vento_brasil_2025-10.tif` com warning no log (`wind_engine.py:32-38`) |
| **Recorte** | janela de **500 km** (~4.5°) ao redor de lat/lon do evento |

## 2. Tratamento no backend

**Chuva (GEE):**
```
get_storm_tiles(start, end)                    gee_client.py:222
  → ee.ImageCollection('NASA/GPM_L3/IMERG_V07').filterDate(...).select('precipitation')
  → .mean().multiply(0.1)
  → visualization = {min: 0.0, max: 12.0, palette: [1e293b, 22d3ee, 3b82f6, a855f7, ef4444]}
  ← {mapid, token, tile_fetcher, visualization}
```

**Vento (storm :8005):** `WindEngine.get_wind_data(lat, lon, date_str)`:
1. Escolhe o COG do mês (`_get_tiff_path_for_date`)
2. `rioxarray.open_rasterio` → recorte espacial da janela (trata orientação do eixo Y)
3. `u = band 1`, `v = band 2`; garante top-bottom; `nan_to_num(0.0)`
4. Monta o formato do **leaflet-velocity**: `[{header:{la1,la2,lo1,lo2,nx,ny,dx,dy,refTime,...}, data:[u,v,u,v,...]}]`

## 3. Plotagem no mapa

- **Chuva:** tiles GEE via `GEETileLayer` (idêntico às demais camadas raster);
  cinza-escuro = seco → ciano → azul → roxo → **vermelho = chuva extrema**
- **Vento:** `WindLayer` = `L.velocityLayer` — partículas animadas seguindo o
  vento real, estilo por severidade do evento (`levelStyles`): Baixa 1.5px,
  Media 2px, Critica 3px
- **VFX 3D:** `bolt` (raio ramificado com flicker, roxo) + shake de câmera

## 4. Interação do usuário — clicar num evento de outro usuário

O Tempestade tem o fluxo de clique **mais rico** — e o fetch de vento foi
desenhado **de propósito** para cobrir o clique em evento alheio
(`GeoRisk.jsx:95-130`, comentário do código):

1. **Popup** do autor original (avatar, tipo, severidade, status, data, descrição)
2. `triggerEvent({...evt, _ts, source: 'marker'})` → evento ativo
3. **flyTo** + **VFX 3D** (raio + shake); após 400 ms (o menor delay) habilita
   o fetch da camada GEE de chuva
4. **Vento:** o `useEffect` do `activeEvent` (`GeoRisk.jsx:101-130`) dispara
   `POST /api/georisk/storm/plot/` com `{latitude, longitude, date: evt.event_date}`
   — **funciona igual para submit próprio e clique em marcador de outro usuário**
   (antes do refactor, o fetch vivia só no submit e o clique não puxava a malha)
5. A chave de dedupe é `lat,lon,event_date,_ts` em `windFetchKeyRef` — refetch
   garantido em cliques repetidos, sem requests duplicados em voo; trocar de
   evento (ou limpar) cancela o fetch anterior via flag `cancelled`
6. **Data do evento importa aqui:** diferente das camadas GEE, o vento usa a
   `event_date` → recorte do COG **do mês do report** (com fallback 2025-10)
7. "✕ Limpar efeito 3D" remove VFX **e** malha de vento (`setWindData(null)`)

**Nuances honestas:**
- Sem checagem de posse — o clique em evento alheio tem experiência idêntica
- Se o mês do evento não tem COG (ex.: 2026), cai no fallback mensal 2025 —
  o vento mostrado é o do arquivo, não o do dia real (dados 2026 são
  pendência via data_prep)

## 5. Arquivos relacionados

| Arquivo | Papel |
|---|---|
| `georisk/services/gee_client.py:222-260` | `get_storm_tiles` — IMERG, ×0.1, paleta chuva |
| `georisk/views.py:42-63` | `StormProxyView` — proxy Django→storm (env `STORM_SERVICE_URL` base + `/api/wind/plot`) |
| `georisk/urls.py:8` | Rota `storm/plot/` |
| `storm/main.py` | FastAPI :8005 — `POST /api/wind/plot` |
| `storm/wind_engine.py` | Recorte COG → JSON leaflet-velocity |
| `storm/data/vento_brasil_2025-*.tif` | 12 COGs mensais (na imagem Docker) |
| `risk_network_frontend/src/pages/GeoRisk.jsx:95-130` | useEffect do vento (cobre clique em marcador alheio) |
| `risk_network_frontend/src/components/Map/WindLayer.jsx` | `L.velocityLayer` + `levelStyles` |
| `risk_network_frontend/src/components/Map/vfx/bolt.js` | VFX do raio |
| `docker-compose.yml` | Serviço `storm` (restart policy, env `STORM_SERVICE_URL`) |