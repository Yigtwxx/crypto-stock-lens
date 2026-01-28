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

# Load NVM if available (for npm/node)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Also check common node paths
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.nvm/versions/node/*/bin:$PATH"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down Oracle-X...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found! Please install Node.js first.${NC}"
    echo -e "${YELLOW}You can install it via:${NC}"
    echo -e "  - Homebrew: brew install node"
    echo -e "  - NVM: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo -e "  - Download: https://nodejs.org/"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found! Please install Python first.${NC}"
    exit 1
fi

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

# Wait for backend to start
sleep 3

# Start Frontend
echo -e "${CYAN}🎨 Starting Frontend (Next.js) on http://localhost:3000${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 4

# Open browser automatically
echo -e "${GREEN}🌐 Opening browser...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:3000 2>/dev/null || sensible-browser http://localhost:3000
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    start http://localhost:3000
fi

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
