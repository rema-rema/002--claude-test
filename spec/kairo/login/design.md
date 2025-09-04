# Login機能 - 詳細設計書（更新版）

## 📋 全体設計書との関連
本設計書は、以下の全体設計書を基盤として作成されています：

- [アーキテクチャ設計](/spec/01_architecture_design.md) - システム全体の技術スタック（FastAPI + Next.js）
- [データベース設計](/spec/02_database_design.md) - PostgreSQL + Redis の設計方針
- [API設計](/spec/03_api_design.md) - FastAPI標準仕様

本書では、上記の全体設計方針に準拠した**ログイン機能固有の実装**について詳述します。

## 1. アーキテクチャ設計

### 1.1 システム全体図
```
[ユーザー] → [Next.js Frontend] → [FastAPI Backend] → [Google OAuth/Mock Auth] → [PostgreSQL/Redis]
                    ↓
              [Dashboard] ← [JWT Authentication]
```

### 1.2 コンポーネント構成
- **Frontend Layer**: Next.js 14 (App Router) + TypeScript
- **API Layer**: FastAPI (Python 3.11+)
- **Authentication Layer**: JWT + Google OAuth 2.0（段階的実装）
- **Session Layer**: Redis（セッション管理）+ HTTPOnly Cookies

### 1.3 段階的実装アプローチ
1. **Phase 1**: モック認証実装（開発効率化）✅ 完了
2. **Phase 2**: UI/UXコンポーネント実装（進行中）
3. **Phase 3**: Google OAuth統合（後日実装）

## 2. 詳細設計

### 2.1 フロントエンド設計（Next.js 14）

#### 2.1.1 ログインページ (`/app/login/page.tsx`)
```tsx
'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { GoogleLoginButton } from '@/features/login/components/GoogleLoginButton';
import { MockLoginForm } from '@/features/login/components/MockLoginForm';
import { useAuthState } from '@/features/login/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthState();
  const isMockAuthEnabled = process.env.NEXT_PUBLIC_MOCK_AUTH_ENABLED === 'true';

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white shadow-lg rounded-lg px-8 pt-6 pb-8">
          <h2 className="text-3xl font-bold text-center mb-6">ログイン</h2>
          
          {isMockAuthEnabled ? (
            <MockLoginForm />
          ) : (
            <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
              <GoogleLoginButton />
            </GoogleOAuthProvider>
          )}
        </div>
      </div>
    </div>
  );
}
```

#### 2.1.2 認証フック (`/features/login/hooks/useAuth.ts`)
```typescript
import { useState, useEffect } from 'react';
import { authService } from '../services/authService';

export function useAuthState() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await authService.checkAuth();
      setIsAuthenticated(response.is_authenticated);
      setUser(response.user);
    } catch (error) {
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  return { isAuthenticated, isLoading, user };
}

export function useAuth() {
  const login = async (email: string, password: string) => {
    const response = await authService.mockLogin(email, password);
    return response;
  };

  const logout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  return { login, logout };
}
```

#### 2.1.3 認証サービス (`/features/login/services/authService.ts`)
```typescript
class AuthService {
  private baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  async mockLogin(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/api/auth/mock-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password })
    });
    return response.json();
  }

  async googleLogin(accessToken: string) {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ 
        access_token: accessToken,
        provider: 'google'
      })
    });
    return response.json();
  }

  async checkAuth() {
    const response = await fetch(`${this.baseURL}/api/auth/me`, {
      credentials: 'include'
    });
    return response.json();
  }

  async logout() {
    await fetch(`${this.baseURL}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    });
  }
}

export const authService = new AuthService();
```

### 2.2 バックエンド設計（FastAPI）

#### 2.2.1 認証ルート (`/backend/src/features/login/routes.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.database import get_db
from src.core.auth import jwt_manager, google_oauth
from .services import auth_service
from .schemas import LoginRequest, TokenResponse, UserResponse

auth_router = APIRouter()

@auth_router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Google OAuth login endpoint with HTTPOnly Cookie security."""
    try:
        # Google OAuth認証（後で実装）
        if request.provider == "google":
            user_info = await google_oauth.verify_access_token(request.access_token)
            user = await auth_service.create_or_update_user(db, user_info)
        
        # JWT生成
        access_token = jwt_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = jwt_manager.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # HTTPOnly Cookie設定
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800
        )
        
        return {"success": True, "user": user}
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@auth_router.get("/me")
async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user information."""
    if not access_token:
        return {"is_authenticated": False, "user": None}
    
    try:
        payload = jwt_manager.verify_token(access_token)
        user = await auth_service.get_user_by_id(db, payload["sub"])
        return {"is_authenticated": True, "user": user}
    except:
        return {"is_authenticated": False, "user": None}
```

#### 2.2.2 モック認証ルート (`/backend/src/features/login/mock_routes.py`)
```python
from fastapi import APIRouter, Response, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

from src.core.auth import jwt_manager
from src.core.config import settings

mock_auth_router = APIRouter()

class MockLoginRequest(BaseModel):
    email: EmailStr
    password: str

# テスト用ユーザーデータ
MOCK_USERS = {
    "test@example.com": {
        "password": "password123",
        "name": "Test User",
        "id": "550e8400-e29b-41d4-a716-446655440001"
    },
    "admin@example.com": {
        "password": "admin123",
        "name": "Admin User",
        "id": "550e8400-e29b-41d4-a716-446655440002"
    }
}

@mock_auth_router.post("/mock-login")
async def mock_login(request: MockLoginRequest, response: Response):
    """開発用モックログインエンドポイント"""
    if not settings.MOCK_AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="Mock auth is disabled")
    
    mock_user = MOCK_USERS.get(request.email)
    if not mock_user or mock_user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # JWT生成
    access_token = jwt_manager.create_access_token(
        data={"sub": mock_user["id"], "email": request.email}
    )
    
    # HTTPOnly Cookie設定
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # 開発環境用
        samesite="lax",
        max_age=1800
    )
    
    return {
        "success": True,
        "user": {
            "id": mock_user["id"],
            "email": request.email,
            "name": mock_user["name"]
        }
    }

@mock_auth_router.get("/mock-users")
async def get_mock_users():
    """利用可能なテストユーザー一覧"""
    if not settings.MOCK_AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="Mock auth is disabled")
    
    return {
        "mock_auth_enabled": True,
        "users": [
            {"email": email, "name": data["name"], "hint": f"password: {data['password'][:3]}***"}
            for email, data in MOCK_USERS.items()
        ]
    }
```

#### 2.2.3 JWT管理 (`/backend/src/core/auth.py`)
```python
from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from .config import settings

class JWTManager:
    """JWT token management."""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        return payload

jwt_manager = JWTManager()
```

### 2.3 データベース設計

#### 2.3.1 ユーザーモデル (`/backend/src/features/login/models.py`)
```python
from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from src.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    picture = Column(String)
    provider = Column(String, default="google")
    provider_id = Column(String)
    metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.4 セキュリティ設計

#### 2.4.1 セキュリティ対策
- **HTTPOnly Cookies**: XSS攻撃対策
- **CSRF Protection**: State parameter検証（Google OAuth実装時）
- **Secure Flag**: HTTPS環境でのみCookie送信（本番環境）
- **SameSite**: CSRF攻撃の追加防御
- **JWT有効期限**: アクセストークン30分、リフレッシュトークン7日

#### 2.4.2 CORS設定
```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:3001", ...]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 3. API仕様

### 3.1 認証エンドポイント

| エンドポイント | メソッド | 説明 | 認証要否 |
|---|---|---|---|
| `/api/auth/login` | POST | Google OAuth ログイン | 不要 |
| `/api/auth/mock-login` | POST | モックログイン（開発用） | 不要 |
| `/api/auth/logout` | POST | ログアウト | 必要 |
| `/api/auth/me` | GET | 現在のユーザー情報取得 | 必要 |
| `/api/auth/refresh` | POST | トークンリフレッシュ | 必要 |
| `/api/auth/mock-users` | GET | テストユーザー一覧（開発用） | 不要 |

### 3.2 レスポンス形式

#### 成功時
```json
{
  "success": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "test@example.com",
    "name": "Test User",
    "picture": "https://..."
  }
}
```

#### エラー時
```json
{
  "detail": "Invalid credentials"
}
```

## 4. 環境変数

```env
# JWT設定
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

# Google OAuth（後で設定）
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/callback

# モック認証
MOCK_AUTH_ENABLED=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8000,http://localhost:8001

# データベース
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
```

## 5. テスト戦略

### 5.1 単体テスト
- JWT生成・検証
- モックログイン機能
- 認証ミドルウェア

### 5.2 統合テスト
- ログインフロー全体
- セッション管理
- Cookie設定・削除

### 5.3 E2Eテスト（Playwright）
- ログイン画面表示
- モックログイン実行
- ダッシュボード遷移
- ログアウト処理

---

**更新日**: 2025-08-29  
**更新理由**: 全体設計書（FastAPI + Next.js）との整合性確保  
**次フェーズ**: UI実装 → Google OAuth統合