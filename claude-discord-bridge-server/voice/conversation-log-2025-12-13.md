# Voice Bridge 会話ログ 2025-12-13

## セッション概要
- 日付: 2025-12-13
- 主要作業: VADレイテンシ改善（43秒→4秒）、ストリーミングClaude実装

---

## 達成した改善

### レイテンシ改善結果
| 項目 | 改善前 | 改善後 |
|------|--------|--------|
| 認識完了まで | 43秒 | ~4秒 |
| Claude応答開始 | 10秒以上 | ~2秒 |
| **合計** | **14秒以上** | **~4秒** |

**改善率: 約70%**

---

## 会話内容

### 1. 43秒遅延問題の発覚
- テスト文: 「本日の会議では、来期の予算計画と新規プロジェクトの進捗について報告します。予算については前年比10%増の見込みです。」
- VADが息継ぎで「発話終了」と誤判定
- 複数回のSTT処理が実行され、43秒かかった

### 2. 根本原因の特定
- **問題**: VADが1.5秒の無音で「発話終了」と判定
- **結果**: 息継ぎのたびにSTT処理が走る → 遅延蓄積

### 3. 解決策A: サーバー側VAD + MIN_SILENCE_MS延長
- streaming_stt_server_v2.py の MIN_SILENCE_MS を 600ms → 1500ms に変更
- クライアント側からendメッセージを送信する方式に変更

### 4. テスト結果（VAD改善後）
- 同じテスト文で4秒に短縮
- 息継ぎで分断されなくなった

### 5. 次のボトルネック: Claude応答時間
- 認識完了後、Claude応答完了まで10秒以上
- ユーザーの指摘: 「読み上げ開始が遅い」

### 6. ストリーミングClaude実装
- Claude APIをストリーミングモードで呼び出し
- 文が完成するたびにTTSに送信
- 全文完了を待たずに読み上げ開始

### 7. 最終テスト結果
- 認識: 「今日の天気はどうですか。」
- Claude応答: 2文がストリーミングで到着
- 1文目到着時点で即座にTTS開始
- TTFS（最初の文まで）: 約2秒

---

## 変更したファイル

### 1. streaming_stt_server_v2.py
```python
# 変更前
MIN_SILENCE_MS = 600

# 変更後
MIN_SILENCE_MS = 1500  # 息継ぎで切れないよう1.5秒に
```

### 2. voice-bot.js
- USE_STREAMING_CLAUDE フラグ追加
- flushSendBuffer() でストリーミングClaude呼び出し
- 文単位でTTS送信

### 3. config.js（新規追加）
```javascript
ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
CLAUDE_MODEL: process.env.CLAUDE_MODEL || "claude-sonnet-4-20250514",
CLAUDE_MAX_TOKENS: parseInt(process.env.CLAUDE_MAX_TOKENS) || 1024,
```

### 4. claude-streaming.js（新規作成）
- Claude APIストリーミングクライアント
- 文末検出（。！？!?\n）でコールバック呼び出し
- 会話履歴管理（最大10メッセージ）

### 5. test-streaming-claude.js（新規作成）
- ストリーミングClaude + TTSテストスクリプト
- TTFS計測機能

---

## 起動コマンド

### ストリーミングモード有効
```bash
cd /home/rema/project/002--claude-test/claude-discord-bridge-server/voice
USE_STREAMING_STT=true USE_STREAMING_CLAUDE=true node voice-bot.js
```

### テスト実行
```bash
node test-streaming-claude.js
```

---

## 技術詳細

### ストリーミングClaudeの仕組み
1. Claude APIにstream=trueでリクエスト
2. Server-Sent Events (SSE) でレスポンスを受信
3. content_block_delta イベントからテキストを抽出
4. 句点(。！？)で文を区切ってTTSに送信
5. 最初の文が完成した時点で読み上げ開始

### VAD改善の仕組み
1. サーバー側Silero VADで音声検出
2. MIN_SILENCE_MS=1500msで発話終了を判定
3. クライアントからendメッセージで明示的に処理開始

---

## 制限事項

1. **TTFS約2秒はClaude API自体のレイテンシ** - これ以上の短縮はAPI側の改善が必要
2. **Sonnet 4使用** - Opus 4だと遅くなる
3. **ストリーミングモードではCLAUDE.mdのコンテキストが適用されない** - シンプルな音声アシスタントとして動作

---

## 履歴
- 2025-12-13 22:30: VAD改善（43秒→4秒）
- 2025-12-13 23:00: ストリーミングClaude実装
- 2025-12-13 23:09: 合成音声テスト完了（TTFS 2128ms平均）
- 2025-12-14 08:17: 実音声テスト成功
