# Claude-Discord Bridge + Voice

Discord経由でClaude Codeと対話するブリッジツール。テキストチャット + 音声会話に対応。

## 機能

### テキストブリッジ
- **マルチセッション**: 複数Discordチャンネルで独立したClaude Codeセッション
- **画像添付対応**: 画像分析ワークフロー
- **スラッシュコマンド**: Discord経由でコマンド実行

### 音声ブリッジ (Voice Bridge)
- **リアルタイム音声認識**: Whisper + Silero VADによる高速STT
- **音声合成**: VOICEVOX連携によるTTS
- **Discord音声チャンネル連携**: 音声で直接Claude Codeと対話

## アーキテクチャ

```
Discord Text Channel ←→ Flask API ←→ Claude Code (tmux)
Discord Voice Channel ←→ Voice Bot ←→ STT Server (Whisper)
                              ↓
                         VOICEVOX (TTS)
```

## システム要件

- Linux / macOS
- Python 3.8+
- Node.js 18+
- tmux
- CUDA対応GPU（音声認識用、推奨）
- VOICEVOX（音声合成用）
- Discord Bot Token

## クイックスタート

### 1. インストール
```bash
git clone https://github.com/yamkz/claude-discord-bridge.git
cd claude-discord-bridge
./install.sh
```

### 2. 環境設定
`.env`ファイルを設定:
```bash
CC_DISCORD_TOKEN=your_bot_token
CC_DISCORD_CHANNEL_ID=your_channel_id
CC_DISCORD_USER_ID=your_user_id
VOICE_CHANNEL_ID=your_voice_channel_id
```

### 3. 起動

**全サービス起動（音声認識含む）:**
```bash
./start-all.sh
```

**テキストブリッジのみ:**
```bash
./start-bridge.sh
```

### 4. 停止
```bash
./stop-all.sh     # 全サービス停止
./stop-bridge.sh  # テキストブリッジのみ停止
```

### 5. 再起動
```bash
./restart-all.sh
```

## コマンド一覧

### サービス管理
| コマンド | 説明 |
|---------|------|
| `./start-all.sh` | 全サービス起動（STT + Voice + Bridge） |
| `./stop-all.sh` | 全サービス停止 |
| `./restart-all.sh` | 全サービス再起動 |
| `./start-bridge.sh` | テキストブリッジのみ起動 |
| `./bin/vai status` | サービス状態確認 |
| `./bin/vai doctor` | 環境診断 |

### セッション管理
| コマンド | 説明 |
|---------|------|
| `./bin/vai view` | 全セッションをtmuxで表示 |
| `./bin/vai add-session <channel_id>` | セッション追加 |
| `./bin/vai remove-session <id>` | セッション削除 |
| `./bin/vai recover <id>` | セッション復旧 |
| `./bin/vai list-sessions` | セッション一覧 |
| `./bin/vexit` | 全セッション停止 |

### Discord送信
| コマンド | 説明 |
|---------|------|
| `./bin/dp "message"` | デフォルトセッションに送信 |
| `./bin/dp 2 "message"` | セッション2に送信 |
| `./bin/dp <channel_id> "message"` | チャンネルID指定で送信 |

## ポート一覧

| サービス | ポート | 用途 |
|---------|--------|------|
| Voice Bot API | 3001 | TTS/音声チャンネル制御 |
| Flask API | 5001 | メッセージルーティング |
| STT Server | 8765 | 音声認識 (WebSocket) |
| VOICEVOX | 50021 | 音声合成 |

## ドキュメント

- [音声ブリッジ仕様書](./docs/voice-bridge-spec.md) - 詳細なシステム仕様

## ライセンス

MIT License
