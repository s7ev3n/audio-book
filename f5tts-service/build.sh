#!/bin/bash

# Build script for F5-TTS service with proxy support
# Usage: ./build.sh

set -e

# Get current user
USERNAME=${USER:-$(whoami)}

echo "Building F5-TTS service Docker image..."
echo "Using proxy settings:"
echo "  HTTP_PROXY: ${HTTP_PROXY:-not set}"
echo "  HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
echo "  NO_PROXY: ${NO_PROXY:-not set}"

# Build the Docker image with proxy settings
docker build \
    --build-arg USE_CUDA=true \
    --build-arg USERNAME=$USERNAME \
    --build-arg HTTP_PROXY=$HTTP_PROXY \
    --build-arg HTTPS_PROXY=$HTTPS_PROXY \
    --build-arg NO_PROXY=$NO_PROXY \
    --network=host \
    -t f5tts-service:latest \
    -f Dockerfile \
    .

echo "Build completed successfully!"
echo "To run the container:"
echo "docker run -d --name f5tts-service --gpus all -p 8001:8001 \\"
echo "  -e HTTP_PROXY=\$HTTP_PROXY \\"
echo "  -e HTTPS_PROXY=\$HTTPS_PROXY \\"
echo "  -e NO_PROXY=\$NO_PROXY \\"
echo "  -v \$(pwd)/cache:/root/.cache/huggingface/hub \\"
echo "  f5tts-service:latest"
