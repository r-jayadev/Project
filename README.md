# Employee Data Processing API

A Dockerized REST API built with **FastAPI**, **PostgreSQL**, **Redis**, and **Pandas** for processing employee data from CSV files. The application provides data upload, employee management, analytics, caching, and health monitoring through RESTful endpoints.

---

# Project Overview

This project demonstrates a modern backend application using:

- **FastAPI** for building REST APIs
- **PostgreSQL** as the relational database
- **SQLAlchemy ORM** for database operations
- **Redis** for caching analytics responses
- **Pandas** for CSV processing and analytics
- **Docker & Docker Compose** for containerization
- **Pytest** for API testing

The application allows users to upload employee records from CSV files, store them in PostgreSQL, perform analytics, cache frequently accessed results using Redis, and expose everything through REST APIs.

---

# Technology Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Programming Language |
| FastAPI | REST API Framework |
| PostgreSQL | Relational Database |
| SQLAlchemy | ORM |
| Redis | Caching Layer |
| Pandas | CSV Processing & Analytics |
| Docker | Containerization |
| Docker Compose | Multi-container Orchestration |
| Pytest | API Testing |

---

# Project Structure

```
Project/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── data_processing.py
│   ├── main.py
│   ├── models.py
│   ├── redis_client.py
│   ├── routers.py
│   └── schemas.py
│
├── tests/
│   ├── conftest.py
│   ├── test_upload.py
│   ├── test_data.py
│   ├── test_analytics.py
│   └── test_health.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── pytest.ini
└── README.md
```

---

# Architecture

```
                    Client
                       │
                       ▼
                FastAPI Application
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   Routers        Data Processing    Redis Cache
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 SQLAlchemy ORM
                       │
                       ▼
                 PostgreSQL Database
```

---

# Request Flow

```
Client Request

      │

      ▼

FastAPI

      │

      ▼

Router

      │

      ▼

Input Validation

      │

      ▼

Business Logic

      │

      ▼

Pandas Processing (if CSV)

      │

      ▼

SQLAlchemy ORM

      │

      ▼

PostgreSQL

      │

      ▼

Redis Cache (Analytics)

      │

      ▼

JSON Response
```

---

# CSV Upload Workflow

```
Upload CSV

      │

      ▼

FastAPI UploadFile

      │

      ▼

Read CSV using Pandas

      │

      ▼

Validate Required Columns

      │

      ▼

Clean Data

      │

      ▼

Convert DataFrame → ORM Objects

      │

      ▼

Store in PostgreSQL

      │

      ▼

Clear Redis Cache

      │

      ▼

Return Success Response
```

---

# Features

- Upload employee data using CSV
- Validate CSV structure
- Store employee records in PostgreSQL
- Retrieve employee details
- Pagination support
- Department analytics
- Hiring trend analytics
- Redis caching
- Health check endpoint
- Dockerized deployment
- Automated API testing

---

# API Endpoints

## Upload Employee CSV

```
POST /data/upload
```

Uploads employee records from a CSV file.

---

## Get Employees

```
GET /data
```

Supports pagination.

Example:

```
GET /data?page=1&per_page=10
```

---

## Get Employee By ID

```
GET /data/{employee_id}
```

---

## Department Summary

```
GET /analytics/summary
```

Returns

- Headcount
- Average Salary
- Total Salary

Grouped by department.

---

## Hiring Trends

```
GET /analytics/trends
```

Optional query parameter

```
?frequency=M
```

or

```
?frequency=Q
```

---

## Health Check

```
GET /health
```

Checks

- API Status
- PostgreSQL Connection
- Redis Connection

---

# Docker Architecture

```
                    Docker Network

      ┌────────────────────────────────────┐

      │                                    │

      ▼                                    ▼

 FastAPI Container                  Redis Container

      │

      ▼

 PostgreSQL Container
```

---

# Setup Instructions

## Clone Repository

```bash
git clone <repository-url>
cd Project
```

---

## Configure Environment

Create a `.env` file.

Example:

```env
POSTGRES_DB=postgres_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

API_HOST=0.0.0.0
API_PORT=8000

CACHE_TTL=300
```

---

## Build and Start Containers

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up -d
```

---

## Stop Containers

```bash
docker compose down
```

---

# API Documentation

After starting the application:

### Swagger UI

```
http://localhost:8000/docs
```

### ReDoc

```
http://localhost:8000/redoc
```

---

# Running Tests

```bash
python -m pytest -v
```

---

# Caching Strategy

Analytics endpoints first check Redis.

```
Request

   │

   ▼

Redis

   │

Cache Hit?
   │

 ┌─Yes──────────────► Return Cached Data

 │

 No

 │

 ▼

PostgreSQL

 │

 ▼

Process Data

 │

 ▼

Store in Redis

 │

 ▼

Return Response
```

---
