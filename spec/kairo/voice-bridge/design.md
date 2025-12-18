# Discord音声ブリッジ - 設計書

## 1. アーキテクチャ概要

### 1.1 技術選定

**音声処理部分: Node.js (@discordjs/voice)**
- 理由: 事例豊富、活発にメンテナンス、ドキュメント充実
- discord.py[voice]は音声受信の事例が少なく地雷踏みやすい

**既存部分: Python (そのまま)**
- 理由: 既存コードを活かす、変更最小限

**連携方式: HTTP API**
- 既存のFlask APIパターンを踏襲
- Python ←HTTP→ Node.js(音声専用)

### 1.2 全体構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                     Discord Server                               │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │ テキストCh    │              │ 音声Ch       │                 │
│  │ (既存)       │              │ (新規)       │                 │
│  └──────┬───────┘              └──────┬───────┘                 │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          ▼                              ▼
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
 │  Claude Code    │                  │
 │  (tmux session) │◄─────────────────┘
 └─────────────────┘    (STT結果をflask経由で転送)
```

### 1.3 データフロー

**音声入力フロー（STT）**:
```
ユーザー発話 → Discord音声Ch → voice-bot.js → stt-client.js(Whisper) → テキスト
                                                                           ↓
                                                 HTTP POST /discord-message
                                                                           ↓
                                                       flask_app.py → Claude Code
```

**音声出力フロー（TTS）**:
```
Claude Code → dpコマンド → HTTP POST /voice-speak → voice-bot.js
                                                         ↓
                                    tts-client.js(VOICEVOX) → Discord音声Ch
```

---

## 2. モジュール設計

### 2.1 新規モジュール（Node.js）

#### voice-bot.js
**責務**: Discord音声チャンネルの接続管理、音声ストリームの送受信

```javascript
// Express server for HTTP API
const express = require('express');
const { joinVoiceChannel, createAudioPlayer } = require('@discordjs/voice');

// POST /voice-speak - テキストを音声で再生
app.post('/voice-speak', async (req, res) => {
    const { text, session_id } = req.body;
    const audio = await ttsClient.synthesize(text);
    await playAudio(audio);
    res.json({ status: 'ok' });
});

// POST /voice-join - 音声チャンネルに参加
app.post('/voice-join', async (req, res) => { ... });

// POST /voice-leave - 音声チャンネルから退出
app.post('/voice-leave', async (req, res) => { ... });
```

#### tts-client.js
**責務**: VOICEVOX APIとの連携

```javascript
class TTSClient {
    async synthesize(text) {
        // VOICEVOX APIを呼び出して音声データ取得
        const query = await fetch(`${VOICEVOX_HOST}/audio_query?text=${text}&speaker=${SPEAKER_ID}`);
        const audio = await fetch(`${VOICEVOX_HOST}/synthesis?speaker=${SPEAKER_ID}`, {
            method: 'POST',
            body: JSON.stringify(await query.json())
        });
        return audio.buffer();
    }
}
```

#### stt-client.js
**責務**: Whisper APIとの連携

```javascript
class STTClient {
    async transcribe(audioBuffer) {
        // OpenAI Whisper APIを呼び出してテキスト取得
        const formData = new FormData();
        formData.append('file', audioBuffer, 'audio.wav');
        formData.append('model', 'whisper-1');

        const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
            headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` },
            method: 'POST',
            body: formData
        });
        return response.json();
    }
}
```

### 2.2 既存モジュールの修正（Python）

#### discord_post.py（bin/dp）
**修正内容**: テキスト送信時に音声出力をトリガー

```python
import requests

def send_message_with_voice(text: str, session_id: int):
    # 既存: テキストチャンネルに送信
    send_to_text_channel(text, session_id)

    # 新規: Node.js音声サーバーに音声再生リクエスト
    try:
        requests.post(
            'http://localhost:3001/voice-speak',
            json={'text': text, 'session_id': session_id},
            timeout=5
        )
    except Exception as e:
        logger.error(f"Voice speak failed: {e}")
        # テキスト送信は成功しているので続行
```

#### flask_app.py
**修正内容**: 変更なし（既存のまま使用）

---

## 3. 外部サービス連携

### 3.1 VOICEVOX（TTS）

**構成**:
- DockerでVOICEVOX Engineを起動
- HTTP APIで音声合成リクエスト

**API仕様**:
```
POST /audio_query?text={text}&speaker={speaker_id}
POST /synthesis?speaker={speaker_id}
```

**Docker起動コマンド**:
```bash
docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

### 3.2 Whisper API（STT）

**構成**:
- OpenAI APIを使用
- 音声ファイルをアップロードしてテキスト取得

**API仕様**:
```python
import openai

audio_file = open("audio.wav", "rb")
transcript = openai.Audio.transcribe("whisper-1", audio_file)
```

---

## 4. ディレクトリ構成

```
claude-discord-bridge-server/
├── src/                          # Python (既存)
│   ├── discord_bot.py            # 既存
│   ├── discord_post.py           # 既存（修正: 音声トリガー追加）
│   └── flask_app.py              # 既存
├── voice/                        # Node.js (新規)
│   ├── package.json
│   ├── voice-bot.js              # メインエントリ
│   ├── tts-client.js             # VOICEVOX連携
│   ├── stt-client.js             # Whisper連携
│   └── config.js                 # 音声設定
├── bin/
│   ├── dp                        # 既存（修正）
│   └── start-voice.sh            # 新規（音声サーバー起動）
└── docker/
    └── docker-compose.voice.yml  # 新規（VOICEVOX用）
```

---

## 5. 設定ファイル

### voice/config.js
```javascript
module.exports = {
    // Discord設定
    DISCORD_TOKEN: process.env.CC_DISCORD_TOKEN,
    VOICE_CHANNEL_ID: "1448208103589019678",

    // サーバー設定
    VOICE_SERVER_PORT: 3001,
    FLASK_SERVER_URL: "http://localhost:5001",

    // TTS設定
    VOICEVOX_HOST: "http://localhost:50021",
    VOICEVOX_SPEAKER_ID: 1,  // ずんだもん

    // STT設定
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,

    // 音声処理設定
    AUDIO_SAMPLE_RATE: 48000,
    AUDIO_CHANNELS: 2
};
```

---

## 6. エラーハンドリング

### 6.1 TTS失敗時（Python側）
```python
try:
    requests.post('http://localhost:3001/voice-speak', json={'text': text}, timeout=5)
except Exception as e:
    logger.error(f"Voice speak failed: {e}")
    # テキスト送信は既に完了しているので続行
```

### 6.2 TTS失敗時（Node.js側）
```javascript
try {
    const audio = await ttsClient.synthesize(text);
    await playAudio(audio);
} catch (e) {
    console.error('TTS failed:', e);
    // エラーログのみ、テキストは既に送信済み
}
```

### 6.3 STT失敗時（Node.js側）
```javascript
try {
    const text = await sttClient.transcribe(audioBuffer);
    await forwardToFlask(text);
} catch (e) {
    console.error('STT failed:', e);
    // 音声で「聞き取れませんでした」と応答
    const errorAudio = await ttsClient.synthesize("聞き取れませんでした。もう一度お願いします。");
    await playAudio(errorAudio);
}
```

---

## 7. 実装順序

### Phase 2: TTS（音声出力）を先に実装
1. voice/ディレクトリ作成、package.json初期化
2. VOICEVOX Docker環境構築
3. tts-client.js実装
4. voice-bot.js実装（Express + @discordjs/voice）
5. discord_post.py修正（音声トリガー追加）
6. 動作確認

### Phase 1: STT（音声入力）を後から実装
1. stt-client.js実装（Whisper API連携）
2. voice-bot.js拡張（音声受信→STT→Flask転送）
3. 動作確認

---

## 履歴
- 2025-12-10: 初版作成
- 2025-12-10: 技術選定変更（Python → Node.js for 音声処理）
