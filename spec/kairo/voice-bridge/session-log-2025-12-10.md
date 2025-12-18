# Voice Bridge 開発セッションログ - 2025-12-10

## 概要
Discord音声ブリッジ開発の初回セッション。要件定義→設計→タスク分解→実装開始まで。

---

## 1. 作業依頼書の受領

ユーザーから作業依頼書（discord-voice-bridge-spec.md）を受領。

**目的**:
- 既存のclaude-discord-bridge（テキストベース）に音声I/O機能を追加
- Discord音声チャンネル経由でClaude Codeと会話できるようにする
- 「肩に乗った妖精と喋る」ような自然な対話体験の実現

**目標構成**:
```
Discord音声Ch → Bot(STT) → [既存テキストパイプライン] → Bot(TTS) → Discord音声Ch
                                    ↓
                            tmux(Claude Code)
```

---

## 2. 開発基盤の決定

**議論内容**: リポジトリ構成をどうするか

**決定**: 同リポジトリ内に並列ディレクトリとして作成
- 既存: `claude-discord-bridge-server/`
- 新規: `claude-discord-voice-bridge/` または `voice/` サブディレクトリ

**理由**:
- 既存bridgeを壊さない
- 共通設定(.env等)を流用できる
- 問題なければ後で切り出せる

---

## 3. Phase 0: コード読解（完了）

既存のclaude-discord-bridge-serverのコード構造を把握。

**アーキテクチャ**:
```
Discord Bot (discord_bot.py)
    ↓ HTTP POST
Flask App (flask_app.py)
    ↓ tmux send-keys
Claude Code (tmux session)
```

**主要ファイル**:
- `src/discord_bot.py`: Discordメッセージ受信・処理
- `src/flask_app.py`: HTTP API、tmuxへの転送
- `src/tmux_manager.py`: Claude Codeセッション管理
- `src/session_manager.py`: マルチセッション管理

**音声機能の差し込みポイント**:
- TTS: dpコマンドでDiscordにテキスト送信するタイミングでフック
- STT: discord_bot.pyに音声チャンネル参加・音声受信機能追加

---

## 4. Kairoフォルダ作成

`spec/kairo/voice-bridge/` を作成。

作成したファイル:
- README.md - モード管理・進捗
- roadmap.md - 開発ロードマップ（Phase 0-4）
- requirements.md - 要件定義書
- design.md - 設計書
- tasks.md - タスク一覧

---

## 5. 要件定義（REQUIREMENTS）

### 100回仮想会議レビュー結果
**初回評価**: 72/100点

**主要な指摘事項**:
1. Claudeの応答をどこでキャプチャするか未定義 → **致命的**
2. VOICEVOXの環境構築が書かれてない
3. コスト見積もりがない
4. エラーハンドリング要件がない
5. 音声とテキストの同期

### 解決策
別セッションでの会話ログを共有してもらい、解決策が判明:
- **応答キャプチャ**: dpコマンドでDiscordにテキスト送信するタイミングで、同時にTTSを呼び出す

### 修正内容
- 応答キャプチャ方式を明記
- トリガー方式を段階的に整理（Phase 1: Push-to-Talk → Phase 2: ウェイクワード）
- エラーハンドリング要件追加
- コスト情報追加（Whisper API: $0.006/分）

### 音声チャンネル
ユーザーが作成: `1448208103589019678`

---

## 6. 設計（DESIGN）

### 技術選定の議論

**当初案**: Python (discord.py[voice])
**最終決定**: Node.js (@discordjs/voice)

**理由**:
- @discordjs/voiceの方が事例・ドキュメントが圧倒的に多い
- discord.py[voice]の音声受信は地雷踏みやすい
- 別プロセスでも既存パターン（HTTP API）で繋げば問題ない

**構成**:
```
Python(既存) ←HTTP→ Node.js(音声専用) ←→ Discord音声Ch
```

### アーキテクチャ
```
┌──────────────────────┐    ┌──────────────────────────────────────┐
│  Python Process      │    │  Node.js Process (音声専用)           │
│  ┌────────────────┐  │    │  ┌──────────────┐  ┌──────────────┐ │
│  │ discord_bot.py │  │    │  │ voice-bot.js │  │ tts-client.js│ │
│  │ (既存テキスト) │  │    │  │ (@discordjs/ │  │ (VOICEVOX)   │ │
│  └───────┬────────┘  │    │  │  voice)      │  └──────────────┘ │
│          │           │    │  └──────┬───────┘  ┌──────────────┐ │
│  ┌───────▼────────┐  │    │         │          │ stt-client.js│ │
│  │ flask_app.py   │◄─┼HTTP┼─────────┤          │ (Whisper)    │ │
│  └───────┬────────┘  │    │         │          └──────────────┘ │
└──────────┼───────────┘    └─────────┼────────────────────────────┘
           │ tmux send-keys           │
           ▼                          │
 ┌─────────────────┐                  │
 │  Claude Code    │◄─────────────────┘
 └─────────────────┘
```

---

## 7. タスク分解（TASK）

### M1: Phase 2 - TTS（音声出力）
- TASK-001: Node.js環境構築 ✅ 完了
- TASK-002: VOICEVOX Docker環境構築 🟡 進行中
- TASK-003: tts-client.js実装
- TASK-004: voice-bot.js実装（TTS部分）
- TASK-005: discord_post.py修正
- TASK-006: Phase 2動作確認

### M2: Phase 1 - STT（音声入力）
- TASK-101: stt-client.js実装
- TASK-102: voice-bot.js拡張（STT部分）
- TASK-103: Phase 1動作確認

---

## 8. 実装開始

### TASK-001: Node.js環境構築 ✅ 完了
- `voice/` ディレクトリ作成
- `package.json` 作成
- npm install完了（discord.js, @discordjs/voice, express等）
- 動作確認OK

### TASK-002: VOICEVOX Docker環境構築 🟡 進行中

**TTS選定の議論**:
- VOICEVOX: 無料、ローカル、日本語特化、自然な音声
- OpenAI TTS: 有料、API呼び出し、環境構築不要

**決定**: VOICEVOXを使用（日本語の自然さが上）

**Docker環境構築**:
1. ユーザーがDockerインストール（`sudo apt-get install -y docker.io`）
2. 権限問題発生（Claude Codeセッションはremaユーザー、rootではdocker動く）
3. 対応中: `sudo usermod -aG docker rema` または rootでVOICEVOX起動

---

## 9. 次のアクション

1. Docker権限問題を解決
2. VOICEVOX起動
3. tts-client.js実装
4. 「こんにちは」で疎通テスト

---

## 作成したファイル一覧

### spec/kairo/voice-bridge/
- README.md
- roadmap.md
- requirements.md
- design.md
- tasks.md
- session-log-2025-12-10.md (このファイル)

### claude-discord-bridge-server/voice/
- package.json
- config.js

### claude-discord-bridge-server/docker/
- docker-compose.voice.yml
