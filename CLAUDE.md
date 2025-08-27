# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 重大事故記録

### 2025-08-26: .envファイル上書き事故
**事故内容**: Claude Code AIが`cp .env.example .env`コマンドを実行し、実際の環境変数値を消失  
**被害**: Discord Bot Token、Claude API Key、Channel ID等の実際の値が全て消失  
**原因**: 作業中の不注意によるファイル上書き  
**教訓**: **絶対に既存の.envファイルを上書きしてはならない**  
**対策**: .envファイル操作前は必ずバックアップ作成を義務化

### 2025-08-26: 方針転換決定記録
**背景**: 95%完成のDiscord Bot実装において「調査します」応答のみで実作業しない問題を発見  
**根本原因**: Claude Messages API制約により、Edit/MCP等の高機能ツールが利用不可  
**解決策**: yamkz/claude-discord-bridge導入による完全Claude Code CLI活用  
**決定**: Track A/B/C/D協議の結果、実用性を優先し方針転換を決定  
**移行方針**: 既存実装保存 → 新ツール導入 → 不要ソース整理 → 本格運用  

## Kiro Spec駆動開発 - 絶対的なルール

### 基本原則
- **CLAUDE.mdが絶対**: このファイルに書かれている内容以外の実装は行わない
- **段階的開発**: requirements → design → task → implementation の順序を厳守
- **モード切替禁止**: 各段階の完了確認なしに次のモードに移行しない

### 開発モード管理

#### 現在のモード: MAINTENANCE

### 実装状況ステータス定義

#### ファイル・機能のステータス
- **`[参考テンプレート]`**: 前のプロジェクトの参考ファイル（未実装・上書き予定）
- **`[設計中]`**: 現在設計・作成中のファイル
- **`[設計完了]`**: 設計完了・確認待ちの状態
- **`[実装中]`**: 実装作業進行中
- **`[実装完了]`**: 実装・テスト完了済み
- **`[未作成]`**: ファイルが存在しない状態
- **`[要修正]`**: バグ・改修が必要な状態

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
- `spec/01_architecture_design.md` [参考テンプレート]
- `spec/02_database_design.md` [参考テンプレート] 
- `spec/03_api_design.md` [参考テンプレート]
- `spec/04_screen_transition_design.md` [参考テンプレート]
- `spec/05_ui_ux_design.md` （未作成）
- `spec/06_error_handling_design.md` [参考テンプレート]
- `spec/07_type_definitions.md` [参考テンプレート]
- `spec/08_development_setup.md` [参考テンプレート]
- `spec/09_operation_design.md` （未作成）

**完了条件**: 設計書01～09の確認依頼 → 確認完了連絡まで次モードに進まない  
**制約**: 「実装して」と言われても「現在はdesign modeのため、設計書の確認が完了し、taskの作成が完了しないとできません」と回答

#### 3. TASK モード（タスク整理）
**成果物**: `spec/task.md` (`spec/tasks.md`として存在)  
**完了条件**: task.md作成完了 → 実装許可確認 → 許可後に実装開始

#### 4. IMPLEMENTATION モード（実装）
**実行内容**: 設計書とタスクに従った実装・テスト  
**重要ルール**: **実装前に必ず合意確認が必要**  
**制約**: 「実装します」ではなく「〇〇を実装してよろしいですか？」で確認後に実装実行

### 継続開発・保守ルール
- **追加機能・バグ修正**: 既存設計書に追加セクションとして記載
- **履歴管理**: 全specファイルに履歴管理セクションを追加
- **実装状況管理**: 上記ステータスタグで管理
- **テンプレート活用**: `[参考テンプレート]`を参考に新規設計・全上書き
- **ルール変更**: 事前確認・すり合わせ後に変更実施

### Kairo機能別開発ルール（厳守）

#### 階層管理方式
**spec/**: 全体設計（プロジェクト俯瞰）
**spec/kairo/**: 機能別詳細設計（小さく切り出し）

#### フォルダ構成
```
spec/
├── requirements.md              # プロジェクト全体要件（高レベル）
├── 01-09_*.md                  # 全体設計書（プロジェクト俯瞰）
├── kairo/                      # 機能別詳細要件
│   ├── [機能名]/               # 各機能フォルダ
│   │   ├── requirements.md     # 機能別要件定義
│   │   ├── design.md          # 機能別設計詳細
│   │   └── tasks.md           # 機能別実装タスク
│   └── [他機能]/
└── integration.md              # kairo成果物の統合管理
```

#### 設計書の粒度・範囲
**spec/01-09設計書**: 全プロジェクトのアーキテクチャ・設計（例：「Discord Bot + Claude Service + Playwright + Web API」全体）
**kairo/[機能]/design.md**: 特定機能に絞った詳細設計（例：「Playwrightレポーター → Discord通知」のみ）

#### 運用ルール（現在：C案で運用中）
**実験的機能開発**: Kairo独立開発
**本格システム開発**: 通常モード（REQUIREMENTS → DESIGN → TASK → IMPLEMENTATION）

1. **spec/requirements.md**: 全体像のみ記載（What we build）
2. **spec/kairo/[機能]/**: 詳細要件記載（How we build it）  
3. **spec/integration.md**: 各kairo成果物の統合状況管理
4. **Kairo完了時**: spec/integration.mdに統合状況を記録
5. **巨大化防止**: spec/requirements.mdは高レベル概要のみ維持

#### 🔄 実装時の進捗更新ルール（厳守）
**実装フェーズでの必須作業**:
1. **タスク開始時**: `spec/kairo/[機能]/tasks.md`で該当タスクを進行中にマーク
2. **タスク完了時**: **必ず**以下を同時実行
   - タスクステータスを完了にマーク（✅完了、完了日付記載）
   - 完了条件すべてにチェック
   - マイルストーン進捗を更新
   - 実装サマリーを追加（ファイル・テスト結果・成果物）
3. **フェーズ完了時**: マイルストーンステータスを更新（🟡進行中 → ✅完了）

**重要**: 実装作業とドキュメント更新は**必ずセット**で実行。これにより進捗の透明性を確保。

#### 📁 開発ツールのディレクトリ配置ルール（厳守）
**Discord関連開発ツールの配置**: 
- **すべてのDiscord関連開発ツール** → `discord-bot/src/` 内に配置
- **理由**: 製品コードとの混在を防ぎ、開発ツールを明確に分離
- **対象**: Discord Bot機能、Discord通知システム、承認システム等

**配置例**:
```
discord-bot/
├── src/
│   ├── components/      # Discord関連コンポーネント
│   ├── services/        # Discord・Claude連携サービス  
│   ├── utils/           # Discord関連ユーティリティ
│   ├── tests/           # Discord関連テスト
│   └── test-results/    # テスト実行結果
├── docs/                # Discord専用ドキュメント
├── jest.config.js       # Discord専用Jest設定
├── jest.setup.js        # Discord専用Jestセットアップ
└── package.json         # Discord専用パッケージ設定
```

**重要**: 
- `src/` 直下にDiscord関連コードを配置しない
- Discord専用の設定ファイルは `discord-bot/` 内に配置
- 他プロジェクト部分とのテスト設定衝突を回避

**注意**: A案（Kairo統合開発プラン）は `kairo-integration-plan.md` に保留中。Tsumiki稼働確認後に検討予定。

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

## Git ブランチ戦略

### ブランチ構成
- **`main`**: 本番環境（リリース済みコード）
- **`develop`**: ステージング環境（開発統合ブランチ）
- **`feature/*`**: 開発環境（機能開発ブランチ）

### 開発フロー
1. **機能開発**: `develop` から `feature/機能名` を作成
2. **ステージング**: `feature/*` → `develop` (PR経由で統合・検証)
3. **本番リリース**: `develop` → `main` (PR経由でリリース)

### ブランチ運用ルール
- **feature開発**: 個別機能ごとに `feature/機能名` で開発
- **PR必須**: 直接pushは禁止、必ずPull Requestで統合
- **検証段階**: develop で統合テスト・ステージング検証
- **本番デプロイ**: main への統合でリリース実行

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

### Git Commands
```bash
# 機能開発開始
git checkout develop
git pull origin develop
git checkout -b feature/新機能名

# 開発完了後
git push -u origin feature/新機能名
# GitHub でdevelopへのPR作成

# ステージング確認後、main へのPR作成
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

### 現在利用中のMCP一覧
- **serena** - コード解析・編集支援ツール
- **tsumiki** - AI支援型TDD (テスト駆動開発) フレームワーク
- **playwright** - ブラウザ自動化・E2Eテスト実行ツール（ヘッドレス対応）

### MCP管理ルール（厳守）

#### MCP追加時の必須手順
1. `.mcp.json`にMCP設定を追加
2. **必ず**上記「現在利用中のMCP一覧」に追加したMCPを記載
3. 追加理由・用途を一覧に併記

#### MCP削除時の必須手順
1. `.mcp.json`からMCP設定を削除
2. **必ず**上記「現在利用中のMCP一覧」から削除したMCPを除去
3. 関連設定・依存関係のクリーンアップ確認

#### MCP修正時の必須手順
1. `.mcp.json`のMCP設定を修正
2. **必ず**上記「現在利用中のMCP一覧」の説明・用途を更新
3. 変更内容の影響範囲を確認・記録

**重要**: MCPの追加・削除・修正を行った際は、このCLAUDE.mdの一覧更新を**絶対に忘れてはならない**。この一覧がプロジェクトの現状把握と運営判断の基準となる。

### MCP設定詳細

#### Serena MCP
This project uses Serena MCP for enhanced code assistance:

```bash
# Setup Serena MCP (already configured in .mcp.json)
claude mcp add serena -s project -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)
```

After restart, run onboarding:
- `/mcp__serena__check_onboarding_performed`
- `/mcp__serena__onboarding` (if needed)

#### Tsumiki Framework
AI支援型テスト駆動開発フレームワーク（Claude Codeスラッシュコマンドとして実装）:

```bash
# Tsumikiインストール
npx tsumiki install
```

利用可能なコマンド:
- `/kairo-requirements` - 要件定義
- `/kairo-design` - 設計フェーズ
- `/kairo-tasks` - タスク分解
- `/kairo-implement` - 実装
- `/tdd-requirements` - TDD要件定義
- `/tdd-testcases` - テストケース作成
- `/tdd-red` - Red phase (failing test)
- `/tdd-green` - Green phase (passing implementation)
- `/tdd-refactor` - リファクタリング

#### Playwright MCP
ブラウザ自動化・E2Eテスト実行ツール（GitHub Codespacesヘッドレス対応）:

```bash
# Playwright MCPインストール
claude mcp add-json playwright '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'

# Chromeブラウザインストール
npx playwright install chrome
```

**GitHub Codespacesでの使用方法:**
```bash
# ヘッドレスモードでテスト実行（推奨）
npx playwright test --headless

# 録画付きテスト実行
npx playwright test --video=on

# 失敗時スクリーンショット
npx playwright test --screenshot=only-on-failure
```

**重要**: GitHub Codespacesでは画面表示できないため、ヘッドレスモードでの実行が必須。テスト結果は録画・スクリーンショット機能で確認可能。

## Claude-Discord-Bridge 導入記録

### 2025-08-26: 方針転換実行
**導入ツール**: yamkz/claude-discord-bridge  
**GitHub**: https://github.com/yamkz/claude-discord-bridge  
**セットアップ**: /home/node/.claude-discord-bridge/  
**設定ファイル**: .env, sessions.json配置完了  

### 起動・操作方法
- **起動**: `~/.claude-discord-bridge/bin/vai`
- **セッション監視**: `~/.claude-discord-bridge/bin/vai view`
- **停止**: `~/.claude-discord-bridge/bin/vexit`
- **セッション追加**: `~/.claude-discord-bridge/bin/vai add-session <channel_id>`

### 設定詳細
- **作業ディレクトリ**: `/workspaces/002--claude-test`
- **Discordチャンネル**: `1405815779198369903` (main)
- **Flaskポート**: `5001`
- **Claude Code**: `--dangerously-skip-permissions` オプション有効

## Discord経由の通知に対応するルール

以下のような文言が含まれるメッセージを受け取った場合、「Discordからの通知」と判断してください：
1. 「Discordからの通知:」で始まるメッセージ
2. メッセージ末尾に `session=数字` が含まれる場合
3. スラッシュコマンド（例：`/project-analyze session=1`）

「Discordからの通知」がきた場合は以下のルールに従ってください：
### 基本的な応答ルール
1. **CLI応答は禁止。すべて`Bash`ツールを使って`dp`コマンドでメッセージを送信してください。**
2. `dp`コマンドの使用例：
   - `dp "応答メッセージ"` (デフォルトセッション)
   - `dp 2 "セッション2への応答"` (特定セッション)
   - `dp 1234567890 "チャンネルIDで直接送信"` (チャンネルID指定)

### Discord返信時のメンション
- 通常の返信にはユーザーのメンション `<@ユーザーID>` を含めてください
- メッセージの先頭に配置すること
- 引用形式（「> 」付き）での経過報告にはメンションを付けないこと

### 画像添付への対応
メッセージに `[添付画像のファイルパス: /path/to/image.png]` が含まれている場合：
1. `Read`ツールでその画像ファイルを読み込み
2. 画像の内容を分析して適切に応答
3. UI/UXレビュー、コードレビュー、ドキュメント処理などに活用

### 出力の例

**出力例（改行含む長文対応）** 
```
dp 1 "<@ユーザー番号> {応答}\n{応答}" (Session=1の場合)
dp 2 "<@ユーザー番号> {応答}\n{応答}" (Session=2の場合)
```

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