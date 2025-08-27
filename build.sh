#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Starting build process..."

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies one by one to avoid conflicts
echo "Installing FastAPI..."
pip install --no-cache-dir fastapi

echo "Installing Uvicorn..."
pip install --no-cache-dir "uvicorn[standard]"

echo "Installing MongoDB drivers..."
pip install --no-cache-dir motor pymongo

echo "Installing other dependencies..."
pip install --no-cache-dir pydantic python-multipart geopy

# Verify critical imports
python -c "
import fastapi
import uvicorn
import motor
import pymongo
import pydantic
import geopy
print('✅ All dependencies installed successfully!')
print(f'Python version: {__import__(\"sys\").version}')
print(f'FastAPI version: {fastapi.__version__}')
"

echo "Build completed successfully!"