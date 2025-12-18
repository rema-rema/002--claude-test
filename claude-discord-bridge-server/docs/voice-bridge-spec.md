# Discord音声ブリッジ システム仕様書

## 概要

Discord音声チャンネル経由でClaude Codeと音声対話を行うシステム。
**マルチセッション対応**: 複数のDiscord Botを使用し、各ボイスチャンネルを独立したClaude Codeセッションに紐づけ可能。

## アーキテクチャ

### シングルセッション構成
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

### マルチセッション構成
```
┌──────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Voice Ch A      │────▶│  Voice Bot A     │────▶│                     │
│  (rema-work-1)   │◀────│  Port: 3001      │     │  Streaming STT      │
└──────────────────┘     │  Session: 1      │     │  Server (共有)      │
                         └────────┬─────────┘     │  Port: 8765         │
                                  │               └─────────────────────┘
┌──────────────────┐     ┌────────▼─────────┐
│  Voice Ch B      │────▶│  Voice Bot B     │
│  (rema-work-2)   │◀────│  Port: 3002      │
└──────────────────┘     │  Session: 2      │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐     ┌─────────────────────┐
                         │  Flask API       │────▶│  Claude Code        │
                         │  Port: 5001      │     │  Session 1 (tmux)   │
                         │  (ルーティング)  │────▶│  Session 2 (tmux)   │
                         └──────────────────┘     └─────────────────────┘
```

**マルチセッションの特徴:**
- 各Voice Botは独立したDiscord Botアカウント
- 各Voice Botは専用ポート（3001, 3002, ...）でAPIを提供
- STTサーバーは全Voice Botで共有
- Flask APIがセッション番号でルーティング
- TTS応答もセッション番号に応じたポートに送信

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
# === Voice Bot A (Session 1) ===
CC_DISCORD_TOKEN=           # Discord Botトークン（Bot A）
CC_DISCORD_CHANNEL_ID_002=  # テキストチャンネルA ID
VOICE_CHANNEL_ID=           # ボイスチャンネルA ID

# === Voice Bot B (Session 2) ===
VOICE_BOT_B_TOKEN=          # Discord Botトークン（Bot B）
VOICE_BOT_B_CHANNEL_ID=     # ボイスチャンネルB ID
CC_DISCORD_CHANNEL_ID_002_B= # テキストチャンネルB ID

# === 共通設定 ===
CC_DISCORD_USER_ID=         # 認証ユーザーID

# STT/TTS設定
USE_STREAMING_STT=true      # ストリーミングSTT有効化
USE_STREAMING_CLAUDE=true   # Claudeストリーミング有効化

# サーバー設定
FLASK_SERVER_URL=http://localhost:5001
```

### インスタンス別ポート

| インスタンス | 環境変数 | Voice Bot Port | Session番号 |
|-------------|---------|----------------|-------------|
| Bot A | `VOICE_BOT_INSTANCE=A` | 3001 | 1 |
| Bot B | `VOICE_BOT_INSTANCE=B` | 3002 | 2 |
| Bot C | `VOICE_BOT_INSTANCE=C` | 3003 | 3 |
| Bot D | `VOICE_BOT_INSTANCE=D` | 3004 | 4 |

## ポート一覧

| サービス | ポート | プロトコル | 備考 |
|---------|--------|-----------|------|
| Voice Bot A | 3001 | HTTP | Session 1用 |
| Voice Bot B | 3002 | HTTP | Session 2用 |
| Voice Bot C | 3003 | HTTP | Session 3用 |
| Voice Bot D | 3004 | HTTP | Session 4用 |
| Flask API | 5001 | HTTP | ルーティング |
| STT Server | 8765 | WebSocket | 共有 |
| VOICEVOX | 50021 | HTTP | TTS（共有） |

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

- 2025-12-15: マルチセッション音声対応（Bot A/B独立、セッション別TTS/テキストルーティング）
- 2024-12-14: TTS非同期化、タイミング計測追加
- 2024-12-13: Silero VAD統合、セマンティック検出実装
- 2024-12-12: ストリーミングSTT実装
- 2024-12-11: 初期実装
