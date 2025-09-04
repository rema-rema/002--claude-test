#!/bin/bash

# Test Session Environment Loading
# This script tests all session environments

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Session Environment Loading${NC}"
echo ""

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Test sessions
SESSIONS=("session-a" "session-b" "session-c" "session-d")

for session in "${SESSIONS[@]}"; do
    echo -e "${YELLOW}Testing ${session}...${NC}"
    
    # Source the environment in a subshell to test loading
    if (
        source "${PROJECT_DIR}/scripts/load-session-env.sh" "${session}" 2>/dev/null && 
        
        # Verify key variables are set
        [[ -n "$SESSION_ID" ]] &&
        [[ -n "$FRONTEND_PORT" ]] &&
        [[ -n "$BACKEND_PORT" ]] &&
        [[ -n "$DATABASE_URL" ]] &&
        [[ -n "$REDIS_URL" ]]
    ); then
        echo -e "  ${GREEN}✅ ${session} loaded successfully${NC}"
        
        # Get the actual values in subshell for verification
        (
            source "${PROJECT_DIR}/scripts/load-session-env.sh" "${session}" 2>/dev/null
            echo -e "    Session: ${SESSION_ID}, Frontend: ${FRONTEND_PORT}, Backend: ${BACKEND_PORT}"
        )
    else
        echo -e "  ${RED}❌ ${session} failed to load${NC}"
        exit 1
    fi
    echo ""
done

echo -e "${GREEN}🎉 All session environments tested successfully!${NC}"
echo ""

# Test Docker Compose integration (optional check)
echo -e "${YELLOW}🐳 Testing Docker Compose Configuration${NC}"

# Check if docker-compose.yml exists and is valid
if command -v docker-compose >/dev/null 2>&1; then
    if docker-compose config >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose configuration is valid${NC}"
        
        # List available services
        echo -e "${BLUE}Available services:${NC}"
        docker-compose config --services | grep -E "session-[a-d]|staging" | sort 2>/dev/null | while read service; do
            echo -e "  • $service"
        done
    else
        echo -e "${YELLOW}⚠️  Docker Compose configuration has validation issues (non-critical)${NC}"
        echo -e "    Services are still usable with manual docker commands"
    fi
else
    echo -e "${YELLOW}⚠️  Docker Compose not available (non-critical)${NC}"
    echo -e "    Individual Docker services can still be started manually"
fi

echo ""
echo -e "${BLUE}📋 Usage Instructions:${NC}"
echo -e "${YELLOW}To use a session environment:${NC}"
echo -e "  source scripts/load-session-env.sh session-a"
echo -e "  npm run dev  # Start development server"
echo ""
echo -e "${YELLOW}To start database services:${NC}"
echo -e "  docker-compose up postgres-session-a redis-session-a -d"
echo -e "  # or manually with docker:"
echo -e "  docker run -d -p 5401:5432 -e POSTGRES_DB=session_a_dev postgres:15-alpine"
echo ""

# Clean up old environment files
echo -e "${BLUE}🧹 Cleaning up old environment files${NC}"
OLD_FILES=(".env.session1" ".env.session2" ".env.session3" ".env.session4")

for old_file in "${OLD_FILES[@]}"; do
    if [[ -f "$old_file" ]]; then
        echo -e "${YELLOW}  Moving $old_file to backups/...${NC}"
        mkdir -p backups/old-env-files
        mv "$old_file" "backups/old-env-files/"
        echo -e "${GREEN}  ✅ Moved $old_file${NC}"
    fi
done

echo ""
echo -e "${GREEN}✨ Environment configuration improved successfully!${NC}"
echo -e "${BLUE}Old .env.session1-4 files replaced with better organized config/sessions/ structure${NC}"