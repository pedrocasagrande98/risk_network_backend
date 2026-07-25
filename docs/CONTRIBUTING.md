# Contributing

Thanks for your interest in Risk Network. This guide covers everything you need to get the project running locally, follow our conventions, and submit changes that are easy to review.

---

## Table of Contents

- [Code of conduct](#code-of-conduct)
- [Prerequisites](#prerequisites)
- [Local setup](#local-setup)
- [Project conventions](#project-conventions)
- [Working with migrations](#working-with-migrations)
- [Running tests](#running-tests)
- [Pull request checklist](#pull-request-checklist)
- [Reporting issues](#reporting-issues)

---

## Code of conduct

Be respectful, assume good faith, and focus on the work. Constructive feedback is welcome; personal attacks are not.

---

## Prerequisites

- **Python 3.13+**
- **Poetry** — https://python-poetry.org/docs/#installation
- **Git**
- *(Optional)* **PostgreSQL** if you want to exercise the production database path.
- *(Optional)* **Postman**, **Insomnia**, or VS Code's **Thunder Client** for testing authenticated endpoints.

---

## Local setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-user>/risk_network.git
cd risk_network

# 2. Install dependencies (creates a virtualenv managed by Poetry)
poetry install

# 3. Create your .env (do not commit it)
cat > .env <<'EOF'
SECRET_KEY=dev-only-change-me
DEBUG=True
# DATABASE_URL=postgres://postgres:postgres@localhost:5432/risk_network
EOF

# 4. Apply migrations
poetry run python manage.py migrate

# 5. Create a superuser (for /admin)
poetry run python manage.py createsuperuser

# 6. Run the dev server
poetry run python manage.py runserver
```

The API will be reachable at `http://127.0.0.1:8000/`. A quick browser-based smoke test is documented in [`testes/check.md`](../testes/check.md).

### Verifying the install

```bash
poetry run python manage.py check
poetry run python manage.py showmigrations
```

Both should run without errors.

---

## Project conventions

### Layout

- One Django app per bounded context: `users` (identity), `tweets` (timeline). New contexts (e.g. `risk` for the geo module) go in a new app — see [`docs/RISK_NETWORK.md`](RISK_NETWORK.md).
- Inside an app, keep the standard files: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`, and a `migrations/` package.

### Style

- **PEP 8** with 4-space indentation.
- **Type-friendly Python 3.13 syntax** (e.g. `list[...]`, `|` unions in annotations where helpful).
- Prefer **class-based DRF views** (`generics.*`, `APIView`) over function-based views, to stay consistent with the existing code in `users/views.py` and `tweets/views.py`.
- **Imports**: standard library first, third-party second, local third, separated by blank lines.
- **Models**: keep business logic in model methods or in serializers/views — not in `__init__` magic.

### Branching

- `main` is the integration branch and is always deployable.
- Feature branches: `feature/<short-slug>` (e.g. `feature/risk-event-model`).
- Bug fixes: `fix/<short-slug>`.
- Documentation-only: `docs/<short-slug>`.

### Commit messages

- Imperative, present tense: "Add risk event endpoint", not "Added…".
- First line ≤ 72 characters; add a blank line and a body for non-trivial changes.
- Reference the issue number when relevant: `(#42)`.

### What not to commit

The following are local-only and **must never** be committed:

- `.env`
- `db.sqlite3`
- `media/` (uploaded files)
- `__pycache__/`
- `.idea/` / `.vscode/` (per-user IDE state)

If any of these appear in `git status`, add them to `.gitignore` (or to your local excludes) before staging.

---

## Working with migrations

Django generates migrations for you. Use them deliberately.

```bash
# After changing a model
poetry run python manage.py makemigrations

# Always review the generated file before committing it

# Apply to your local database
poetry run python manage.py migrate
```

**Guidelines**

- **Always review** the generated `migrations/000N_*.py` file. Auto-generated names are fine; the operations should match your intent.
- **One concern per migration** when possible. Split unrelated model changes into separate migrations.
- **Do not edit** a migration that has already been applied to a shared branch — add a new one instead.
- The two-step pattern in `tweets/migrations/0001_initial.py` + `0002_initial.py` (table first, FKs after) is the recommended approach when your model references `AUTH_USER_MODEL` and is being added in a brand-new app.

---

## Running tests

The project ships placeholder `tests.py` modules in both apps. When adding tests, prefer Django's standard `TestCase` and DRF's `APITestCase`.

```bash
# Run the full suite
poetry run python manage.py test

# Run a single app
poetry run python manage.py test users
poetry run python manage.py test tweets

# Run a single test class / method
poetry run python manage.py test tweets.tests.<TestClass>.<test_method>
```

**What to test when you add a feature**

- Serializer validation (happy path + at least one invalid payload).
- Permission enforcement (anonymous vs authenticated vs author).
- Side effects (e.g. a `DELETE` that should be forbidden for non-authors returns 403).
- Any new model method or property that has logic.

---

## Pull request checklist

Before opening a PR, confirm:

- [ ] Code follows the conventions above and is consistent with the surrounding files.
- [ ] `poetry run python manage.py check` is clean.
- [ ] New behavior is covered by tests in the relevant app.
- [ ] `poetry run python manage.py test` passes locally.
- [ ] New migrations are committed.
- [ ] `.env`, `db.sqlite3`, `media/`, and `__pycache__/` are **not** part of the diff.
- [ ] Public API changes are reflected in [`docs/API.md`](API.md).
- [ ] Architectural changes are reflected in [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).
- [ ] The PR description explains *what* changed and *why*, with links to issues if any.

---

## Reporting issues

When opening an issue, please include:

- A clear, specific title.
- Steps to reproduce (for bugs) or the user story (for features).
- Expected vs actual behavior.
- Environment: Python version, OS, branch/commit, and any relevant settings.
- For security issues, **do not** open a public issue — email the maintainer privately instead.
