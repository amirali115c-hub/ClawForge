#!/bin/bash
echo "============================================"
echo "   CLAWFORGE - Starting All Services"
echo "============================================"

# Check if backend is already running
if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "[BACKEND] Already running"
else
    echo "[BACKEND] Starting backend server..."
    cd backend
    python api.py &
    BACKEND_PID=$!
    cd ..
    echo "[BACKEND] Started (PID: $BACKEND_PID)"
fi

# Wait for backend
echo "[WAITING] For backend to initialize (5s)..."
sleep 5

# Start frontend
echo "[FRONTEND] Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "============================================"
echo "   CLAWFORGE Started Successfully!"
echo "============================================"
echo "   Frontend: http://localhost:7860"
echo "   Backend:  http://127.0.0.1:8000"
echo "============================================"
