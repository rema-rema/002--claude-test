# 開発環境セットアップ設計書

## 1. 概要

### 1.1 開発環境の目的
- **統一性**: 全開発者が同じ環境で作業
- **効率性**: 迅速なセットアップと開発開始
- **再現性**: 問題の再現と解決の容易さ
- **自動化**: 手動作業の最小化
- **品質保証**: 一貫した開発品質の維持

### 1.2 対象環境
- **Windows**: Windows 10/11（メイン開発環境）
- **macOS**: macOS 12以降（サブ対応）
- **Linux**: Ubuntu 20.04以降（サーバー環境）

## 2. 必要ツール・ソフトウェア

### 2.1 基本開発ツール

#### 2.1.1 Node.js環境
```bash
# Node.js 18.x以降（推奨: 20.x LTS）
# Windows: 公式インストーラーまたはnvm-windows
# macOS: Homebrew または nvm
# Linux: nvm または apt

# nvm使用例（推奨）
nvm install 20
nvm use 20
node --version  # v20.x.x
npm --version   # 10.x.x
```

#### 2.1.2 Python環境
```bash
# Python 3.11以降（推奨: 3.11.x）
# Windows: 公式インストーラーまたはpyenv-win
# macOS: Homebrew または pyenv
# Linux: pyenv または apt

# pyenv使用例（推奨）
pyenv install 3.11.7
pyenv global 3.11.7
python --version  # Python 3.11.7
pip --version     # pip 23.x.x
```

#### 2.1.3 Git
```bash
# Git 2.30以降
# Windows: Git for Windows
# macOS: Xcode Command Line Tools または Homebrew
# Linux: apt install git

git --version  # git version 2.x.x
```

### 2.2 開発支援ツール

#### 2.2.1 エディタ・IDE
**推奨: Visual Studio Code**
```json
// 推奨拡張機能 (.vscode/extensions.json)
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-eslint",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense"
  ]
}
```

#### 2.2.2 パッケージマネージャー
```bash
# npm（Node.js標準）
npm --version

# yarn（オプション、高速化）
npm install -g yarn
yarn --version

# pip（Python標準）
pip --version

# pipenv（Python仮想環境、推奨）
pip install pipenv
pipenv --version
```

### 2.3 デプロイ・運用ツール

#### 2.3.1 Docker
```bash
# Docker Desktop（Windows/macOS）
# Docker Engine（Linux）
docker --version     # Docker version 24.x.x
docker-compose --version  # Docker Compose version 2.x.x
```

#### 2.3.2 Fly.io CLI
```bash
# Windows: PowerShell
iwr https://fly.io/install.ps1 -useb | iex

# macOS: Homebrew
brew install flyctl

# Linux: curl
curl -L https://fly.io/install.sh | sh

# 確認
flyctl version
```

## 3. プロジェクトセットアップ

### 3.1 リポジトリクローン
```bash
# GitHubからクローン
git clone https://github.com/your-username/ai-chat-app.git
cd ai-chat-app

# ブランチ確認
git branch -a
git checkout main
```

### 3.2 環境変数設定

#### 3.2.1 環境変数ファイル作成
```bash
# ルートディレクトリで実行
cp .env.example .env

# .envファイル編集（必須）
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ACCESS_TOKEN=your-access-token-here（オプション）
# PORT=5000
# FLASK_ENV=development
```

#### 3.2.2 環境変数の説明
```bash
# .env.example の内容と説明
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # OpenAI APIキー（必須）
ACCESS_TOKEN=your-access-token-here                   # アクセス制御用トークン（オプション）
PORT=5000                                            # バックエンドポート番号
FLASK_ENV=development                                # Flask実行環境
NODE_ENV=development                                 # Node.js実行環境
```

### 3.3 依存関係インストール

#### 3.3.1 バックエンド（Python）
```bash
# バックエンドディレクトリに移動
cd backend

# 仮想環境作成（推奨）
python -m venv venv

# 仮想環境有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 開発用依存関係（オプション）
pip install -r requirements-dev.txt
```

#### 3.3.2 フロントエンド（Node.js）
```bash
# フロントエンドディレクトリに移動
cd client

# 依存関係インストール
npm install
# または
yarn install

# 型定義確認
npm run type-check
```

## 4. 開発サーバー起動

### 4.1 自動起動スクリプト（推奨）

#### 4.1.1 Windows用スクリプト
```batch
@echo off
echo AI Chat App 開発環境起動中...

REM 環境変数確認
if not exist .env (
    echo エラー: .envファイルが見つかりません
    echo .env.exampleをコピーして.envを作成してください
    pause
    exit /b 1
)

REM バックエンド起動（バックグラウンド）
echo バックエンド起動中...
cd backend
start /min cmd /c "python app.py"
cd ..

REM フロントエンド起動（バックグラウンド）
echo フロントエンド起動中...
cd client
start /min cmd /c "npm run dev"
cd ..

echo 起動完了！
echo バックエンド: http://localhost:5000
echo フロントエンド: http://localhost:3000
echo.
echo 停止するには stop.bat を実行してください
pause
```

#### 4.1.2 macOS/Linux用スクリプト
```bash
#!/bin/bash
echo "AI Chat App 開発環境起動中..."

# 環境変数確認
if [ ! -f .env ]; then
    echo "エラー: .envファイルが見つかりません"
    echo ".env.exampleをコピーして.envを作成してください"
    exit 1
fi

# バックエンド起動（バックグラウンド）
echo "バックエンド起動中..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# フロントエンド起動（バックグラウンド）
echo "フロントエンド起動中..."
cd client
npm run dev &
FRONTEND_PID=$!
cd ..

echo "起動完了！"
echo "バックエンド: http://localhost:5000"
echo "フロントエンド: http://localhost:3000"
echo ""
echo "停止するには Ctrl+C を押してください"

# プロセスID保存
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 終了シグナル待機
trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT TERM
wait
```

### 4.2 手動起動手順

#### 4.2.1 バックエンド起動
```bash
# ターミナル1: バックエンド
cd backend

# 仮想環境有効化（必要に応じて）
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# サーバー起動
python app.py

# 起動確認
# http://localhost:5000/health にアクセス
```

#### 4.2.2 フロントエンド起動
```bash
# ターミナル2: フロントエンド
cd client

# 開発サーバー起動
npm run dev
# または
yarn dev

# 起動確認
# http://localhost:3000 にアクセス
```

### 4.3 動作確認

#### 4.3.1 ヘルスチェック
```bash
# バックエンドAPI確認
curl http://localhost:5000/health

# 期待されるレスポンス
{
  "status": "healthy",
  "service": "AI Chat Backend"
}
```

#### 4.3.2 チャット機能テスト
```bash
# チャットAPI確認
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "history": []}'

# フロントエンド確認
# ブラウザで http://localhost:3000 にアクセス
# メッセージを送信してAI応答を確認
```

## 5. 開発ワークフロー

### 5.1 日常的な開発手順

#### 5.1.1 開発開始
```bash
# 1. 最新コードを取得
git pull origin main

# 2. 依存関係更新確認
cd backend && pip install -r requirements.txt
cd ../client && npm install

# 3. 開発サーバー起動
# start.bat（Windows）または ./start.sh（macOS/Linux）

# 4. ブラウザで動作確認
# http://localhost:3000
```

#### 5.1.2 開発中
```bash
# コード変更
# - バックエンド: app.py等を編集
# - フロントエンド: src/以下を編集

# 自動リロード確認
# - Flask: デバッグモードで自動リロード
# - Next.js: Hot Module Replacement

# 型チェック（TypeScript）
cd client && npm run type-check

# リンター実行
cd client && npm run lint
cd backend && flake8 .
```

#### 5.1.3 開発終了
```bash
# サーバー停止
# stop.bat（Windows）または Ctrl+C

# 変更をコミット
git add .
git commit -m "feat: 新機能追加"
git push origin feature-branch
```

### 5.2 ブランチ戦略

#### 5.2.1 ブランチ命名規則
```bash
# 機能開発
feature/chat-improvement
feature/user-authentication

# バグ修正
fix/openai-error-handling
fix/ui-responsive-issue

# ホットフィックス
hotfix/security-patch
hotfix/critical-bug

# リリース
release/v1.0.0
release/v1.1.0
```

#### 5.2.2 開発フロー
```bash
# 1. 新機能ブランチ作成
git checkout -b feature/new-feature

# 2. 開発・テスト
# コード変更、テスト実行

# 3. コミット
git add .
git commit -m "feat: 新機能実装"

# 4. プッシュ
git push origin feature/new-feature

# 5. プルリクエスト作成
# GitHub上でPR作成

# 6. レビュー・マージ
# レビュー後、mainブランチにマージ
```

## 6. トラブルシューティング

### 6.1 よくある問題と解決方法

#### 6.1.1 バックエンド起動エラー
```bash
# 問題: ModuleNotFoundError
# 解決: 依存関係再インストール
pip install -r requirements.txt

# 問題: OpenAI API key not configured
# 解決: .envファイルでOPENAI_API_KEY設定

# 問題: Port 5000 already in use
# 解決: ポート変更またはプロセス終了
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

#### 6.1.2 フロントエンド起動エラー
```bash
# 問題: npm ERR! missing script: dev
# 解決: package.json確認、npm install実行

# 問題: Port 3000 already in use
# 解決: 自動的に3001ポートに変更される

# 問題: TypeScript compilation errors
# 解決: 型定義確認、npm run type-check
```

#### 6.1.3 API通信エラー
```bash
# 問題: CORS error
# 解決: Flask-CORS設定確認

# 問題: 401 Unauthorized
# 解決: ACCESS_TOKEN設定確認

# 問題: OpenAI API error
# 解決: APIキー有効性確認、使用量確認
```

### 6.2 デバッグ手法

#### 6.2.1 バックエンドデバッグ
```python
# ログ出力追加
import logging
logging.basicConfig(level=logging.DEBUG)

# デバッガー使用
import pdb
pdb.set_trace()

# Flask デバッグモード
app.run(debug=True)
```

#### 6.2.2 フロントエンドデバッグ
```typescript
// コンソールログ
console.log('Debug info:', data)

// React Developer Tools使用
// ブラウザ拡張機能インストール

// Network タブでAPI通信確認
// ブラウザ開発者ツール（F12）
```

### 6.3 パフォーマンス問題

#### 6.3.1 起動時間改善
```bash
# Node.js依存関係キャッシュ
npm ci  # package-lock.jsonから高速インストール

# Python依存関係キャッシュ
pip install --cache-dir .pip-cache -r requirements.txt

# Docker使用（オプション）
docker-compose up -d
```

#### 6.3.2 開発効率向上
```bash
# ホットリロード確認
# - Flask: FLASK_ENV=development
# - Next.js: 自動有効

# 並列実行
# concurrently使用（オプション）
npm install -g concurrently
concurrently "npm run dev" "python ../backend/app.py"
```

## 7. 開発環境の拡張

### 7.1 追加ツール（オプション）

#### 7.1.1 データベース（将来）
```bash
# PostgreSQL（Supabase用）
# Windows: PostgreSQL installer
# macOS: brew install postgresql
# Linux: apt install postgresql

# pgAdmin（GUI管理ツール）
# 公式サイトからダウンロード
```

#### 7.1.2 API テストツール
```bash
# Postman
# 公式サイトからダウンロード

# curl（コマンドライン）
# 標準搭載（Windows 10以降）

# HTTPie（curl代替）
pip install httpie
http GET localhost:5000/health
```

#### 7.1.3 監視・ログツール
```bash
# ログ監視
tail -f backend/app.log

# プロセス監視
# Windows: Task Manager
# macOS: Activity Monitor
# Linux: htop
```

### 7.2 IDE設定最適化

#### 7.2.1 VS Code設定
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "files.exclude": {
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/venv": true
  }
}
```

#### 7.2.2 デバッグ設定
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/app.py",
      "env": {
        "FLASK_ENV": "development"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Next.js: debug server-side",
      "type": "node",
      "request": "attach",
      "port": 9229,
      "skipFiles": ["<node_internals>/**"]
    }
  ]
}
```

## 8. チーム開発環境

### 8.1 環境統一

#### 8.1.1 Docker Compose（オプション）
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app
    environment:
      - FLASK_ENV=development
    env_file:
      - .env

  frontend:
    build: ./client
    ports:
      - "3000:3000"
    volumes:
      - ./client:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
```

#### 8.1.2 開発環境ドキュメント
```markdown
# 新メンバー向けセットアップガイド
1. 必要ツールインストール（Node.js, Python, Git）
2. リポジトリクローン
3. 環境変数設定（.env作成）
4. 依存関係インストール
5. 開発サーバー起動
6. 動作確認

# 推定セットアップ時間: 30分
```

### 8.2 品質管理

#### 8.2.1 プリコミットフック
```bash
# husky + lint-staged設定
npm install --save-dev husky lint-staged

# package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  },
  "lint-staged": {
    "*.{js,ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.py": ["flake8", "black"]
  }
}
```

#### 8.2.2 継続的インテグレーション
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd client && npm ci
          cd ../backend && pip install -r requirements.txt
      - name: Run tests
        run: |
          cd client && npm test
          cd ../backend && python -m pytest
```