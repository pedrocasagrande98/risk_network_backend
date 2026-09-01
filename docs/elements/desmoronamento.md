# 🪨 Desmoronamento — evento puro + VFX 3D

> O elemento mais simples: **sem dados geoespaciais de terceiros hoje** —
> registra o evento, mostra o pin e a experiência cinematográfica 3D.
> O endpoint GEE responde **400 proposital** para este tipo. Fonte da
> verdade: `views_gee.py:67-71`, `GeoRisk.jsx`, `ThreeVFXOverlay.jsx`.

## 1. Base de dados

| | |
|---|---|
| **Fonte externa** | — (nenhuma camada de satélite/sensor definida) |
| **Dados** | apenas o registro do evento: tipo, severidade, descrição, data, lat/lon, autor |
| **Extensão futura (OCP)** | basta um `get_landslide_tiles()` no `GEEProvider` (ex.: suscetibilidade de encosta) + entrada em `TYPE_TO_GEE` no frontend — nada mais muda |

## 2. Tratamento no backend

- `POST /api/georisk/` → Celery → `DefaultEventProcessor`
  (`processors.py:101-107`): marca `COMPLETED` sem IA/processamento externo
- `GET /api/georisk/gee/desmoronamento/` → **400** "Tipo de camada GEE
  desconhecido" (a view só conhece queimada/geada/tempestade)
- O frontend nem faz o fetch: `TYPE_TO_GEE` em `GeoRisk.jsx:24-28` não
  contém `Desmoronamento`

## 3. Plotagem no mapa

- **Pin marrom** (`#854d0e`) no cluster de marcadores
- Status `PENDING` pulsa laranja; `COMPLETED` fixa o marrom
- Sem camada de dados além do basemap — o elemento vive da **experiência 3D**

## 4. Interação do usuário — clicar num evento de outro usuário

Fluxo ao clicar num marcador de Desmoronamento (`GeoRisk.jsx:501-511`):

1. **Popup** do autor original (avatar/inicial, `@username`, tipo, severidade,
   status, data, descrição)
2. `triggerEvent({...evt, _ts, source: 'marker'})` → evento ativo
3. **flyTo** até a coordenada (zoom 12)
4. **VFX 3D — o coração deste elemento** (`GEE_TRIGGER_DELAY.Desmoronamento =
   800 ms`): rachadura do terreno + pedras + poeira no canvas Three.js
   (`vfx/`), com flash e coreografia
5. Ao fim do delay, `onGEETileRequest('Desmoronamento')` é chamado e
   **corretamente ignorado** (não há camada GEE — nenhum request é feito)
6. "✕ Limpar efeito 3D" encerra a experiência

**Nuances honestas:**
- Sem checagem de posse — clique em evento alheio é idêntico ao próprio
- Como não há dados externos, não existe a "desatualização" das outras
  camadas: o que se vê é sempre o registro do autor + VFX

## 5. Arquivos relacionados

| Arquivo | Papel |
|---|---|
| `georisk/processors.py:101-107` | `DefaultEventProcessor` — COMPLETED direto |
| `georisk/views_gee.py:67-71` | 400 para tipo sem camada GEE |
| `risk_network_frontend/src/pages/GeoRisk.jsx:24-28` | `TYPE_TO_GEE` sem Desmoronamento |
| `risk_network_frontend/src/components/Map/vfx/` | Efeitos 3D (rachadura/pedras/poeira) |
| `risk_network_frontend/src/components/Map/ThreeVFXOverlay.jsx:41-47` | Delay 800 ms |