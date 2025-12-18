#!/bin/bash
#
# Voice Bot C 起動スクリプト
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 環境変数読み込み（set -a で自動export）
set -a
source /home/rema/project/002--claude-test/.env
set +a

# Voice Bot C として起動
export VOICE_BOT_INSTANCE=C

echo "🎤 Starting Voice Bot C..."
echo "   Token: ${VOICE_BOT_C_TOKEN:0:20}..."
echo "   Voice Channel: $VOICE_BOT_C_CHANNEL_ID"
echo "   API Port: 3003"

node voice-bot.js
