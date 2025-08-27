#!/usr/bin/env bash
# Start the FastAPI application with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port $PORT