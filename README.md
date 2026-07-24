# Natthapong Backend Playground

**Status: Work in progress**

A FastAPI backend playground for learning and demonstrating authentication,
authorization, API security, audit logging, rate limiting, and timezone-aware
country clocks.

The executable project in this repository is the backend API. Features mentioned
in planning documents, such as reminders, email delivery, WebSockets, Nginx load
balancing, and a frontend, are not implemented on the current branch.

## Features

- User registration and current-profile retrieval
- OAuth2-compatible form login
- JWT access and refresh tokens
- Refresh-token rotation and Redis-backed token revocation
- Login brute-force protection by email and source IP
- Registration throttling by source IP
- Active-user checks and role-based authorization
- `SuperAdmin`-only audit-log access
- Best-effort audit logging for mutations, failed requests, and audit-log reads
- Authenticated country search and country-code lookup
- DST-aware local times and UTC offsets from IANA timezone data
- Batch clock snapshots calculated from one shared UTC reference time
- Configurable CORS and browser security headers
- PostgreSQL and Redis readiness checks
- Asynchronous API tests with pytest and HTTPX

## Technology

- Python 3.12
- FastAPI and Uvicorn
- Pydantic 2 and pydantic-settings
- SQLAlchemy 2 with asyncpg
- PostgreSQL 15
- Redis 7
- bcrypt and python-jose
- Python `zoneinfo` with `tzdata`
- pytest, pytest-asyncio, and HTTPX
- Docker Compose for local infrastructure

## Architecture

The backend uses a layered structure:

```text
app/
|-- api/
|   |-- controllers/     # HTTP routes
|   `-- dependencies.py  # Database, Redis, authentication, and role dependencies
|-- core/                # Configuration, security, middleware, and Redis client
|-- data/                # Static country and timezone records
|-- models/              # SQLAlchemy entities
|-- schemas/             # Pydantic request and response contracts
|-- services/            # Reusable business and data-access logic
`-- main.py              # Application startup, middleware, routes, and health checks

tests/test_controllers/  # Asynchronous endpoint tests
codebase-docs/           # Plain-text documentation for each source file
structures.txt           # Canonical project-layout blueprint
```

At startup, FastAPI creates missing PostgreSQL tables and verifies Redis
connectivity. The project does not currently include a database migration tool.

## Prerequisites

- 64-bit Python 3.12 (`py -3.12` must work on Windows)
- Docker Desktop, or Docker Engine with the Compose v2 plugin (`docker compose`)
- Available local ports `5432`, `6379`, and `8000`

You can use independently installed PostgreSQL and Redis instead of Docker, but
the setup below uses the included Compose file.

## Quick Start

### Windows (recommended)

Clone the repository and open its folder in Command Prompt or PowerShell:

```bat
git clone https://github.com/natthapong-playground/natthapong-back-playground.git
cd natthapong-back-playground
setup.bat
```

`setup.bat` performs the complete local setup without activating Python or
installing packages globally. It:

- Requires Python 3.12 and Docker Compose v2.
- Creates only the repository-local `.venv` directory.
- Calls `.venv\Scripts\python.exe -m pip` for every package installation.
- Installs and validates `requirements.txt` inside `.venv`.
- Creates `.env` only when it is missing and replaces public placeholders with
  random local values.
- Never overwrites an existing `.env` or incompatible `.venv`.

Start Docker Desktop, then run:

```bat
start.bat
```

`start.bat` verifies `.venv` and `.env`, starts this project's PostgreSQL and
Redis containers, waits for both health checks, and runs Uvicorn from `.venv` at
<http://127.0.0.1:8000>. Press `Ctrl+C` to stop the API. Stop the project
containers without deleting them by running:

```bat
stop.bat
```

The scripts resolve paths from their own location, so they do not create or
modify files outside this repository. Docker still manages the project's
containers through its normal Docker Desktop storage.

### Manual setup (Linux and macOS)

#### 1. Configure the environment

Create a local `.env` from the committed template.

```bash
cp .env.example .env
```

Replace both `POSTGRES_PASSWORD` occurrences with the same private password and
replace `SECRET_KEY` with a strong random value. Generate safe values with:

```bash
python3.12 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not commit or publish `.env`.

#### 2. Create a virtual environment

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

These commands call the local environment's interpreter directly and do not
install into global Python.

#### 3. Start PostgreSQL and Redis

```bash
docker compose up -d --wait --wait-timeout 90 postgres redis
docker compose ps
```

The Compose file starts PostgreSQL and Redis only. FastAPI runs locally in the
next step. Both ports bind to `127.0.0.1`, not every network interface. The
services do not define persistent volumes, so `docker compose down` deletes the
PostgreSQL container and its database contents.

#### 4. Run the API

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Run these commands from the repository root so the application can find `.env`
and `app/data/countries.json`.

## Environment Variables

Every application setting is required. See [`.env.example`](.env.example) for
working local values and comments.

| Variable | Purpose |
| --- | --- |
| `PROJECT_NAME` | FastAPI application and OpenAPI title |
| `API_V1_STR` | Versioned route prefix, normally `/api/v1` |
| `POSTGRES_USER` | PostgreSQL user used by Docker Compose |
| `POSTGRES_PASSWORD` | PostgreSQL password used by Docker Compose |
| `POSTGRES_DB` | PostgreSQL database used by Docker Compose |
| `DATABASE_URL` | Async SQLAlchemy connection URL |
| `REDIS_URL` | Redis connection URL |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT signing algorithm, normally `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh-token lifetime |
| `LOGIN_RATE_LIMIT_MAX_ATTEMPTS` | Failed logins allowed before lockout |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Login counter and lockout lifetime |
| `REGISTER_RATE_LIMIT_MAX_ATTEMPTS` | Registrations allowed per source IP |
| `REGISTER_RATE_LIMIT_WINDOW_SECONDS` | Registration throttle window |
| `ORIGINS_API` | JSON array of allowed CORS origins |

`POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` configure the Compose
container. Ensure that the same credentials are present in `DATABASE_URL`.

The committed `.env.example` intentionally contains public placeholders. The
real `.env` is ignored by Git and excluded from Docker builds.

## API Access

With the example configuration and default Uvicorn port:

- Application: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI JSON: <http://127.0.0.1:8000/api/v1/openapi.json>
- Readiness probe: <http://127.0.0.1:8000/health>

Use Swagger UI for an interactive description of request and response schemas.
Login expects form data, with the user's email in the `username` field. Protected
routes expect `Authorization: Bearer <access-token>`.

## Routes

Paths below assume the default `API_V1_STR=/api/v1`.

| Method | Path | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/` | Public | Welcome message and project name |
| `GET` | `/health` | Public | `200` when PostgreSQL and Redis are reachable; otherwise `503` |
| `POST` | `/api/v1/users/register` | Public | Register with JSON `email`, `password`, and optional `role` |
| `POST` | `/api/v1/login` | Public | Log in with form fields `username` and `password` |
| `POST` | `/api/v1/refresh-token` | Public | Rotate a refresh token and return a new token pair |
| `POST` | `/api/v1/logout` | Bearer token | Revoke the bearer token and an optional refresh token |
| `GET` | `/api/v1/users/myprofile` | Active user | Return the authenticated user |
| `GET` | `/api/v1/audit-logs` | `SuperAdmin` | Filter and paginate recorded API activity |
| `GET` | `/api/v1/countries` | Active user | Search countries by name; supports `search` and `limit` |
| `GET` | `/api/v1/countries/{code}` | Active user | Case-insensitive country-code lookup |
| `GET` | `/api/v1/clock?code=TH,JP` | Active user | Return ordered clock data; unknown codes are omitted |

Supported role values are `Guest`, `Regular`, `Admin`, and `SuperAdmin`.
Country and clock responses use camelCase fields such as `utcOffsetMinutes`,
`localTime`, and `referenceUtc`; user and audit responses use snake_case.

## Testing

Start PostgreSQL and Redis and confirm `.env` points to them before running tests.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Linux or macOS:

```bash
.venv/bin/python -m pytest
```

Run one test module with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_controllers/test_refresh.py
```

Important test behavior:

- Tests use the real PostgreSQL and Redis services configured in `.env`.
- There is no dedicated test database or per-test transaction rollback.
- Created users and audit records remain in PostgreSQL.
- Redis rate-limit and denylist keys can remain until their TTL expires.
- HTTPX does not run the FastAPI lifespan in the current test fixture.
- Never point this test suite at production or valuable development services.

## GitHub Publication Safety

- `.env`, alternate environment files, virtual environments, caches, local
  databases, IDE settings, and `.claude/settings.local.json` are ignored.
- `.dockerignore` uses an allowlist: Docker receives only Python/JSON files from
  `app/`, plus `requirements.txt` and `Dockerfile`.
- The Dockerfile copies `app/` explicitly, so it cannot package the local `.env`,
  `.git`, `.venv`, tests, or machine-local settings.
- `.env.example` contains placeholders only and is safe to publish.

Before every push, inspect exactly what Git will publish:

```bash
git status --short
git diff --check
git ls-files .env .venv venv venv2 .claude/settings.local.json
```

The final command should print nothing. Never use `git add -f` for any of those
paths.

## Security Notes

- Passwords are salted and hashed with bcrypt.
- Application-issued JWTs include expiration, token type, subject, role, and a
  unique `jti` used for revocation.
- Protected routes require access tokens and verify that the user still exists
  and is active.
- Successful refresh rotates and revokes the supplied refresh token.
- Failed-login limits are scoped to lowercased email plus client IP.
- Registration limits are scoped to client IP.
- CORS origins come from `ORIGINS_API`.
- The middleware adds CSP, HSTS, frame, MIME-sniffing, referrer, and permissions
  policy headers to responses returned through the middleware stack.

## Current Limitations

This is a learning project and is not production-ready without additional work:

- Public registration currently lets clients choose any role, including
  `SuperAdmin`.
- Client IP extraction trusts `X-Forwarded-For` without enforcing a trusted
  proxy boundary.
- There are no migrations, administrator provisioning, or administrative user
  management routes.
- User operations are limited to registration and current-profile retrieval.
- SQLAlchemy query logging is enabled with `echo=True`.
- Audit persistence is best-effort and suppresses logging failures.
- Each country has one representative IANA timezone; multi-zone countries are
  not fully modeled.
- Docker Compose has no API service, persistent volumes, or proxy.
- The Docker image still runs as root and installs development dependencies from
  the combined requirements file.
- Reminder scheduling, email, WebSockets, Nginx, and frontend code are planned
  concepts rather than current implementations.

## Documentation

- [`structures.txt`](structures.txt) is the canonical layout blueprint.
- [`codebase-docs/_INDEX.txt`](codebase-docs/_INDEX.txt) explains the per-source
  documentation map and maintenance protocol.
- [`codebase-docs/_KNOWLEDGE.txt`](codebase-docs/_KNOWLEDGE.txt) describes
  cross-cutting architecture, authentication, security, and data flow.
- [`DETAILS.md`](DETAILS.md) contains additional project notes.

Changes under `app/` or `tests/` should include an update to the matching
`codebase-docs/*.txt` file with a refreshed `LAST-SYNCED` date.
