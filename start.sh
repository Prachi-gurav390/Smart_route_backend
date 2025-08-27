#!/usr/bin/env bash
# Start the FastAPI application with uvicorn
PORT=${PORT:-8000}
uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info