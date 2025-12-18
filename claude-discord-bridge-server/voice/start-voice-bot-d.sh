#!/bin/bash
#
# Voice Bot D 起動スクリプト
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 環境変数読み込み（set -a で自動export）
set -a
source /home/rema/project/002--claude-test/.env
set +a

# Voice Bot D として起動
export VOICE_BOT_INSTANCE=D

echo "🎤 Starting Voice Bot D..."
echo "   Token: ${VOICE_BOT_D_TOKEN:0:20}..."
echo "   Voice Channel: $VOICE_BOT_D_CHANNEL_ID"
echo "   API Port: 3004"

node voice-bot.js
