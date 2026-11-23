#!/bin/sh
# Demo traffic generator: steady normal bookings, then a burst of double-bookings (409 errors).
# Usage:  ./monitoring/scripts/demo.sh            (stub: booking-service on localhost:8003)
# Tune with env vars, e.g.  N_OK=120 N_FAIL=30 ./monitoring/scripts/demo.sh
#
# When the real services exist, change BOOK_CMD below to the real call
# (POST /api/bookings with a body) and make the "fail" case book the same slot twice.

BASE="${BASE:-http://localhost:8003}"
N_OK="${N_OK:-60}"          # normal requests
N_FAIL="${N_FAIL:-20}"      # failing requests (slot already taken)
SLEEP_OK="${SLEEP_OK:-0.5}"
SLEEP_FAIL="${SLEEP_FAIL:-0.25}"
STAMP=$(date +%s)

book() {  # $1 = correlation id, $2 = slot_free (true/false)
  curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "X-Correlation-ID: $1" "$BASE/book?slot_free=$2"
}

echo "Phase 1: $N_OK normal bookings (~$(echo "$N_OK * $SLEEP_OK" | bc | cut -d. -f1)s)"
i=1
while [ "$i" -le "$N_OK" ]; do
  code=$(book "demo-$STAMP-ok-$i" true)
  printf "."
  [ "$code" = "200" ] || printf "[%s]" "$code"
  sleep "$SLEEP_OK"
  i=$((i + 1))
done
echo

echo "Phase 2: $N_FAIL double-bookings (these should return 409)"
i=1
while [ "$i" -le "$N_FAIL" ]; do
  code=$(book "demo-$STAMP-fail-$i" false)
  printf "%s " "$code"
  sleep "$SLEEP_FAIL"
  i=$((i + 1))
done
echo
echo
echo "Done. Error spike is on the Grafana dashboard (App overview, last 15m)."
echo "Pick a failed request and search its logs. In Grafana > Explore > Loki:"
echo "  {service=~\"student-service|room-service|booking-service\"} | json | correlation_id=\"demo-$STAMP-fail-1\""
echo "Or type demo-$STAMP-fail-1 into the Correlation ID box on the dashboard."
