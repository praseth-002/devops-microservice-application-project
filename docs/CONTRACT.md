# Team Contract

Everything here is a rule other roles depend on. Change it only by PR + telling the team.

## 1. Services, names, ports
All containers join the Docker network **`app-net`**. Services reach each other by service name.

| Service | Compose name | Container port | DB |
|---|---|---|---|
| Frontend (Nginx) | `frontend` | 80 (published on host 80) | none |
| Student Service | `student-service` | 8000 | `students_db` (PostgreSQL) |
| Room Service | `room-service` | 8000 | `rooms_db` (PostgreSQL) |
| Booking Service | `booking-service` | 8000 | `bookings_db` (PostgreSQL) |

Every backend listens on **8000 inside the container**. Only `frontend` (80) and Grafana (3000)
are published publicly; backends and DBs stay internal. Nginx proxies `/api/*` to the services.

## 2. Required endpoints on every backend
- `GET /health` returns `200 {"status":"ok"}` (used by Docker healthchecks).
- `GET /metrics` Prometheus format. FastAPI: `prometheus-fastapi-instrumentator`
  (`Instrumentator().instrument(app).expose(app)`).

## 3. Error status codes (the demo depends on these)
- Student not found: `404`
- Slot already taken: `409`
- Downstream service unreachable: `502`
- Unexpected errors: `500`

The error-rate dashboard counts 4xx and 5xx, so the "slot not available" demo shows up as a spike.

## 4. Correlation ID
- Header: **`X-Correlation-ID`**.
- Nginx / the first service to receive a request generates a UUID if the header is missing.
- Every outgoing service-to-service call **must forward** the header.
- Every response returns it in the response header.
- Every log line includes it (see below).

## 5. Log format
One JSON object per line, written to **stdout** (not files). Promtail collects Docker stdout.

Required fields:
```json
{"timestamp":"2026-11-23T10:15:30.123Z","level":"INFO","service":"booking-service","correlation_id":"b3c1...","message":"booking created"}
```
- `timestamp`: ISO 8601 UTC
- `level`: `DEBUG|INFO|WARNING|ERROR`
- `service`: must equal the compose service name
- `correlation_id`: the request's ID (`"-"` if none, e.g. startup logs)
- `message`: short human-readable text

Optional but encouraged on request logs: `method`, `path`, `status`, `duration_ms`.
Log every failed booking at `WARNING` or `ERROR` with the reason.

## 6. Environment variables and secrets
- Names are `UPPER_SNAKE_CASE`. Commit `.env.example`, never `.env`.
- DB credentials and URLs come from env vars, never hard-coded.
- CI/CD and cloud secrets live in GitHub Actions secrets.

## 7. Compose ownership
- `docker-compose.yml` (app stack): owned by the Containerization role.
- `monitoring/docker-compose.monitoring.yml`: owned by Observability.
- The `app-net` network is created once (`docker network create app-net`) or declared by the main compose;
  monitoring references it as `external: true`.
- Every service in the main compose needs a `healthcheck`, and its service name must match section 1.

## 8. Git workflow
- `main` is protected: no direct pushes, merges via PR with at least 1 review.
- Branches: `feature/<name>-<topic>`, e.g. `feature/sett-monitoring`.
- CI runs tests and builds images on every push/PR; images publish to Docker Hub only on merge to `main`.
- Each service has its own `tests/` folder runnable with one command (`pytest`).

## 9. Owners
| Area | Owner |
|---|---|
| Frontend | Hak Kimly |
| Student & Room Services | TBD |
| Booking Service & Containerization | TBD |
| CI/CD & Cloud Deployment | Chhorn Norakjed |
| Observability | Sett |
