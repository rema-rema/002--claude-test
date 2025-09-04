# sessions テーブル定義

**参照元**: [データベース設計書](/dev_tools/spec/02_database_design.md)  
**関連機能**: [ログイン機能](/dev_tools/spec/kairo/login/)

## テーブル構造

```sql
CREATE TABLE sessions (
    -- 共通カラム
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- リレーション
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- セッション情報
    session_token VARCHAR(255) UNIQUE NOT NULL,  -- JWTトークンまたはセッションID
    ip_address INET,                            -- クライアントIPアドレス
    user_agent TEXT,                            -- ブラウザ情報
    
    -- セッションデータ（JSONB）
    data JSONB DEFAULT '{}',                    -- セッション固有データ
    
    -- 状態管理
    is_active BOOLEAN DEFAULT TRUE,             -- アクティブ状態
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT NULL -- 無効化時刻
);
```

## インデックス

```sql
-- 基本インデックス
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_ip_address ON sessions(ip_address);

-- JSONB用GINインデックス
CREATE INDEX idx_sessions_data_gin ON sessions USING GIN (data);

-- 複合インデックス
CREATE INDEX idx_sessions_user_active ON sessions (user_id, is_active, expires_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_sessions_cleanup ON sessions (expires_at, revoked_at) WHERE NOT is_active;

-- 部分インデックス（アクティブセッションのみ）
CREATE INDEX idx_sessions_active_user ON sessions (user_id) WHERE is_active = TRUE AND revoked_at IS NULL;
```

## 制約

### 外部キー制約
```sql
-- ユーザーテーブルとの関連
ALTER TABLE sessions 
ADD CONSTRAINT fk_sessions_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### CHECK制約
```sql
-- 有効期限の妥当性チェック
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_expires_future 
CHECK (expires_at > created_at);

-- セッショントークンの最小長
ALTER TABLE sessions ADD CONSTRAINT chk_sessions_token_length 
CHECK (LENGTH(session_token) >= 32);

-- IPアドレス形式チェック（PostgreSQL INETで自動）
```

## JSONB構造例

### data カラム（セッション固有データ）
```json
{
    "login_method": "google_oauth",
    "device_info": {
        "platform": "Web",
        "browser": "Chrome",
        "version": "120.0.0.0",
        "mobile": false
    },
    "location": {
        "country": "JP",
        "city": "Tokyo",
        "timezone": "Asia/Tokyo"
    },
    "security": {
        "two_factor_verified": false,
        "suspicious_activity": false,
        "login_attempts": 1
    },
    "preferences": {
        "remember_me": true,
        "auto_logout": 3600  // 秒
    }
}
```

### セッション状態管理例
```json
{
    "state": "active",
    "last_activity": "2025-08-29T10:30:00Z",
    "page_views": 15,
    "api_calls": 42,
    "features_used": ["dashboard", "profile"],
    "warnings": []
}
```

## SQLクエリ例

### 基本操作
```sql
-- セッション作成
INSERT INTO sessions (user_id, session_token, ip_address, user_agent, expires_at, data) 
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    '192.168.1.100',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    CURRENT_TIMESTAMP + INTERVAL '24 hours',
    '{"login_method": "google_oauth", "device_info": {"browser": "Chrome"}}'
);

-- アクティブセッション取得
SELECT s.id, s.created_at, s.expires_at, s.data
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE u.email = 'user@example.com'
  AND s.is_active = TRUE
  AND s.expires_at > CURRENT_TIMESTAMP
  AND s.revoked_at IS NULL;

-- セッション無効化
UPDATE sessions 
SET is_active = FALSE, 
    revoked_at = CURRENT_TIMESTAMP
WHERE session_token = ?;

-- 期限切れセッション削除
DELETE FROM sessions 
WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
```

### 高度なクエリ
```sql
-- ユーザーの同時セッション数制限チェック
SELECT COUNT(*) as active_sessions
FROM sessions 
WHERE user_id = ? 
  AND is_active = TRUE 
  AND expires_at > CURRENT_TIMESTAMP
  AND revoked_at IS NULL;

-- 怪しいセッションの検出
SELECT s.*, u.email
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.data->>'security'->>'suspicious_activity' = 'true'
  OR s.ip_address != ALL(
    SELECT DISTINCT ip_address 
    FROM sessions 
    WHERE user_id = s.user_id 
      AND created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
  );

-- セッション統計
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN data->>'login_method' = 'google_oauth' THEN 1 END) as google_logins
FROM sessions 
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date;
```

## セキュリティ機能

### セッション管理ポリシー
```sql
-- 最大セッション数制限（例：5個）
CREATE OR REPLACE FUNCTION enforce_max_sessions()
RETURNS TRIGGER AS $$
BEGIN
    -- 古いセッションを自動無効化
    UPDATE sessions 
    SET is_active = FALSE, revoked_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id 
      AND is_active = TRUE
      AND id != NEW.id
      AND created_at < (
        SELECT created_at 
        FROM sessions 
        WHERE user_id = NEW.user_id AND is_active = TRUE
        ORDER BY created_at DESC 
        LIMIT 1 OFFSET 4
      );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_max_sessions
AFTER INSERT ON sessions
FOR EACH ROW EXECUTE FUNCTION enforce_max_sessions();
```

### セッション監査
```sql
-- セッション変更履歴（監査ログ）
CREATE TABLE session_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'created', 'updated', 'revoked', 'expired'
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## パフォーマンス最適化

### 定期クリーンアップ
```sql
-- 期限切れセッション削除（Celeryタスク）
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions 
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
       OR (revoked_at IS NOT NULL AND revoked_at < CURRENT_TIMESTAMP - INTERVAL '1 day');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

### パーティショニング（大規模時）
```sql
-- 月別パーティション例
CREATE TABLE sessions_partitioned (
    LIKE sessions INCLUDING ALL
) PARTITION BY RANGE (created_at);

CREATE TABLE sessions_2025_08 PARTITION OF sessions_partitioned
FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
```

## 履歴
- **2025-08-29**: 初期テーブル定義作成
- **2025-08-29**: セキュリティ機能設計完了