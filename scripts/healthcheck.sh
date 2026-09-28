#!/bin/bash
set -e

echo "Checking backend health..."
response=$(curl -s -f http://localhost:8000/health)

status=$(echo $response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
mongo=$(echo $response | grep -o '"mongo":"[^"]*"' | cut -d'"' -f4)
model_loaded=$(echo $response | grep -o '"model_loaded":true')

if [[ "$status" != "ok" && "$status" != "degraded" ]]; then
    echo "Healthcheck failed: invalid status $status"
    exit 1
fi

if [[ "$mongo" != "up" ]]; then
    echo "Healthcheck failed: mongo is $mongo"
    exit 1
fi

if [[ -z "$model_loaded" ]]; then
    echo "Healthcheck failed: model not loaded"
    exit 1
fi

echo "Healthcheck OK."
exit 0
