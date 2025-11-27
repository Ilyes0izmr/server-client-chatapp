#!/bin/bash
echo "🚀 Setting up Chat App Virtual Environment..."

# Create virtual environment
python3 -m venv chat_app_env
source chat_app_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Virtual environment setup complete!"