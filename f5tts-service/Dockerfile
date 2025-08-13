FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

USER root

ARG DEBIAN_FRONTEND=noninteractive
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG USE_CUDA=true
ARG USERNAME

# Set proxy environment variables for build and runtime
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTPS_PROXY
ENV no_proxy=$NO_PROXY
ENV HTTP_PROXY=$HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY
ENV NO_PROXY=$NO_PROXY

LABEL github_repo="https://github.com/SWivid/F5-TTS"

# Install basic dependencies and git for cloning
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libsndfile1-dev \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /workspace

# Configure git to use proxy if needed
RUN if [ -n "$HTTP_PROXY" ]; then \
        git config --global http.proxy $HTTP_PROXY && \
        git config --global https.proxy $HTTPS_PROXY; \
    fi

# Clone F5-TTS repository
RUN git clone https://github.com/SWivid/F5-TTS.git /workspace/F5-TTS

# Install F5-TTS with proper proxy handling
RUN cd F5-TTS && \
    if [ -n "$HTTP_PROXY" ]; then \
        pip config set global.proxy $HTTP_PROXY; \
    fi && \
    pip install -e . --no-cache-dir

# Install FastAPI and dependencies
RUN if [ -n "$HTTP_PROXY" ]; then \
        pip config set global.proxy $HTTP_PROXY; \
    fi && \
    pip install fastapi uvicorn python-multipart

# Copy the FastAPI app
COPY app.py /workspace/app.py

# Copy custom reference audio files
COPY ref_audio/ /workspace/ref_audio/

# Create necessary directories
RUN mkdir -p /tmp/f5tts_outputs && \
    mkdir -p /root/.cache/huggingface/hub

# Set environment variables for Hugging Face
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV HF_DATASETS_CACHE=/root/.cache/huggingface/datasets

ENV SHELL=/bin/bash

# Volume for Hugging Face cache
VOLUME /root/.cache/huggingface/hub/

EXPOSE 8001

# Run the FastAPI service
CMD ["python", "/workspace/app.py"]