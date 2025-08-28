#!/bin/bash

# チャンネルCでの通知テスト

echo "🧪 チャンネルC通知テスト開始"
echo "チャンネルID: 1410119561562558534"

# 環境変数設定
source .env
export CURRENT_SESSION_ID="002_C"

echo "テスト実行中..."
npx playwright test test-failure-case --reporter=./src/multichannel-notify/playwright-channel-reporter.js