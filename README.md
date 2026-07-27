# Natthapong Backend Playground

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Status: learning project](https://img.shields.io/badge/status-learning_project-F59E0B)](#project-status)

A FastAPI service for exploring authentication, authorization, API security,
audit logging, rate limiting, and timezone-aware country clocks.

## Highlights

- Issue and rotate JWT access and refresh tokens with Redis-backed revocation.
- Protect accounts with active-user checks, roles, and login throttling.
- Search countries and return DST-aware clocks from one synchronized UTC instant.
- Record mutations, failed requests, and audit access for `SuperAdmin` review.
- Check PostgreSQL and Redis readiness from a dedicated health endpoint.
- Explore and test the API through generated Swagger UI and ReDoc pages.

## Overview

Natthapong Backend Playground is an asynchronous Python API built with FastAPI,
SQLAlchemy, PostgreSQL, and Redis. It is a compact learning project for studying
how authentication and cross-cutting security concerns fit into a layered web
service.

The API also powers the
[Natthapong Frontend Playground](https://github.com/natthapong-playground/natthapong-front-playground),
which provides profile, audit-log, and interactive world-clock screens.

### Author

Created and maintained by
[Natthapong Playground](https://github.com/natthapong-playground).

## Usage

Once the service is running, open <http://127.0.0.1:8000/docs> to register a
user, obtain a token pair, authorize Swagger UI, and try the protected routes.

Check the application and its dependencies from a terminal:

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"ok","database":true,"redis":true}
```

Useful local URLs:

| URL | Purpose |
| --- | --- |
| <http://127.0.0.1:8000/docs> | Interactive Swagger UI |
| <http://127.0.0.1:8000/redoc> | ReDoc API reference |
| <http://127.0.0.1:8000/api/v1/openapi.json> | OpenAPI schema |
| <http://127.0.0.1:8000/health> | PostgreSQL and Redis readiness |

## Installation

### Windows (recommended)

Requirements: 64-bit Python 3.12, Docker Desktop with Docker Compose v2, and
available local ports `5432`, `6379`, and `8000`.

```bat
git clone https://github.com/natthapong-playground/natthapong-back-playground.git
cd natthapong-back-playground
setup.bat
start.bat
```

Open <http://127.0.0.1:8000/docs>. `setup.bat` creates a repository-local
Python environment, installs dependencies, and generates a private `.env` with
random local credentials. `start.bat` starts PostgreSQL and Redis, waits for
both services, and launches the API. Nothing is installed globally.

Press `Ctrl+C` to stop Uvicorn. Run `stop.bat` to stop the project containers.

### Linux and macOS

Install Python 3.12 and Docker Compose v2. Then create `.env` from the template
and replace every public credential placeholder with a private value.

```bash
git clone https://github.com/natthapong-playground/natthapong-back-playground.git
cd natthapong-back-playground
cp .env.example .env
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
docker compose up -d --wait postgres redis
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Generate a strong password and JWT secret with:

```bash
python3.12 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not commit `.env`. Keep the PostgreSQL credentials in `DATABASE_URL`
consistent with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.

## API at a Glance

All feature routes use the default `/api/v1` prefix.

| Feature | Routes | Access |
| --- | --- | --- |
| Authentication | `POST /login`, `/google-login`, `/refresh-token`, `/logout` | Public or bearer token |
| Users | `POST /users/register`, `GET /users/myprofile` | Public or active user |
| Countries | `GET /countries`, `/countries/{code}` | Active user |
| Clocks | `GET /clock?code=TH,JP` | Active user |
| Audit logs | `GET /audit-logs` | `SuperAdmin` |

Login uses OAuth2 form data with the email address in `username`. Protected
routes expect `Authorization: Bearer <access-token>`. Supported roles are
`Guest`, `Regular`, `Admin`, and `SuperAdmin`.

Google login accepts a Google Identity Services ID token. Its first use creates a
new `Regular` account bound to Google's stable account identifier; later uses
must match that identifier. If the verified email already belongs to a local
password account, the API refuses a silent link and the user signs in with the
original method. Local password login and registration remain available.

## Configuration

Core settings are required. [`.env.example`](.env.example) documents the local
PostgreSQL and Redis connections, JWT lifetimes, rate limits, API prefix, and
allowed CORS origins. The application fails at startup when a required setting
is missing or invalid.

To enable Google sign-in, create a Google OAuth **Web application** client, add
the frontend URL (for example `http://localhost:4200`) as an authorized
JavaScript origin, and set its public client ID as `GOOGLE_CLIENT_ID` in `.env`.
Set the same value as `googleClientId` in the Angular environment. A Google
client secret is not used by this ID-token flow.

## Testing

With PostgreSQL and Redis running, execute:

```bash
.venv/bin/python -m pytest
```

On Windows, use the repository-local interpreter:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use the real services configured in `.env`; records and Redis keys can
remain after a run. Never point the suite at production or valuable data.

## Architecture

```text
app/
|-- api/controllers/   HTTP routes
|-- core/              Configuration, security, middleware, and Redis
|-- data/              Country and timezone records
|-- models/            SQLAlchemy entities
|-- schemas/           Pydantic request and response contracts
|-- services/          Business and data-access logic
`-- main.py            Application startup, middleware, routes, and health checks
```

See [`structures.txt`](structures.txt) for the canonical layout and
[`codebase-docs/_KNOWLEDGE.txt`](codebase-docs/_KNOWLEDGE.txt) for the detailed
authentication, security, and data flows.

## Project Status

This is a work-in-progress learning project, not a production-ready service.
Important limitations include client-selected roles during public registration,
untrusted `X-Forwarded-For` handling, no database migrations, no dedicated test
database, and containers that do not persist data through replacement. Planned
reminders, email, WebSockets, and proxy deployment are not implemented.

## Feedback and Contributing

Feedback and pull requests are welcome. Public issue creation is currently
restricted by the repository settings, so propose fixes through a
[pull request](https://github.com/natthapong-playground/natthapong-back-playground/pulls).
Changes under `app/` or `tests/` must update the matching file in
[`codebase-docs/`](codebase-docs/) and refresh its `LAST-SYNCED` date.

## License

The project's original code and documentation are available under the
[MIT License](LICENSE).
