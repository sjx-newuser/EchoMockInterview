#!/bin/bash
# Echo Mock System - Local Dev Runner

# Get the absolute path of the project root
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo "=========================================="
echo "  Starting Echo Mock System Dev Services  "
echo "=========================================="

# Start backend
echo "[1/2] Starting fastAPI Backend..."
cd "$PROJECT_ROOT/backend" || exit
# If using conda environment named mock-interview:
conda run --no-capture-output -n mock-interview uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "[2/2] Starting Vue3 Frontend..."
cd "$PROJECT_ROOT/frontend" || exit
npm run dev &
FRONTEND_PID=$!

# Handle graceful shutdown
trap "echo 'Shutting down services...'; kill $BACKEND_PID $FRONTEND_PID; exit" EXIT INT TERM

wait