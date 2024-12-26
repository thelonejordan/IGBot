#!/bin/bash

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set in .env file!"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    exit 1
fi

echo "Starting Letta service..."
# Stop existing Letta container if running
docker ps -q --filter "ancestor=letta/letta:latest" | xargs -r docker stop

# Start Letta service
#LETTA_LLM_MODEL=gpt-4o-mini
# LETTA_EMBEDDING_ENDPOINT_TYPE=openai
# LETTA_EMBEDDING_MODEL=text-embedding-ada-002
CONTAINER_ID=$(docker run -d \
    -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
    -p 8283:8283 \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e LETTA_LLM_MODEL="${LETTA_LLM_MODEL}" \
    -e LETTA_EMBEDDING_ENDPOINT_TYPE="${LETTA_EMBEDDING_ENDPOINT_TYPE}" \
    -e LETTA_EMBEDDING_MODEL="${LETTA_EMBEDDING_MODEL}" \
    letta/letta:latest)

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
