#!/bin/bash

# Session Runner Script - Start applications with proper environment
# Usage: ./scripts/session-runner.sh <session> <app> [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SESSIONS=("session1" "session2" "session3" "session4" "staging")
APPS=("frontend" "backend" "both")

print_usage() {
    echo "Usage: $0 <session> <app> [command]"
    echo ""
    echo "Sessions: session1, session2, session3, session4, staging"
    echo "Apps: frontend, backend, both"
    echo "Commands: dev (default), build, test, clean"
    echo ""
    echo "Examples:"
    echo "  $0 session1 frontend dev    # Run frontend in development mode"
    echo "  $0 session2 backend dev     # Run backend in development mode"
    echo "  $0 session3 both dev        # Run both frontend and backend"
    echo "  $0 staging frontend build   # Build frontend for staging"
}

validate_session() {
    local session=$1
    if [[ " ${SESSIONS[@]} " =~ " $session " ]]; then
        return 0
    else
        echo -e "${RED}Error: Invalid session '$session'${NC}"
        echo -e "Valid sessions: ${SESSIONS[@]}"
        return 1
    fi
}

validate_app() {
    local app=$1
    if [[ " ${APPS[@]} " =~ " $app " ]]; then
        return 0
    else
        echo -e "${RED}Error: Invalid app '$app'${NC}"
        echo -e "Valid apps: ${APPS[@]}"
        return 1
    fi
}

load_env() {
    local session=$1
    local env_file=".env.$session"
    
    if [[ ! -f "$env_file" ]]; then
        echo -e "${RED}Error: Environment file $env_file not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Loading environment for $session...${NC}"
    set -a  # automatically export all variables
    source "$env_file"
    set +a
    
    echo -e "${GREEN}Environment loaded:${NC}"
    echo -e "  Database: $DATABASE_URL"
    echo -e "  Redis: $REDIS_URL"
    echo -e "  Frontend Port: $FRONTEND_PORT"
    echo -e "  Backend Port: $BACKEND_PORT"
}

check_database() {
    local session=$1
    
    echo -e "${BLUE}Checking database connection...${NC}"
    
    # Get port from session
    local port
    case $session in
        "session1") port=5401 ;;
        "session2") port=5402 ;;
        "session3") port=5403 ;;
        "session4") port=5404 ;;
        "staging") port=5405 ;;
    esac
    
    if ! nc -z localhost $port; then
        echo -e "${RED}Error: Database not running on port $port${NC}"
        echo -e "${YELLOW}Run: ./scripts/docker-manager.sh start $session${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Database is running${NC}"
}

check_redis() {
    local session=$1
    
    echo -e "${BLUE}Checking Redis connection...${NC}"
    
    # Get port from session
    local port
    case $session in
        "session1") port=6401 ;;
        "session2") port=6402 ;;
        "session3") port=6403 ;;
        "session4") port=6404 ;;
        "staging") port=6405 ;;
    esac
    
    if ! nc -z localhost $port; then
        echo -e "${RED}Error: Redis not running on port $port${NC}"
        echo -e "${YELLOW}Run: ./scripts/docker-manager.sh start $session${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Redis is running${NC}"
}

run_frontend() {
    local session=$1
    local command=${2:-"dev"}
    
    echo -e "${GREEN}Starting frontend for $session...${NC}"
    
    cd frontend
    
    case $command in
        "dev")
            if [[ ! -d "node_modules" ]]; then
                echo -e "${YELLOW}Installing dependencies...${NC}"
                npm install
            fi
            echo -e "${GREEN}Starting Next.js development server on port $FRONTEND_PORT${NC}"
            npm run dev -- --port $FRONTEND_PORT
            ;;
        "build")
            npm run build
            ;;
        "test")
            npm run test
            ;;
        "clean")
            rm -rf node_modules .next
            echo -e "${GREEN}Frontend cleaned${NC}"
            ;;
        *)
            echo -e "${RED}Unknown frontend command: $command${NC}"
            return 1
            ;;
    esac
}

run_backend() {
    local session=$1
    local command=${2:-"dev"}
    
    echo -e "${GREEN}Starting backend for $session...${NC}"
    
    cd backend
    
    case $command in
        "dev")
            if [[ ! -d "venv" ]]; then
                echo -e "${YELLOW}Creating virtual environment...${NC}"
                python -m venv venv
            fi
            
            echo -e "${YELLOW}Activating virtual environment...${NC}"
            source venv/bin/activate
            
            if [[ ! -f "requirements.installed" ]] || [[ "requirements.txt" -nt "requirements.installed" ]]; then
                echo -e "${YELLOW}Installing dependencies...${NC}"
                pip install -r requirements.txt
                touch requirements.installed
            fi
            
            echo -e "${GREEN}Starting FastAPI server on port $BACKEND_PORT${NC}"
            uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT
            ;;
        "build")
            echo -e "${GREEN}Backend build completed${NC}"
            ;;
        "test")
            source venv/bin/activate
            pytest
            ;;
        "clean")
            rm -rf venv __pycache__ .pytest_cache requirements.installed
            echo -e "${GREEN}Backend cleaned${NC}"
            ;;
        *)
            echo -e "${RED}Unknown backend command: $command${NC}"
            return 1
            ;;
    esac
}

run_both() {
    local session=$1
    local command=${2:-"dev"}
    
    if [[ "$command" == "dev" ]]; then
        echo -e "${GREEN}Starting both frontend and backend for $session...${NC}"
        echo -e "${YELLOW}Note: This will run in background. Use 'ps aux | grep node\\|uvicorn' to see processes.${NC}"
        
        # Start backend in background
        (run_backend "$session" "$command" > "logs/${session}_backend.log" 2>&1 &)
        
        # Start frontend in background  
        (run_frontend "$session" "$command" > "logs/${session}_frontend.log" 2>&1 &)
        
        echo -e "${GREEN}Both services started. Check logs:${NC}"
        echo -e "  Backend: tail -f logs/${session}_backend.log"
        echo -e "  Frontend: tail -f logs/${session}_frontend.log"
        
    else
        run_backend "$session" "$command"
        run_frontend "$session" "$command"
    fi
}

# Main execution
if [[ $# -lt 2 ]]; then
    print_usage
    exit 1
fi

SESSION=$1
APP=$2
COMMAND=${3:-"dev"}

# Validation
if ! validate_session "$SESSION"; then
    exit 1
fi

if ! validate_app "$APP"; then
    exit 1
fi

# Load environment
if ! load_env "$SESSION"; then
    exit 1
fi

# Check services (only for dev command)
if [[ "$COMMAND" == "dev" ]]; then
    if ! check_database "$SESSION"; then
        exit 1
    fi
    
    if ! check_redis "$SESSION"; then
        exit 1
    fi
fi

# Create necessary directories
mkdir -p uploads/$SESSION logs

# Run the application
case $APP in
    "frontend")
        run_frontend "$SESSION" "$COMMAND"
        ;;
    "backend")
        run_backend "$SESSION" "$COMMAND"
        ;;
    "both")
        run_both "$SESSION" "$COMMAND"
        ;;
esac