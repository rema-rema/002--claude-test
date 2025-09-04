# auth_providers テーブル定義

**参照元**: [データベース設計書](/dev_tools/spec/02_database_design.md)  
**関連機能**: [ログイン機能](/dev_tools/spec/kairo/login/)

## テーブル構造

```sql
CREATE TABLE auth_providers (
    -- 共通カラム
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- リレーション
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- プロバイダー情報
    provider VARCHAR(50) NOT NULL,          -- 'google', 'github', 'discord', etc
    provider_user_id VARCHAR(255) NOT NULL,-- プロバイダー側のユーザーID
    
    -- 認証データ（JSONB）
    auth_data JSONB DEFAULT '{}',           -- トークン、スコープ等
    
    -- 複合ユニーク制約
    UNIQUE(provider, provider_user_id)
);
```

## インデックス

```sql
-- 基本インデックス
CREATE INDEX idx_auth_providers_user_id ON auth_providers(user_id);
CREATE INDEX idx_auth_providers_provider ON auth_providers(provider);
CREATE INDEX idx_auth_providers_provider_user_id ON auth_providers(provider_user_id);

-- JSONB用GINインデックス
CREATE INDEX idx_auth_providers_auth_data_gin ON auth_providers USING GIN (auth_data);

-- 複合インデックス
CREATE INDEX idx_auth_providers_provider_user ON auth_providers (provider, provider_user_id);
```

## 制約

### 外部キー制約
```sql
-- ユーザーテーブルとの関連
ALTER TABLE auth_providers 
ADD CONSTRAINT fk_auth_providers_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### CHECK制約
```sql
-- サポートするプロバイダー制限
ALTER TABLE auth_providers ADD CONSTRAINT chk_auth_providers_provider 
CHECK (provider IN ('google', 'github', 'discord', 'microsoft', 'apple'));

-- プロバイダーユーザーIDの最小長
ALTER TABLE auth_providers ADD CONSTRAINT chk_auth_providers_provider_user_id 
CHECK (LENGTH(provider_user_id) >= 1);
```

### UNIQUE制約
```sql
-- 同一プロバイダーでの重複アカウント防止
CREATE UNIQUE INDEX idx_auth_providers_unique 
ON auth_providers (provider, provider_user_id);
```

## JSONB構造例

### Google OAuth認証データ
```json
{
    "access_token": "ya29.a0ARrdaM...",
    "refresh_token": "1//0e...",
    "token_type": "Bearer",
    "expires_at": "2025-08-29T11:00:00Z",
    "scope": ["email", "profile", "openid"],
    "user_info": {
        "email": "user@gmail.com",
        "name": "田中太郎",
        "picture": "https://lh3.googleusercontent.com/...",
        "locale": "ja",
        "email_verified": true
    },
    "raw_response": {
        "iss": "https://accounts.google.com",
        "aud": "client_id.googleusercontent.com",
        "sub": "1234567890"
    }
}
```

### GitHub OAuth認証データ（将来用）
```json
{
    "access_token": "gho_xxxxxxxxxxxxxxxxxxxx",
    "token_type": "bearer",
    "scope": "read:user,user:email",
    "user_info": {
        "login": "username",
        "email": "user@github.com", 
        "name": "田中太郎",
        "avatar_url": "https://avatars.githubusercontent.com/..."
    }
}
```

## SQLクエリ例

### 基本操作
```sql
-- 認証プロバイダー追加
INSERT INTO auth_providers (user_id, provider, provider_user_id, auth_data) 
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    'google',
    '1234567890',
    '{"access_token": "ya29...", "user_info": {"email": "user@gmail.com"}}'
);

-- ユーザーの認証プロバイダー取得
SELECT ap.provider, ap.auth_data->>'user_info' as user_info
FROM auth_providers ap
JOIN users u ON ap.user_id = u.id
WHERE u.email = 'user@example.com';

-- トークンリフレッシュ
UPDATE auth_providers 
SET auth_data = jsonb_set(auth_data, '{access_token}', '"new_token"'),
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = ? AND provider = 'google';

-- プロバイダー別ユーザー数
SELECT provider, COUNT(*) as user_count
FROM auth_providers 
GROUP BY provider;
```

### 高度なクエリ
```sql
-- 複数プロバイダーを持つユーザー
SELECT u.email, array_agg(ap.provider) as providers
FROM users u
JOIN auth_providers ap ON u.id = ap.user_id
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.email
HAVING COUNT(ap.id) > 1;

-- 期限切れトークンのクリーンアップ
DELETE FROM auth_providers
WHERE auth_data->>'expires_at' < CURRENT_TIMESTAMP::TEXT;
```

## セキュリティ考慮

### トークン暗号化（高セキュリティ要求時）
```sql
-- 機密トークンの暗号化保存
UPDATE auth_providers 
SET auth_data = jsonb_set(
    auth_data, 
    '{access_token}', 
    to_jsonb(pgp_sym_encrypt(auth_data->>'access_token', 'encryption_key'))
)
WHERE provider = 'google';
```

### アクセス制御
```sql
-- Row Level Security (将来実装)
ALTER TABLE auth_providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY auth_providers_user_policy ON auth_providers
FOR ALL TO app_user
USING (user_id = current_user_id());
```

## パフォーマンス最適化

### 定期メンテナンス
```sql
-- 期限切れトークンの自動削除（Celeryタスク用）
DELETE FROM auth_providers
WHERE auth_data->>'expires_at' < (CURRENT_TIMESTAMP - INTERVAL '1 day')::TEXT;

-- 統計情報更新
ANALYZE auth_providers;
```

## 履歴
- **2025-08-29**: 初期テーブル定義作成
- **2025-08-29**: Google OAuth対応設計完了