#!/bin/bash

echo "🛑 Stopping Staging Environment"
echo "===================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
STAGING_DIR="/home/rema/project/002--claude-test"
BACKEND_PID_FILE="$STAGING_DIR/backend-staging.pid"
FRONTEND_PID_FILE="$STAGING_DIR/frontend-staging.pid"

# Stop backend
if [ -f "$BACKEND_PID_FILE" ]; then
    PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Backend process stopped (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Backend process not running${NC}"
    fi
    rm "$BACKEND_PID_FILE"
else
    echo -e "${YELLOW}⚠ Backend PID file not found${NC}"
fi

# Stop frontend
if [ -f "$FRONTEND_PID_FILE" ]; then
    PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend process stopped (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend process not running${NC}"
    fi
    rm "$FRONTEND_PID_FILE"
else
    echo -e "${YELLOW}⚠ Frontend PID file not found${NC}"
fi

# Stop Docker containers
echo -e "${YELLOW}Stopping Docker containers...${NC}"
cd "$STAGING_DIR"
docker-compose -f docker-compose.staging.yml down 2>/dev/null

echo ""
echo -e "${GREEN}✓ Staging environment stopped${NC}"