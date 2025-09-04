# users テーブル定義

**参照元**: [データベース設計書](/dev_tools/spec/02_database_design.md)  
**関連機能**: [ログイン機能](/dev_tools/spec/kairo/login/)

## テーブル構造

```sql
CREATE TABLE users (
    -- 共通カラム
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- 必須カラム（構造化）
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    
    -- 柔軟カラム（JSONB）
    profile JSONB DEFAULT '{}',      -- 名前、アバター、プロフィール情報
    preferences JSONB DEFAULT '{}', -- ユーザー設定
    metadata JSONB DEFAULT '{}'     -- システムメタデータ
);
```

## インデックス

```sql
-- 基本インデックス
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);

-- JSONB用GINインデックス
CREATE INDEX idx_users_profile_gin ON users USING GIN (profile);
CREATE INDEX idx_users_preferences_gin ON users USING GIN (preferences);

-- 複合インデックス
CREATE INDEX idx_users_status_created ON users (status, created_at DESC) WHERE deleted_at IS NULL;

-- 部分インデックス（論理削除対応）
CREATE INDEX idx_users_active_email ON users (email) WHERE deleted_at IS NULL;
```

## 制約

### 外部キー制約
なし（親テーブル）

### CHECK制約
```sql
-- ステータス値制限
ALTER TABLE users ADD CONSTRAINT chk_users_status 
CHECK (status IN ('active', 'inactive', 'suspended'));

-- メール形式検証
ALTER TABLE users ADD CONSTRAINT chk_users_email_format 
CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$');
```

### UNIQUE制約
```sql
-- 論理削除を考慮したユニーク制約
CREATE UNIQUE INDEX idx_users_email_unique 
ON users (email) WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX idx_users_username_unique 
ON users (username) WHERE deleted_at IS NULL;
```

## JSONB構造例

### profile カラム
```json
{
    "name": {
        "first": "太郎",
        "last": "田中", 
        "display": "田中太郎"
    },
    "avatar": "https://example.com/avatar.jpg",
    "bio": "ソフトウェアエンジニア",
    "social": {
        "twitter": "@example",
        "github": "example",
        "website": "https://example.com"
    },
    "location": "Tokyo, Japan",
    "timezone": "Asia/Tokyo"
}
```

### preferences カラム
```json
{
    "theme": "dark",
    "language": "ja",
    "notifications": {
        "email": true,
        "push": false,
        "frequency": "daily"
    },
    "ui": {
        "sidebar_collapsed": false,
        "grid_view": true,
        "items_per_page": 20
    },
    "privacy": {
        "profile_public": false,
        "activity_public": false
    }
}
```

### metadata カラム
```json
{
    "signup_ip": "192.168.1.1",
    "signup_user_agent": "Chrome/120.0.0.0",
    "email_verified": true,
    "email_verified_at": "2025-08-29T10:00:00Z",
    "last_login": "2025-08-29T09:30:00Z",
    "login_count": 42,
    "account_source": "google_oauth",
    "terms_accepted_version": "1.0"
}
```

## SQLクエリ例

### 基本操作
```sql
-- ユーザー作成
INSERT INTO users (email, profile) VALUES (
    'user@example.com',
    '{"name": {"display": "田中太郎"}, "timezone": "Asia/Tokyo"}'
);

-- プロフィール更新
UPDATE users 
SET profile = jsonb_set(profile, '{bio}', '"新しい自己紹介"')
WHERE id = ?;

-- 設定変更
UPDATE users 
SET preferences = preferences || '{"theme": "light"}'
WHERE id = ?;

-- 複合検索
SELECT * FROM users 
WHERE profile->>'bio' LIKE '%エンジニア%' 
  AND preferences->>'theme' = 'dark'
  AND deleted_at IS NULL;
```

## パフォーマンス考慮

### クエリ最適化
```sql
-- EXPLAIN ANALYZE で性能確認
EXPLAIN ANALYZE SELECT * FROM users WHERE profile->>'name' = '田中太郎';

-- インデックスヒント
SELECT * FROM users WHERE email = ? ORDER BY created_at DESC LIMIT 10;
-- → idx_users_active_email が使用される
```

## 履歴
- **2025-08-29**: 初期テーブル定義作成
- **2025-08-29**: JSONB構造設計完了