#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AXIOMFLOW_API_BASEURL:-http://localhost:8000}"
COOKIE_JAR="$(mktemp)"

EMAIL="test_$(date +%Y%m%d_%H%M%S)@example.com"
PASSWORD="TestPassw0rd!"

echo "[1] Register: $EMAIL"
curl -sS -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"username\":\"testuser\",\"password\":\"$PASSWORD\"}" | jq .

echo
echo "[2] Login"
curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -c "$COOKIE_JAR" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq .

echo
echo "[3] Refresh (cookie-based)"
curl -sS -X POST "$BASE_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
  -d "{}" | jq .

echo
echo "[4] Logout"
curl -sS -X POST "$BASE_URL/auth/logout" \
  -H "Content-Type: application/json" \
  -b "$COOKIE_JAR" \
  -d "{}" | jq .

echo
echo "Done."
echo "Verify/reset need token from email links."

