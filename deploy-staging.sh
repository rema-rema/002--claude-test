#!/bin/bash

echo "🚀 Deploying to Staging Environment"
echo "===================================="

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
STAGING_DIR="/home/rema/project/002--claude-test"
BACKEND_PID_FILE="$STAGING_DIR/backend-staging.pid"
FRONTEND_PID_FILE="$STAGING_DIR/frontend-staging.pid"

# Function to stop existing processes
stop_existing() {
    echo -e "${YELLOW}Stopping existing staging processes...${NC}"
    
    # Stop backend
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null
            echo -e "${GREEN}✓ Backend process stopped (PID: $PID)${NC}"
        fi
        rm "$BACKEND_PID_FILE"
    fi
    
    # Stop frontend
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null
            echo -e "${GREEN}✓ Frontend process stopped (PID: $PID)${NC}"
        fi
        rm "$FRONTEND_PID_FILE"
    fi
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting Backend API Server...${NC}"
    cd "$STAGING_DIR/backend"
    
    # Export staging environment variables
    export DATABASE_URL="sqlite+aiosqlite:///./staging.db"
    export BACKEND_PORT=8005
    export CORS_ORIGINS="http://localhost:3005,http://localhost:8005"
    export JWT_SECRET="staging-jwt-secret-key"
    export GOOGLE_CLIENT_ID="staging-client-id"
    export GOOGLE_CLIENT_SECRET="staging-client-secret"
    export DEBUG="false"
    export APP_NAME="002 Claude Test Backend - Staging"
    
    # Run database migrations
    echo "Running database migrations..."
    python -m alembic upgrade head
    
    # Start backend server
    nohup python -m uvicorn main:app --host 0.0.0.0 --port 8005 > "$STAGING_DIR/logs/backend-staging.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"
    
    echo -e "${GREEN}✓ Backend started on http://localhost:8005 (PID: $BACKEND_PID)${NC}"
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}Starting Frontend Next.js Server...${NC}"
    cd "$STAGING_DIR/frontend"
    
    # Create staging environment file
    cat > .env.staging << EOF
NEXT_PUBLIC_API_URL=http://localhost:8005
NEXT_PUBLIC_SESSION_ID=staging
NEXT_PUBLIC_GOOGLE_CLIENT_ID=staging-client-id
NODE_ENV=production
EOF
    
    # Build Next.js application
    echo "Building Next.js application..."
    npm run build
    
    # Start frontend server
    PORT=3005 nohup npm start > "$STAGING_DIR/logs/frontend-staging.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
    
    echo -e "${GREEN}✓ Frontend started on http://localhost:3005 (PID: $FRONTEND_PID)${NC}"
}

# Function to verify deployment
verify_deployment() {
    echo -e "${YELLOW}Verifying deployment...${NC}"
    sleep 5
    
    # Check backend health
    if curl -s http://localhost:8005/health > /dev/null; then
        echo -e "${GREEN}✓ Backend API is healthy${NC}"
    else
        echo -e "${RED}✗ Backend API health check failed${NC}"
    fi
    
    # Check frontend
    if curl -s http://localhost:3005 > /dev/null; then
        echo -e "${GREEN}✓ Frontend is accessible${NC}"
    else
        echo -e "${RED}✗ Frontend accessibility check failed${NC}"
    fi
}

# Main execution
main() {
    echo "Starting staging deployment..."
    
    # Create logs directory if it doesn't exist
    mkdir -p "$STAGING_DIR/logs"
    
    # Stop existing processes
    stop_existing
    
    # Start services
    start_backend
    sleep 3
    start_frontend
    
    # Verify deployment
    verify_deployment
    
    echo ""
    echo -e "${GREEN}===================================="
    echo "🎉 Staging Deployment Complete!"
    echo "===================================="
    echo ""
    echo "📍 Access Points:"
    echo "  - Frontend: http://localhost:3005"
    echo "  - Backend API: http://localhost:8005"
    echo "  - API Docs: http://localhost:8005/docs"
    echo ""
    echo "📊 Monitoring:"
    echo "  - Backend logs: tail -f $STAGING_DIR/logs/backend-staging.log"
    echo "  - Frontend logs: tail -f $STAGING_DIR/logs/frontend-staging.log"
    echo ""
    echo "🛑 To stop staging:"
    echo "  ./stop-staging.sh"
    echo -e "${NC}"
}

# Run main function
main