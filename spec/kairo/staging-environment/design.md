# ステージング環境構築システム - 設計書

## 1. アーキテクチャ設計

### 1.1 システム全体構成図
```
[VPN Client] ←→ [Tailscale] ←→ [Ubuntu Server]
                                     ↓
[Internet] ←→ [DNS(dnsmasq)] → [nginx(Proxy)] 
                                     ↓
                            [Next.js:3001] + [FastAPI:8000]
                                     ↓
                              [SQLite/File System]
```

### 1.2 ネットワーク・アクセス層設計

#### DNS解決アーキテクチャ
- **既存dnsmasq継続利用**: `/etc/dnsmasq.d/home.conf`
- **解決フロー**: `home.poco → 100.115.216.73 (Tailscale IP)`
- **フォールバック**: 外部DNS（8.8.8.8）への転送

#### リバースプロキシアーキテクチャ
- **既存nginx基盤**: `/etc/nginx/sites-available/home`
- **プロキシ設定変更**: `localhost:3000 → localhost:3001`
- **追加APIプロキシ**: `/api/* → localhost:8000`

### 1.3 アプリケーション層設計

#### フロントエンド（Next.js）アーキテクチャ
```
/release/002--claude-test/frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # ルートレイアウト
│   │   ├── page.tsx            # ランディングページ
│   │   ├── login/              # ログインページ
│   │   │   └── page.tsx
│   │   └── dashboard/          # ダッシュボード
│   │       └── page.tsx
│   ├── features/login/         # 認証機能
│   │   ├── hooks/              # カスタムフック
│   │   ├── components/         # UIコンポーネント
│   │   ├── services/           # API通信
│   │   └── types/              # 型定義
│   └── lib/                    # ユーティリティ
├── public/                     # 静的アセット
└── .next/                      # ビルド成果物
```

#### バックエンド（FastAPI）アーキテクチャ
```
/release/002--claude-test/backend/
├── app/
│   ├── main.py                 # FastAPIアプリケーション
│   ├── auth/                   # 認証モジュール
│   │   ├── router.py          # 認証エンドポイント
│   │   ├── jwt_handler.py     # JWT管理
│   │   ├── models.py          # データモデル
│   │   └── utils.py           # ユーティリティ
│   ├── database/               # データベース
│   │   ├── connection.py      # DB接続管理
│   │   ├── models.py          # SQLAlchemy モデル
│   │   └── migrations/        # マイグレーション
│   ├── middleware/             # ミドルウェア
│   │   ├── cors.py            # CORS設定
│   │   ├── security.py        # セキュリティ
│   │   └── logging.py         # ログ管理
│   └── utils/                  # 共通ユーティリティ
├── config/
│   ├── settings.py            # 設定管理
│   └── staging.env            # 環境変数
└── requirements.txt           # 依存関係
```

## 2. データベース設計

### 2.1 テーブル設計

#### users テーブル
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture_url VARCHAR(500),
    google_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### sessions テーブル
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### audit_logs テーブル
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.2 データアクセス層設計

#### SQLAlchemy モデル設計
```python
# app/database/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture_url = Column(String(500))
    google_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="sessions")
```

## 3. API設計

### 3.1 認証API設計

#### エンドポイント一覧
| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v1/auth/login` | ログイン | LoginRequest | AuthResponse |
| POST | `/api/v1/auth/logout` | ログアウト | - | StatusResponse |
| GET | `/api/v1/auth/me` | ユーザー情報取得 | - | UserResponse |
| POST | `/api/v1/auth/refresh` | トークン更新 | RefreshRequest | AuthResponse |
| GET | `/api/v1/health` | ヘルスチェック | - | HealthResponse |

#### データモデル設計
```python
# app/auth/models.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    user: UserResponse

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str]
    is_authenticated: bool

class RefreshRequest(BaseModel):
    refresh_token: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
```

### 3.2 認証フロー設計

#### ログインフロー
```
1. [Frontend] POST /api/v1/auth/login
   ↓
2. [Backend] ユーザー認証・JWT生成
   ↓
3. [Backend] セッション作成・DB保存
   ↓
4. [Backend] HTTPOnly Cookie設定
   ↓
5. [Frontend] ダッシュボードリダイレクト
```

#### 自動ログインフロー
```
1. [Frontend] ダッシュボードURL直接アクセス
   ↓
2. [Frontend] GET /api/v1/auth/me (Cookie送信)
   ↓
3. [Backend] JWT検証・セッション確認
   ↓
4. [Case A] 認証OK → ダッシュボード表示
5. [Case B] 認証NG → ログインページリダイレクト
```

## 4. セキュリティ設計

### 4.1 JWT・セッション管理設計

#### JWT設計
```python
# JWT Payload設計
{
    "sub": "user_id",           # ユーザーID
    "email": "user@example.com", # ユーザーメール
    "iat": 1627849200,          # 発行時刻
    "exp": 1627852800,          # 有効期限（1時間）
    "type": "access_token"      # トークンタイプ
}

# Refresh Token Payload
{
    "sub": "user_id",
    "session_id": "sess_xyz123",
    "iat": 1627849200,
    "exp": 1628454000,          # 有効期限（7日間）
    "type": "refresh_token"
}
```

#### Cookie設定
```python
# HTTPOnly Cookie設定
cookie_settings = {
    "httponly": True,
    "secure": True,           # HTTPS必須
    "samesite": "strict",     # CSRF対策
    "max_age": 3600,          # 1時間
    "path": "/",
    "domain": "home.poco"
}
```

### 4.2 CSRF対策設計

#### CSRFトークン実装
```python
# CSRF Token生成・検証
import secrets
from fastapi import Request, HTTPException

def generate_csrf_token():
    return secrets.token_urlsafe(32)

def verify_csrf_token(request: Request, token: str):
    session_token = request.session.get("csrf_token")
    if not session_token or session_token != token:
        raise HTTPException(status_code=403, detail="CSRF token invalid")
```

### 4.3 ログ・監査設計

#### 監査ログ設計
```python
# app/middleware/logging.py
import logging
from fastapi import Request
from datetime import datetime

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
    
    def log_auth_event(self, user_id: int, action: str, request: Request, details: dict = None):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "details": details
        }
        self.logger.info(f"AUDIT: {log_entry}")
```

## 5. インフラ・運用設計

### 5.1 ディレクトリ構成設計

#### /release ディレクトリ設計
```
/release/
└── 002--claude-test/                   # プロジェクトルート
    ├── frontend/                       # Next.js アプリケーション
    │   ├── src/                        # ソースコード
    │   ├── .next/                      # ビルド成果物
    │   ├── package.json                # 依存関係
    │   └── next.config.js              # Next.js設定
    ├── backend/                        # FastAPI アプリケーション
    │   ├── app/                        # アプリケーションコード
    │   ├── config/                     # 設定ファイル
    │   ├── requirements.txt            # Python依存関係
    │   └── main.py                     # エントリーポイント
    ├── config/                         # システム設定
    │   ├── nginx/                      # nginx設定
    │   │   └── staging-home.conf       # サーバー設定
    │   ├── systemd/                    # systemd設定
    │   │   ├── staging-frontend.service
    │   │   └── staging-backend.service
    │   └── env/                        # 環境変数
    │       ├── staging.frontend.env
    │       └── staging.backend.env
    ├── data/                           # データファイル
    │   ├── sqlite/                     # SQLiteデータベース
    │   │   └── staging.db
    │   └── logs/                       # ログファイル
    │       ├── frontend/
    │       ├── backend/
    │       └── nginx/
    ├── scripts/                        # 運用スクリプト
    │   ├── deploy.sh                   # デプロイ
    │   ├── start.sh                    # 一括起動
    │   ├── stop.sh                     # 一括停止
    │   ├── backup.sh                   # バックアップ
    │   └── health-check.sh             # ヘルスチェック
    └── docs/                           # ドキュメント
        ├── deployment.md               # デプロイ手順
        ├── troubleshooting.md          # トラブルシューティング
        └── api.md                      # API仕様書
```

### 5.2 nginx設定設計

#### プロキシ設定
```nginx
# /etc/nginx/sites-available/staging-home
server {
    listen 0.0.0.0:80;
    server_name home.poco *.poco;
    
    # フロントエンド（Next.js）
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # バックエンドAPI（FastAPI）
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静的ファイル最適化
    location /_next/static/ {
        proxy_pass http://localhost:3001;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # ヘルスチェック
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### 5.3 systemd サービス設計

#### フロントエンドサービス
```ini
# /etc/systemd/system/staging-frontend.service
[Unit]
Description=Staging Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/release/002--claude-test/frontend
Environment=NODE_ENV=production
Environment=PORT=3001
EnvironmentFile=/release/002--claude-test/config/env/staging.frontend.env
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### バックエンドサービス
```ini
# /etc/systemd/system/staging-backend.service
[Unit]
Description=Staging Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/release/002--claude-test/backend
Environment=PYTHONPATH=/release/002--claude-test/backend
EnvironmentFile=/release/002--claude-test/config/env/staging.backend.env
ExecStart=/usr/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.4 監視・ログ設計

#### ログ設定
```python
# app/config/logging.py
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "audit": {
            "format": "%(asctime)s - AUDIT - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": "/release/002--claude-test/data/logs/backend/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "audit",
            "filename": "/release/002--claude-test/data/logs/backend/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
        "audit": {
            "level": "INFO",
            "handlers": ["audit_file"],
            "propagate": False,
        },
    },
}
```

## 6. パフォーマンス・最適化設計

### 6.1 キャッシュ戦略設計

#### Next.js最適化設定
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // 本番最適化
  compress: true,
  poweredByHeader: false,
  
  // 画像最適化
  images: {
    domains: ['lh3.googleusercontent.com'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // キャッシュ設定
  async headers() {
    return [
      {
        source: '/_next/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },
  
  // バンドル最適化
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['@/components'],
  },
}

module.exports = nextConfig
```

#### FastAPI最適化設定
```python
# app/config/settings.py
from functools import lru_cache
import os

class Settings:
    # キャッシュ設定
    CACHE_TTL: int = 300  # 5分
    
    # データベース接続プール
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # セッション設定
    SESSION_CLEANUP_INTERVAL: int = 3600  # 1時間
    
    @lru_cache()
    def get_cache_key(self, key: str) -> str:
        return f"staging:{key}"

@lru_cache()
def get_settings():
    return Settings()
```

### 6.2 負荷テスト設計

#### 負荷テストシナリオ
```bash
# scripts/load-test.sh
#!/bin/bash

echo "=== ステージング環境負荷テスト ==="

# 1. 基本接続テスト
echo "1. 基本接続テスト"
curl -I http://home.poco/

# 2. ログインAPI負荷テスト (10並行)
echo "2. ログインAPI負荷テスト"
ab -n 100 -c 10 -H "Content-Type: application/json" \
   -p login-data.json http://home.poco/api/v1/auth/login

# 3. ダッシュボード表示テスト (5並行)
echo "3. ダッシュボード負荷テスト"
ab -n 50 -c 5 -C "session_token=test_token" \
   http://home.poco/dashboard

# 4. API応答時間測定
echo "4. API応答時間測定"
curl -w "@curl-format.txt" -o /dev/null -s http://home.poco/api/v1/health
```

## 7. エラーハンドリング・フォールバック設計

### 7.1 フロントエンドエラーハンドリング

#### エラー境界設計
```tsx
// src/components/ErrorBoundary.tsx
'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface State {
  hasError: boolean;
  error?: Error;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // 監査ログに送信
    fetch('/api/v1/audit/error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString()
      })
    }).catch(console.error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen bg-red-50 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-800 mb-4">
              アプリケーションエラー
            </h1>
            <p className="text-red-600 mb-6">
              申し訳ございません。予期しないエラーが発生しました。
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 text-white px-6 py-2 rounded-md hover:bg-red-700"
            >
              ページを再読み込み
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

### 7.2 バックエンドエラーハンドリング

#### グローバル例外ハンドラー
```python
# app/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """グローバル例外ハンドラー"""
    
    # ログ出力
    logger.error(f"Global exception: {exc}", extra={
        "url": str(request.url),
        "method": request.method,
        "client": request.client.host if request.client else None,
        "traceback": traceback.format_exc()
    })
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "success": False}
        )
    
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "入力データに問題があります",
                "errors": exc.errors(),
                "success": False
            }
        )
    
    # その他の例外
    return JSONResponse(
        status_code=500,
        content={
            "detail": "内部サーバーエラーが発生しました",
            "success": False
        }
    )
```

## 8. デプロイ・運用設計

### 8.1 デプロイスクリプト設計

#### 自動デプロイスクリプト
```bash
#!/bin/bash
# scripts/deploy.sh

set -e  # エラー時に停止

echo "=== ステージング環境デプロイ開始 ==="

# 設定
PROJECT_ROOT="/release/002--claude-test"
BACKUP_DIR="/release/backups/$(date +%Y%m%d_%H%M%S)"
SOURCE_DIR="/home/rema/project/002--claude-test"

# 1. 現在の環境をバックアップ
echo "1. 環境バックアップ中..."
sudo mkdir -p "$BACKUP_DIR"
if [ -d "$PROJECT_ROOT" ]; then
    sudo cp -r "$PROJECT_ROOT" "$BACKUP_DIR/"
fi

# 2. プロジェクトディレクトリ作成
echo "2. プロジェクトディレクトリ準備中..."
sudo mkdir -p "$PROJECT_ROOT"
sudo mkdir -p "$PROJECT_ROOT/data/logs/{frontend,backend,nginx}"
sudo mkdir -p "$PROJECT_ROOT/data/sqlite"

# 3. ソースコード複製
echo "3. ソースコード複製中..."
sudo cp -r "$SOURCE_DIR/frontend" "$PROJECT_ROOT/"
sudo cp -r "$SOURCE_DIR/backend" "$PROJECT_ROOT/" || {
    # backend ディレクトリが存在しない場合は作成
    echo "backend ディレクトリを新規作成..."
    sudo mkdir -p "$PROJECT_ROOT/backend"
}

# 4. フロントエンドビルド
echo "4. フロントエンドビルド中..."
cd "$PROJECT_ROOT/frontend"
sudo npm install
sudo npm run build

# 5. バックエンド依存関係インストール
echo "5. バックエンド依存関係インストール中..."
cd "$PROJECT_ROOT/backend"
sudo pip install -r requirements.txt || true  # requirements.txtが無い場合は無視

# 6. 設定ファイル配置
echo "6. 設定ファイル配置中..."
sudo cp "$SOURCE_DIR/spec/kairo/staging-environment/config"/* "$PROJECT_ROOT/config/" || true

# 7. nginx設定更新
echo "7. nginx設定更新中..."
sudo ln -sf "$PROJECT_ROOT/config/nginx/staging-home.conf" /etc/nginx/sites-available/staging-home
sudo ln -sf /etc/nginx/sites-available/staging-home /etc/nginx/sites-enabled/
sudo nginx -t  # 設定テスト

# 8. systemdサービス登録
echo "8. systemdサービス登録中..."
sudo cp "$PROJECT_ROOT/config/systemd"/*.service /etc/systemd/system/ || true
sudo systemctl daemon-reload

# 9. サービス起動
echo "9. サービス起動中..."
sudo systemctl restart nginx
sudo systemctl enable staging-frontend staging-backend || true
sudo systemctl start staging-frontend staging-backend || true

# 10. ヘルスチェック
echo "10. ヘルスチェック実行中..."
sleep 5
curl -f http://localhost:3001/ || echo "フロントエンド接続確認に失敗"
curl -f http://localhost:8000/health || echo "バックエンド接続確認に失敗"
curl -f http://home.poco/ || echo "プロキシ接続確認に失敗"

echo "=== デプロイ完了 ==="
echo "アクセスURL: http://home.poco/"
echo "バックアップ: $BACKUP_DIR"
```

## 9. 技術検証結果・設計改善（2025-09-05）

### 9.1 検証で確認された設計の有効性
✅ **アーキテクチャ設計**: nginx → Next.js(3001) + FastAPI(8000) 構成が正常動作  
✅ **認証フロー設計**: HTTPOnly Cookie + セッション管理が期待通り動作  
✅ **API設計**: REST APIエンドポイント（/api/v1/auth/*）が仕様通り動作  
✅ **プロキシ設計**: nginx経由でのAPIアクセスが正常に転送される  

### 9.2 発見された設計改善ポイント

#### 9.2.1 ビルド管理設計の強化
**問題**: Next.js JavaScript ファイル名の動的変更（hash）とキャッシュ不整合  
**設計改善**:
- ビルド成果物の管理強化（`.next/` ディレクトリクリーンアップ）
- 環境別ビルド設定の分離（staging.next.config.js）
- ビルドキャッシュ戦略の見直し

#### 9.2.2 バックエンドエラーハンドリング設計の改善
**問題**: datetime import / リクエストボディ処理での500エラー  
**設計改善**:
```python
# 改善されたFastAPI設定
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel, ValidationError
import traceback
import logging

# より堅牢なエラーハンドリング
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "success": False}
    )
```

#### 9.2.3 開発・ステージング分離設計の強化
**現状**: 開発環境の設定がステージング環境に影響  
**設計改善**:
```
/release/002--claude-test/
├── config/
│   ├── env/
│   │   ├── staging.frontend.env    # ステージング専用環境変数
│   │   └── staging.backend.env     # バックエンド専用設定
│   ├── next/
│   │   └── staging.config.js       # ステージング専用Next.js設定
│   └── nginx/
│       └── staging-home.conf       # ステージング専用nginx設定
└── scripts/
    ├── staging-build.sh            # ステージング専用ビルド
    └── staging-deploy.sh           # ステージング専用デプロイ
```

### 9.3 実装済み技術検証ファイル（一時的）
技術検証で使用した一時ファイルの管理:
- `/tmp/temp_backend.py` - 修正版バックエンド（技術検証用）
- `/tmp/tech_verification_login.html` - HTML版ログインテスト
- `tests/e2e/final-complete-test.spec.js` - Step1-6完全テスト

**注意**: 本格実装時は一時ファイルを本番コードに統合すること

---

## 履歴管理

| 日付 | バージョン | 変更内容 | 承認者 |
|------|------------|----------|--------|
| 2025-09-04 | 1.0 | 設計書初版作成 | - |
| 2025-09-05 | 1.1 | 技術検証結果反映・設計改善追加 | - |

---

**作成日**: 2025-09-04  
**更新日**: 2025-09-05  
**モード**: DESIGN（技術検証完了）  
**次フェーズ**: 本格実装 → 最終テスト → ユーザーテスト