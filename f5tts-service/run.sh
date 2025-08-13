#!/bin/bash

# Run script for F5-TTS service with proxy support
# Usage: ./run.sh

set -e

# Create cache directory if it doesn't exist
mkdir -p $(pwd)/cache

echo "Starting F5-TTS service container..."
echo "Using proxy settings:"
echo "  HTTP_PROXY: ${HTTP_PROXY:-not set}"
echo "  HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
echo "  NO_PROXY: ${NO_PROXY:-not set}"

# Stop and remove existing container if it exists
docker stop f5tts-service 2>/dev/null || true
docker rm f5tts-service 2>/dev/null || true

# Run the container with proper proxy settings and volume mounts
docker run -d \
    --name f5tts-service \
    --gpus all \
    -p 8001:8001 \
    -e HTTP_PROXY=$HTTP_PROXY \
    -e HTTPS_PROXY=$HTTPS_PROXY \
    -e NO_PROXY=$NO_PROXY \
    -e HF_HOME=/root/.cache/huggingface \
    -e TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers \
    -e HF_DATASETS_CACHE=/root/.cache/huggingface/datasets \
    -v $(pwd)/cache:/root/.cache/huggingface/hub \
    --network host \
    f5tts-service:latest

echo "Container started successfully!"
echo "Service will be available at: http://localhost:8001"
echo "To check logs: docker logs -f f5tts-service"
echo "To stop: docker stop f5tts-service"
