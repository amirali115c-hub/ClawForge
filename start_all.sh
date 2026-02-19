#!/bin/bash
# ClawForge v4.0 - Start All Services (Linux/Mac)
# Usage: bash start_all.sh

set -e

echo "🚀 Starting ClawForge AI Agent System..."
echo "=============================================="

# Pull Ollama model
echo ""
echo "📦 Pulling Ollama model (llama3)..."
ollama pull llama3

# Start backend (FastAPI on port 8000)
echo ""
echo "🔧 Starting Backend Server (port 8000)..."
cd "$(dirname "$0")"
python backend/main.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Start frontend (React on port 7860)
echo ""
echo "🎨 Starting Frontend Dashboard (port 7860)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "=============================================="
echo "✅ All services started!"
echo "   Dashboard: http://127.0.0.1:7860"
echo "   API:       http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait
