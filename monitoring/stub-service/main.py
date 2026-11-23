"""Throwaway stub that follows docs/CONTRACT.md so monitoring can be built before the real services exist.
Delete once the real services are in the main compose file."""
import asyncio
import json
import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

SERVICE = os.getenv("SERVICE_NAME", "stub-service")
STUDENT_URL = os.getenv("STUDENT_SERVICE_URL", "http://student-service:8000")
ROOM_URL = os.getenv("ROOM_SERVICE_URL", "http://room-service:8000")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        ts = datetime.fromtimestamp(record.created, timezone.utc)
        data = {
            "timestamp": ts.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "service": SERVICE,
            "correlation_id": getattr(record, "correlation_id", "-"),
            "message": record.getMessage(),
        }
        data.update(getattr(record, "fields", {}))
        return json.dumps(data)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log = logging.getLogger("app")
log.addHandler(handler)
log.setLevel(logging.INFO)
log.propagate = False

app = FastAPI(title=SERVICE)
Instrumentator().instrument(app).expose(app)  # GET /metrics


@app.middleware("http")
async def correlation_and_logging(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.cid = cid
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error", extra={"correlation_id": cid})
        response = JSONResponse({"detail": "internal error"}, status_code=500)
    response.headers["X-Correlation-ID"] = cid
    if request.url.path not in ("/health", "/metrics"):
        status = response.status_code
        level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
        log.log(level, "request", extra={
            "correlation_id": cid,
            "fields": {
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        })
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/work")
async def work(fail_rate: float = 0.0, delay_ms: int = 0):
    """Normal endpoint. fail_rate=0.3 -> 30% of calls return 500. delay_ms adds latency."""
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    if random.random() < fail_rate:
        return JSONResponse({"detail": "simulated failure"}, status_code=500)
    return {"status": "ok", "service": SERVICE}


@app.get("/conflict")
def conflict():
    return JSONResponse({"detail": "slot not available"}, status_code=409)


@app.post("/book")
async def book(request: Request, slot_free: bool = True):
    """Mimics Booking Service: calls student-service then room-service, forwarding the correlation ID.
    slot_free=false makes room-service answer 409, like a double booking."""
    cid = request.state.cid
    headers = {"X-Correlation-ID": cid}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.get(f"{STUDENT_URL}/work", headers=headers)
            room = await client.get(f"{ROOM_URL}/work" if slot_free else f"{ROOM_URL}/conflict", headers=headers)
    except httpx.RequestError as exc:
        log.error("downstream unreachable: %s", exc, extra={"correlation_id": cid})
        return JSONResponse({"detail": "downstream unavailable"}, status_code=502)
    if room.status_code == 409:
        log.warning("booking rejected: slot not available", extra={"correlation_id": cid})
        return JSONResponse({"detail": "slot not available"}, status_code=409)
    return {"status": "booked"}
