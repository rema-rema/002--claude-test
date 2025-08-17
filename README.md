# Discord Claude Code Interface

Discord経由でClaude AIと対話できるボットです。

## セットアップ

### 1. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定してください：

```bash
CC_DISCORD_TOKEN=your-discord-bot-token
CC_DISCORD_CHANNEL_ID=your-channel-id  
CC_DISCORD_USER_ID=your-user-id
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 2. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. 新しいアプリケーションを作成
3. Bot セクションでボットを作成し、トークンを取得
4. OAuth2 > URL Generator で以下の権限を選択：
   - Bot
   - Send Messages
   - Use Slash Commands
   - Create Public Threads
   - Send Messages in Threads

### 3. 必要な情報の取得

- **Channel ID**: 対象のDiscordチャンネルで開発者モードを有効にし、チャンネルを右クリックして「IDをコピー」
- **User ID**: 自分のDiscordプロフィールを右クリックして「IDをコピー」
- **Anthropic API Key**: [Anthropic Console](https://console.anthropic.com/)でAPIキーを作成

### 4. 依存関係のインストール

```bash
npm install
```

### 5. Serena MCP セットアップ (Claude Code用)

Claude Codeでより高度なコード支援を受けるために、Serena MCPを設定します：

```bash
# uvパッケージマネージャーのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# Serena MCPをプロジェクトに追加
claude mcp add serena -s project -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)

# Claude Codeを再起動後、以下のコマンドでオンボーディング実行
# /mcp__serena__check_onboarding_performed
# /mcp__serena__onboarding
```

### 6. 起動

```bash
npm start
```

または開発モード：

```bash
npm run dev
```

## 使い方

ボットが起動すると、指定したチャンネルでメッセージを送信するとスレッドが作成され、Claudeが応答します。

### コマンド

- `!clear` - 会話履歴をクリア
- `!history` - 会話履歴の長さを表示
- `!help` - ヘルプを表示

## 注意事項

- このボットは個人使用を想定しています
- APIキーや機密情報は適切に管理してください
- Discord Botの権限は最小限に設定することを推奨します