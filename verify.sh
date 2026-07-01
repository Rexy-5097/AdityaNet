#!/usr/bin/env bash
set -e

echo "===== SuryaNet Sprint 1 Verification ====="

python3 --version
pip --version

# Create and activate virtual environment (if not already created)
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install project dependencies
pip install -r requirements.txt

# Start backend infrastructure
docker compose up -d

# Wait for containers to become healthy
echo "Waiting for Docker containers to be healthy..."
sleep 5

echo ""
echo "===== Docker Containers ====="
docker ps

echo ""
echo "===== TimescaleDB Logs ====="
docker compose logs --no-color timescaledb | tail -n 20

echo ""
echo "===== Redis Logs ====="
docker compose logs --no-color redis | tail -n 20

echo ""
echo "===== Check FastAPI App ====="

# Run app in background (using app.main:app)
uvicorn app.main:app --reload > uvicorn_verify.log 2>&1 &
UVICORN_PID=$!

echo "Waiting for FastAPI to start..."
sleep 5

echo "Health endpoint:"
curl -s http://127.0.0.1:8000/api/v1/health
echo ""

echo ""
echo "OpenAPI schema:"
curl -s http://127.0.0.1:8000/api/v1/openapi.json | head -c 500
echo ""

echo ""
echo "Docs response headers:"
curl -I http://127.0.0.1:8000/docs

echo ""
echo "===== Cleanup ====="
kill $UVICORN_PID || true
rm -f uvicorn_verify.log

echo ""
echo "===== Sprint 1 Verification Complete ====="
