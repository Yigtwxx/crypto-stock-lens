#!/bin/bash

# Oracle-X Financial Terminal - Quick Start Script
# Runs both backend and frontend with a single command

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS & STYLES
# ═══════════════════════════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Box drawing characters
H_LINE="═"
V_LINE="║"
TL_CORNER="╔"
TR_CORNER="╗"
BL_CORNER="╚"
BR_CORNER="╝"
T_JOINT="╦"
B_JOINT="╩"
L_JOINT="╠"
R_JOINT="╣"
CROSS="╬"

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

print_banner() {
    clear
    echo ""
    echo -e "${PURPLE}${BOLD}"
    echo "    ╔═══════════════════════════════════════════════════════════════╗"
    echo "    ║                                                               ║"
    echo "    ║      ██████╗ ██████╗  █████╗  ██████╗██╗     ███████╗         ║"
    echo "    ║     ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔════╝         ║"
    echo "    ║     ██║   ██║██████╔╝███████║██║     ██║     █████╗           ║"
    echo "    ║     ██║   ██║██╔══██╗██╔══██║██║     ██║     ██╔══╝           ║"
    echo "    ║     ╚██████╔╝██║  ██║██║  ██║╚██████╗███████╗███████╗         ║"
    echo "    ║      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝         ║"
    echo "    ║                                                               ║"
    echo -e "    ║           ${CYAN}⚡ FINANCIAL INTELLIGENCE TERMINAL ⚡${PURPLE}              ║"
    echo "    ║                                                               ║"
    echo "    ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

print_separator() {
    echo -e "${GRAY}    ─────────────────────────────────────────────────────────────────${NC}"
}

print_section() {
    local title=$1
    echo ""
    echo -e "${WHITE}${BOLD}    ▸ ${title}${NC}"
    echo -e "${GRAY}    ─────────────────────────────────────────────────────────────────${NC}"
}

print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "info")
            echo -e "    ${CYAN}ℹ${NC}  ${message}"
            ;;
        "success")
            echo -e "    ${GREEN}✓${NC}  ${message}"
            ;;
        "warning")
            echo -e "    ${YELLOW}⚠${NC}  ${message}"
            ;;
        "error")
            echo -e "    ${RED}✗${NC}  ${message}"
            ;;
        "wait")
            echo -e "    ${BLUE}◌${NC}  ${message}"
            ;;
        "run")
            echo -e "    ${PURPLE}▶${NC}  ${message}"
            ;;
    esac
}

print_url() {
    local label=$1
    local url=$2
    echo -e "    ${GRAY}│${NC}   ${WHITE}${label}:${NC} ${CYAN}${BOLD}${url}${NC}"
}

spinner() {
    local pid=$1
    local message=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % ${#spin} ))
        printf "\r    ${PURPLE}${spin:$i:1}${NC}  ${message}"
        sleep 0.1
    done
    printf "\r    ${GREEN}✓${NC}  ${message}\n"
}

progress_bar() {
    local current=$1
    local total=$2
    local width=40
    local percent=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))
    
    printf "\r    ${GRAY}[${NC}"
    printf "${PURPLE}%*s${NC}" $filled | tr ' ' '█'
    printf "${GRAY}%*s${NC}" $empty | tr ' ' '░'
    printf "${GRAY}]${NC} ${WHITE}%3d%%${NC}" $percent
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load NVM if available (for npm/node)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Also check common node paths
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.nvm/versions/node/*/bin:$PATH"

# Function to cleanup on exit
cleanup() {
    echo ""
    print_separator
    echo ""
    echo -e "    ${YELLOW}${BOLD}🛑 Shutting down Oracle-X...${NC}"
    echo ""
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        print_status "info" "Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        print_status "info" "Frontend stopped"
    fi
    
    echo ""
    echo -e "    ${GRAY}Thank you for using Oracle-X! 👋${NC}"
    echo ""
    exit 0
}

trap cleanup SIGINT SIGTERM

# Print banner
print_banner

# ─────────────────────────────────────────────────────────────────
# SYSTEM CHECK
# ─────────────────────────────────────────────────────────────────
print_section "SYSTEM CHECK"

# Check npm
if ! command -v npm &> /dev/null; then
    print_status "error" "npm not found!"
    echo ""
    echo -e "    ${YELLOW}Install Node.js via:${NC}"
    echo -e "    ${GRAY}•${NC} Homebrew: ${CYAN}brew install node${NC}"
    echo -e "    ${GRAY}•${NC} NVM: ${CYAN}curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash${NC}"
    echo -e "    ${GRAY}•${NC} Download: ${CYAN}https://nodejs.org/${NC}"
    echo ""
    exit 1
else
    print_status "success" "Node.js $(node -v) ${GRAY}detected${NC}"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_status "error" "Python3 not found!"
    echo ""
    exit 1
else
    print_status "success" "Python $(python3 --version | cut -d' ' -f2) ${GRAY}detected${NC}"
fi

# ─────────────────────────────────────────────────────────────────
# DEPENDENCIES
# ─────────────────────────────────────────────────────────────────
print_section "DEPENDENCIES"

# Check virtual environment
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    print_status "wait" "Creating Python virtual environment..."
    python3 -m venv "$SCRIPT_DIR/backend/venv" 2>/dev/null
    source "$SCRIPT_DIR/backend/venv/bin/activate"
    print_status "wait" "Installing Python packages..."
    pip install -r "$SCRIPT_DIR/backend/requirements.txt" -q 2>/dev/null
    print_status "success" "Python environment ready"
else
    source "$SCRIPT_DIR/backend/venv/bin/activate"
    print_status "success" "Python environment ${GRAY}(cached)${NC}"
fi

# Check node_modules
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    print_status "wait" "Installing frontend packages..."
    cd "$SCRIPT_DIR/frontend" && npm install --silent 2>/dev/null
    print_status "success" "Frontend packages installed"
else
    print_status "success" "Frontend packages ${GRAY}(cached)${NC}"
fi

# ─────────────────────────────────────────────────────────────────
# STARTING SERVICES
# ─────────────────────────────────────────────────────────────────
print_section "STARTING SERVICES"

# Start Backend
print_status "run" "Starting ${BOLD}Backend${NC} ${GRAY}(FastAPI)${NC}..."
cd "$SCRIPT_DIR/backend"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 2

# Check if backend started
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_status "success" "Backend running ${GRAY}(PID: $BACKEND_PID)${NC}"
else
    print_status "error" "Backend failed to start!"
    exit 1
fi

# Start Frontend
print_status "run" "Starting ${BOLD}Frontend${NC} ${GRAY}(Next.js)${NC}..."
cd "$SCRIPT_DIR/frontend"
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!
sleep 3

# Check if frontend started
if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_status "success" "Frontend running ${GRAY}(PID: $FRONTEND_PID)${NC}"
else
    print_status "error" "Frontend failed to start!"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────
# READY
# ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}"
echo "    ╔═══════════════════════════════════════════════════════════════╗"
echo "    ║                                                               ║"
echo "    ║              🎉  ORACLE-X IS READY!  🎉                       ║"
echo "    ║                                                               ║"
echo "    ╠═══════════════════════════════════════════════════════════════╣"
echo -e "${NC}"
print_url "Frontend" "http://localhost:3000"
print_url "Backend " "http://localhost:8000"
print_url "API Docs" "http://localhost:8000/docs"
echo -e "${GREEN}${BOLD}"
echo "    ║                                                               ║"
echo "    ╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000 2>/dev/null
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:3000 2>/dev/null || sensible-browser http://localhost:3000 2>/dev/null
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    start http://localhost:3000 2>/dev/null
fi

echo ""
echo -e "    ${GRAY}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "    ${GRAY}│${NC}  ${YELLOW}⌨${NC}  Press ${BOLD}Ctrl+C${NC} to stop all services                      ${GRAY}│${NC}"
echo -e "    ${GRAY}│${NC}  ${CYAN}📊${NC}  Logs are hidden for cleaner output                       ${GRAY}│${NC}"
echo -e "    ${GRAY}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

# Wait for both processes
wait
