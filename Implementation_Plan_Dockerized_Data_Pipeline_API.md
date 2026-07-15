# Implementation Plan: Dockerized Data Pipeline API
### FastAPI + PostgreSQL + Redis + Pandas + Docker Compose

This is a **step-by-step, no-step-skipped** plan. Follow it top to bottom. Every big task is broken into small tasks. Simple language is used everywhere so it is easy to follow even if you are doing this for the first time.

---

## 0. How This Plan Is Organized

1. **Phase 0** – Before you write any code (planning, folder setup, Git setup)
2. **Phase 1** – Docker & environment configuration (Dockerfile, docker-compose, .env)
3. **Phase 2** – Database design (PostgreSQL schema)
4. **Phase 3** – Redis setup and caching strategy
5. **Phase 4** – FastAPI application skeleton
6. **Phase 5** – Pydantic models (data validation schemas)
7. **Phase 6** – Pandas data-cleaning pipeline
8. **Phase 7** – Building each endpoint one by one
9. **Phase 8** – Caching logic wiring (Redis + 5 min TTL)
10. **Phase 9** – Error handling & status codes
11. **Phase 10** – Testing (pytest) — 10+ tests
12. **Phase 11** – README + documentation
13. **Phase 12** – Git commit strategy (10+ meaningful commits)
14. **Phase 13** – Final verification checklist mapped to evaluation criteria
15. **Phase 14** – Suggested time schedule (09:00–17:00 with 12:30 and 15:30 check-ins)

---

## PHASE 0 — Planning & Project Setup (Do this first, before writing code)

### 0.1 Understand what we are building (in simple words)
We are building a small web service (an API) that:
- Lets someone **upload a CSV file** of employee/company data (e.g. name, department, salary, hire date, status).
- **Cleans** that data using Pandas (fixes missing values, wrong types, duplicate rows).
- **Saves** the cleaned data into a PostgreSQL database (a permanent storage).
- Lets people **read back** the data (single record, or a list with filters and pages).
- Provides **analytics** (summary numbers, trends over time) computed using Pandas.
- **Caches** the analytics answers in Redis for 5 minutes so we don't recompute them every time (faster + cheaper).
- Everything runs inside **Docker containers** so it works the same on any machine, started with one command: `docker compose up`.

### 0.2 Create the project folder locally
```bash
mkdir data-pipeline-api
cd data-pipeline-api
```

### 0.3 Initialize Git immediately (before any code)
```bash
git init
git branch -M main
```
Create a `.gitignore` file right away (this is Commit #1 material):
```
__pycache__/
*.pyc
.env
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
postgres_data/
redis_data/
.DS_Store
uploads/*.csv
!uploads/.gitkeep
```

### 0.4 Decide the final folder structure (keep it simple for this mini-project)
```
data-pipeline-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entrypoint
│   ├── config.py               # Environment variables
│   ├── database.py             # SQLAlchemy engine/session/Base
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic models
│   ├── data_processing.py      # Pandas cleaning & analytics
│   ├── redis_client.py         # Redis connection and cache helpers
│   └── routers.py              # All API endpoints
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_upload.py
│   ├── test_records.py
│   ├── test_analytics.py
│   └── test_health.py
│
├── uploads/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .env
├── .dockerignore
├── .gitignore
├── sample_data.csv
└── README.md
```

### 0.5 Decide the CSV schema (the columns we expect the uploaded CSV to have)
Write this down clearly so Pydantic + Pandas cleaning logic matches:

| Column name    | Type            | Notes                                    |
|----------------|-----------------|-------------------------------------------|
| employee_id    | integer (optional, auto if missing) | unique per row |
| name           | string          | required, non-empty                       |
| department     | string           | required (e.g. Engineering, Sales, HR)   |
| salary         | float            | required, must be >= 0                    |
| hire_date      | date (YYYY-MM-DD)| required, used for trends                |
| status         | string           | one of: active, inactive, terminated     |

This becomes the contract used across Pydantic schemas, Pandas cleaning, and the DB table.

### 0.6 List all the tools/versions you will use (decide now, write in README later)
- Python 3.12 (slim)
- FastAPI (latest 0.11x)
- Uvicorn (ASGI server)
- SQLAlchemy 2.x (ORM)
- psycopg2-binary or psycopg (Postgres driver)
- Pandas 2.x
- Redis-py (Python Redis client)
- PostgreSQL 16 (Docker image `postgres:16`)
- Redis 7 (Docker image `redis:7-alpine`)
- pytest, pytest-asyncio, httpx (for FastAPI TestClient), pytest-cov

### 0.7 Debugging, readability, and error-handling expectations
- Use the VS Code debugger while developing the API and tests.
- Create a `.vscode/launch.json` file for debugging the FastAPI app and pytest tests.
- Add `try/except` blocks wherever input parsing, file handling, database access, Redis access, or external service calls can fail.
- Catch errors early and return clear messages instead of letting the app crash silently.
- Use meaningful exception messages for CSV parsing issues, missing columns, invalid data, and database/Redis connection failures.
- Write simple, beginner-friendly code. Avoid over-engineering or unnecessary abstractions.
- Keep functions short and focused. Each function should do one clear job.
- Add comments inside the code to explain what each function does, especially for Pandas cleaning and analytics logic.
- Prefer readable variable names such as `cleaned_df`, `rows_inserted`, and `cache_key`.
- Keep the implementation easy to follow for someone learning FastAPI, SQLAlchemy, Pandas, and Docker together.

---

## PHASE 1 — Docker & Environment Configuration

### 1.1 Write `requirements.txt` (production dependencies)
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
pandas==2.2.2
redis==5.0.8
python-multipart==0.0.9
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
```

### 1.2 Write `requirements-dev.txt` (only needed for testing/dev, not in the slim final image)
```
-r requirements.txt
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
pytest-cov==5.0.0
faker==28.4.1
```

### 1.3 Write the multi-stage `Dockerfile`
Step-by-step logic:
1. **Stage 1 (builder)**: use a full Python image, install build tools, install Python packages into a virtual environment or a local wheel cache. This keeps compile-time junk out of the final image.
2. **Stage 2 (runtime)**: use `python:3.12-slim`, copy only the installed packages and app code from the builder stage, run as a non-root user, expose port, set the start command.

```dockerfile
# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install OS packages needed to compile some Python packages (e.g. psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (this enables Docker layer caching -
# if requirements don't change, this layer is reused = faster builds)
COPY requirements.txt .

# Install dependencies into an isolated location we can copy later
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /code

# Install only the runtime OS library needed by psycopg2 (not the -dev/compiler version)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY ./app ./app
COPY sample_data.csv ./sample_data.csv

# Create a non-root user for security best practice
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Basic healthcheck so `docker ps` shows container health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Small tasks inside this step:**
- [ ] Create the file `Dockerfile` in project root.
- [ ] Confirm `libpq-dev` is only in builder stage (compiler headers), `libpq5` only in runtime (shared library) — this keeps final image slim.
- [ ] Add `.dockerignore` (see 1.4) so build context is small and fast.
- [ ] Test build alone first: `docker build -t data-pipeline-api:test .`
- [ ] Check final image size: `docker images | grep data-pipeline-api` (should be well under 300MB).

### 1.4 Write `.dockerignore`
```
__pycache__
*.pyc
.git
.gitignore
.env
.venv
venv
tests
.pytest_cache
htmlcov
.coverage
README.md
```

### 1.5 Write `.env.example` (commit this) and `.env` (do NOT commit this — real values)
```
# --- App ---
API_PORT=8000
ENVIRONMENT=development

# --- PostgreSQL ---
POSTGRES_USER=pipeline_user
POSTGRES_PASSWORD=pipeline_pass
POSTGRES_DB=pipeline_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://pipeline_user:pipeline_pass@db:5432/pipeline_db

# --- Redis ---
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
CACHE_TTL_SECONDS=300
```
Copy it to make your real working `.env`:
```bash
cp .env.example .env
```

### 1.6 Write `docker-compose.yml` (the main orchestration file)

Small tasks/thinking before writing it:
- We need **3 services**: `app` (FastAPI), `db` (Postgres), `redis` (Redis).
- We need a **shared network** so containers can talk to each other by service name (`db`, `redis`).
- We need **named volumes** so Postgres data (and optionally Redis data) survive container restarts.
- `app` should **wait for db/redis to be healthy** before starting (use `depends_on` with `condition: service_healthy`).
- For **hot reload in dev**, bind-mount the `./app` folder into the container and run uvicorn with `--reload`.

```yaml
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pipeline_app
    env_file:
      - .env
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./app:/code/app          # bind mount for hot reload during dev
      - ./sample_data.csv:/code/sample_data.csv
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - pipeline_net
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped

  db:
    image: postgres:16
    container_name: pipeline_db
    env_file:
      - .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - pipeline_net
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: pipeline_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - pipeline_net
    restart: unless-stopped

networks:
  pipeline_net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

**Small tasks inside this step:**
- [ ] Create `docker-compose.yml` in project root.
- [ ] Double check indentation (YAML is whitespace-sensitive).
- [ ] Run `docker compose config` to validate the file parses correctly before starting anything.
- [ ] Run `docker compose up --build` and confirm all 3 containers report healthy (`docker compose ps`).
- [ ] Confirm `app` container logs show Uvicorn running on `0.0.0.0:8000`.
- [ ] Open `http://localhost:8000/docs` in a browser to see FastAPI's auto Swagger UI (even before endpoints are built, base app should load).

### 1.7 (Optional but recommended) Separate dev vs prod compose
Create `docker-compose.override.yml` (auto-merged by Docker Compose when present) to hold dev-only settings like the bind mount and `--reload` flag, so a "prod" version of `docker-compose.yml` can stay clean. Since the brief asks for hot-reload by default, the plan above already includes it directly in the main file — this step is optional polish.

---

## PHASE 2 — Database Design (PostgreSQL)

### 2.1 Design the table schema (map directly to the CSV schema from 0.5)
Table name: `records`

| Column        | Type              | Constraints                          |
|---------------|-------------------|----------------------------------------|
| id            | Integer            | Primary key, autoincrement            |
| employee_id   | Integer            | unique, indexed                        |
| name          | String(255)         | not null                              |
| department    | String(100)        | not null, indexed (used for filtering)|
| salary        | Float               | not null, check >= 0                  |
| hire_date     | Date                | not null, indexed (used for trends)   |
| status        | String(20)          | not null, indexed (used for filtering)|
| created_at    | DateTime            | default now(), server-side timestamp  |
| updated_at    | DateTime            | default now(), on update now()        |

### 2.2 Write `app/database.py`
Small tasks:
- [ ] Create SQLAlchemy `engine` using `DATABASE_URL` from settings.
- [ ] Create `SessionLocal` (sessionmaker).
- [ ] Create `Base = declarative_base()`.
- [ ] Create a `get_db()` FastAPI dependency (yields a session, closes it after request).
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2.3 Write `app/models.py` (the ORM table definition)
```python
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func
from app.database import Base

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False, index=True)
    salary = Column(Float, nullable=False)
    hire_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 2.4 Decide table creation strategy
Two options — pick one and write it down:
- **Simple (recommended for this project's scope)**: call `Base.metadata.create_all(bind=engine)` on FastAPI startup event. Easiest, works well for a mini-project.
- **Production-grade (optional stretch)**: use Alembic migrations. Mention as a "future improvement" in README if skipped, to show awareness.

Small tasks:
- [ ] Add a FastAPI `startup` event (or lifespan handler) in `main.py` that calls `Base.metadata.create_all(bind=engine)`.
- [ ] Verify by running `docker compose exec db psql -U pipeline_user -d pipeline_db -c '\dt'` and confirming the `records` table exists after the app starts.

### 2.5 Write `app/config.py` (centralized settings using pydantic-settings)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    REDIS_URL: str
    CACHE_TTL_SECONDS: int = 300

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## PHASE 3 — Redis Setup & Caching Strategy

### 3.1 Write `app/redis_client.py`
Small tasks:
- [ ] Create a Redis connection using `redis.from_url(settings.REDIS_URL)`.
- [ ] Write a helper `get_cache(key)` that returns parsed JSON or `None`.
- [ ] Write a helper `set_cache(key, value, ttl=None)` that JSON-serializes and stores with expiry.
- [ ] Write a helper `ping_redis()` used by the `/health` endpoint.
```python
import json
import redis
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache(key: str):
    data = redis_client.get(key)
    if data is None:
        return None
    return json.loads(data)

def set_cache(key: str, value, ttl: int = None):
    ttl = ttl or settings.CACHE_TTL_SECONDS
    redis_client.set(key, json.dumps(value, default=str), ex=ttl)

def invalidate_cache(pattern: str = "analytics:*"):
    """Delete all cached analytics keys, e.g. after a new upload."""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

def ping_redis() -> bool:
    try:
        return redis_client.ping()
    except Exception:
        return False
```

### 3.2 Decide the cache key naming convention (write this down clearly)
- `analytics:summary` → cached result of `/analytics/summary`
- `analytics:trends:monthly` → cached result of `/analytics/trends?interval=month`
- `analytics:trends:quarterly` → cached result of `/analytics/trends?interval=quarter`

### 3.3 Decide cache invalidation rule
- Whenever a new CSV is uploaded (`POST /data/upload` succeeds), call `invalidate_cache("analytics:*")` so stale analytics aren't served after new data arrives. This is important — write it as a specific small task:
  - [ ] In `upload.py`, after successfully committing new records to DB, call `invalidate_cache()`.

### 3.4 Decide cache TTL
- 5 minutes = 300 seconds, matches `CACHE_TTL_SECONDS` in `.env`. Confirmed already in config.

---

## PHASE 4 — FastAPI Application Skeleton

### 4.1 Write `app/main.py`
Small tasks:
- [ ] Import FastAPI, create `app = FastAPI(title="Data Pipeline API", version="1.0.0")`.
- [ ] Add a `lifespan` (or `@app.on_event("startup")`) that creates DB tables.
- [ ] Include all routers (`upload`, `records`, `analytics`, `health`).
- [ ] Add root `/` endpoint returning a friendly welcome message + link to `/docs`.
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.routers import upload, records, analytics, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Data Pipeline API",
    description="Ingests CSV/JSON data, processes with Pandas, serves analytics",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["Health"])
app.include_router(upload.router, prefix="/data", tags=["Upload"])
app.include_router(records.router, prefix="/data", tags=["Records"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "Data Pipeline API is running. Visit /docs for API documentation."}
```

### 4.2 Create empty router files first (so imports don't break), then fill in later phases
- [ ] `app/routers/__init__.py` (empty)
- [ ] `app/routers/health.py`
- [ ] `app/routers/upload.py`
- [ ] `app/routers/records.py`
- [ ] `app/routers/analytics.py`

### 4.3 Sanity check after skeleton
- [ ] Run `docker compose up --build`.
- [ ] Visit `/docs`, confirm the base route and health tag show up even with stub implementations.

---

## PHASE 5 — Pydantic Schemas (`app/schemas.py`)

Small tasks — define one schema class per use case:

### 5.1 Input schema for a single record (used internally after CSV parsing)
```python
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class RecordBase(BaseModel):
    employee_id: int
    name: str = Field(..., min_length=1)
    department: str = Field(..., min_length=1)
    salary: float = Field(..., ge=0)
    hire_date: date
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"active", "inactive", "terminated"}
        if v.lower() not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v.lower()
```

### 5.2 Output schema for a single record (response model)
```python
class RecordOut(RecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 5.3 Paginated list response schema
```python
class PaginatedRecords(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[RecordOut]
```

### 5.4 Upload response schema
```python
class UploadResponse(BaseModel):
    message: str
    rows_received: int
    rows_inserted: int
    rows_skipped_duplicates: int
    rows_failed_validation: int
```

### 5.5 Analytics summary schema
```python
class DepartmentSummary(BaseModel):
    department: str
    headcount: int
    avg_salary: float
    total_spend: float

class SummaryResponse(BaseModel):
    departments: List[DepartmentSummary]
    company_headcount: int
    company_avg_salary: float
    company_total_spend: float
    cached: bool
```

### 5.6 Analytics trends schema
```python
class TrendPoint(BaseModel):
    period: str          # e.g. "2025-01" or "2025-Q1"
    hires: int

class TrendsResponse(BaseModel):
    interval: str         # "month" or "quarter"
    trends: List[TrendPoint]
    cached: bool
```

### 5.7 Health check schema
```python
class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
```

### 5.8 Error schema (for consistent error responses)
```python
class ErrorResponse(BaseModel):
    detail: str
```

---

## PHASE 6 — Pandas Data-Cleaning Pipeline (`app/data_processing.py`)

This is the heart of the "process with Pandas" requirement. Break it into small, testable functions.

### 6.1 Function: `read_csv_to_dataframe(file_bytes) -> pd.DataFrame`
Small tasks:
- [ ] Use `pd.read_csv(io.BytesIO(file_bytes))`.
- [ ] Wrap in try/except — if the file isn't valid CSV, raise a clear `ValueError`.

### 6.2 Function: `clean_dataframe(df) -> tuple[pd.DataFrame, dict]`
Break the cleaning into these exact sub-steps (do each one, in this order):
1. **Standardize column names**: lowercase, strip spaces, replace spaces with underscores.
   - [ ] `df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")`
2. **Check required columns exist**: `{employee_id, name, department, salary, hire_date, status}`. If any are missing, raise a validation error listing which ones.
3. **Handle missing values**:
   - [ ] Drop rows where `name` or `department` is null (can't guess these).
   - [ ] Fill missing `salary` with the department's median salary (a good default), or 0 if department itself unknown at that point — document this choice in code comments.
   - [ ] Fill missing `status` with `"active"` as a safe default.
   - [ ] Track how many rows were affected by each fill for the response summary.
4. **Type conversions**:
   - [ ] Convert `employee_id` to nullable integer type: `pd.to_numeric(df["employee_id"], errors="coerce").astype("Int64")`.
   - [ ] Convert `salary` to float: `pd.to_numeric(df["salary"], errors="coerce")`.
   - [ ] Convert `hire_date` to datetime: `pd.to_datetime(df["hire_date"], errors="coerce")`; rows that fail to parse become `NaT` and should be flagged as validation failures, then dropped.
   - [ ] Lowercase and strip `status` and `department` strings.
5. **Duplicate detection**:
   - [ ] Detect duplicate `employee_id` values **within the uploaded file** using `df.duplicated(subset=["employee_id"], keep="first")`. Keep the first, drop the rest, but count them.
   - [ ] Duplicate rows against rows **already in the database** are checked later at insert time (see 6.4), since that requires querying the DB, not just the DataFrame.
6. **Drop invalid rows**:
   - [ ] Any row where `employee_id` is null (failed numeric conversion) → drop, count as "failed validation".
   - [ ] Any row where `hire_date` is `NaT` → drop, count as "failed validation".
   - [ ] Any row where `salary` < 0 → drop, count as "failed validation".
   - [ ] Any row where `status` not in `{active, inactive, terminated}` → drop, count as "failed validation".
7. **Return** the cleaned DataFrame plus a small dict of stats: `{rows_received, rows_after_cleaning, duplicates_dropped, failed_validation}`.

### 6.3 Function: `dataframe_to_records(df) -> list[dict]`
- [ ] Convert cleaned DataFrame rows into plain Python dicts ready for building SQLAlchemy `Record` objects (or Pydantic `RecordBase` objects for a final validation pass before DB insert).

### 6.4 Function used inside the upload router: `insert_records(db, records) -> tuple[int, int]`
- [ ] For each record dict, check whether `employee_id` already exists in the DB (`db.query(Record).filter_by(employee_id=...).first()`).
- [ ] If it exists, skip and count as a duplicate-against-DB.
- [ ] If not, create the `Record` ORM object and add to session.
- [ ] Bulk commit at the end (`db.commit()`) rather than committing per-row, for performance.
- [ ] Return `(rows_inserted, rows_skipped_duplicates)`.

### 6.5 Function: `compute_summary(db) -> dict` (used by `/analytics/summary`)
Small tasks:
- [ ] Query all records from DB into a DataFrame: `pd.read_sql(db.query(Record).statement, db.bind)` (or fetch via SQLAlchemy and build DataFrame manually).
- [ ] Group by department: `df.groupby("department").agg(headcount=("id","count"), avg_salary=("salary","mean"), total_spend=("salary","sum"))`.
- [ ] Round `avg_salary` and `total_spend` to 2 decimal places.
- [ ] Compute company-wide totals across all rows (not grouped).
- [ ] Return a dict shaped like `SummaryResponse`.

### 6.6 Function: `compute_trends(db, interval="month") -> list[dict]` (used by `/analytics/trends`)
Small tasks:
- [ ] Load all records into a DataFrame, ensure `hire_date` is a proper `datetime64` column.
- [ ] Set `hire_date` as the DataFrame index: `df.set_index("hire_date", inplace=True)`.
- [ ] If `interval == "month"`: `df.resample("ME").size()` (counts hires per month).
- [ ] If `interval == "quarter"`: `df.resample("QE").size()` (counts hires per quarter).
- [ ] Format the period label nicely:
  - Month → `"2025-01"` via `.strftime("%Y-%m")`
  - Quarter → `"2025-Q1"` via `.to_period("Q").astype(str)`
- [ ] Sort chronologically (resample already returns sorted, but double check).
- [ ] Return list of `{period, hires}` dicts.

### 6.7 Edge cases to handle explicitly in this phase (write tests for these later)
- [ ] Empty CSV file (0 data rows) → should not crash; summary/trends should return empty gracefully.
- [ ] CSV with extra unexpected columns → should be ignored, not cause failure.
- [ ] CSV with all rows invalid → response should say `rows_inserted: 0` with a clear count of failures, not a 500 error.
- [ ] Non-CSV file uploaded (e.g. .txt or .png) → should return HTTP 400 with a clear error message.

---

## PHASE 7 — Building Each Endpoint (one by one)

### 7.1 `GET /health` (`app/routers/health.py`)
Small tasks:
- [ ] Import `get_db`, `ping_redis`.
- [ ] Try a trivial DB query (`db.execute(text("SELECT 1"))`) inside try/except to check DB connectivity.
- [ ] Call `ping_redis()` to check Redis connectivity.
- [ ] Return `HealthResponse(status="ok" or "degraded", database="up"/"down", redis="up"/"down")`.
- [ ] Return HTTP 200 if both up, HTTP 503 if either is down.
```python
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.redis_client import ping_redis
from app.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(response: Response, db: Session = Depends(get_db)):
    db_status = "up"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    redis_status = "up" if ping_redis() else "down"

    overall = "ok" if db_status == "up" and redis_status == "up" else "degraded"
    if overall != "ok":
        response.status_code = 503

    return HealthResponse(status=overall, database=db_status, redis=redis_status)
```

### 7.2 `POST /data/upload` (`app/routers/upload.py`)
Small tasks:
- [ ] Accept `UploadFile` via `python-multipart` (`file: UploadFile = File(...)`).
- [ ] Validate file extension is `.csv` (reject others with HTTP 400).
- [ ] Read file bytes: `contents = await file.read()`.
- [ ] Call `read_csv_to_dataframe(contents)` — catch parse errors → HTTP 400.
- [ ] Call `clean_dataframe(df)` — get cleaned df + stats dict.
- [ ] Convert to records, validate each with `RecordBase` Pydantic schema as a final safety net.
- [ ] Call `insert_records(db, records)`.
- [ ] Call `invalidate_cache()` so analytics recompute fresh next time.
- [ ] Return `UploadResponse` with full counts (received, inserted, duplicates skipped, failed validation).
- [ ] Return HTTP 201 on success (even partial success, e.g. some rows failed but some succeeded) — but if literally everything failed, consider still 201 with counts showing zero inserted, unless the file was structurally invalid (missing required columns), which should be HTTP 400.

### 7.3 `GET /data` (`app/routers/records.py`)
Small tasks:
- [ ] Query params: `page: int = 1`, `per_page: int = 20`, `department: Optional[str] = None`, `status: Optional[str] = None`.
- [ ] Validate `page >= 1` and `1 <= per_page <= 100` (use FastAPI `Query(..., ge=1)` etc.) — return HTTP 422 automatically via Pydantic/FastAPI validation if violated.
- [ ] Build SQLAlchemy query, apply `.filter(Record.department == department)` if provided, same for `status`.
- [ ] Get `total = query.count()`.
- [ ] Apply `.offset((page-1)*per_page).limit(per_page)`.
- [ ] Compute `total_pages = ceil(total / per_page)`.
- [ ] Return `PaginatedRecords`.

### 7.4 `GET /data/{id}` (`app/routers/records.py`)
Small tasks:
- [ ] Query `Record` by primary key `id`.
- [ ] If not found → raise `HTTPException(status_code=404, detail="Record not found")`.
- [ ] If found → return `RecordOut`.

### 7.5 `GET /analytics/summary` (`app/routers/analytics.py`)
Small tasks:
- [ ] Check Redis cache key `"analytics:summary"` first via `get_cache()`.
- [ ] If cache hit → return cached data with `cached=True`.
- [ ] If cache miss → call `compute_summary(db)`, store result via `set_cache("analytics:summary", result)`, return with `cached=False`.

### 7.6 `GET /analytics/trends` (`app/routers/analytics.py`)
Small tasks:
- [ ] Query param `interval: str = Query("month", pattern="^(month|quarter)$")` — invalid values auto-rejected with HTTP 422.
- [ ] Cache key becomes `f"analytics:trends:{interval}"`.
- [ ] Same cache-check-then-compute-then-store pattern as 7.5.
- [ ] Call `compute_trends(db, interval)`.

### 7.7 After building all endpoints — manual smoke test checklist
- [ ] `docker compose up --build`
- [ ] Open `/docs`, use the Swagger UI to manually upload `sample_data.csv`.
- [ ] Call `GET /data` and confirm pagination works.
- [ ] Call `GET /data/1` and confirm single record works; call `GET /data/99999` and confirm 404.
- [ ] Call `GET /analytics/summary` twice in a row — second call should show `cached: true` and be noticeably faster.
- [ ] Call `GET /analytics/trends?interval=month` and `?interval=quarter`.
- [ ] Call `GET /health` and confirm `status: ok`.
- [ ] Stop the Redis container (`docker compose stop redis`) and call `/health` again — should show `redis: down`, `status: degraded`, HTTP 503. Then restart Redis.

---

## PHASE 8 — Wiring Caching End-to-End (recap / consolidation)

This phase is really "double-check phase" since caching code was written inline above. Confirm these specific behaviors:
- [ ] Analytics endpoints check cache BEFORE querying Postgres/Pandas.
- [ ] Analytics endpoints write to cache AFTER computing, with TTL from `.env` (`CACHE_TTL_SECONDS=300`).
- [ ] Upload endpoint invalidates all `analytics:*` keys after a successful insert.
- [ ] `cached` boolean field in the response accurately reflects whether Redis served it.
- [ ] Manually verify TTL: call `/analytics/summary`, then run `docker compose exec redis redis-cli TTL analytics:summary` — should show a number close to 300, counting down.

---

## PHASE 9 — Error Handling & Status Codes (consolidated checklist)

Go through every endpoint and confirm the right HTTP status code:

| Situation                                   | Expected Status |
|----------------------------------------------|------------------|
| Successful GET                                | 200              |
| Successful POST /data/upload                  | 201              |
| Invalid/non-CSV file uploaded                  | 400              |
| CSV missing required columns                   | 400              |
| Record not found (`GET /data/{id}`)            | 404              |
| Invalid query params (bad page/per_page/interval) | 422           |
| DB or Redis down (`/health`)                    | 503            |
| Unexpected server error                          | 500 (with generic message, no stack trace leaked) |

Small tasks:
- [ ] Add a global exception handler in `main.py` for unhandled exceptions, returning a clean JSON error instead of leaking tracebacks:
```python
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```
- [ ] Confirm FastAPI's default validation errors (422) already work out of the box for bad query params — no extra code needed, just verify via `/docs`.

---

## PHASE 10 — Testing (pytest) — Minimum 10 Tests

### 10.1 Test infrastructure setup — `tests/conftest.py`
Small tasks:
- [ ] Use a **separate test database** (either SQLite in-memory for speed, or a second Postgres DB via docker-compose test override) — for simplicity in a mini-project, SQLite in-memory is acceptable and fast; note in README that Postgres is used for integration/manual testing and SQLite for fast unit tests, OR spin a dedicated `test_db` service. Pick one approach and be consistent.
- [ ] Override the `get_db` dependency in FastAPI's `app.dependency_overrides` to point to the test session.
- [ ] Create a pytest fixture `client` that returns a `TestClient(app)`.
- [ ] Create a pytest fixture `db_session` that creates all tables before each test and drops them after (clean slate per test).
- [ ] Create a fixture `sample_csv_bytes` that builds a small in-memory CSV for upload tests.

```python
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def sample_csv_bytes():
    csv_content = (
        "employee_id,name,department,salary,hire_date,status\n"
        "1,Alice Smith,Engineering,90000,2024-01-15,active\n"
        "2,Bob Jones,Sales,60000,2024-02-20,active\n"
        "3,Carol Lee,Engineering,95000,2024-03-05,inactive\n"
    )
    return io.BytesIO(csv_content.encode("utf-8"))
```
Note: since Redis is also a dependency, either (a) mock `redis_client` functions in tests using `unittest.mock.patch`, or (b) point tests at a real Redis test container. For a mini-project, mocking is simpler and faster — small task:
- [ ] Add a fixture that monkeypatches `get_cache` to always return `None` and `set_cache`/`invalidate_cache` to no-ops, unless a specific test is checking caching behavior directly (in which case use `fakeredis` package as a lightweight alternative).

### 10.2 `tests/test_health.py` (2 tests)
- [ ] **Test 1**: `test_health_check_returns_ok` — call `GET /health`, assert status 200, assert `status == "ok"` (with DB/Redis mocked as up).
- [ ] **Test 2**: `test_health_check_reports_down_dependency` — mock Redis ping to fail, call `/health`, assert status 503 and `redis == "down"`.

### 10.3 `tests/test_upload.py` (4 tests)
- [ ] **Test 3**: `test_upload_valid_csv_success` — upload `sample_csv_bytes`, assert status 201, assert `rows_inserted == 3`.
- [ ] **Test 4**: `test_upload_rejects_non_csv_file` — upload a `.txt` file, assert status 400.
- [ ] **Test 5**: `test_upload_handles_missing_required_column` — upload CSV missing the `salary` column, assert status 400 with a clear message.
- [ ] **Test 6**: `test_upload_deduplicates_existing_employee_ids` — upload the same CSV twice, assert second upload's `rows_skipped_duplicates == 3` and `rows_inserted == 0`.

### 10.4 `tests/test_records.py` (5 tests)
- [ ] **Test 7**: `test_get_data_returns_paginated_list` — upload sample data first, then `GET /data?page=1&per_page=2`, assert `len(data["data"]) == 2` and `total == 3`.
- [ ] **Test 8**: `test_get_data_filters_by_department` — `GET /data?department=Engineering`, assert all returned rows have `department == "Engineering"` and count is 2.
- [ ] **Test 9**: `test_get_data_filters_by_status` — `GET /data?status=inactive`, assert count is 1.
- [ ] **Test 10**: `test_get_single_record_by_id_success` — `GET /data/1`, assert status 200, assert correct `name`.
- [ ] **Test 11**: `test_get_single_record_not_found` — `GET /data/9999`, assert status 404.

### 10.5 `tests/test_analytics.py` (3 tests)
- [ ] **Test 12**: `test_analytics_summary_computes_correct_headcount_and_avg` — upload sample data, `GET /analytics/summary`, assert `company_headcount == 3`, assert Engineering `avg_salary` is correctly averaged `(90000+95000)/2`.
- [ ] **Test 13**: `test_analytics_summary_is_cached_on_second_call` — call summary twice, assert first call `cached == False`, second call `cached == True` (requires real or fake Redis in this specific test, using `fakeredis`).
- [ ] **Test 14**: `test_analytics_trends_monthly_grouping` — `GET /analytics/trends?interval=month`, assert returned periods match `2024-01, 2024-02, 2024-03` each with `hires == 1`.

**Total: 14 tests** — comfortably above the 10-test minimum, covering happy paths, filters, pagination, not-found, bad input, duplicates, and caching.

### 10.6 Run tests and check coverage
```bash
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=term-missing
```
Small tasks:
- [ ] All tests pass locally before committing.
- [ ] Aim for reasonable coverage on `data_processing.py` and routers (this is what graders check under "good coverage of happy paths and errors").
- [ ] Add a `pytest.ini` or `pyproject.toml` section to configure test discovery paths cleanly:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

---

## PHASE 11 — Documentation (`README.md`)

### 11.1 README structure to write (in this exact order)
1. **Project Title & one-line description**
2. **Features list** (bullet points matching the brief's requirements)
3. **Architecture Diagram (text-based)** — example:
```
                ┌─────────────┐
   CSV Upload → │   FastAPI    │ ← REST clients (curl / browser / Postman)
                │  (app/main)  │
                └──────┬───────┘
             ┌──────────┼───────────┐
             ▼                      ▼
     ┌───────────────┐      ┌───────────────┐
     │  PostgreSQL 16  │      │   Redis 7      │
     │  (records table)│      │ (analytics cache,│
     │                  │      │  5 min TTL)     │
     └───────────────┘      └───────────────┘
             ▲
             │  Pandas cleaning + analytics
             │  (data_processing.py)
             └── runs inside the FastAPI app process
```
4. **Tech Stack** (list versions: FastAPI, PostgreSQL 16, Redis 7, Pandas, SQLAlchemy, Docker Compose)
5. **Prerequisites** (Docker + Docker Compose installed; no local Python needed since everything runs in containers)
6. **Setup Instructions** — exact commands:
```bash
git clone <repo-url>
cd data-pipeline-api
cp .env.example .env
docker compose up --build
```
7. **How to test the API**:
   - Visit `http://localhost:8000/docs` for interactive Swagger UI.
   - Example `curl` commands for each endpoint (upload, list, single record, summary, trends, health).
8. **Running Tests**:
```bash
docker compose exec app pip install -r requirements-dev.txt
docker compose exec app pytest -v --cov=app
```
   (or explain running tests locally outside Docker as an alternative)
9. **Environment Variables table** (mirror `.env.example` with descriptions)
10. **CSV Format Expected** (mirror the table from step 0.5, include a link/reference to `sample_data.csv`)
11. **API Endpoint Reference table**:

| Method | Path                  | Description                          |
|--------|-----------------------|----------------------------------------|
| POST   | /data/upload           | Upload and process a CSV file          |
| GET    | /data                  | List records (paginated, filterable)   |
| GET    | /data/{id}             | Get a single record                    |
| GET    | /analytics/summary     | Department-level analytics summary     |
| GET    | /analytics/trends      | Hiring trends by month/quarter         |
| GET    | /health                | Health check for DB and Redis          |

12. **Caching Notes** (explain 5-min TTL, invalidation-on-upload behavior)
13. **Project Structure** (paste the folder tree from step 0.4)
14. **Known Limitations / Future Improvements** (e.g. no auth, no Alembic migrations yet, no rate limiting) — shows maturity/awareness to graders.
15. **License** (optional)

### 11.2 Small tasks for README polish
- [ ] Include badges (optional) e.g. "Built with FastAPI", "Docker Compose Ready".
- [ ] Proofread all commands actually work by literally copy-pasting them into a clean terminal.
- [ ] Make sure the Swagger docs link is correct: `http://localhost:8000/docs`.

---

## PHASE 12 — Git Commit Strategy (Minimum 10 Meaningful Commits)

Commit **as you complete each phase**, not all at the end. Suggested commit sequence (this alone gives 15+ commits):

1. `chore: initialize repo with .gitignore and project structure`
2. `feat: add Dockerfile with multi-stage build`
3. `feat: add docker-compose.yml with app, postgres, redis services`
4. `chore: add .env.example and environment configuration`
5. `feat: add database connection setup and SQLAlchemy Record model`
6. `feat: add Redis client and caching helper functions`
7. `feat: add FastAPI app skeleton with router registration`
8. `feat: add Pydantic schemas for records, uploads, analytics, health`
9. `feat: implement Pandas data cleaning pipeline`
10. `feat: implement POST /data/upload endpoint`
11. `feat: implement GET /data and GET /data/{id} endpoints`
12. `feat: implement GET /analytics/summary with Redis caching`
13. `feat: implement GET /analytics/trends with Pandas resample`
14. `feat: implement GET /health endpoint`
15. `feat: add global exception handler and status code cleanup`
16. `test: add pytest fixtures and conftest setup`
17. `test: add tests for health, upload, records, analytics (14 tests)`
18. `docs: add comprehensive README with architecture diagram`
19. `chore: add sample_data.csv for demo/testing`
20. `fix: <describe any bug fixed during manual testing>`

Small tasks:
- [ ] Commit early, commit often — after each small working chunk, not one giant commit at the end.
- [ ] Write commit messages in **imperative mood** ("add", "fix", "implement") not past tense.
- [ ] Optionally follow Conventional Commits prefixes (`feat:`, `fix:`, `docs:`, `test:`, `chore:`) — makes history easy to scan.
- [ ] Before final submission, run `git log --oneline` and confirm 10+ commits with clear, distinct messages (not "update", "fix2", "wip").

---

## PHASE 13 — Final Verification Checklist (Mapped to Evaluation Criteria)

### FastAPI endpoints & Pydantic models (25%)
- [ ] All 6 endpoints implemented and reachable via `/docs`.
- [ ] Every request/response uses a Pydantic model (no raw dicts returned).
- [ ] Correct status codes per Phase 9 table.
- [ ] Query parameter validation works (page, per_page, department, status, interval).

### Pandas data processing (20%)
- [ ] Missing value handling implemented and tested (median fill for salary, default for status).
- [ ] Type conversions implemented (employee_id, salary, hire_date).
- [ ] Duplicate detection implemented (within file AND against DB).
- [ ] `groupby` used correctly for summary; `resample` used correctly for trends.
- [ ] Code avoids obviously inefficient patterns (no row-by-row Python loops where vectorized Pandas ops would do — check `clean_dataframe` for any accidental `.iterrows()` that could be vectorized).

### Docker setup (25%)
- [ ] Dockerfile has 2 clear stages (builder, runtime).
- [ ] Final image is slim (no build tools/compilers baked into the runtime layer).
- [ ] `docker compose up --build` starts all 3 services with one command.
- [ ] Named volumes persist Postgres/Redis data across `docker compose down` (without `-v`) and `docker compose up` again.
- [ ] Healthchecks configured for db/redis; app waits for both.
- [ ] Hot reload confirmed: edit a file in `app/`, save, and see Uvicorn auto-reload in logs without rebuilding the image.
- [ ] `.env` used for all configurable values — no hardcoded secrets/ports in code.

### Tests (15%)
- [ ] 14 tests present, all passing.
- [ ] Coverage includes happy paths AND error cases (400, 404, 422, 503).
- [ ] Tests are isolated (don't depend on execution order, clean DB state per test).

### Documentation & Git (15%)
- [ ] README has architecture diagram, setup steps, endpoint reference, env var table.
- [ ] `docker compose up` truly works from a completely fresh clone (test this on a clean clone in a temp folder before submitting).
- [ ] 10+ meaningful, well-labeled commits.
- [ ] No `.env`, `__pycache__`, or volume data accidentally committed (check with `git status` and `git ls-files`).

---

## PHASE 14 — Suggested Time Schedule (09:00–17:00)

| Time          | Focus                                                                 |
|---------------|------------------------------------------------------------------------|
| 09:00–09:30   | Phase 0: planning, folder structure, Git init, CSV schema decision      |
| 09:30–10:30   | Phase 1: Dockerfile + docker-compose.yml + .env, get `docker compose up` working with empty app |
| 10:30–11:15   | Phase 2 + 3: Postgres models/config, Redis client setup                |
| 11:15–12:00   | Phase 4 + 5: FastAPI skeleton, Pydantic schemas                        |
| 12:00–12:30   | Phase 6: Pandas cleaning pipeline (first half — read/clean functions)  |
| **12:30**     | **Check-in #1** — demo: containers running, DB/Redis connected, skeleton endpoints visible in `/docs` |
| 12:30–13:15   | Lunch / buffer                                                          |
| 13:15–14:00   | Phase 6 (finish): analytics compute functions (summary, trends)         |
| 14:00–15:00   | Phase 7: build all 6 endpoints, wire Pandas + Redis caching in         |
| 15:00–15:30   | Phase 8 + 9: caching verification, error handling pass                 |
| **15:30**     | **Check-in #2** — demo: full upload → query → analytics flow working end-to-end with caching visible |
| 15:30–16:15   | Phase 10: write and run all pytest tests, fix any bugs found            |
| 16:15–16:45   | Phase 11: write README fully                                            |
| 16:45–17:00   | Phase 12 + 13: finalize commits, run final checklist, fresh-clone test  |

---

## Appendix A — Example `sample_data.csv` (commit this to the repo)
```csv
employee_id,name,department,salary,hire_date,status
1,Alice Smith,Engineering,90000,2024-01-15,active
2,Bob Jones,Sales,60000,2024-02-20,active
3,Carol Lee,Engineering,95000,2024-03-05,inactive
4,David Kim,HR,55000,2024-01-28,active
5,Eva Brown,Sales,62000,2024-04-10,terminated
6,Frank Wu,Engineering,98000,2024-05-02,active
7,Grace Chen,HR,,2024-06-18,active
8,Henry Patel,Marketing,58000,2024-07-01,active
```
Note row 7 intentionally has a missing salary — good for demonstrating the missing-value-handling logic during a live demo.

## Appendix B — Handy Commands Reference
```bash
# Start everything
docker compose up --build

# Start in background
docker compose up -d --build

# View logs
docker compose logs -f app

# Stop everything (keep data)
docker compose down

# Stop everything and wipe volumes (fresh DB/Redis)
docker compose down -v

# Open a shell inside the app container
docker compose exec app bash

# Open psql inside the db container
docker compose exec db psql -U pipeline_user -d pipeline_db

# Open redis-cli inside the redis container
docker compose exec redis redis-cli

# Run tests inside the running app container
docker compose exec app pytest -v --cov=app

# Check Redis TTL on a cache key
docker compose exec redis redis-cli TTL analytics:summary
```

## Appendix C — Common Pitfalls to Avoid
- [ ] Forgetting `condition: service_healthy` in `depends_on` → app starts before Postgres is ready and crashes.
- [ ] Committing the real `.env` file with secrets → always double check `.gitignore` first commit.
- [ ] Using `.iterrows()` in Pandas for cleaning → slow, avoid; use vectorized operations instead.
- [ ] Not invalidating cache after upload → stale analytics served to users after new data arrives.
- [ ] Hardcoding `localhost` instead of service names (`db`, `redis`) inside container-to-container config → containers can't find each other, always use the Compose service name as hostname.
- [ ] Skipping the "fresh clone" test → a plan that only works on your machine because of leftover local state isn't actually done.

---

**End of Plan.** Follow phases in order, check off every small task box as you go, and commit after each phase completes successfully.
