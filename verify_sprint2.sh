#!/usr/bin/env bash
set -e

echo "===== SuryaNet Sprint 2 Verification ====="

source venv/bin/activate
export PYTHONPATH=$PWD

# Install requirements
pip install -r requirements.txt

# Ensure containers are up
docker compose up -d

# Initialize database schemas and hypertables
echo "Initializing database..."
python3 app/db/init_db.py

# Ingest solar flare data and GOES telemetry
echo "Running data ingestion pipeline..."
python3 scripts/ingest_goes.py

# Start FastAPI app in background
echo "Starting FastAPI app..."
uvicorn app.main:app --reload > uvicorn_sprint2.log 2>&1 &
UVICORN_PID=$!

sleep 10

echo ""
echo "===== API Health Check ====="
curl -s http://127.0.0.1:8000/api/v1/health
echo ""

echo ""
echo "===== Latest Solar Observation ====="
curl -s http://127.0.0.1:8000/api/v1/solar/latest
echo ""

echo ""
echo "===== Latest Flare Events ====="
curl -s http://127.0.0.1:8000/api/v1/flares/latest
echo ""

echo ""
echo "===== Verify Tables in Database ====="
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "\dt"

echo ""
echo "===== Verify GOES Records Count ====="
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT COUNT(*) FROM goesxrs;"

echo ""
echo "===== Verify Flare Records Count ====="
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT COUNT(*) FROM flareevent;"

echo ""
echo "===== Verify Hypertables in TimescaleDB ====="
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT * FROM timescaledb_information.hypertables;"

echo ""
echo "===== Cleanup ====="
kill $UVICORN_PID || true
rm -f uvicorn_sprint2.log

echo ""
echo "===== SPRINT 2 COMPLETE ====="
