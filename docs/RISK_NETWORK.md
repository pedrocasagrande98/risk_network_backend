# Risk Network — Module Design Proposal

> **Status:** Design proposal. **Not yet implemented.** This document describes the *target* behavior of the Risk Network module: a map-backed, geo-located extension of the timeline that lets users report extreme weather events with GPS coordinates and photos.

---

## 1. Vision

The Twitter-style timeline is great for general conversation. The Risk Network module adds a **map-first surface** for the moments that matter most — when a flood, storm, tornado, or drought is unfolding and people need to know *what is happening, where, and how bad*.

Each event report is a small structured object: **what**, **where**, **when**, **how bad**, **what stage**, **optional photo**. Reports are visualized as pins on a map; the timeline continues to drive discovery and discussion.

---

## 2. Goals & non-goals

**Goals**

- Lightweight reporting flow that works in <30 seconds on a phone in the field.
- A single map view that answers: *"What is happening around me right now?"*
- A predictable, filterable REST surface for the front-end to consume.

**Non-goals (for v0.1)**

- Official emergency-alert ingestion (no integration with civil defense APIs yet).
- Server-side reverse geocoding stored on the event (left as a front-end concern in v0.1).
- Push notifications (in-app only in v0.1).

---

## 3. Data model (proposed)

These models would live in a new app, e.g. `risk/`. The fields below are normative — name and types must remain stable so that the REST contract in §5 holds.

### `RiskEvent`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `BigAutoField` (PK) | |
| `author` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="risk_events")` | Reporter. |
| `title` | `CharField(max_length=120)` | Short headline. |
| `description` | `TextField(blank=True)` | Optional narrative. |
| `category` | `CharField(choices=CATEGORY_CHOICES, max_length=16)` | See §3.1. |
| `status` | `CharField(choices=STATUS_CHOICES, max_length=10)` | See §3.2. |
| `severity` | `PositiveSmallIntegerField(choices=SEVERITY_CHOICES, default=1)` | See §3.3. |
| `latitude` | `DecimalField(max_digits=9, decimal_places=6)` | Required. |
| `longitude` | `DecimalField(max_digits=9, decimal_places=6)` | Required. |
| `accuracy_m` | `FloatField(null=True, blank=True)` | From `Position.coords.accuracy`. |
| `address` | `CharField(max_length=255, blank=True)` | Optional reverse-geocoded label. |
| `occurred_at` | `DateTimeField(null=True, blank=True)` | When the event happened (vs. when reported). |
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `updated_at` | `DateTimeField(auto_now=True)` | |

#### 3.1 `category` choices

`flood` · `storm` · `tornado` · `drought` · `fire` · `landslide` · `other`

#### 3.2 `status` choices

- `forecast` — risk is expected (e.g. a forecast storm).
- `ongoing` — currently happening.
- `past` — already over.

#### 3.3 `severity` choices

`1` (low) · `2` · `3` (medium) · `4` · `5` (extreme)

### `RiskEventPhoto`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `BigAutoField` (PK) | |
| `event` | `ForeignKey(RiskEvent, on_delete=CASCADE, related_name="photos")` | |
| `image` | `ImageField(upload_to="risk_events/")` | Handled by `Pillow` (already in `pyproject.toml`). |
| `caption` | `CharField(max_length=200, blank=True)` | |
| `uploaded_by` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True, blank=True)` | Survives user deletion. |
| `created_at` | `DateTimeField(auto_now_add=True)` | |

### Django meta

- Add `risk` to `INSTALLED_APPS` (`core/settings.py:38-50`).
- No changes to `AUTH_USER_MODEL` required.
- Add `risk/` to `core/urls.py:23-27` once the app exposes URLs.

---

## 4. Why these design choices

- **Separate app (`risk/`).** Keeps the social layer (`tweets/`) and the geo layer from coupling. Each can be versioned and tested independently.
- **Decimal coordinates.** 6 decimal places ≈ 11 cm of horizontal precision — well within GPS noise and storage-friendly.
- **`severity` as integer.** Easy filtering (`severity__gte=3`), predictable JSON, no enum-library dependency.
- **`status` as text choices.** Maps cleanly to UI tabs ("Forecast / Ongoing / Past").
- **`address` stored as text, not a foreign key to a `Place` table.** Reversing addresses at write time keeps the read path simple; we can promote it to a structured model later if search/autocomplete becomes a requirement.
- **Photos in a related model, not on `RiskEvent` directly.** Multiple photos per report, deletion cascade, and per-photo metadata (caption, uploader) come for free.

---

## 5. REST API (proposed)

All endpoints are prefixed by `/api/risk/`. Same JWT auth as the rest of the API.

| Method | URL | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET`  | `/api/risk/events/` | Public | List events (supports filters below) |
| `POST` | `/api/risk/events/` | Bearer | Create an event |
| `GET`  | `/api/risk/events/<int:pk>/` | Public | Retrieve an event |
| `PUT`  | `/api/risk/events/<int:pk>/` | Author | Update an event |
| `DELETE` | `/api/risk/events/<int:pk>/` | Author | Delete an event |
| `POST` | `/api/risk/events/<int:pk>/photos/` | Bearer | Attach a photo |
| `GET`  | `/api/risk/events/near/` | Public | Events near a coordinate |

### Filters on `GET /api/risk/events/`

Query parameters (all optional, combinable):

- `status` — one of `forecast` / `ongoing` / `past`
- `category` — one of the categories above
- `severity__gte` — minimum severity
- `bbox=minLng,minLat,maxLng,maxLat` — bounding box
- `since=ISO8601` — events created after this timestamp
- Ordering: `?ordering=-created_at` (default), `?ordering=-severity`

### `GET /api/risk/events/near/?lat=&lng=&radius_km=`

Required: `lat`, `lng`. Optional: `radius_km` (default 25, max 500). Returns events ordered by distance ascending.

### `POST /api/risk/events/`

```json
{
  "title": "Street flooded on Av. Brasil",
  "description": "Water level ~50cm, cars stalled.",
  "category": "flood",
  "status": "ongoing",
  "severity": 4,
  "latitude": -22.9068,
  "longitude": -43.1729,
  "accuracy_m": 12.0,
  "address": "Av. Brasil, RJ",
  "occurred_at": "2026-07-25T10:00:00Z"
}
```

Response `201 Created` — the created event, including `id` and timestamps.

### `POST /api/risk/events/<int:pk>/photos/`

`multipart/form-data` with `image` (required) and optional `caption`. Response `201 Created` with the `RiskEventPhoto` payload.

---

## 6. Front-end flow (proposed)

1. The user opens the **Risk Network** tab.
2. The map (Leaflet + OpenStreetMap tiles) centers on the device's last known position, fetched with `navigator.geolocation.getCurrentPosition`.
3. Existing `RiskEvent` pins are loaded from `GET /api/risk/events/?bbox=...` and overlaid.
4. The user taps **Report**:
   - A form asks for `category`, `status`, `severity`, `title`, `description`.
   - GPS is auto-captured; the user can drag the pin to refine.
   - Optional photo is picked via `<input type="file" accept="image/*" capture="environment">`.
5. On submit, the front-end does:
   - `POST /api/risk/events/` with the JSON payload.
   - If a photo is attached, `POST /api/risk/events/<id>/photos/` with `multipart/form-data`.
6. The new pin appears on the map without a page refresh.
7. Tapping a pin opens a side panel with details, photos, and a link to the related discussion on the timeline (a future feature: a `tweet` field on `RiskEvent`, or a hashtag convention).

### Map library choice

**Leaflet + OpenStreetMap** is the recommended default: zero-cost, no API key, plenty of community plugins (marker clustering, heatmaps, drawing tools). Mapbox/Google Maps can be swapped in later by changing only the tile layer configuration.

---

## 7. Permissions matrix

| Action | Anonymous | Authenticated | Author |
| :--- | :---: | :---: | :---: |
| List / read events | ✅ | ✅ | ✅ |
| Create event | ❌ | ✅ | ✅ |
| Update event | ❌ | ❌ | ✅ |
| Delete event | ❌ | ❌ | ✅ |
| Add photo | ❌ | ✅ | ✅ |

The same `IsAuthenticatedOrReadOnly` + author-only `IsOwner` pattern already used in `tweets/` is recommended for consistency.

---

## 8. Implementation checklist (when ready)

- [ ] Create the `risk` app: `python manage.py startapp risk`
- [ ] Register it in `INSTALLED_APPS`
- [ ] Implement `RiskEvent` and `RiskEventPhoto` models
- [ ] Generate and apply migrations
- [ ] Build serializers, viewsets, and URL conf
- [ ] Add a bbox/near filter (Django ORM `__range` or PostGIS `dwithin` if Postgres is enabled)
- [ ] Wire the map UI in the front-end
- [ ] Wire the GPS capture flow in the front-end
- [ ] Add manual end-to-end tests (create event → pin appears → photo attached)
- [ ] Document the new endpoints in `docs/API.md`

---

## 9. Open questions

- **PostGIS?** The bounding-box filter can be done in pure SQL on SQLite/Postgres, but efficient radius queries over thousands of events are easier with PostGIS. Defer until volume justifies it.
- **Moderation.** Do we need a "verified" flag for emergency services / civil defense accounts? (Out of scope for v0.1.)
- **Time zones.** `occurred_at` is stored as UTC; the front-end will localize for display.
