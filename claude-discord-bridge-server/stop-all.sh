#!/bin/bash
#
# Discord Bridge + 音声認識 全サービス停止スクリプト
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Discord Bridge + 音声認識 全サービス停止${NC}"
echo "================================================="

PID_DIR="$SCRIPT_DIR/.pids"

# ========== 1. Discord Bridge 停止 ==========
echo -e "\n${BLUE}[1/3] Discord Bridge 停止...${NC}"
if ./bin/vai status 2>/dev/null | grep -q "Discord Bot: ✅ Running"; then
    ./bin/vexit 2>/dev/null || true
    echo -e "${GREEN}  ✅ Discord Bridge 停止完了${NC}"
else
    echo -e "${YELLOW}  ⚠️  Discord Bridge は起動していません${NC}"
fi

# ========== 2. Voice Bot 停止 ==========
echo -e "\n${BLUE}[2/3] Voice Bot 停止...${NC}"
if pgrep -f "voice-bot.js" > /dev/null; then
    pkill -f "voice-bot.js" || true
    rm -f "$PID_DIR/voice-bot.pid" 2>/dev/null || true
    echo -e "${GREEN}  ✅ Voice Bot 停止完了${NC}"
else
    echo -e "${YELLOW}  ⚠️  Voice Bot は起動していません${NC}"
fi

# ========== 3. STT Server 停止 ==========
echo -e "\n${BLUE}[3/3] STT Server 停止...${NC}"
if pgrep -f "streaming_stt_server_v2.py" > /dev/null; then
    pkill -f "streaming_stt_server_v2.py" || true
    rm -f "$PID_DIR/stt-server.pid" 2>/dev/null || true
    echo -e "${GREEN}  ✅ STT Server 停止完了${NC}"
else
    echo -e "${YELLOW}  ⚠️  STT Server は起動していません${NC}"
fi

# ========== 確認 ==========
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}🛑 全サービス停止完了${NC}"
echo ""

# 状態確認
echo -e "${BLUE}📊 サービス状態:${NC}"
echo "  STT Server:    $(pgrep -f streaming_stt_server_v2.py > /dev/null && echo '⚠️ まだ起動中' || echo '✅ 停止')"
echo "  Voice Bot:     $(pgrep -f voice-bot.js > /dev/null && echo '⚠️ まだ起動中' || echo '✅ 停止')"
echo "  Discord Bot:   $(pgrep -f discord_bot.py > /dev/null && echo '⚠️ まだ起動中' || echo '✅ 停止')"
echo "  Flask API:     $(pgrep -f flask_app.py > /dev/null && echo '⚠️ まだ起動中' || echo '✅ 停止')"

echo ""
echo -e "${BLUE}🚀 再起動:${NC}"
echo "  ./start-all.sh"
