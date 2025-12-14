#!/bin/bash
#
# Discord Bridge + 音声認識 全サービス再起動スクリプト
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Discord Bridge + 音声認識 全サービス再起動${NC}"
echo "================================================="

# 停止
echo -e "\n${BLUE}[Step 1] 全サービス停止...${NC}"
./stop-all.sh

# 少し待機
echo -e "\n${BLUE}[Step 2] 5秒待機...${NC}"
sleep 5

# 起動
echo -e "\n${BLUE}[Step 3] 全サービス起動...${NC}"
./start-all.sh

echo -e "\n${GREEN}🔄 再起動完了！${NC}"
