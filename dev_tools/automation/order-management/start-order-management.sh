#!/bin/bash

# Order Management Server Startup Script
# 起動時にシステム全体を初期化・起動

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}🚀 Order Management Server Starting...${NC}"

# 1. Environment check
echo -e "${YELLOW}📋 Environment Check${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}ℹ️  Copying .env.example to .env${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual values${NC}"
    exit 1
fi

if [ ! -f "config/hooks.json" ]; then
    echo -e "${RED}❌ hooks.json not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration files found${NC}"

# 2. Python dependencies
echo -e "${YELLOW}📦 Checking Python Dependencies${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Install dependencies if needed
python3 -c "import pkg_resources; pkg_resources.require(open('requirements.txt', mode='r').read().split())" 2>/dev/null || {
    echo -e "${YELLOW}📥 Installing Python dependencies${NC}"
    pip install -r requirements.txt
}

echo -e "${GREEN}✅ Python dependencies ready${NC}"

# 3. Directory structure
echo -e "${YELLOW}📁 Creating Directory Structure${NC}"

directories=(
    "queue"
    "active" 
    "completed"
    "templates"
    "logs"
    "scripts"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✅ Created directory: $dir${NC}"
    fi
done

# 4. Bridge integration check
echo -e "${YELLOW}🔗 Bridge Integration Check${NC}"

BRIDGE_DIR="../claude-discord-bridge-server"
if [ -d "$BRIDGE_DIR" ]; then
    if [ -f "$BRIDGE_DIR/sessions.json" ]; then
        echo -e "${GREEN}✅ Claude Discord Bridge integration ready${NC}"
    else
        echo -e "${YELLOW}⚠️  Bridge sessions.json not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Claude Discord Bridge not found at $BRIDGE_DIR${NC}"
fi

# 5. System initialization
echo -e "${YELLOW}⚙️  System Initialization${NC}"

python3 -c "
import sys
sys.path.insert(0, './src')

try:
    from config.settings import settings
    from session_manager import SessionManager
    from queue_manager import QueueManager
    from hooks_manager import HooksManager
    from discord_proxy import DiscordProxy
    
    print('✅ All modules imported successfully')
    
    # Test basic initialization
    sm = SessionManager()
    sm.monitoring = False  # Disable for quick test
    qm = QueueManager()
    hm = HooksManager()
    dp = DiscordProxy()
    
    print('✅ All components initialized successfully')
    
    # Quick system test
    from session_manager import SessionRole
    test_session = sm.create_session('test_startup', SessionRole.WORKER)
    print(f'✅ Test session created: {test_session.session_id}')
    
    sm.destroy_session('test_startup')
    sm.shutdown()
    print('✅ System test completed')
    
except Exception as e:
    print(f'❌ Initialization failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ System initialization successful${NC}"
else
    echo -e "${RED}❌ System initialization failed${NC}"
    exit 1
fi

# 6. Ready message
echo -e "${BLUE}🎉 Order Management Server Ready!${NC}"
echo -e ""
echo -e "${GREEN}📖 Usage:${NC}"
echo -e "  • Run examples: ${YELLOW}python examples/basic_usage.py${NC}"
echo -e "  • Run tests: ${YELLOW}python tests/test_simple_integration.py${NC}"
echo -e "  • Send test request: ${YELLOW}python -c \"from src.discord_proxy import DiscordProxy; dp = DiscordProxy(); dp.send_work_request('2', {'request_id': 'TEST_001', 'task_description': 'Test task'})\"${NC}"
echo -e ""
echo -e "${GREEN}📋 System Status:${NC}"
echo -e "  • Configuration: ✅ Ready"
echo -e "  • Dependencies: ✅ Installed"
echo -e "  • Directories: ✅ Created"
echo -e "  • Components: ✅ Initialized"
echo -e ""
echo -e "${BLUE}🔗 Integration:${NC}"
echo -e "  • Discord Bridge: $([ -d "$BRIDGE_DIR" ] && echo "✅ Available" || echo "⚠️  Not found")"
echo -e "  • Sessions Config: $([ -f "$BRIDGE_DIR/sessions.json" ] && echo "✅ Ready" || echo "⚠️  Missing")"

echo -e ""
echo -e "${GREEN}🚀 System is ready for operation!${NC}"