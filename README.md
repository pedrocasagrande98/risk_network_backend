# Risk Network

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-092E20.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A social network that helps people communicate more efficiently during **extreme weather events** — floods, storms, tornadoes, droughts, and related climate risks that intensify in years like El Niño.

Originally built as the **final project of the Full Stack Python course at EBAC (Escola Britânica de Artes e Ciências Exatas)** as a Twitter-style social network, and now extended with a **geospatial Risk Network** module that pairs a map with an event report form, GPS capture, and photo uploads.

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Roadmap](#roadmap)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [License](#license)

---

## About

Risk Network is a platform for **collective awareness and rapid information sharing** during climate-driven extreme events. The core idea is simple: when a flood, storm, tornado, or drought is happening (or likely to happen), people in the affected area should be able to:

1. **See** what is going on around them, on a map, in real time.
2. **Report** an event with a few details (category, status, severity, description).
3. **Attach** their current GPS location automatically and an optional photo.
4. **Communicate** with their network through the Twitter-style timeline (tweets, likes, comments, follow).

The social side keeps the community engaged between events; the geo side becomes critical when seconds matter.

---

## Features

### Implemented today (v0.1.0)

- **User accounts** with custom `User` model (bio, avatar, follow graph)
- **JWT authentication** (`djangorestframework-simplejwt`) — register, login, refresh
- **Profile management** — view and update the authenticated user's profile
- **Follow / unfollow** users (toggle endpoint)
- **Tweets** — create, list, retrieve, delete (author-only deletion)
- **Likes** — toggle like on a tweet
- **Comments** — list and create comments on a tweet
- **Personalized feed** — tweets authored by users you follow
- **Django admin** — out-of-the-box management UI for all models
- **CORS** open by default for front-end development

### Planned (Risk Network module)

- 📍 **Event reports with geolocation** — capture the user's GPS via `navigator.geolocation` and attach `latitude` / `longitude` to the report
- 🗺️ **Interactive map** — pins per event, filterable by status, category and severity (Leaflet + OpenStreetMap recommended)
- 🏷️ **Event status** — `forecast` / `ongoing` / `past`
- 🌪️ **Event category** — `flood`, `storm`, `tornado`, `drought`, `fire`, `other`
- ⚠️ **Severity scale** — 1 to 5
- 📷 **Photo upload** — `Pillow` is already in the dependency list, ready to handle images
- 📡 **"Near me" queries** — radius search by coordinates
- 🔔 **Notifications** — when a followed user reports a nearby event

---

## Roadmap

| Status | Item |
| :---: | --- |
| ✅ | User model with custom fields (bio, avatar, follow graph) |
| ✅ | JWT authentication (register, login, refresh) |
| ✅ | Tweets, likes, comments |
| ✅ | Personalized feed |
| ✅ | Django admin |
| ⏳ | `RiskEvent` model (category, status, severity, geo, photos) |
| ⏳ | Geo endpoints (`/api/risk/events/`, `near/`, `photos/`) |
| ⏳ | Map view in the front-end (Leaflet / MapLibre) |
| ⏳ | GPS auto-capture flow on the front-end |
| ⏳ | Photo upload endpoint |
| ⏳ | Reverse geocoding (display human-readable address) |
| ⏳ | Push / in-app notifications for nearby events |
| ⏳ | Offline-friendly PWA front-end |

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.13 |
| Web framework | Django 6.0.7 |
| API framework | Django REST Framework 3.17 |
| Auth | `djangorestframework-simplejwt` 5.5 |
| CORS | `django-cors-headers` 4.9 |
| Images | `Pillow` 12.3 |
| Database | SQLite (default) · PostgreSQL via `psycopg2` + `dj-database-url` |
| Packaging | Poetry |
| Front-end (planned) | Leaflet / MapLibre, OpenStreetMap tiles |

See `pyproject.toml` for the authoritative dependency list.

---

## Quick Start

### Prerequisites

- **Python 3.13+**
- **Poetry** (https://python-poetry.org/)

### Setup

```bash
# 1. Clone
git clone <your-repo-url> risk_network
cd risk_network

# 2. Install dependencies
poetry install

# 3. Create your .env file (a sample is shown below)
#    At minimum, set SECRET_KEY and DEBUG.
cp .env.example .env   # or create .env manually

# 4. Apply database migrations
poetry run python manage.py migrate

# 5. Create a superuser (for /admin)
poetry run python manage.py createsuperuser

# 6. Run the development server
poetry run python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

### `.env` example

```dotenv
SECRET_KEY=change-me-in-production
DEBUG=True
# Uncomment to use PostgreSQL instead of SQLite
# DATABASE_URL=postgres://postgres:postgres@localhost:5432/risk_network
```

The settings module reads `SECRET_KEY`, `DEBUG`, and an optional `DATABASE_URL` through `python-dotenv` and `dj_database_url`. See `core/settings.py`.

### Quick test with the browser

The Django REST Framework browsable API lets you exercise the endpoints without any extra tool:

1. `POST /api/users/auth/register/` — create a user
2. `POST /api/users/auth/login/` — obtain `access` and `refresh` JWT
3. `GET/PUT /api/users/me/` — view or update your profile (requires `Authorization: Bearer <access>`)
4. `POST /api/tweets/` — create a tweet (max 280 chars)
5. `POST /api/tweets/<id>/like/` — like / unlike

For authenticated calls, the recommended tooling is **Postman**, **Insomnia**, or VS Code's **Thunder Client** extension. The `check.md` file in `testes/` contains a step-by-step smoke test.

---

## Project Structure

```
risk_network/
├── core/                   # Django project (settings, root URLs, WSGI/ASGI)
├── users/                  # Custom User model, auth views, profile, follow
├── tweets/                 # Tweet, Like, Comment models + API
├── docs/                   # Architecture, API reference, Risk Network design, contributing
├── testes/                 # Smoke test notes and screenshots
├── manage.py
├── pyproject.toml
├── poetry.lock
├── .env                    # Local secrets (do not commit)
└── README.md
```

Each app follows the conventional Django layout: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`, and a `migrations/` directory.

---

## Documentation

Detailed documentation lives in [`docs/`](docs/):

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — stack, apps, models, relationships, request flows
- [docs/API.md](docs/API.md) — complete REST endpoint reference
- [docs/RISK_NETWORK.md](docs/RISK_NETWORK.md) — design proposal for the geo module (data model, endpoints, map/GPS flow)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — local setup, conventions, migrations, tests

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
