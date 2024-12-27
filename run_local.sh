#!/bin/bash

# List of required environment variables
REQUIRED_VARS=(
  "OPENAI_API_KEY"
  "LETTA_LLM_MODEL"
  "LETTA_EMBEDDING_ENDPOINT_TYPE"
  "LETTA_EMBEDDING_MODEL"
)

# Check each environment variable
for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo "Error: $VAR is not set!"
    exit 1
  fi
done

echo "All required environment variables are set."

# run letta server
python3 -m pip list | grep letta
python3 -m letta --help
python3 -m letta server --port 8283 > /dev/null 2>&1 &

if [ $? -ne 0 ]; then
    echo "Error: Failed to start Letta service!"
    exit 1
fi

echo "Waiting for Letta service to be ready..."
# Wait for Letta service to be healthy (max 150 seconds)
ATTEMPTS=0
MAX_ATTEMPTS=30
until curl http://localhost:8283/v1/health > /dev/null || [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; do
    echo ">>>>DEBUG<<<<"
    curl -v --trace-ascii trace.log http://localhost:8283/v1/health
    echo "Waiting for Letta service... ($(($MAX_ATTEMPTS - $ATTEMPTS)) attempts remaining)"
    sleep 5
    ATTEMPTS=$((ATTEMPTS + 1))
done

if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
    echo "Error: Letta service failed to start within 150 seconds!"
    exit 1
fi

echo "Letta service is ready!"
echo "Starting webhook handler..."

# Start webhook handler
uvicorn src.webhook_handler:app --host 0.0.0.0 --port 8000 --reload
