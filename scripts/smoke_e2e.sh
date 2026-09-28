#!/bin/bash
set -e

# Wait for services to be ready
echo "Waiting for services..."
sleep 5

# Create a test run via the API
echo "Creating a synthetic run..."
cd backend
python -c "
import asyncio
from app.db.client import connect_db
from data.generator import generate_run
import app.constants as k
async def main():
    await connect_db()
    generate_run('smoke_test_run', '/tmp')
asyncio.run(main())
"
cd ..

# Get runs
echo "Fetching forecast runs..."
RUNS=$(curl -s -f http://localhost:8000/api/v1/forecast-runs)
RUN_ID=$(echo $RUNS | grep -o '"run_id":"[^"]*"' | head -n 1 | cut -d'"' -f4)

if [ -z "$RUN_ID" ]; then
    echo "No runs found"
    exit 1
fi

echo "Using Run ID: $RUN_ID"

# 1. Confidence map (Day 1)
echo "Testing confidence map Day 1..."
curl -s -f "http://localhost:8000/api/v1/confidence-map?run_id=${RUN_ID}&lead_time=1" > /dev/null

# 2. Bust probability
echo "Testing bust probability..."
curl -s -f "http://localhost:8000/api/v1/bust-probability?run_id=${RUN_ID}" > /dev/null

# 3. Detections
echo "Testing detections..."
curl -s -f "http://localhost:8000/api/v1/bust-detections?run_id=${RUN_ID}" > /dev/null

# 4. Telemetry
echo "Testing telemetry..."
curl -s -f "http://localhost:8000/api/v1/telemetry" > /dev/null

echo "E2E smoke test OK."
exit 0
