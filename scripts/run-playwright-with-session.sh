#!/bin/bash

# Integration script for running Playwright with session detection
# Usage: ./scripts/run-playwright-with-session.sh [session_id] [test_pattern]

set -e

# Default values
SESSION_ID=${1:-"002"}
TEST_PATTERN=${2:-"colorful-video"}

echo "🎭 Running Playwright tests with multi-channel notification"
echo "📡 Session: ${SESSION_ID}"
echo "🧪 Test Pattern: ${TEST_PATTERN}"
echo "----------------------------------------"

# Source environment variables from .env
if [[ -f .env ]]; then
    echo "📁 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env file not found"
fi

# Set session environment variable
export CURRENT_SESSION_ID="${SESSION_ID}"

# Extract channel ID for the session from environment
CHANNEL_VAR="CC_DISCORD_CHANNEL_ID_${SESSION_ID}"
CHANNEL_ID=${!CHANNEL_VAR}

if [[ -n "${CHANNEL_ID}" ]]; then
    echo "✅ Channel mapping: Session ${SESSION_ID} → Channel ${CHANNEL_ID}"
else
    echo "⚠️  Warning: No channel configured for session ${SESSION_ID}"
    echo "💡 Available channels:"
    env | grep "CC_DISCORD_CHANNEL_ID_" | sed 's/^/    /'
fi

echo "----------------------------------------"

# Run Playwright with the multi-channel reporter
npx playwright test "${TEST_PATTERN}" --reporter=./src/multichannel-notify/playwright-channel-reporter.js

echo "----------------------------------------"
echo "✅ Playwright execution completed"