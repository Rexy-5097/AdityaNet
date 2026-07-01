#!/usr/bin/env bash
set -e

echo "===== SuryaNet Sprint 3.5 Verification ====="

source venv/bin/activate
export PYTHONPATH=$PWD

# Install dependencies
pip install -r requirements.txt

# Ensure containers are up
docker compose up -d

# Historical GOES backfill (using narrow range for instant checkpoint matching)
echo "Running GOES backfill..."
python3 scripts/backfill_goes.py --start-date 2024-01-01 --end-date 2024-01-02

# Historical flare backfill (using narrow range for instant checkpoint matching)
echo "Running Flare backfill..."
python3 scripts/backfill_flares.py --start-date 2024-01-01 --end-date 2024-01-02

# Start API in background
echo "Starting FastAPI app..."
uvicorn app.main:app --reload > uvicorn_sprint3.5.log 2>&1 &
UVICORN_PID=$!

sleep 10

echo ""
echo "===== Verify Dataset Summary ====="
curl -s http://127.0.0.1:8000/api/v1/system/dataset-summary
echo ""

echo ""
echo "===== Check Record Counts in Database ====="
echo "GOES Records:"
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT COUNT(*) FROM goesxrs;"
echo "Flare Records:"
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT COUNT(*) FROM flareevent;"
echo "M-class Flares:"
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT COUNT(*) FROM flareevent WHERE flare_class LIKE 'M%';"
echo "X-class Flares:"
docker exec suryanet_timescaledb psql -U postgres -d suryanet -c "SELECT COUNT(*) FROM flareevent WHERE flare_class LIKE 'X%';"

echo ""
echo "===== Verify Saved Artifact ====="
cat artifacts/dataset_summary.json
echo ""

echo ""
echo "===== Cleanup ====="
kill $UVICORN_PID || true
rm -f uvicorn_sprint3.5.log

echo ""
echo "===== SPRINT 3.5 COMPLETE ====="
