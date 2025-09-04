# Login機能 - 詳細設計書

## 📋 全体設計書との関連
本設計書は、以下の全体設計書を基盤として作成されています：

- [アーキテクチャ設計](/dev_tools/spec/01_architecture_design.md) - システム全体の技術スタックとアーキテクチャパターン
- [データベース設計](/dev_tools/spec/02_database_design.md) - PostgreSQL + Redis の設計方針
- [API設計](/dev_tools/spec/03_api_design.md) - FastAPI標準仕様

本書では、上記の全体設計方針に準拠した**ログイン機能固有の実装**について詳述します。

## 1. アーキテクチャ設計

### 1.1 システム全体図
```
[ユーザー] → [Frontend] → [Backend API] → [Google OAuth] → [Session Store]
                ↓
          [Top Page] ← [Redirect Handler]
```

### 1.2 コンポーネント構成
- **Frontend Layer**: HTML/CSS/JS（認証UI）
- **API Layer**: Express.js（認証エンドポイント）
- **Authentication Layer**: Google OAuth 2.0（認証処理）
- **Session Layer**: Express Session（状態管理）

## 2. 詳細設計

### 2.1 フロントエンド設計

#### 2.1.1 ログイン画面 (`login.html`)
```html
<!-- 提供されたデザイン仕様を使用 -->
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ログイン</title>
  <link rel="stylesheet" href="login.css">
</head>
<body>
  <div class="login-container">
    <div class="login-form">
      <h1>ログイン</h1>
      <div id="g_id_onload"
           data-client_id="[CLIENT_ID]"
           data-callback="handleCredentialResponse">
      </div>
      <div class="g_id_signin" data-type="standard"></div>
    </div>
  </div>
  <script src="https://accounts.google.com/gsi/client" async defer></script>
  <script src="login.js"></script>
</body>
</html>
```

#### 2.1.2 認証処理 (`login.js`)
```javascript
// State生成（CSRF対策）
function generateState() {
  return crypto.getRandomValues(new Uint32Array(4)).join('-');
}

// 認証レスポンス処理
function handleCredentialResponse(response) {
  const state = generateState();
  sessionStorage.setItem('auth_state', state);
  
  fetch('/api/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      credential: response.credential,
      state: state
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.href = '/index.html';
    } else {
      showError(data.message);
    }
  })
  .catch(err => showError('ログインに失敗しました'));
}
```

#### 2.1.3 トップページ (`index.html`)
```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MyApp - ホーム</title>
  <link rel="stylesheet" href="/src/shared/styles/common.css">
</head>
<body>
  <div class="app-container">
    <header class="app-header">
      <h1>MyApp</h1>
      <div class="user-info">
        <span id="user-name">読み込み中...</span>
        <button id="logout-btn">ログアウト</button>
      </div>
    </header>
    
    <main class="app-main">
      <section class="feature-grid">
        <div class="feature-card" onclick="navigateToFeature('discord-bot')">
          <h3>Discord Bot</h3>
          <p>Discord連携ツール</p>
        </div>
        <div class="feature-card" onclick="navigateToFeature('playwright')">
          <h3>Playwright Tests</h3>
          <p>ブラウザテスト実行</p>
        </div>
        <div class="feature-card" onclick="navigateToFeature('profile')">
          <h3>プロフィール</h3>
          <p>ユーザー設定</p>
        </div>
      </section>
    </main>
  </div>
  
  <script src="/src/shared/js/app.js"></script>
  <script src="/src/shared/js/auth-check.js"></script>
</body>
</html>
```

### 2.2 バックエンド設計

#### 2.2.1 認証API (`auth-routes.js`)
```javascript
const express = require('express');
const { OAuth2Client } = require('google-auth-library');
const router = express.Router();

// Google OAuth設定
const client = new OAuth2Client(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.GOOGLE_REDIRECT_URI
);

// ログイン処理
router.post('/auth/google', async (req, res) => {
  try {
    const { credential, state } = req.body;
    
    // State検証（CSRF対策）
    if (!state || !req.session.auth_state || state !== req.session.auth_state) {
      return res.status(400).json({ success: false, message: 'Invalid state' });
    }
    
    // Google トークン検証
    const ticket = await client.verifyIdToken({
      idToken: credential,
      audience: process.env.GOOGLE_CLIENT_ID
    });
    
    const payload = ticket.getPayload();
    
    // セッション作成
    req.session.user = {
      id: payload.sub,
      email: payload.email,
      name: payload.name,
      picture: payload.picture
    };
    
    res.json({ success: true, user: req.session.user });
    
  } catch (error) {
    console.error('Auth error:', error);
    res.status(500).json({ success: false, message: 'ログインに失敗しました' });
  }
});

module.exports = router;
```

#### 2.2.2 セッション管理 (`session-manager.js`)
```javascript
const session = require('express-session');
const MongoStore = require('connect-mongo'); // またはMemoryStore for dev

const sessionConfig = {
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS必須
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000, // 24時間
    sameSite: 'strict'
  }
};

if (process.env.NODE_ENV === 'production') {
  sessionConfig.store = MongoStore.create({
    mongoUrl: process.env.MONGODB_URI
  });
}

module.exports = session(sessionConfig);
```

### 2.3 セキュリティ設計

#### 2.3.1 CSRF対策
- **State Parameter**: 各認証リクエストにランダムなstateを生成
- **Session Validation**: サーバーサイドでstate検証
- **Token Binding**: セッションとトークンの紐づけ

#### 2.3.2 セッション管理
```javascript
// 認証ミドルウェア
function requireAuth(req, res, next) {
  if (!req.session.user) {
    return res.redirect('/src/features/login/frontend/login.html');
  }
  next();
}

// ログアウト処理
router.post('/auth/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ success: false });
    }
    res.clearCookie('connect.sid');
    res.json({ success: true });
  });
});
```

## 3. データベース設計

### 3.1 セッション管理
```javascript
// セッションデータ構造
{
  _id: ObjectId,
  session_id: String,
  user_data: {
    google_id: String,
    email: String,
    name: String,
    picture: String
  },
  created_at: Date,
  expires_at: Date,
  last_accessed: Date
}
```

### 3.2 ユーザー情報（将来拡張用）
```javascript
// ユーザー基本情報
{
  _id: ObjectId,
  google_id: String,
  email: String,
  name: String,
  picture: String,
  created_at: Date,
  last_login: Date,
  settings: {
    theme: String,
    language: String
  }
}
```

## 4. API設計

### 4.1 認証API仕様
```
POST /api/auth/google
Request:
{
  "credential": "eyJ...",
  "state": "abc123-def456"
}

Response Success (200):
{
  "success": true,
  "user": {
    "id": "123456789",
    "email": "user@example.com",
    "name": "ユーザー名",
    "picture": "https://..."
  }
}

Response Error (400/500):
{
  "success": false,
  "message": "エラーメッセージ"
}
```

### 4.2 セッション管理API
```
GET /api/auth/me
Response:
{
  "authenticated": true,
  "user": { ... }
}

POST /api/auth/logout
Response:
{
  "success": true
}
```

## 5. 画面遷移設計

### 5.1 遷移フロー
```
[未認証状態]
  ↓ アクセス
[/login.html] 
  ↓ Googleボタンクリック
[Google認証画面]
  ↓ 認証成功
[コールバック処理]
  ↓ セッション作成
[/index.html (トップページ)]

[認証済み状態]
  ↓ 直接アクセス
[/index.html] (認証チェック → そのまま表示)
```

### 5.2 認証ガード
```javascript
// 全ページで認証状態をチェック
window.addEventListener('DOMContentLoaded', async () => {
  const authStatus = await fetch('/api/auth/me');
  const data = await authStatus.json();
  
  if (!data.authenticated) {
    window.location.href = '/src/features/login/frontend/login.html';
  }
});
```

## 6. エラーハンドリング設計

### 6.1 エラー分類
- **認証エラー**: Google認証拒否、トークン無効
- **ネットワークエラー**: 通信障害、タイムアウト
- **セッションエラー**: セッション期限切れ、不正セッション
- **システムエラー**: サーバー障害、設定エラー

### 6.2 エラー表示
```javascript
// エラー表示関数
function showError(message) {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.textContent = message;
  document.querySelector('.login-form').appendChild(errorDiv);
  
  setTimeout(() => {
    errorDiv.remove();
  }, 5000);
}
```

## 7. テスト設計

### 7.1 テストデータ移行
```bash
# testaccount.txt → tests/login/test-accounts.json
{
  "test_user": {
    "email": "bpdy.dev01@gmail.com",
    "password": "c0me1nFr1end",
    "google_id": "mock_google_id_123",
    "name": "Test User",
    "purpose": "開発・テスト用アカウント"
  }
}
```

### 7.2 テストケース設計
```javascript
describe('Login Feature', () => {
  test('Google認証成功時のトップページ遷移', async () => {
    // Google認証モックを使用したテスト
  });
  
  test('認証失敗時のエラーハンドリング', async () => {
    // エラー表示の確認
  });
  
  test('CSRF攻撃に対する防御', async () => {
    // State parameter検証
  });
});
```

## 8. 環境設定

### 8.1 環境変数
```bash
# .env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
SESSION_SECRET=your_session_secret
NODE_ENV=development
```

### 8.2 Google Cloud Console設定
1. **OAuth 2.0クライアント作成**
2. **承認済みリダイレクトURI**: `http://localhost:3000/auth/callback`
3. **承認済みJavaScriptの生成元**: `http://localhost:3000`

## 9. デプロイメント設計

### 9.1 本番環境
- **Vercel**: 静的ファイル配信
- **Node.js API**: 認証バックエンド
- **HTTPS**: SSL証明書必須

### 9.2 開発環境
- **GitHub Codespaces**: ローカル開発環境
- **HTTP**: 開発時のみHTTP許可
- **Hot Reload**: ファイル変更時の自動更新

## 10. パフォーマンス設計

### 10.1 最適化戦略
- **CDN**: Google Identity Servicesの使用
- **キャッシュ**: 静的ファイルの適切なキャッシュ設定
- **圧縮**: CSS/JSファイルの最小化

### 10.2 ローディング設計
```javascript
// ログインボタンローディング状態
function showLoading() {
  const button = document.querySelector('.g_id_signin');
  button.innerHTML = '<div class="loading-spinner"></div>';
}
```

## 11. ファイル構成実装

### 11.1 Feature-based Structure実装
```
/src/features/login/
  /frontend/
    login.html              # ログイン画面
    login.css               # 提供デザインベース
    login.js                # 認証UI制御
  /backend/
    google-oauth.service.js # Google OAuth実装
    auth.routes.js          # 認証APIルート
    session.middleware.js   # セッション管理
  /config/
    oauth.config.js         # OAuth設定
  /tests/
    login.integration.test.js
    auth.unit.test.js
  README.md                 # 機能説明書

/src/shared/                  # 共通コンポーネント
  /styles/
    common.css              # 共通スタイル
  /js/
    auth-guard.js           # 認証ガード
    api-client.js           # API通信共通
  /components/
    error-notification.js   # エラー表示共通

/src/
  index.html                # トップページ
  app.js                    # アプリケーションエントリーポイント

/tests/login/               # テスト専用
  test-accounts.json        # テストアカウント情報
```

## 12. デプロイメントアーキテクチャ

### 12.1 セルフホスティング構成

#### Docker Compose構成
```yaml
version: '3.9'

services:
  # Next.js フロントエンド
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    restart: unless-stopped

  # FastAPI バックエンド
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads  # ローカルファイルストレージ
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups  # バックアップ用
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Celery Worker
  celery:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  # Celery Beat (定期タスク)
  celery-beat:
    build: ./backend
    command: celery -A app.celery beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  # Nginx (リバースプロキシ)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl  # SSL証明書
      - ./uploads:/var/www/uploads  # 静的ファイル配信
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 12.2 ポータビリティ設計

#### 環境変数管理
```bash
# .env.example
# === 共通設定 ===
NODE_ENV=production
DOMAIN=example.com

# === Frontend ===
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxx

# === Backend ===
DATABASE_URL=postgresql://user:pass@localhost:5432/myapp
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx

# === Storage ===
UPLOAD_DIR=/app/uploads  # ローカルファイルシステム
MAX_UPLOAD_SIZE=10485760  # 10MB
```

#### マルチ環境対応
```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 環境別設定
    environment: str = "development"
    
    # データベース
    database_url: str
    
    # ストレージ設定（S3不使用）
    upload_dir: str = "/app/uploads"
    use_local_storage: bool = True
    
    # 将来のクラウド移行用（オプション）
    # aws_s3_bucket: str | None = None
    # gcs_bucket: str | None = None
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

### 12.3 セルフホスト用システム要件

#### 最小要件
- **CPU**: 2コア
- **メモリ**: 4GB RAM
- **ストレージ**: 20GB（アプリ + DB + アップロード）
- **OS**: Ubuntu 22.04 LTS / Debian 12

#### 推奨要件
- **CPU**: 4コア
- **メモリ**: 8GB RAM
- **ストレージ**: 50GB SSD
- **ネットワーク**: 固定IP or DDNS

### 12.4 セットアップスクリプト

#### 自動インストールスクリプト
```bash
#!/bin/bash
# install.sh

# Dockerインストール
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose インストール
sudo apt-get update
sudo apt-get install docker-compose-plugin

# ディレクトリ作成
mkdir -p uploads backups nginx/ssl

# 環境変数設定
cp .env.example .env
echo "Please edit .env file with your settings"

# SSL証明書生成（Let's Encrypt）
sudo apt-get install certbot
sudo certbot certonly --standalone -d example.com

# 起動
docker compose up -d

echo "Installation complete! Access http://localhost"
```

### 12.5 将来のホスティングサービス移行

#### 移行可能なサービス（無料枠あり）
1. **Fly.io**: 
   - 3GB RAM、3共有CPU無料
   - PostgreSQL 1GB無料
   
2. **Railway**:
   - $5無料クレジット/月
   - PostgreSQL、Redis含む

3. **Render**:
   - 静的サイト無料
   - PostgreSQL 90日無料

4. **Oracle Cloud Free Tier**:
   - 4 ARM CPU、24GB RAM永久無料
   - 200GB ストレージ

#### 移行用設定
```yaml
# fly.toml (Fly.io用)
app = "myapp"
kill_signal = "SIGINT"
kill_timeout = 5

[env]
  PORT = "8000"

[experimental]
  allowed_public_ports = []
  auto_rollback = true

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"
```

## 13. 技術スタック（確定版）

### 12.1 フロントエンド
- **Next.js 14+**: React フレームワーク（App Router使用）
- **TypeScript**: 型安全性の確保
- **Tailwind CSS**: ユーティリティファーストCSS
- **@react-oauth/google**: Google認証用Reactライブラリ

### 12.2 バックエンド
- **FastAPI**: Python製高速Webフレームワーク
- **Python 3.11+**: 最新の型ヒント機能活用
- **Pydantic**: データバリデーション
- **SQLAlchemy 2.0**: ORM（非同期対応）
- **Alembic**: データベースマイグレーション

### 12.3 認証・セッション
- **python-jose[cryptography]**: JWT生成・検証
- **python-multipart**: フォームデータ処理
- **google-auth**: Google OAuth検証
- **httpx**: 非同期HTTPクライアント

### 12.4 自動化・タスク処理
- **Celery**: 分散タスクキュー
- **Playwright**: ブラウザ自動化
- **BeautifulSoup4**: HTMLパース
- **Scrapy**: 高度なスクレイピング（必要時）

### 12.5 データベース
- **PostgreSQL 15+**: メインデータベース（JSONB活用）
- **Redis**: キャッシュ・セッション・Celeryブローカー
- **ローカルファイルシステム**: ファイルストレージ（S3不使用）

### 12.6 開発ツール
- **Poetry**: Python依存関係管理
- **Black**: Pythonコードフォーマッター
- **Ruff**: 高速Pythonリンター
- **pytest**: Pythonテストフレームワーク
- **pre-commit**: Git hooks管理

---

**設計完了日**: 2025-08-29  
**次フェーズ**: TASK（タスク分解）