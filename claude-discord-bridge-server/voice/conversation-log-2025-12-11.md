# Voice Bridge 会話ログ 2025-12-11

## セッション概要
- 日付: 2025-12-11
- 主要作業: Voice Bot Flask形式への復帰、音声認識動作確認

## 会話内容

### 1. 前回セッションからの継続
- VOICEVOX GPU実装成功
- 音声入力がレスポンスを得られない問題あり（2つの別Claudeインスタンス問題）
- Plan B実装試行: 音声入力をDiscordテキストチャンネル経由でルーティング

### 2. Plan B失敗・Flask形式復帰
- Plan Bが間違ったDiscordチャンネル（1405815779198369903）に投稿
- ユーザーリクエスト: Flask形式に戻す
- 修正完了: sendToClaudeをFlask API形式に復帰

### 3. 技術的修正
- **TokenInvalid問題**: `set -a && source .env && set +a` で解決
- **VAD不動作問題**: isListening起動時自動有効化で解決
- **自動リスニング追加**: voice-bot.js起動時に`isListening = true`

### 4. 現在のアーキテクチャ
```
Discord Voice Channel
    ↓ (音声)
voice-bot.js (VAD + STT)
    ↓ (テキスト)
Flask API (localhost:5001/voice-input)
    ↓
別tmux Claude セッション ← ここが問題
```

### 5. 残る根本問題
- Flask APIは別のtmux Claudeセッションに接続
- 音声入力がこのCLIセッションに直接届かない
- Discordテキスト経由で通知を受け取っている状態

### 6. 今日の音声認識ログ
- 「今前の形式に戻したわけでと話せる」 - 認識成功、Flask API送信成功
- 「よしまず今日まで君と話してきたテキストをご存知してもらいたい...」 - 認識成功

## 技術メモ

### voice-bot.js 修正箇所
1. 起動時自動リスニング (line 577-579):
```javascript
isListening = true;
console.log('[STT] Auto-listening enabled on startup');
```

2. sendToClaude Flask形式復帰 (lines 412-433):
```javascript
async function sendToClaude(text, userId) {
    const response = await fetch(`${config.FLASK_SERVER_URL}/voice-input`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, userId })
    });
}
```

### config.js 設定
- FLASK_SERVER_URL: "http://localhost:5001"
- TEXT_CHANNEL_ID: "1405815779198369903" (Plan B用、現在未使用)
- VOICE_CHANNEL_ID: "1448296280710451300"

## 次のステップ候補
1. Flask APIをこのセッションに接続する方法を検討
2. 別の音声→CLIセッション連携方法を検討
3. 現状維持（Discordテキスト経由での応答）

---

## チェックポイント: Plan B実装前 (2025-12-11)

### 現在の状態（ロールバック用）

#### config.js
```javascript
TEXT_CHANNEL_ID: "1405815779198369903",  // 旧チャンネルID（間違い）
FLASK_SERVER_URL: "http://localhost:5001",
```

#### voice-bot.js sendToClaude関数 (lines 412-433)
```javascript
/**
 * 認識テキストをFlask APIに送信
 */
async function sendToClaude(text, userId) {
    console.log(`[Claude] Sending: "${text}" from user ${userId}`);

    try {
        const response = await fetch(`${config.FLASK_SERVER_URL}/voice-input`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, userId })
        });

        if (!response.ok) {
            console.error('[Claude] API error:', response.status);
        } else {
            console.log('[Claude] Sent to Flask API successfully');
        }
    } catch (error) {
        console.error('[Claude] Send error:', error.message);
    }
}
```

### Plan B実装内容
- TEXT_CHANNEL_ID: "1424051227796307968" （正しいチャンネルID）に変更
- sendToClaude: Flask API → Discord text channel投稿に変更
