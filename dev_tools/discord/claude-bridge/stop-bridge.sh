#!/bin/bash
#
# Claude-Discord Bridge 停止スクリプト
# 手動での簡単停止用
#

set -e

# Get script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Claude-Discord Bridge マルチセッション停止${NC}"
echo "========================================="

# Check if running
if cd "$SCRIPT_DIR" && ./bin/vai status | grep -q "Discord Bot: ❌ Stopped"; then
    echo -e "${GREEN}✅ サービスは既に停止済みです${NC}"
    echo ""
    # Show final session status
    echo -e "${BLUE}📊 最終セッション状態:${NC}"
    cd "$SCRIPT_DIR" && ./bin/vai list-sessions 2>/dev/null | grep -A10 "Configured Sessions:" | tail -n +3 || echo "  セッション一覧の取得に失敗"
    exit 0
fi

# Show sessions before stopping
echo -e "${BLUE}📊 停止前セッション状態:${NC}"
cd "$SCRIPT_DIR" && ./bin/vai status 2>/dev/null | grep -A20 "Discord Sessions:" | head -10 || echo "  状態取得に失敗"

# Stop services
echo ""
echo -e "${BLUE}📡 全セッション・サービスを停止中...${NC}"
cd "$SCRIPT_DIR" && ./bin/vexit

echo ""
echo -e "${GREEN}✅ 停止完了！${NC}"
echo ""
echo "再起動方法:"
echo "  ./start-bridge.sh    - サービス起動"
echo "  ./bin/vai status     - 状態確認"