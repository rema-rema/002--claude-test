# Discord音声ブリッジ開発 - ロードマップ

## 概要
既存のclaude-discord-bridge（テキストベース）に音声I/O機能を追加し、Discord音声チャンネル経由でClaude Codeと会話できるようにする。

## 目的
- ハンズフリーでAIと会話できる環境を構築
- 「肩に乗った妖精と喋る」ような自然な対話体験の実現
- 既存のテキストブリッジ資産を活かした最小改造

## ベースリポジトリ
- オリジナル: https://github.com/yamkz/claude-discord-bridge
- Fork版: https://github.com/rema-rema/002--claude-test/tree/main/claude-discord-bridge-server

## 現状の構成
```
tmux(Claude Codeセッション) <--> Botプロセス <--> Discord テキストCh
```

## 目標構成
```
Discord音声Ch --> Bot(STT) --> [既存テキストパイプライン] --> Bot(TTS) --> Discord音声Ch
                                       |
                               tmux(Claude Code)
```

## Phase一覧

| Phase | 目標 | 作業内容 | 想定工数 | ステータス |
|-------|------|----------|----------|------------|
| 0 | 現状確認 | 既存ブリッジのコード構造把握、依存関係確認 | 2-3時間 | ✅ 完了 |
| 1 | 音声入力 | Discord音声Ch受信 → STT → 既存テキスト処理に接続 | 2-5日 | ✅ 完了 |
| 2 | 音声出力 | Claude応答 → TTS → Discord音声Chへ送信 | 半日-1日 | ✅ 完了 |
| 3 | チューニング | レイテンシ削減、発話区切り検知、割り込み対応 | 任意 | 未着手 |
| 4 | 拡張（任意） | ウェイクワード対応、スマートグラス連携 | 任意 | 未着手 |

---

## 各Phaseの達成条件（高校生でもわかる版）

### Phase 0: 調査 ✅完了
**やること**: 今あるコードがどうなってるか調べる
**達成条件**: コードの仕組みが分かって、どこをいじればいいか分かった

### Phase 1: 音声入力（STT = Speech To Text）✅完了
**やること**: あなたが声で喋ったら、AIが文字として受け取れるようにする
**達成条件**:
- 音声チャンネルで「こんにちは」と喋る
- Claude Codeに「こんにちは」というテキストが届く

### Phase 2: 音声出力（TTS = Text To Speech）✅完了
**やること**: AIの返事を音声で読み上げる
**達成条件**:
- Claude Codeが返事を書く
- その返事が音声チャンネルで声として聞こえる
**完了日**: 2025-12-11

### Phase 3: チューニング（調整）
**やること**: もっと使いやすくする
**達成条件**:
- 反応が速くなる（今は遅い）
- 話の途中で切れなくなる
- 「あー」「えーと」などを無視できる

### Phase 4: 拡張（おまけ）
**やること**: 便利機能を追加
**達成条件**:
- 「OK Claude」と言ったら起きる（ウェイクワード）
- スマートグラスから使える

---

### 実装順序
**Phase 2 → Phase 1** の順で実装した。
理由: TTSは素直に動く。先に「Claudeが喋る」を体験してからSTTに取り組む方がモチベーション維持しやすい。

---

## Phase 0: 現状確認（完了）

### 実施内容
1. Fork版リポジトリのコード構造把握
2. メッセージ受信→Claude Code転送→応答返却のフロー追跡
3. 音声機能を差し込むべき箇所を特定

### 分析結果

#### 既存アーキテクチャ
```
┌─────────────────┐
│  Discord Bot    │  (discord_bot.py)
│  - メッセージ受信
│  - 添付ファイル処理
│  - ローディング表示
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│  Flask App      │  (flask_app.py)
│  - /discord-message
│  - 検証・転送
└────────┬────────┘
         │ tmux send-keys
         ▼
┌─────────────────┐
│  Claude Code    │  (tmux_manager.py)
│  - claude-session-{N}
└─────────────────┘
```

#### 主要ファイル
- `src/discord_bot.py`: Discordメッセージ受信・処理
- `src/flask_app.py`: HTTP API、tmuxへの転送
- `src/tmux_manager.py`: Claude Codeセッション管理
- `src/session_manager.py`: マルチセッション管理
- `src/attachment_manager.py`: 添付ファイル処理

#### 音声機能の差し込みポイント

**TTS（音声出力）**
- 現状: dpコマンドでDiscordへテキスト送信
- 追加箇所: テキスト送信時に並行してTTS→音声チャンネルへ送信
- 対象: discord_bot.pyまたは新規voice_handler.py

**STT（音声入力）**
- 追加箇所: discord_bot.pyに音声チャンネル参加・音声受信機能
- フロー: 音声受信 → STT → 既存テキストパイプライン

---

## Phase 2: 音声出力（TTS）

### 2-1. 環境準備
- @discordjs/voice インストール（またはPython: discord.py[voice]）
- TTSエンジン選定・セットアップ
  - 候補: VOICEVOX（日本語・無料・ローカル）/ ElevenLabs

### 2-2. 実装
- Claudeの応答テキストを受け取るフックポイント特定
- テキスト → TTS → 音声ファイル生成
- 音声ファイル → Discord音声チャンネルへストリーミング送信

### 2-3. 動作確認
- テキストチャンネルにメッセージ送信
- Claudeが応答
- 音声チャンネルで応答が再生される

---

## Phase 1: 音声入力（STT）

### 1-1. 環境準備
- Whisper API or ローカルWhisperセットアップ
- Discord音声受信の仕組み調査

### 1-2. 実装
- Botを音声チャンネルに参加させる
- ユーザーの音声ストリームを受信
- 音声データをSTTエンジンに渡してテキスト化
- テキストを既存パイプライン（Claude Code転送部分）に流す

### 1-3. トリガー方式
- 初期実装: Push-to-Talk（Discord側設定に依存）
- 将来拡張: ウェイクワード or VAD（Voice Activity Detection）

---

## 技術要件

### 音声入力（STT）候補
- Whisper API（OpenAI）
- ローカルWhisper
- Deepgram

### 音声出力（TTS）候補
- VOICEVOX（日本語・無料・ローカル）
- ElevenLabs

### Discord音声ライブラリ
- Python: discord.py[voice]
- Node.js: @discordjs/voice

---

## 成果物
- 音声対応版claude-discord-bridge
- セットアップ手順ドキュメント
- 各Phaseの実装レポート

---

## 備考
- 内部処理は全てテキスト。音声変換は入口と出口のみ
- クライアント（スマホ/PC）はDiscord通話してるだけ。TTS/STT処理は全てサーバー側Bot
- 最短週末1回、現実的には2-3週末で動くものができる見込み
