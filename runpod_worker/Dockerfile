FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/runpod-volume/hf \
    TRANSFORMERS_CACHE=/runpod-volume/hf \
    HUGGINGFACE_HUB_CACHE=/runpod-volume/hf \
    DIFFUSERS_CACHE=/runpod-volume/hf \
    TORCH_HOME=/runpod-volume/torch \
    TMPDIR=/runpod-volume/tmp

# Install Python 3.10, pip, ffmpeg, git
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip ffmpeg git \
    && rm -rf /var/lib/apt/lists/*

# Create cache directories
RUN mkdir -p /runpod-volume/hf /runpod-volume/torch /runpod-volume/tmp

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir --default-timeout=180 --retries 10 -r requirements.txt

# Copy handler
COPY handler.py .

# Run handler
CMD ["python3", "-u", "handler.py"]
