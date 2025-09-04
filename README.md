# 002-claude-test - Multi-Session Development Environment

Google OAuth 2.0を利用したログイン機能を備えたWebアプリケーション開発プロジェクト

## 🏗️ アーキテクチャ

- **Frontend**: Next.js 14+ (React, TypeScript, Tailwind CSS)
- **Backend**: FastAPI (Python 3.11+, Pydantic, SQLAlchemy 2.0)
- **Database**: PostgreSQL 15+ (JSONB活用)
- **Cache**: Redis 7+
- **Infrastructure**: Docker Compose

## 🚀 クイックスタート

### 1. 環境変数設定
```bash
# セッション環境変数を読み込み
source dev_tools/scripts/load-session-env.sh session-a

# または他のセッション
source dev_tools/scripts/load-session-env.sh session-b
source dev_tools/scripts/load-session-env.sh session-c  
source dev_tools/scripts/load-session-env.sh session-d
```

### 2. データベース・サービス起動
```bash
# Docker Compose でデータベースサービスを起動
docker-compose up postgres-session-a redis-session-a -d

# または他のセッション
docker-compose up postgres-session-b redis-session-b -d
```

### 3. アプリケーション実行
```bash
# 環境変数読み込み後、開発サーバー起動
npm run dev
```

### 4. ブラウザでアクセス
- **Session A**: http://localhost:3001
- **Session B**: http://localhost:3002
- **Session C**: http://localhost:3003
- **Session D**: http://localhost:3004
- **Staging**: http://localhost:3005

## 🔧 開発環境管理

### 環境管理
```bash
# セッション環境テスト
dev_tools/scripts/test-session-env.sh

# 特定セッションの環境変数確認
source dev_tools/scripts/load-session-env.sh session-a
echo "Session: $SESSION_ID, Frontend: $FRONTEND_PORT, Backend: $BACKEND_PORT"

# Docker Compose操作
docker-compose up postgres-session-a redis-session-a -d    # サービス開始
docker-compose down                                         # 全サービス停止
docker-compose ps                                          # サービス状態確認
```

### 管理ツール
```bash
# データベース・Redis管理ツールを起動
docker-compose up pgadmin redis-commander -d

# アクセス
# pgAdmin: http://localhost:8080 (admin@example.com / admin123)
# Redis Commander: http://localhost:8081
```

## 🗂️ プロジェクト構造

```
├── dev-env/
│   ├── base.env                 # 共通環境変数
│   └── sessions/                # セッション別環境変数
│       ├── session-a.env        # Session A設定
│       ├── session-b.env        # Session B設定
│       ├── session-c.env        # Session C設定
│       └── session-d.env        # Session D設定
├── scripts/
│   ├── load-session-env.sh      # 環境変数読み込みスクリプト
│   └── test-session-env.sh      # 環境テストスクリプト
├── frontend/                    # Next.js フロントエンド
├── backend/                     # FastAPI バックエンド
├── spec/                        # 設計書
├── uploads/                     # セッション別アップロードファイル
├── logs/                        # アプリケーションログ
├── backups/                     # データベースバックアップ
└── docker-compose.yml           # Docker サービス定義
```

## 🗄️ データベース構成

### セッション別データベース
| セッション | PostgreSQL | Redis | 用途 |
|-----------|------------|-------|------|
| Session A | localhost:5401 | localhost:6401 | 基本機能開発 |
| Session B | localhost:5402 | localhost:6402 | UI/UX開発 |
| Session C | localhost:5403 | localhost:6403 | API開発 |
| Session D | localhost:5404 | localhost:6404 | テスト・デバッグ |
| Staging | localhost:5405 | localhost:6405 | 統合テスト環境 |

### 環境変数
セッション別環境変数設定:
- `dev-env/base.env` - 全セッション共通設定
- `dev-env/sessions/session-a.env` - Session A用設定
- `dev-env/sessions/session-b.env` - Session B用設定  
- `dev-env/sessions/session-c.env` - Session C用設定
- `dev-env/sessions/session-d.env` - Session D用設定

環境変数の読み込み:
```bash
# セッション環境を読み込み（base.env + session-specific.env）
source dev_tools/scripts/load-session-env.sh session-a
```

## 🔐 セキュリティ設定

### Google OAuth設定
1. Google Cloud Consoleでプロジェクト作成
2. OAuth 2.0クライアント作成
3. 各セッションのリダイレクトURIを設定:
   - Session A: `http://localhost:3001/auth/callback`
   - Session B: `http://localhost:3002/auth/callback`
   - Session C: `http://localhost:3003/auth/callback`
   - Session D: `http://localhost:3004/auth/callback`

4. 環境変数に設定:
```bash
# dev-env/base.env に共通設定として追加
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## 🧪 テスト

### テストアカウント
開発・テスト用のアカウント情報: `tests/login/test-accounts.json`

### 環境テスト
```bash
# セッション環境設定テスト
dev_tools/scripts/test-session-env.sh

# 特定セッションのテスト
source dev_tools/scripts/load-session-env.sh session-a
echo "環境確認 - Session: $SESSION_ID, Port: $FRONTEND_PORT"
```

## 📊 監視・メンテナンス

### ログ確認
```bash
# Docker サービスログ
docker-compose logs postgres-session-a
docker-compose logs redis-session-a

# アプリケーションログ（セッション別）
tail -f logs/session-a.log
tail -f logs/session-b.log
```

### データ管理
```bash
# Dockerボリューム確認
docker volume ls | grep session

# データベースバックアップ（手動）
docker exec postgres-session-a pg_dump -U session_a_user session_a_dev > backups/session-a-$(date +%Y%m%d).sql

# セッションデータクリーンアップ
docker-compose down
docker volume prune
```

## 🌐 本番デプロイ

### ステージング環境
```bash
# ステージング環境起動
docker-compose up postgres-staging redis-staging -d
source dev_tools/scripts/load-session-env.sh staging
npm run dev

# http://localhost:3005 でアクセス
```

### 本番用ビルド
```bash
# セッション環境で本番ビルド
source dev_tools/scripts/load-session-env.sh session-a
npm run build
```

## 📚 開発ガイド

### 新しい機能開発
1. 利用可能なセッションを選択 (session-a/b/c/d)
2. セッション環境を読み込み: `source dev_tools/scripts/load-session-env.sh session-a`
3. データベースサービス起動: `docker-compose up postgres-session-a redis-session-a -d`
4. 機能別設計書を `spec/kairo/` に作成
5. 開発・テスト
6. ステージング環境で統合テスト

### マルチセッション並行開発
- 複数のClaude Codeセッションで同時開発可能
- 各セッションは完全に分離された環境（A, B, C, D）
- データベース・ファイル・ポートが独立
- 新しい環境変数管理システムで設定が簡潔

### トラブルシューティング
- 環境変数エラー: `dev_tools/scripts/test-session-env.sh` で環境確認
- サービス起動エラー: `docker-compose ps` で状態確認
- ポート競合: 他のセッション（A/B/C/D）を使用
- データベース接続エラー: `docker-compose restart postgres-session-a`

## 🔄 アップデート履歴

- **2025-08-29**: 環境変数管理システム改善完了
  - `.env.session1-4` を `dev-env/sessions/session-a/b/c/d.env` に整理
  - `dev-env/base.env` による共通設定分離  
  - `dev_tools/scripts/load-session-env.sh` による環境読み込み自動化
  - 新しいA/B/C/D命名規則に統一
  - 製品コードとの混同を避けるため `config` → `dev-env` にリネーム
- **2025-08-29**: マルチセッション開発環境構築完了
- **2025-08-29**: Docker Compose設定・管理スクリプト作成
- **2025-08-29**: 設計書分離・MECE構造確立

---

**開発環境**: 自宅Linuxサーバー  
**技術スタック**: Next.js + FastAPI + PostgreSQL + Redis + Docker