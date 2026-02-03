#!/bin/bash
set -e

echo "=== CogVideoX Pod Bootstrap v9 ==="

# Install system dependencies
echo "Installing system packages..."
apt-get update
apt-get install -y git ffmpeg python3-pip python3-venv

# Clone repo
cd /workspace
if [ ! -d "videoexpressai" ]; then
    echo "Cloning repository..."
    git clone https://github.com/nanichwdry/videoexpressai.git
fi

cd videoexpressai/workers/video_worker

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Export environment variables
export HF_HOME=/workspace/hf
export TRANSFORMERS_CACHE=/workspace/hf
export HUGGINGFACE_HUB_CACHE=/workspace/hf
export DIFFUSERS_CACHE=/workspace/hf
export TORCH_HOME=/workspace/torch
export TMPDIR=/workspace/tmp

# Create directories
mkdir -p /workspace/hf /workspace/torch /workspace/tmp /workspace/outputs

# Start server
echo "Starting CogVideoX API server on port 8001..."
python3 api_server.py
