# Voice Bridge 会話ログ 2025-12-12

## セッション概要
- 日付: 2025-12-12
- 主要作業: 🎤プレフィックス音声入力の動作確認 → Flask直接転送によるレイテンシ改善

---

## 現在の状態（再起動後の復元用）

### 完了した作業
1. 🎤プレフィックス音声入力の動作確認 → 成功
2. Flask直接転送への変更 → 完了、動作確認済み
3. 二重転送問題の修正 → コード変更済み、**再起動待ち**

### 未適用の変更（再起動で反映）
- `src/discord_bot.py` 274-278行: 🎤メッセージをdiscord-bridgeで処理しないように変更

### 次のアクション
1. discord-bridge再起動
2. voice-bot再起動（必要なら）
3. テスト: 二重転送が解消されたか確認
4. レイテンシ計測（タイムスタンプログ追加を検討）

---

## 会話内容

### 1. 問題の説明（ユーザーより）
- voice-botとdiscord-bridgeが同じDiscordアカウント「rema-gpt」を使用
- discord-bridgeは「自分自身が投稿したメッセージは無視する」ルールがある
- voice-botが投稿した音声認識テキストも「自分の投稿」として無視される

### 2. 代替案の提案（ユーザーより）
- discord-bridgeのルールを変更
- 「🎤で始まるメッセージだけは自分の投稿でも処理する」

### 3. コード確認結果
discord_bot.py (274-278行) に既に実装済みだった:
```python
if message.author == self.user:
    if message.content.startswith('🎤'):
        logger.info(f'音声入力メッセージを処理: {message.content[:50]}...')
    else:
        return False
```

### 4. voice-bot起動・テスト
- voice-botが停止していた
- 起動コマンド: `cd voice && set -a && source /home/rema/project/002--claude-test/.env && set +a && node voice-bot.js`
- テスト成功: 🎤プレフィックス付きメッセージがClaude Codeに届いた

### 5. レイテンシ改善の議論

#### 現状のフロー（Discord経由・遅い）
```
voice-bot → Discord🎤投稿 → discord-bridge受信待ち → Flask → Claude
```

#### 改善案（Flask直接転送）
```
voice-bot → Flask /voice-input 直接 → Claude
              ↓（Flask内部で）
           Discord🎤投稿（ログ用）
```

#### ユーザーの体感
- 改善後: 「やっぱり早くなった感じがする」

### 6. 二重転送問題の発覚と修正

#### 問題
Flask直接転送とdiscord-bridge経由の両方でClaudeにメッセージが届いていた。

#### 原因
1. Flask直接転送 → Claude（意図した経路）
2. Flask内部のDiscord🎤投稿 → discord-bridge → Claude（二重）

#### 修正内容
discord_bot.py を変更し、🎤メッセージはログのみで処理しないようにした:
```python
# 修正後（274-278行）
if message.author == self.user:
    if message.content.startswith('🎤'):
        logger.info(f'音声入力メッセージ（ログのみ、処理スキップ）: {message.content[:50]}...')
    return False
```

---

## 変更したファイル

### 1. voice/voice-bot.js（sendToClaude関数）
**変更前（Discord投稿方式）:**
```javascript
async function sendToClaude(text, userId) {
    const channel = await client.channels.fetch(config.TEXT_CHANNEL_ID);
    await channel.send(`🎤 ${text}`);
}
```

**変更後（Flask直接転送方式）:**
```javascript
async function sendToClaude(text, userId) {
    const response = await fetch(`${config.FLASK_SERVER_URL}/voice-input`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, userId })
    });
}
```

### 2. src/discord_bot.py（_validate_message関数 274-278行）
**変更前:**
```python
if message.author == self.user:
    if message.content.startswith('🎤'):
        logger.info(f'音声入力メッセージを処理: {message.content[:50]}...')
    else:
        return False
```

**変更後:**
```python
if message.author == self.user:
    if message.content.startswith('🎤'):
        logger.info(f'音声入力メッセージ（ログのみ、処理スキップ）: {message.content[:50]}...')
    return False
```

---

## セッション構成

```
tmux list-sessions:
- claude-discord-bridge    ← Discord Bot + Flask
- claude-session-1         ← 現在のClaude Codeセッション
- claude-session-2
- claude-session-3
- claude-session-4
- keepalive
```

Flask /voice-input は session 1 に転送 → 現在のセッションに届く

---

## 設定値

### voice/config.js
- FLASK_SERVER_URL: "http://localhost:5001"
- TEXT_CHANNEL_ID: "1424051227796307968"
- VOICE_CHANNEL_ID: "1448296280710451300"

### 環境変数（/home/rema/project/002--claude-test/.env）
- CC_DISCORD_CHANNEL_ID_002: 1424051227796307968（session 1）

---

## 参考資料

### 関連ファイル
| ファイル | 説明 |
|---------|------|
| `src/discord_bot.py` | 🎤処理ロジック（274-278行） |
| `src/flask_app.py` | /voice-input エンドポイント（420-450行） |
| `voice/voice-bot.js` | sendToClaude関数（416-435行） |
| `voice/config.js` | 設定値 |

### 関連ログ
| ファイル | 説明 |
|---------|------|
| `voice/conversation-log-2025-12-11.md` | 昨日のログ（Flask形式復帰、2つのClaudeインスタンス問題） |
| `spec/kairo/voice-bridge/session-log-2025-12-10.md` | 初日の開発ログ |
| `spec/kairo/voice-bridge/requirements.md` | 要件定義書（NFR-001 レイテンシ目標） |
| `spec/kairo/voice-bridge/tasks.md` | タスク一覧（M1-M3完了済み） |

---

## ロールバック手順

### voice-bot.jsをDiscord投稿方式に戻す場合
```javascript
async function sendToClaude(text, userId) {
    const channel = await client.channels.fetch(config.TEXT_CHANNEL_ID);
    await channel.send(`🎤 ${text}`);
}
```

### discord_bot.pyの🎤処理を元に戻す場合
```python
if message.author == self.user:
    if message.content.startswith('🎤'):
        logger.info(f'音声入力メッセージを処理: {message.content[:50]}...')
    else:
        return False
```

---

## 再起動コマンド

### discord-bridge再起動
```bash
cd /home/rema/project/002--claude-test/claude-discord-bridge-server
./stop-bridge.sh
./start-bridge.sh
```

### voice-bot単体再起動
```bash
pkill -f "node.*voice-bot.js"
cd /home/rema/project/002--claude-test/claude-discord-bridge-server/voice
set -a && source /home/rema/project/002--claude-test/.env && set +a
node voice-bot.js &
```

---

## 履歴
- 2025-12-12 午前: 🎤プレフィックス動作確認、テスト成功
- 2025-12-12 午後: Flask直接転送実装、レイテンシ改善確認
- 2025-12-12 午後: 二重転送問題発覚、discord_bot.py修正（再起動待ち）
