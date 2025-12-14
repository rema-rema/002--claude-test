#!/bin/bash
#
# Discord Bridge + 音声認識 全サービス起動スクリプト
#
# 起動するサービス:
# 1. Streaming STT Server (Whisper + Silero VAD)
# 2. Voice Bot (Discord音声連携)
# 3. Discord Bridge (Flask + Claude Code sessions)
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

echo -e "${BLUE}🚀 Discord Bridge + 音声認識 全サービス起動${NC}"
echo "================================================="

# PIDファイルディレクトリ
PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"

# ========== 1. Streaming STT Server ==========
echo -e "\n${BLUE}[1/3] Streaming STT Server (Whisper + Silero VAD)...${NC}"

if pgrep -f "streaming_stt_server_v2.py" > /dev/null; then
    echo -e "${GREEN}  ✅ STT Server は既に起動済み${NC}"
else
    echo -e "${YELLOW}  📡 STT Server を起動中...${NC}"

    # Python仮想環境をアクティベート
    if [ -d "$SCRIPT_DIR/voice/.venv" ]; then
        source "$SCRIPT_DIR/voice/.venv/bin/activate"
    fi

    # バックグラウンドで起動
    cd "$SCRIPT_DIR/voice"
    nohup python streaming_stt_server_v2.py > "$SCRIPT_DIR/logs/stt-server.log" 2>&1 &
    STT_PID=$!
    echo $STT_PID > "$PID_DIR/stt-server.pid"
    cd "$SCRIPT_DIR"

    # 起動確認 (Whisperモデルロードに時間がかかる)
    echo -e "  ⏳ モデルロード中... (約30秒)"
    sleep 5

    if pgrep -f "streaming_stt_server_v2.py" > /dev/null; then
        echo -e "${GREEN}  ✅ STT Server 起動成功 (PID: $STT_PID)${NC}"
    else
        echo -e "${RED}  ❌ STT Server 起動失敗${NC}"
        echo "     ログ確認: tail -f logs/stt-server.log"
    fi
fi

# ========== 2. Voice Bot ==========
echo -e "\n${BLUE}[2/3] Voice Bot (Discord音声連携)...${NC}"

if pgrep -f "voice-bot.js" > /dev/null; then
    echo -e "${GREEN}  ✅ Voice Bot は既に起動済み${NC}"
else
    echo -e "${YELLOW}  🎤 Voice Bot を起動中...${NC}"

    cd "$SCRIPT_DIR/voice"

    # 環境変数設定 (ストリーミングモード有効)
    export USE_STREAMING_STT=true
    export USE_STREAMING_CLAUDE=false

    nohup node voice-bot.js > "$SCRIPT_DIR/logs/voice-bot.log" 2>&1 &
    VOICE_PID=$!
    echo $VOICE_PID > "$PID_DIR/voice-bot.pid"
    cd "$SCRIPT_DIR"

    sleep 3

    if pgrep -f "voice-bot.js" > /dev/null; then
        echo -e "${GREEN}  ✅ Voice Bot 起動成功 (PID: $VOICE_PID)${NC}"
    else
        echo -e "${RED}  ❌ Voice Bot 起動失敗${NC}"
        echo "     ログ確認: tail -f logs/voice-bot.log"
    fi
fi

# ========== 3. Discord Bridge ==========
echo -e "\n${BLUE}[3/3] Discord Bridge (Flask + Claude Code)...${NC}"

if ./bin/vai status 2>/dev/null | grep -q "Discord Bot: ✅ Running"; then
    echo -e "${GREEN}  ✅ Discord Bridge は既に起動済み${NC}"
else
    echo -e "${YELLOW}  🤖 Discord Bridge を起動中...${NC}"
    ./bin/vai

    # 起動通知
    echo -e "\n${BLUE}  📡 各セッションに起動通知を送信中...${NC}"
    sleep 5
    ./bin/startup-notify.py 2>/dev/null || true
fi

# ========== 状態確認 ==========
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}🎉 全サービス起動完了！${NC}"
echo ""

# ポート確認
echo -e "${BLUE}📊 サービス状態:${NC}"
echo "  STT Server:    ws://localhost:8765 $(pgrep -f streaming_stt_server_v2.py > /dev/null && echo '✅' || echo '❌')"
echo "  Voice Bot:     http://localhost:3001 $(pgrep -f voice-bot.js > /dev/null && echo '✅' || echo '❌')"
echo "  Flask API:     http://localhost:5001 $(pgrep -f flask_app.py > /dev/null && echo '✅' || echo '❌')"

echo ""
echo -e "${BLUE}📁 ログファイル:${NC}"
echo "  tail -f logs/stt-server.log  # STT Server"
echo "  tail -f logs/voice-bot.log   # Voice Bot"

echo ""
echo -e "${BLUE}🛑 停止方法:${NC}"
echo "  ./stop-all.sh"

echo ""
echo -e "${BLUE}🔄 再起動:${NC}"
echo "  ./restart-all.sh"
