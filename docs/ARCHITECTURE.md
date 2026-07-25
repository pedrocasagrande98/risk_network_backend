# Architecture

This document describes how Risk Network is organized: the stack, the apps, the data model, and the request flows that hold the system together.

## Table of Contents

- [Stack](#stack)
- [Directory layout](#directory-layout)
- [Apps at a glance](#apps-at-a-glance)
- [Settings highlights](#settings-highlights)
- [Data model](#data-model)
- [Request flows](#request-flows)
- [Cross-cutting concerns](#cross-cutting-concerns)

---

## Stack

| Layer | Technology | Source of truth |
| --- | --- | --- |
| Language | Python 3.13 | `pyproject.toml` — `requires-python = ">=3.13"` |
| Web framework | Django 6.0.7 | `pyproject.toml` |
| API layer | Django REST Framework 3.17 | `pyproject.toml` |
| Auth | `djangorestframework-simplejwt` 5.5 | `core/settings.py:135-142` |
| CORS | `django-cors-headers` 4.9 | `core/settings.py:45,54,133` |
| Database (default) | SQLite | `core/settings.py:86-90` |
| Database (optional) | PostgreSQL via `psycopg2` + `dj-database-url` | `core/settings.py:16,86-90` |
| Images | `Pillow` 12.3 | `users/models.py:6`, `core/settings.py:128-129` |
| Configuration | `.env` via `python-dotenv` | `core/settings.py:15-18` |
| Packaging | Poetry | `pyproject.toml`, `poetry.lock` |

---

## Directory layout

```
risk_network/
├── core/                       # Django project package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # All configuration
│   ├── urls.py                 # Root URL conf
│   └── wsgi.py
│
├── users/                      # Accounts, auth, profile, follow graph
│   ├── migrations/
│   │   └── 0001_initial.py     # User model schema
│   ├── admin.py
│   ├── apps.py
│   ├── models.py               # User (extends AbstractUser)
│   ├── serializers.py          # UserSerializer, RegisterSerializer
│   ├── tests.py
│   ├── urls.py                 # /api/users/...
│   └── views.py                # Register, profile, follow
│
├── tweets/                     # Tweets, likes, comments
│   ├── migrations/
│   │   ├── 0001_initial.py     # Tweet, Like, Comment tables (no FKs yet)
│   │   └── 0002_initial.py     # Adds FKs to AUTH_USER_MODEL
│   ├── admin.py
│   ├── apps.py
│   ├── models.py               # Tweet, Like, Comment
│   ├── serializers.py          # TweetSerializer, CommentSerializer
│   ├── tests.py
│   ├── urls.py                 # /api/tweets/...
│   └── views.py                # List/create, detail, feed, like, comments
│
├── docs/                       # Documentation
├── testes/                     # Manual test notes and screenshots
│
├── manage.py
├── pyproject.toml
├── poetry.lock
├── .env                        # Local environment, not committed
├── db.sqlite3                  # Local DB (when using the default config)
└── README.md
```

---

## Apps at a glance

### `core`

The Django project. It only wires URLs and configures settings. It does not define business models.

- `core/urls.py:23-27` mounts:
  - `admin/` — Django admin
  - `api/users/` — `users.urls`
  - `api/tweets/` — `tweets.urls`
- `core/settings.py:128-129` configures `MEDIA_URL` / `MEDIA_ROOT` and serves media in `DEBUG` via `core/urls.py:29-30`.

### `users`

Owns the `User` model and every endpoint related to identity and social graph.

- `users/models.py:4-12` defines `User(AbstractUser)` with:
  - `bio: TextField` (optional)
  - `avatar: ImageField` (uploaded to `avatars/`)
  - `following: ManyToManyField('self', symmetrical=False, related_name='followers')`
- `users/views.py`:
  - `RegisterView` — `generics.CreateAPIView`, public
  - `UserProfileView` — `RetrieveUpdateAPIView` of `request.user`
  - `FollowUserView` — toggles the M2M relation
- `users/urls.py:5-10`:
  - `auth/register/`
  - `auth/login/` (SimpleJWT `TokenObtainPairView`)
  - `auth/refresh/` (SimpleJWT `TokenRefreshView`)
  - `me/`
  - `<int:pk>/follow/`

### `tweets`

Owns the timeline features.

- `tweets/models.py`:
  - `Tweet` — `author (FK User)`, `content (CharField, max 280)`, `created_at`, `updated_at`
  - `Like` — `user (FK User)`, `tweet (FK Tweet)`, `created_at`; `unique_together = (user, tweet)`
  - `Comment` — `user (FK User)`, `tweet (FK Tweet)`, `content (Text)`, `created_at`
- `tweets/views.py`:
  - `TweetListCreateView` — `GET` public list (newest first), `POST` authenticated create
  - `TweetDetailView` — `GET` public detail, `DELETE` author-only
  - `FeedView` — `GET` tweets from `request.user.following.all()` (auth required)
  - `LikeTweetView` — toggles a `Like`
  - `CommentListCreateView` — `GET` public, `POST` auth

---

## Settings highlights

| Setting | Value | Location | Note |
| --- | --- | --- | --- |
| `AUTH_USER_MODEL` | `users.User` | `core/settings.py:131` | Custom user model |
| `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` | `JWTAuthentication` | `core/settings.py:135-138` | All DRF auth is JWT |
| `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` | `IsAuthenticated` | `core/settings.py:139-141` | Individual views override with `IsAuthenticatedOrReadOnly` / `AllowAny` |
| `CORS_ALLOW_ALL_ORIGINS` | `True` | `core/settings.py:133` | Convenience for the local front-end; tighten in production |
| `MEDIA_URL` / `MEDIA_ROOT` | `media/` / `BASE_DIR / "media"` | `core/settings.py:128-129` | Avatars live under `avatars/` |
| `DATABASES.default` | `dj_database_url.config(default="sqlite:///db.sqlite3")` | `core/settings.py:86-90` | Switches to Postgres if `DATABASE_URL` is set |
| `TIME_ZONE` | `UTC` | `core/settings.py:117` | |

---

## Data model

```text
┌────────────────────────────┐
│           User             │
│  (users.User — AbstractUser)│
├────────────────────────────┤
│ id                          │
│ username (unique)           │
│ email                       │
│ password                    │
│ bio                         │
│ avatar (ImageField)         │
│ following (M2M → self) ◄────┼──┐  symmetrical=False
│ followers (rev of above) ◄──┼──┘
│ first_name, last_name, ...  │
└────────────┬───────────────┘
             │
             │ 1:N (related_name="tweets")
             ▼
┌────────────────────────────┐         ┌──────────────────────────┐
│           Tweet            │ 1     N │          Like            │
├────────────────────────────┤─────────├──────────────────────────┤
│ id                          │         │ id                       │
│ author (FK → User)          │         │ user (FK → User)         │
│ content (≤ 280)             │         │ tweet (FK → Tweet)       │
│ created_at                  │         │ created_at               │
│ updated_at                  │         │ UNIQUE(user, tweet)      │
└────────────┬───────────────┘         └──────────────────────────┘
             │
             │ 1:N (related_name="comments")
             ▼
┌────────────────────────────┐
│          Comment           │
├────────────────────────────┤
│ id                          │
│ user (FK → User)            │
│ tweet (FK → Tweet)          │
│ content (Text)              │
│ created_at                  │
└────────────────────────────┘
```

**Field reference**

- `User` — `users/models.py:4-12`
- `Tweet` — `tweets/models.py:4-11`
- `Like` — `tweets/models.py:13-22`
- `Comment` — `tweets/models.py:24-30`

**Cascade behavior**

- Deleting a `User` cascades to its `Tweet`s, `Like`s, and `Comment`s.
- Deleting a `Tweet` cascades to its `Like`s and `Comment`s.

---

## Request flows

### 1. Register → Login → Tweet

1. `POST /api/users/auth/register/` (`users/views.py:8-11`) creates a `User` via `RegisterSerializer.create` (`users/serializers.py:26-32`).
2. `POST /api/users/auth/login/` returns a SimpleJWT pair (`access`, `refresh`).
3. `POST /api/tweets/` with header `Authorization: Bearer <access>` is handled by `TweetListCreateView.perform_create` (`tweets/views.py:13-14`), which attaches `request.user` as the author.

### 2. Follow → Feed

1. `POST /api/users/<id>/follow/` (`users/views.py:23-34`) toggles the M2M row in `User.following`.
2. `GET /api/tweets/feed/` (`tweets/views.py:28-35`) returns `Tweet.objects.filter(author__in=user.following.all())` ordered by `-created_at`.

### 3. Like / Unlike

`POST /api/tweets/<id>/like/` (`tweets/views.py:37-47`) attempts `Like.objects.get_or_create(user, tweet)`. If the row already existed it is deleted; otherwise it is created. The response distinguishes the two outcomes with HTTP `200` vs `201`.

### 4. Comments

`GET / POST /api/tweets/<id>/comments/` (`tweets/views.py:49-57`) reads/writes `Comment` rows scoped to the tweet in the URL.

---

## Cross-cutting concerns

- **Authentication everywhere.** Every view that mutates data requires `IsAuthenticated`; read-only views are `IsAuthenticatedOrReadOnly`. Public endpoints (register, login, refresh) use `AllowAny`.
- **Media handling.** `users.User.avatar` and (planned) `RiskEvent.photo` rely on `MEDIA_ROOT` and `Pillow`. Files are served by Django only in `DEBUG` (`core/urls.py:29-30`).
- **CORS.** `CORS_ALLOW_ALL_ORIGINS = True` is set to ease front-end development. For production, replace with an explicit allow-list.
- **Configuration through `.env`.** `SECRET_KEY` and `DEBUG` are loaded via `python-dotenv`; `DATABASE_URL` (if present) is parsed by `dj_database_url`.
- **Migrations.** Two-step pattern is visible in `tweets/migrations/0001_initial.py` and `0002_initial.py`: tables are created first, foreign keys are added in a follow-up migration once the `AUTH_USER_MODEL` is swappable. This is the recommended Django pattern.
