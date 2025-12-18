#!/bin/bash
#
# Voice Bot B 起動スクリプト
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 環境変数読み込み
source /home/rema/project/002--claude-test/.env

# Voice Bot B として起動
export VOICE_BOT_INSTANCE=B

echo "🎤 Starting Voice Bot B..."
echo "   Token: ${VOICE_BOT_B_TOKEN:0:20}..."
echo "   Voice Channel: $VOICE_BOT_B_CHANNEL_ID"
echo "   API Port: 3002"

node voice-bot.js
