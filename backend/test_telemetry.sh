#!/bin/bash
# Simulate sensor posting data for bin-01

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "Simulating sensor readings for bin-01..."
for i in {1..5}; do
  FILL=$((20 + i * 15))  # 35%, 50%, 65%, 80%, 95%
  DISTANCE=$(echo "60 - ($FILL * 0.5)" | bc)  # Linear: 60cm@0% → 10cm@100%
  TS=$(date +%s)

  PAYLOAD=$(cat <<EOF
{
  "bin_id": "bin-01",
  "distance_cm": $DISTANCE,
  "fill_percent": $FILL,
  "ts": $TS
}
EOF
)

  echo "[$i] Sending: fill=$FILL%, distance=${DISTANCE}cm"
  curl -s -X POST "$BACKEND_URL/telemetry" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" | jq -r '.status'

  sleep 12  # Wait 12s (longer than frontend poll interval)
done

echo "Done. Check dashboard to verify bin-01 fill level increased from 35% → 95%"
