# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kiro Spec駆動開発 - 絶対的なルール

### 基本原則
- **CLAUDE.mdが絶対**: このファイルに書かれている内容以外の実装は行わない
- **段階的開発**: requirements → design → task → implementation の順序を厳守
- **モード切替禁止**: 各段階の完了確認なしに次のモードに移行しない

### 開発モード管理

#### 現在のモード: MAINTENANCE

#### 0. MAINTENANCE モード（メンテナンス）
**目的**: CLAUDE.mdの修正・全体管理作業  
**実行内容**: 
- CLAUDE.mdの構造・ルール修正
- specフォルダ構造の整理
- 開発プロセスの調整・改善
- プロジェクト全体の管理作業

**制約**: 実装・要件定義・設計作業は行わない  
**注意**: 「要件定義して」「実装して」「設計して」と言われても「現在はmaintenance modeのため、それらの作業はできません。まずモード切替の指示をお待ちしています」と回答

#### 1. REQUIREMENTS モード（要件定義）
**成果物**: `spec/requirements.md`  
**完了条件**: 要件定義書の確認依頼 → 確認完了連絡まで次モードに進まない  
**制約**: 「実装して」と言われても「現在はrequirements modeのため、要件定義書の確認が完了するまで進められません」と回答

#### 2. DESIGN モード（設計）
**成果物**: 
- `spec/01_architecture_design.md` [実装完了済み]
- `spec/02_database_design.md` [実装完了済み] 
- `spec/03_api_design.md` [実装完了済み]
- `spec/04_screen_transition_design.md` [実装完了済み]
- `spec/05_ui_ux_design.md` （未作成）
- `spec/06_error_handling_design.md` [実装完了済み]
- `spec/07_type_definitions.md` [実装完了済み]
- `spec/08_development_setup.md` [実装完了済み]
- `spec/09_operation_design.md` （未作成）

**完了条件**: 設計書01～09の確認依頼 → 確認完了連絡まで次モードに進まない  
**制約**: 「実装して」と言われても「現在はdesign modeのため、設計書の確認が完了し、taskの作成が完了しないとできません」と回答

#### 3. TASK モード（タスク整理）
**成果物**: `spec/task.md` (`spec/tasks.md`として存在)  
**完了条件**: task.md作成完了 → 実装許可確認 → 許可後に実装開始

#### 4. IMPLEMENTATION モード（実装）
**実行内容**: 設計書とタスクに従った実装・テスト

### 継続開発・保守ルール
- **追加機能・バグ修正**: 既存設計書に追加セクションとして記載
- **履歴管理**: 全specファイルに履歴管理セクションを追加
- **実装状況管理**: `[実装完了済み]`、`[実装中]`、`[未実装]`タグで管理
- **ルール変更**: 事前確認・すり合わせ後に変更実施

## Project Overview

このプロジェクトは開発フレームワーク構築の段階です。具体的なプロジェクト内容については `spec/requirements.md` を参照してください。

**現在の状況**:
- プロジェクトの要件定義は未確定
- 既存のDiscord Botは開発支援ツール（運用ツール）として存在
- Discord経由でClaude Codeとの実装連携を可能にする標準機能
- 使用するかは設計者の判断による

## Architecture

プロジェクトのアーキテクチャは要件定義完了後に確定します。現在は開発フレームワークの構築段階です。

### 現在存在する開発支援ツール

**Discord Bot (`discord-bot/src/`)** - 運用ツールとして存在:
- `DiscordClaudeInterface` - Discord と Claude の連携管理
- `DiscordBot` - Discord.js クライアント（メッセージ・スレッド管理）
- `ClaudeService` - Anthropic SDK 統合（会話履歴管理：10メッセージ制限）
- `config.js` - 環境変数管理

**Vercel API (`api/`)**:
- `wake.js` - Serverless function for GitHub Codespace management via GitHub API

### Key Design Patterns

- **Service Layer Architecture**: Clear separation between Discord handling, Claude API calls, and configuration
- **Event-Driven**: Discord message events trigger Claude AI responses
- **Thread-Based Conversations**: Each user interaction creates a Discord thread for organized conversations
- **Stateful History Management**: ClaudeService maintains conversation context with automatic cleanup

## Development Commands

### Core Commands
```bash
# Install dependencies
npm install

# Start production bot
npm start

# Start development mode with file watching
npm run dev
```

### Discord Bot Commands
- `!clear` - Clear conversation history
- `!history` - Show conversation length
- `!help` - Display help message
- `!wake` - Trigger GitHub Codespace startup (via web endpoint)

### Environment Setup
Copy `.env.example` to `.env` and configure:
- `CC_DISCORD_TOKEN` - Discord bot token
- `CC_DISCORD_CHANNEL_ID` - Target Discord channel
- `CC_DISCORD_USER_ID` - Authorized user ID
- `ANTHROPIC_API_KEY` - Claude API key
- `GITHUB_TOKEN`, `GITHUB_USERNAME`, `GITHUB_REPO_NAME` - For Codespace integration

## Code Conventions

- **ES Modules**: Uses `import/export` syntax throughout
- **Async/Await**: Consistent async pattern for all API calls
- **Error Handling**: Try-catch blocks with user-friendly Discord error messages
- **Message Splitting**: Automatic handling of Discord's 2000 character limit
- **Japanese Localization**: User-facing messages in Japanese

## MCP Integration

This project uses Serena MCP for enhanced code assistance:

```bash
# Setup Serena MCP (already configured in .mcp.json)
claude mcp add serena -s project -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)
```

After restart, run onboarding:
- `/mcp__serena__check_onboarding_performed`
- `/mcp__serena__onboarding` (if needed)

## Testing and Debugging

- **Bot Process Management**: PID stored in `bot.pid` for process management
- **Graceful Shutdown**: SIGINT/SIGTERM handlers for clean bot shutdown
- **Console Logging**: Comprehensive logging for message flow and errors
- **Wake Endpoint**: Test via `https://002-claude-test.vercel.app/api/wake?wake=true`

## Important Implementation Details

- **Thread Management**: Bot automatically creates Discord threads for conversations
- **Message Rate Limiting**: Built-in Discord.js rate limiting handling
- **Conversation Context**: ClaudeService maintains rolling 10-message history
- **Error Recovery**: Bot continues running even if individual message processing fails
- **Deployment**: Dual deployment (Vercel for API, direct Node.js for bot)