#!/bin/bash

# Oracle-X Financial Terminal - Quick Start Script
# Runs both backend and frontend with a single command

echo "🚀 Oracle-X Financial Terminal Starting..."
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down Oracle-X...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if virtual environment exists for backend
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    echo -e "${YELLOW}📦 Setting up Python virtual environment...${NC}"
    python3 -m venv "$SCRIPT_DIR/backend/venv"
    source "$SCRIPT_DIR/backend/venv/bin/activate"
    pip install -r "$SCRIPT_DIR/backend/requirements.txt" -q
else
    source "$SCRIPT_DIR/backend/venv/bin/activate"
fi

# Check if node_modules exists for frontend
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd "$SCRIPT_DIR/frontend" && npm install
fi

# Start Backend
echo -e "${CYAN}🔧 Starting Backend (FastAPI) on http://localhost:8000${NC}"
cd "$SCRIPT_DIR/backend"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start Frontend
echo -e "${CYAN}🎨 Starting Frontend (Next.js) on http://localhost:3000${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ Oracle-X is running!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "   ${CYAN}Frontend:${NC} http://localhost:3000"
echo -e "   ${CYAN}Backend:${NC}  http://localhost:8000"
echo -e "   ${CYAN}API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait
