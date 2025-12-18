# Discord音声ブリッジ - タスク一覧

## マイルストーン

| # | マイルストーン | 説明 | ステータス |
|---|---------------|------|-----------|
| M1 | Phase 2: TTS実装 | Claudeの応答を音声で再生 | ✅ 完了 |
| M2 | Phase 1: STT実装 | 音声入力をテキスト化してClaude Codeへ | ✅ 完了 |
| M3 | Phase 3: チューニング | 先読みTTS、パラメータ最終調整 | ✅ 完了 |

---

## M1: Phase 2 - TTS（音声出力）

### TASK-001: Node.js環境構築 ✅ 完了
**説明**: voice/ディレクトリ作成、必要なパッケージインストール

**完了条件**:
- [x] voice/ディレクトリ作成
- [x] package.json初期化
- [x] 依存パッケージインストール（discord.js, @discordjs/voice, express, prism-media）

**完了日**: 2025-12-10

---

### TASK-002: VOICEVOX Docker環境構築 ✅ 完了
**説明**: VOICEVOXエンジンをDockerで起動

**完了条件**:
- [x] docker-compose.voice.yml作成
- [x] VOICEVOXコンテナ起動確認
- [x] APIエンドポイント疎通確認（curl等）

**完了日**: 2025-12-10
**備考**: Windows Docker Desktop経由で起動

---

### TASK-003: tts-client.js実装 ✅ 完了
**説明**: VOICEVOX APIと連携するクライアント実装

**完了条件**:
- [x] tts-client.js作成
- [x] text → audio変換動作確認
- [x] エラーハンドリング実装

**完了日**: 2025-12-10
**成果物**: voice/tts-client.js

---

### TASK-004: voice-bot.js実装（TTS部分）✅ 完了
**説明**: Discord音声チャンネル接続と音声再生

**完了条件**:
- [x] Discord.js Client初期化
- [x] 音声チャンネル参加機能
- [x] 音声再生機能（@discordjs/voice）
- [x] HTTP API（POST /speak, /join, /leave）

**完了日**: 2025-12-10
**成果物**: voice/voice-bot.js

---

### TASK-005: discord_post.py修正 ⏸️ 保留
**説明**: テキスト送信時に音声サーバーへリクエスト

**ステータス**: 保留（既存フローを変更せず、別経路で音声再生を実装予定）

---

### TASK-006: Phase 2動作確認 ✅ 完了
**説明**: テキストチャンネルにメッセージ送信→音声チャンネルで再生

**完了条件**:
- [x] POST /speak APIでテキスト送信
- [x] 音声チャンネルでTTS音声が再生される
- [x] エラー時の動作確認

**完了日**: 2025-12-10

---

## M2: Phase 1 - STT（音声入力）

### TASK-101: stt-client.js実装 ✅ 完了
**説明**: whisper.cpp（ローカルSTT）と連携するクライアント実装

**完了条件**:
- [x] stt-client.js作成
- [x] audio → text変換動作確認
- [x] エラーハンドリング実装

**完了日**: 2025-12-10
**変更点**: Whisper API（有料）→ whisper.cpp（無料ローカル）に変更
**成果物**: voice/stt-client.js, whisper.cpp/

---

### TASK-102: voice-bot.js拡張（STT部分）✅ 完了
**説明**: 音声受信→STT→Flask転送

**完了条件**:
- [x] ユーザー音声ストリーム受信（selfDeaf: false）
- [x] Opus→PCMデコード（prism-media）
- [x] PCM→WAV変換（ffmpeg）
- [x] STTでテキスト化（whisper.cpp）
- [x] Flask APIに転送（/voice-input エンドポイント）

**完了日**: 2025-12-10〜11
**技術詳細**:
- 無音検出: 1.2秒
- Whisperタイムアウト: 60秒
- ノイズワードフィルタ: [音楽], (笑), [拍手], [BGM]

---

### TASK-103: Phase 1動作確認 ✅ 完了
**説明**: 音声チャンネルで話す→Claude Codeに転送→応答

**完了条件**:
- [x] 常時リスニングで発話検出
- [x] テキスト化されてClaude Codeに転送（tmux経由）
- [x] Claudeからの応答が音声で返る（TASK-301で完了）

**完了日**: 2025-12-11
**備考**: Push-to-Talk→常時リスニングに変更

---

## 追加タスク

### TASK-201: Flask /voice-input エンドポイント追加 ✅ 完了
**説明**: Voice Botからの音声入力を受け付けるエンドポイント

**完了条件**:
- [x] /voice-input POST エンドポイント追加
- [x] ノイズワードフィルタリング
- [x] tmux経由でClaude Codeに転送

**完了日**: 2025-12-11
**成果物**: src/flask_app.py（handle_voice_input追加）

---

## 残タスク

### TASK-301: Claude応答のTTS再生 ✅ 完了
**説明**: Claudeの応答をTTSで音声チャンネルに再生

**完了条件**:
- [x] Claudeの出力を検出（dpコマンド経由）
- [x] TTS APIに送信（discord_post.py → Voice Bot /speak）
- [x] 音声チャンネルで再生

**完了日**: 2025-12-11
**実装内容**: discord_post.pyにsend_to_tts()関数を追加。Discord投稿と同時にVoice BotのTTS APIを呼び出す

---

---

## M3: Phase 3 - チューニング

### TASK-401: 先読みTTS実装 ✅ 完了
**説明**: 文間の待ち時間を解消するため、再生中に次の文を並列合成

**完了条件**:
- [x] textQueue / audioQueue の2キュー構造に変更
- [x] prefetchAudio() で次の文を先読み合成
- [x] playNextAudio() で再生完了後に即座に次を再生
- [x] 割り込み時に両キューをクリア

**完了日**: 2025-12-11
**成果物**: voice/voice-bot.js（speak関数の全面改修）

---

### TASK-402: パラメータ最終調整 ✅ 完了
**説明**: VAD/STT/TTSパラメータの最終チューニング

**確定設定**:
- VAD: SILENCE_TIMEOUT 1秒、AfterSilence 500ms
- STT: whisper.cpp baseモデル（147MB）
- TTS: VOICEVOX WhiteCUL（ID 23）、speedScale 1.35
- 割り込み: ユーザー発話検知でTTS即時停止

**完了日**: 2025-12-11

---

## 履歴
- 2025-12-10: 初版作成
- 2025-12-11: 実装完了状態に更新（M1/M2完了）
- 2025-12-11: Phase 3チューニング完了（先読みTTS、パラメータ最終調整）
