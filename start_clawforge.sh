#!/bin/bash
# ClawForge v4.0 - Linux/macOS Startup Script

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "============================================"
echo "  ClawForge v4.0 - Starting Services"
echo "============================================"
echo ""

# Create logs directory
mkdir -p logs

# Start Backend
echo "[1/2] Starting Backend Server (port 8000)..."
nohup python backend/main.py --server > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "      Backend PID: $BACKEND_PID"

# Wait for backend
sleep 5

# Start Frontend
echo "[2/2] Starting Frontend Dashboard (port 7860)..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "      Frontend PID: $FRONTEND_PID"
cd ..

echo ""
echo "============================================"
echo "  ClawForge is Running!"
echo "============================================"
echo ""
echo "  Backend:  http://127.0.0.1:8000"
echo "  Frontend: http://127.0.0.1:7860"
echo "  API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "PIDs saved to .clawforge_pids"
echo "$BACKEND_PID $FRONTEND_PID" > .clawforge_pids

# Save PIDs for stopping
echo "$BACKEND_PID $FRONTEND_PID" > .clawforge_pids
echo "Press Ctrl+C to stop all services..."
