# Study Room Booking (DevOps Project, Team 1, SE-G4)

Students book study rooms online. Frontend (Nginx) + 3 FastAPI services (Student, Room, Booking),
one PostgreSQL DB each. The focus is the DevOps lifecycle: Docker Compose, GitHub Actions CI/CD,
cloud VM deploy, Prometheus/Grafana metrics, Loki logs.

**Read `docs/CONTRACT.md` before writing any service code.** It defines the shared rules
(ports, health/metrics endpoints, log format, correlation ID) that monitoring depends on.

## Layout
```
frontend/           Nginx + static UI
student-service/    FastAPI + students_db
room-service/       FastAPI + rooms_db
booking-service/    FastAPI + bookings_db
monitoring/         Prometheus, Grafana, Loki, Promtail, cAdvisor (own compose file)
docs/               Contract and notes
.github/workflows/  CI/CD pipeline
docker-compose.yml  Main app stack (owned by Containerization role)
```

## Run locally
```bash
cp .env.example .env
docker network create app-net            # once
docker compose up -d --build             # app stack
docker compose -f monitoring/docker-compose.monitoring.yml up -d   # monitoring
```
Grafana: http://localhost:3000  |  Prometheus: http://localhost:9090
