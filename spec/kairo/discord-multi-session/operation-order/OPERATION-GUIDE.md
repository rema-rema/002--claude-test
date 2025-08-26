# Discord承認システム 運用手順書

## 🚀 起動手順

### 1. 環境変数設定
```bash
# .envファイルを作成
cp .env.example .env

# 必要な値を設定
# CC_DISCORD_TOKEN - Discord Botトークン
# CC_DISCORD_CHANNEL_ID - 通知チャンネルID
# CC_DISCORD_USER_ID - 権限ユーザーID
# ANTHROPIC_API_KEY - Claude APIキー
```

### 2. 依存関係のインストール
```bash
npm install
```

### 3. Bot起動
```bash
# 本番環境
npm start

# 開発環境（ファイル監視）
npm run dev
```

## 💬 Discord承認フロー

### 自動承認依頼
1. **テスト失敗発生** → 自動分析 → Discord通知
2. **通知内容**:
   - テスト名・エラー内容
   - 修正提案・信頼度
   - 承認コマンド（`!approve [id]`）

### 手動承認操作
```bash
# 承認（修正実行）
!approve abc123

# 拒否（修正スキップ）
!reject abc123

# ステータス確認
!status abc123
```

### 既存コマンド
```bash
!clear    # Claude会話履歴クリア
!history  # 会話履歴長確認
!help     # コマンド一覧表示
```

## 🔧 トラブルシューティング

### Bot起動失敗
**症状**: `npm start` でエラー
**原因**: 環境変数未設定
**解決**: `.env`ファイルの確認・設定

### Discord通知が来ない
**症状**: テスト失敗しても通知なし
**原因**: チャンネルID・権限設定ミス
**解決**: `CC_DISCORD_CHANNEL_ID`とBot権限確認

### 承認コマンド無応答
**症状**: `!approve`しても反応なし  
**原因**: 
1. 無効なApproval ID
2. すでに処理済み
3. タイムアウト（24時間経過）
**解決**: `!status [id]`でステータス確認

### Claude修正が実行されない
**症状**: 承認後に修正が進まない
**原因**: Claude API接続エラー
**解決**: `ANTHROPIC_API_KEY`とネットワーク確認

### メモリリーク・性能問題
**症状**: 長時間運用で動作が重い
**原因**: 承認依頼の蓄積
**解決**: Bot再起動（承認依頼は自動クリーンアップ）

## 📊 監視ポイント

### 正常動作確認
- [ ] テスト失敗時にDiscord通知
- [ ] 承認・拒否コマンドが動作
- [ ] Claude修正依頼が送信
- [ ] 24時間タイムアウトが機能

### 異常検知
- [ ] 同一テストの10回連続失敗
- [ ] Discord API連携エラー
- [ ] Claude API連携エラー
- [ ] メモリ使用量異常増加

## 🛠️ メンテナンス

### 定期作業（週次）
- [ ] 承認依頼履歴の確認
- [ ] エラーログの確認
- [ ] ディスク使用量確認

### 緊急時対応
```bash
# Bot緊急停止
pkill -f "node.*discord-bot"

# ログ確認
tail -f bot.log

# 強制再起動
npm start
```