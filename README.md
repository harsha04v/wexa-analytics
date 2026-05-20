# Wexa — Real-Time Analytics & Reporting Platform

A production-grade SaaS analytics platform that allows organizations to ingest event data from multiple sources, visualize metrics through customizable dashboards, and manage teams with role-based access control.

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Next.js 14     │────▶│   FastAPI         │────▶│ PostgreSQL   │
│   (App Router)   │     │   (async)         │     │ (SQLAlchemy  │
│   React 18 + TS  │     │                   │     │  2.0 async)  │
└──────────────────┘     │   Celery Worker   │────▶│              │
                         │   (background)    │     └──────────────┘
                         └────────┬──────────┘
                                  │
                         ┌────────▼──────────┐
                         │     Redis 7       │
                         │ (broker + cache)  │
                         └───────────────────┘
```

**Design Pattern:** Clean Architecture with layered separation  
`Routers → Services → Repositories → Models`  
Dependency injection via FastAPI `Depends()`, async/await throughout.

## Tech Stack

| Layer      | Technology                                          |
|------------|-----------------------------------------------------|
| Frontend   | Next.js 14, React 18, TypeScript, Tailwind CSS      |
| Charts     | Recharts                                            |
| State      | Zustand, TanStack Query v5                          |
| Backend    | FastAPI, Python 3.12, Pydantic v2                   |
| Database   | PostgreSQL 16, SQLAlchemy 2.0 (async + asyncpg)     |
| Migrations | Alembic                                             |
| Task Queue | Celery + Redis                                      |
| Auth       | JWT (python-jose), bcrypt (passlib)                  |
| Testing    | pytest, pytest-asyncio, httpx (async ASGI tests)     |
| Logging    | structlog (structured, with correlation IDs)         |

## Features Implemented

### Authentication & Multi-Tenancy
- Email/password signup and signin with bcrypt hashing
- JWT access tokens (short-lived) + refresh tokens
- Organization creation during signup
- Invite-based team onboarding
- Role hierarchy: Owner → Admin → Analyst → Viewer
- Permission guards via dependency injection
- Organization-level data isolation at the query layer

### Data Ingestion
- REST API for single and batch event ingestion
- CSV file upload with async processing via Celery
- Pydantic schema validation on all events
- API key management (generate, revoke per organization)
- Rate limiting on ingestion endpoints (slowapi)
- Data source tracking

### Dashboards & Visualizations
- Custom dashboards with drag-and-drop widget placement (react-grid-layout)
- Widget types: line charts, bar charts, pie charts, KPI cards, tables
- Configurable time ranges on analytics queries
- Dashboard sharing via public links (read-only)
- Analytics endpoints: time-series, top events, KPI aggregations

## Project Structure

```
wexa/
├── docker-compose.yml          # PostgreSQL + Redis
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app, middleware, exception handlers
│   │   ├── core/               # config, database, security, dependencies
│   │   ├── models/             # SQLAlchemy models (11 tables)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── repositories/       # Database query layer
│   │   ├── services/           # Business logic layer
│   │   ├── routers/            # API endpoints (auth, ingestion, dashboards, health)
│   │   └── tasks/              # Celery background tasks
│   ├── alembic/                # Database migrations
│   ├── tests/                  # pytest async test suite
│   ├── seed.py                 # Demo data seeder
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── app/                # Next.js App Router pages
    │   ├── components/         # React components (WidgetRenderer, AddWidgetModal)
    │   └── lib/                # API client, store, utilities
    ├── package.json
    └── tailwind.config.ts
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Start Infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (port 5432) and Redis (port 6379).

### 2. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://wexa:wexa_dev_password@localhost:5432/wexa
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000"]
```

Run database migrations:

```bash
alembic upgrade head
```

Start the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

Start the Celery worker (separate terminal):

```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### 3. Seed Demo Data (Optional)

```bash
python seed.py
```

Creates demo users, dashboards, and sample events:
- `owner@demo.com` / `password123` (Owner)
- `analyst@demo.com` / `password123` (Analyst)
- `viewer@demo.com` / `password123` (Viewer)

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Running Tests

```bash
cd backend

# Create test database (one-time)
docker exec wexa-postgres-1 psql -U wexa -d wexa -c "CREATE DATABASE wexa_test OWNER wexa"

# Run tests
python -m pytest tests/ -v
```

16 tests covering all three core modules:
- **Auth**: signup, signin, token auth, RBAC enforcement
- **Ingestion**: API keys, event ingestion, CSV upload, data sources
- **Dashboards**: CRUD, widgets, public sharing, analytics

## API Overview

All endpoints are prefixed with `/api/v1`.

| Group        | Endpoint                        | Auth         | Description                  |
|--------------|---------------------------------|--------------|------------------------------|
| Auth         | `POST /auth/signup`             | Public       | Register + create org        |
| Auth         | `POST /auth/signin`             | Public       | Login                        |
| Auth         | `GET /auth/me`                  | JWT          | Current user profile         |
| Auth         | `POST /auth/invite`             | JWT + RBAC   | Invite team member           |
| Ingestion    | `POST /ingestion/events/single` | API Key      | Ingest single event          |
| Ingestion    | `POST /ingestion/events/batch`  | API Key      | Ingest event batch           |
| Ingestion    | `POST /ingestion/upload-csv`    | JWT          | Upload CSV file              |
| Ingestion    | `POST /ingestion/api-keys`      | JWT + RBAC   | Create API key               |
| Dashboards   | `POST /dashboards`              | JWT + RBAC   | Create dashboard             |
| Dashboards   | `GET /dashboards`               | JWT          | List dashboards              |
| Dashboards   | `POST /dashboards/{id}/widgets` | JWT + RBAC   | Add widget                   |
| Dashboards   | `GET /dashboards/public/{token}`| Public       | View shared dashboard        |
| Analytics    | `GET /dashboards/analytics/*`   | JWT          | Time-series, KPI, top events |
| Health       | `GET /health`                   | Public       | Health check                 |

## Environment Variables

| Variable                     | Description                     | Default       |
|------------------------------|---------------------------------|---------------|
| `DATABASE_URL`               | PostgreSQL connection string    | —             |
| `REDIS_URL`                  | Redis connection string         | —             |
| `SECRET_KEY`                 | JWT signing key                 | —             |
| `ALGORITHM`                  | JWT algorithm                   | `HS256`       |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Access token TTL                | `30`          |
| `REFRESH_TOKEN_EXPIRE_DAYS`  | Refresh token TTL               | `7`           |
| `CORS_ORIGINS`               | Allowed frontend origins (JSON) | `["http://localhost:3000"]` |

## Deployment

The project is fully deployment-ready with a Render Blueprint (`render.yaml`) included. It defines all five services (API, frontend, worker, PostgreSQL, Redis) as infrastructure-as-code. To deploy:

```bash
# On Render: New → Blueprint → Connect this repo → Apply
```

The backend also includes:
- `async_database_url` config property that auto-converts `postgres://` → `postgresql+asyncpg://` for cloud providers
- Alembic migrations run automatically on deploy via `alembic upgrade head`
- Celery worker configured as a separate background service
- CORS and API URL configured via environment variables
