# Discord音声ブリッジ システム仕様書

## 概要

Discord音声チャンネル経由でClaude Codeと音声対話を行うシステム。

## アーキテクチャ

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Discord    │────▶│  Voice Bot   │────▶│  Streaming STT      │
│  Voice Ch   │     │  (Node.js)   │     │  Server (Python)    │
│             │◀────│  Port: 3001  │     │  Port: 8765         │
└─────────────┘     └──────────────┘     │  Whisper + Silero   │
                           │              └─────────────────────┘
                           │
                    ┌──────▼──────┐     ┌─────────────────────┐
                    │  Flask API  │────▶│  Claude Code        │
                    │  Port: 5001 │     │  (tmux sessions)    │
                    └─────────────┘     └─────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  VOICEVOX   │
                    │  Port: 50021│
                    │  (TTS)      │
                    └─────────────┘
```

## コンポーネント

### 1. Voice Bot (`voice/voice-bot.js`)

Discord.jsベースの音声処理ボット。

**機能:**
- Discord音声チャンネルへの参加・音声受信
- 音声データのデコード (Opus → PCM)
- VADによる発話検出
- STTサーバーへのストリーミング送信
- TTS音声の再生 (VOICEVOX連携)

**設定:**
- `USE_STREAMING_STT=true`: ストリーミングSTTモード
- `USE_STREAMING_CLAUDE=true`: Claudeストリーミング応答

**Express API:**
- `GET /health` - ヘルスチェック
- `POST /speak` - TTS音声再生
- `POST /join` - 音声チャンネル参加
- `POST /leave` - 音声チャンネル退出
- `POST /listen/start` - 音声認識開始
- `POST /listen/stop` - 音声認識停止

### 2. Streaming STT Server (`voice/streaming_stt_server_v2.py`)

WhisperLive方式のリアルタイム音声認識サーバー。

**技術スタック:**
- Faster Whisper (`large-v3-turbo`)
- Silero VAD (発話区間検出)
- WebSocket通信

**処理フロー:**
1. クライアントから16kHz mono PCMを受信
2. Silero VADで発話区間を検出
3. 発話終了時にWhisperで認識
4. セマンティック判定 (文完結チェック)
5. 結果をWebSocketで返却

**VAD設定:**
- `VAD_THRESHOLD=0.5` - 音声検出閾値
- `MIN_SILENCE_MS=1500` - 発話終了判定の無音時間
- `MIN_SPEECH_MS=250` - 最小発話長

**フィルタリング:**
- 繰り返しパターン検出・除去
- ハルシネーション除去 (「ご視聴ありがとう」等)

### 3. Flask API (`src/flask_app.py`)

音声入力をClaude Codeセッションに転送するブリッジ。

**エンドポイント:**
- `POST /voice-input` - 音声認識結果を受信
  - Discord `🎤` 投稿
  - tmuxセッションへの転送

**タイミング計測:**
- Flask受信→パース
- Discord投稿時間
- tmux転送時間

### 4. Discord Post (`src/discord_post.py`)

Discordへのメッセージ送信とTTS連携。

**TTS処理:**
- 非同期送信 (スレッド化)
- メンション・コードブロック除去
- 200文字制限 (超過は省略)
- `🎤` `🔧` で始まるメッセージはスキップ

## 環境変数

```bash
# Discord設定
CC_DISCORD_TOKEN=       # Discord Botトークン
CC_DISCORD_CHANNEL_ID=  # テキストチャンネルID
CC_DISCORD_USER_ID=     # 認証ユーザーID
VOICE_CHANNEL_ID=       # 音声チャンネルID

# STT/TTS設定
USE_STREAMING_STT=true  # ストリーミングSTT有効化
USE_STREAMING_CLAUDE=true # Claudeストリーミング有効化

# サーバー設定
VOICE_SERVER_PORT=3001  # Voice Bot APIポート
FLASK_SERVER_URL=http://localhost:5001
```

## ポート一覧

| サービス | ポート | プロトコル |
|---------|--------|-----------|
| Voice Bot API | 3001 | HTTP |
| Flask API | 5001 | HTTP |
| STT Server | 8765 | WebSocket |
| VOICEVOX | 50021 | HTTP |

## レイテンシ目標

- 発話終了 → テキスト認識: ~500ms
- テキスト認識 → Claude応答開始: ~1s
- 合計ターンアラウンド: ~2-3s

## 依存関係

### Node.js (voice/)
- discord.js
- @discordjs/voice
- prism-media
- express

### Python (voice/)
- faster-whisper
- torch (Silero VAD)
- websockets
- numpy

### システム
- ffmpeg (音声変換)
- VOICEVOX (TTS)

## ファイル構成

```
voice/
├── voice-bot.js           # メインVoice Bot
├── streaming_stt_server_v2.py  # STTサーバー
├── streaming-stt-client.js     # STTクライアント
├── tts-client.js          # VOICEVOXクライアント
├── stt-client.js          # バッチSTTクライアント
├── claude-streaming.js    # Claudeストリーミング
├── config.js              # 設定
└── .venv/                 # Python仮想環境

src/
├── flask_app.py           # Flask API
└── discord_post.py        # Discord投稿
```

## 更新履歴

- 2024-12-14: TTS非同期化、タイミング計測追加
- 2024-12-13: Silero VAD統合、セマンティック検出実装
- 2024-12-12: ストリーミングSTT実装
- 2024-12-11: 初期実装
