#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip and install dependencies
pip install --upgrade pip

# Install only production dependencies
pip install --no-cache-dir -r requirements.txt

# Verify installation
python -c "import fastapi, uvicorn, motor, pymongo, pydantic, geopy; print('All dependencies installed successfully')"

echo "Build completed successfully!"