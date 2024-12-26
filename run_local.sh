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
letta server > /dev/null 2>&1 &

if [ $? -ne 0 ]; then
    echo "Error: Failed to start Letta service!"
    exit 1
fi

echo "Waiting for Letta service to be ready..."
# Wait for Letta service to be healthy (max 150 seconds)
ATTEMPTS=0
MAX_ATTEMPTS=30
until curl -s http://localhost:8283/health > /dev/null || [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; do
    echo "Waiting for Letta service... ($(($MAX_ATTEMPTS - $ATTEMPTS)) attempts remaining)"
    sleep 5
    ATTEMPTS=$((ATTEMPTS + 1))
done

if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
    echo "Error: Letta service failed to start within 150 seconds!"
    docker stop $CONTAINER_ID
    exit 1
fi

echo "Letta service is ready!"
echo "Starting webhook handler..."

# Start webhook handler
uvicorn src.webhook_handler:app --port 8000 --reload

# Cleanup on script exit
trap 'echo "Stopping services..."; docker stop $CONTAINER_ID' EXIT
