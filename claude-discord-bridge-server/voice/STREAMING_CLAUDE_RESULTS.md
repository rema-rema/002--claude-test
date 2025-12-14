# Streaming Claude 実装結果レポート

## 実装日
2025-12-13

## 目的
話し終わりから読み上げ開始までの時間を短縮する

## 変更前の問題点
- 話し終わり → 認識完了: 約4秒
- 認識完了 → Claude応答完了: 10秒以上
- 合計: 14秒以上

## 実装内容

### 1. ストリーミングClaude API呼び出し
- 新規ファイル: `claude-streaming.js`
- Claude APIをストリーミングモードで呼び出し
- 文が完成するたびにコールバックを呼び出す

### 2. voice-bot.jsの修正
- `USE_STREAMING_CLAUDE=true` で有効化
- 文が完成するたびに即座にTTSに送信
- 全文完了を待たずに読み上げ開始

### 3. config.jsの追加設定
```javascript
ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
CLAUDE_MODEL: process.env.CLAUDE_MODEL || "claude-sonnet-4-20250514",
CLAUDE_MAX_TOKENS: parseInt(process.env.CLAUDE_MAX_TOKENS) || 1024,
```

## テスト結果

### 合成音声テスト (test-streaming-claude.js)

| テスト | TTFS (最初の文まで) | 合計時間 | 文数 |
|--------|---------------------|----------|------|
| 今日の天気は？ | 2074ms | 2576ms | 2 |
| おすすめの言語は？ | 2211ms | 3264ms | 3 |
| 短い詩を作って | 2100ms | 2651ms | 3 |

**平均TTFS: 2128ms**

### 改善効果
- 変更前: 10秒以上
- 変更後: 約2秒
- **改善率: 約80%**

## 使用方法

### 起動コマンド
```bash
cd /home/rema/project/002--claude-test/claude-discord-bridge-server/voice

# ストリーミングClaude + ストリーミングSTT有効
USE_STREAMING_STT=true USE_STREAMING_CLAUDE=true node voice-bot.js
```

### 環境変数
```bash
# .env に追加
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514  # オプション
CLAUDE_MAX_TOKENS=1024  # オプション
```

### テスト実行
```bash
node test-streaming-claude.js
```

## 技術詳細

### ストリーミングの仕組み
1. Claude APIにstream=trueでリクエスト
2. Server-Sent Events (SSE) でレスポンスを受信
3. content_block_delta イベントからテキストを抽出
4. 句点(。！？)で文を区切ってTTSに送信
5. 最初の文が完成した時点で読み上げ開始

### 会話履歴
- 最大10メッセージを保持
- `clearHistory()` でリセット可能

## 制限事項

1. **TTFS 約2秒はClaude API自体のレイテンシ**
   - これ以上の短縮はAPI側の改善が必要

2. **モデル選択**
   - Sonnet 4を使用（速度重視）
   - Opus 4を使うと遅くなる

3. **従来のtmux経由モードとの違い**
   - ストリーミングモードではCLAUDE.mdのコンテキストが適用されない
   - シンプルな音声アシスタントとして動作

## 次のステップ（オプション）

1. Haiku 3.5への変更（さらに高速化、精度低下あり）
2. システムプロンプトのカスタマイズ
3. 会話履歴の永続化
