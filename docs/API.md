# API Reference

Complete reference of the REST endpoints exposed by Risk Network. All endpoints are mounted under the `/api/` prefix by `core/urls.py`.

> **Conventions**
> - All `POST` / `PUT` / `DELETE` endpoints require an `Authorization: Bearer <access_token>` header unless marked **Public**.
> - JSON request and response bodies.
> - IDs are integers.
> - Times are ISO 8601, in UTC.

---

## Authentication

All authenticated endpoints use **SimpleJWT**. The `access` token is short-lived; the `refresh` token is long-lived.

```http
Authorization: Bearer eyJhbGciOi...
```

Get a token pair:

```http
POST /api/users/auth/login/
Content-Type: application/json

{
  "username": "joao",
  "password": "senha123"
}
```

Response `200 OK`:

```json
{
  "access":  "eyJhbGciOi...access...",
  "refresh": "eyJhbGciOi...refresh..."
}
```

Refresh:

```http
POST /api/users/auth/refresh/
Content-Type: application/json

{ "refresh": "eyJhbGciOi...refresh..." }
```

---

## Users (`/api/users/...`)

Defined in `users/urls.py`.

| Method | URL | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/users/auth/register/` | Public | Create a new user |
| `POST` | `/api/users/auth/login/` | Public | Obtain JWT pair |
| `POST` | `/api/users/auth/refresh/` | Public | Refresh `access` token |
| `GET`  | `/api/users/me/` | Bearer | Get the authenticated user profile |
| `PUT`  | `/api/users/me/` | Bearer | Update the authenticated user profile |
| `POST` | `/api/users/<int:pk>/follow/` | Bearer | Toggle follow on user `<pk>` |

### `POST /api/users/auth/register/`

View: `users.views.RegisterView` (`users/views.py:8-11`).

```json
{
  "username": "joao",
  "email":    "joao@example.com",
  "password": "senha123"
}
```

Response `201 Created`:

```json
{ "id": 1, "username": "joao", "email": "joao@example.com" }
```

### `GET / PUT /api/users/me/`

View: `users.views.UserProfileView` (`users/views.py:13-18`).

Response `200 OK` (and body for `PUT`):

```json
{
  "id": 1,
  "username": "joao",
  "email": "joao@example.com",
  "bio": "Climatology enthusiast.",
  "avatar": "http://127.0.0.1:8000/media/avatars/joao.png",
  "followers_count": 12,
  "following_count": 7
}
```

Read-only fields: `id`, `email`. `avatar` accepts a multipart upload.

### `POST /api/users/<int:pk>/follow/`

View: `users.views.FollowUserView` (`users/views.py:20-34`). Toggles the relationship.

Response `200 OK`:

```json
{ "message": "You followed maria" }
```

Self-follow returns `400 Bad Request` with `{ "error": "You cannot follow yourself." }`.

---

## Tweets (`/api/tweets/...`)

Defined in `tweets/urls.py`.

| Method | URL | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET`  | `/api/tweets/` | Public | List all tweets (newest first) |
| `POST` | `/api/tweets/` | Bearer | Create a tweet (max 280 chars) |
| `GET`  | `/api/tweets/feed/` | Bearer | Tweets from users you follow |
| `GET`  | `/api/tweets/<int:pk>/` | Public | Retrieve a tweet |
| `DELETE` | `/api/tweets/<int:pk>/` | Author | Delete a tweet |
| `POST` | `/api/tweets/<int:pk>/like/` | Bearer | Toggle like on a tweet |
| `GET`  | `/api/tweets/<int:pk>/comments/` | Public | List comments on a tweet |
| `POST` | `/api/tweets/<int:pk>/comments/` | Bearer | Comment on a tweet |

### `GET / POST /api/tweets/`

View: `tweets.views.TweetListCreateView` (`tweets/views.py:8-14`).

`POST` body:

```json
{ "content": "First tweet from Risk Network!" }
```

Response `201 Created`:

```json
{
  "id": 1,
  "author": {
    "id": 1, "username": "joao", "email": "joao@example.com",
    "bio": "", "avatar": null,
    "followers_count": 12, "following_count": 7
  },
  "content": "First tweet from Risk Network!",
  "created_at": "2026-07-25T10:00:00Z",
  "updated_at": "2026-07-25T10:00:00Z",
  "likes_count": 0,
  "comments_count": 0,
  "is_liked": false
}
```

`is_liked` is `true` only when the requester is authenticated and has liked the tweet.

### `GET /api/tweets/feed/`

View: `tweets.views.FeedView` (`tweets/views.py:28-35`). Same response shape as the list, filtered to `request.user.following.all()`.

### `GET / DELETE /api/tweets/<int:pk>/`

View: `tweets.views.TweetDetailView` (`tweets/views.py:16-26`).

`DELETE` is restricted to the author; otherwise `403 PermissionDenied` with detail `"You can only delete your own tweets."`.

### `POST /api/tweets/<int:pk>/like/`

View: `tweets.views.LikeTweetView` (`tweets/views.py:37-47`).

- First call: `201 Created` — `{ "message": "Tweet liked" }`
- Second call: `200 OK` — `{ "message": "Tweet unliked" }`

### `GET / POST /api/tweets/<int:pk>/comments/`

View: `tweets.views.CommentListCreateView` (`tweets/views.py:49-57`).

`POST` body:

```json
{ "content": "Stay safe, everyone." }
```

Response `201 Created`:

```json
{
  "id": 1,
  "user": { "id": 1, "username": "joao", "email": "joao@example.com", "bio": "", "avatar": null, "followers_count": 12, "following_count": 7 },
  "tweet": 1,
  "content": "Stay safe, everyone.",
  "created_at": "2026-07-25T10:05:00Z"
}
```

---

## Admin

| Method | URL | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET`  | `/admin/` | Superuser | Django admin (manage `User`, `Tweet`, `Like`, `Comment`) |

Create a superuser:

```bash
poetry run python manage.py createsuperuser
```

---

## Error responses

DRF returns standard HTTP status codes with a JSON body. Common ones used in this project:

| Code | Where | Body example |
| :--- | :--- | :--- |
| `400` | Invalid payload | `{ "field": ["error message"] }` |
| `401` | Missing / invalid JWT | `{ "detail": "Authentication credentials were not provided." }` |
| `403` | Permission denied (e.g. deleting someone else's tweet) | `{ "detail": "You can only delete your own tweets." }` |
| `404` | Object not found | `{ "detail": "Not found." }` |
