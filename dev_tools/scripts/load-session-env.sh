#!/bin/bash

# Session Environment Loader
# Usage: source dev_tools/scripts/load-session-env.sh [session-name]
# Example: source dev_tools/scripts/load-session-env.sh session-a

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get project directory (from dev_tools/scripts -> project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Default session if not specified
SESSION_NAME="${1:-session-a}"

# Validate session name
VALID_SESSIONS=("session-a" "session-b" "session-c" "session-d")
if [[ ! " ${VALID_SESSIONS[@]} " =~ " ${SESSION_NAME} " ]]; then
    echo -e "${RED}❌ Invalid session name: ${SESSION_NAME}${NC}"
    echo -e "${YELLOW}Valid sessions: ${VALID_SESSIONS[*]}${NC}"
    return 1
fi

# Paths
BASE_ENV="${PROJECT_DIR}/dev_tools/environments/base.env"
SESSION_ENV="${PROJECT_DIR}/dev_tools/environments/sessions/${SESSION_NAME}.env"

# Check if files exist
if [[ ! -f "${BASE_ENV}" ]]; then
    echo -e "${RED}❌ Base environment file not found: ${BASE_ENV}${NC}"
    return 1
fi

if [[ ! -f "${SESSION_ENV}" ]]; then
    echo -e "${RED}❌ Session environment file not found: ${SESSION_ENV}${NC}"
    return 1
fi

# Create temporary combined environment file
TEMP_ENV=$(mktemp)
trap "rm -f ${TEMP_ENV}" EXIT

# Combine base.env and session-specific env
echo "# Combined Environment for ${SESSION_NAME}" > "${TEMP_ENV}"
echo "# Generated at $(date)" >> "${TEMP_ENV}"
echo "" >> "${TEMP_ENV}"

echo "# Base Configuration" >> "${TEMP_ENV}"
cat "${BASE_ENV}" >> "${TEMP_ENV}"
echo "" >> "${TEMP_ENV}"

echo "# Session-Specific Configuration" >> "${TEMP_ENV}"
cat "${SESSION_ENV}" >> "${TEMP_ENV}"

# Load environment variables
set -a  # automatically export all variables
source "${TEMP_ENV}"
set +a  # stop automatically exporting

# Display loaded configuration
echo -e "${GREEN}✅ Environment loaded for ${SESSION_NAME}${NC}"
echo -e "${YELLOW}📋 Configuration Summary:${NC}"
echo -e "  • Session: ${SESSION_ID} (${SESSION_NAME})"
echo -e "  • Frontend: http://localhost:${FRONTEND_PORT}"
echo -e "  • Backend: http://localhost:${BACKEND_PORT}"
echo -e "  • Database: ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo -e "  • Redis: ${REDIS_HOST}:${REDIS_PORT}"
echo -e "  • Upload Dir: ${UPLOAD_DIR}"
echo -e "  • Log File: ${LOG_FILE}"

# Export common variables for scripts
export PROJECT_SESSION="${SESSION_NAME}"
export PROJECT_SESSION_ID="${SESSION_ID}"

# Create session directories if they don't exist
mkdir -p "${PROJECT_DIR}/dev_tools/uploads/${SESSION_NAME}"
mkdir -p "${PROJECT_DIR}/dev_tools/logs"

echo -e "${GREEN}✅ Environment ready for development${NC}"