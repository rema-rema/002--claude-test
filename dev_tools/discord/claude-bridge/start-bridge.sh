#!/bin/bash
#
# Claude-Discord Bridge 起動スクリプト
# 手動での簡単起動用
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Claude-Discord Bridge マルチセッション起動${NC}"
echo "========================================="

# Check if already running
if ./bin/vai status | grep -q "Discord Bot: ✅ Running"; then
    echo -e "${GREEN}✅ サービスは既に起動済みです${NC}"
    echo ""
    ./bin/vai status
    exit 0
fi

# Start services
echo -e "${BLUE}📡 サービスを起動中...${NC}"
./bin/vai

echo ""
echo -e "${GREEN}✅ 起動完了！${NC}"
echo ""
echo "マルチセッション利用方法:"
echo "  ./bin/vai status           - 状態確認（全セッション）"
echo "  ./bin/vai list-sessions    - セッション一覧表示"
echo "  ./bin/vai add-session <ID> - 新セッション追加"
echo "  ./bin/vai recover <N>      - セッション復旧"
echo "  ./bin/vai view             - セッション並列表示"
echo "  ./bin/vai doctor           - 環境診断" 
echo "  ./bin/vexit                - サービス停止"
echo ""
echo "Discord送信コマンド:"
echo "  dp 'メッセージ'            - デフォルトセッション"
echo "  dp 2 'メッセージ'          - セッション2指定"
echo "  dp 3 'メッセージ'          - セッション3指定"
echo "  dp 4 'メッセージ'          - セッション4指定"
echo ""

# Display active sessions
echo -e "${BLUE}📱 設定済みセッション:${NC}"
./bin/vai list-sessions 2>/dev/null | grep -A10 "Configured Sessions:" | tail -n +3 || echo "  設定済みセッションの取得に失敗"
echo ""
echo -e "${BLUE}Working Directory: /workspaces/002--claude-test${NC}"

# セッション起動通知を送信
echo ""
echo -e "${BLUE}📡 各セッションに起動通知を送信中...${NC}"
sleep 5  # セッションが完全に起動するまで待機
./bin/startup-notify.py

echo ""
echo -e "${GREEN}✅ 全セッションの準備が完了しました！${NC}"
echo -e "${GREEN}   会話を開始できます${NC}"