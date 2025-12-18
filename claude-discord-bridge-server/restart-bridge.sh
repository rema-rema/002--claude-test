#!/bin/bash

# Discord Bridge 再起動スクリプト

echo "=== Discord Bridge 再起動開始 ==="

# 現在のディレクトリに移動
cd /home/rema/project/002--claude-test/claude-discord-bridge-server

# 既存のセッションを停止
echo "既存のセッションを停止中..."
./stop-bridge.sh

# 少し待機
sleep 3

# 再起動
echo "Discord Bridgeを再起動中..."
./start-bridge.sh

echo "=== 再起動完了 ==="
