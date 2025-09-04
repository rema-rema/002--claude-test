# データベース設計書

## 1. データベース全体方針

### 1.1 設計思想
本システムのデータベース設計は、**柔軟性と堅牢性の両立**を目指し、以下の原則に従います：

- **ハイブリッド型データ管理**: 構造化データ（リレーショナル）と非構造化データ（JSONB）の適材適所
- **スキーマ進化への対応**: マイグレーション容易性とダウンタイム最小化
- **パフォーマンス最適化**: 適切なインデックス戦略とキャッシュ活用
- **データ整合性**: トランザクション管理とバリデーション

### 1.2 データストア構成

#### PostgreSQL（メインデータベース）
- **用途**: トランザクショナルデータ、マスターデータ
- **バージョン**: 15以上
- **特徴**: JSONB型による柔軟なスキーマ対応

#### Redis（キャッシュ・セッション）
- **用途**: セッション管理、キャッシュ、タスクキュー
- **バージョン**: 7以上
- **永続化**: AOF（Append Only File）有効

#### ローカルファイルシステム
- **用途**: アップロードファイル、静的コンテンツ
- **構造**: 階層型ディレクトリ管理
- **将来**: S3互換ストレージへの移行可能

## 2. PostgreSQL設計詳細

### 2.1 データベース構造
```sql
-- データベース作成
CREATE DATABASE myapp
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ja_JP.UTF-8'
    LC_CTYPE = 'ja_JP.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- 拡張機能
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### 2.2 共通カラム定義
すべてのテーブルに含まれる共通カラム：
```sql
id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
deleted_at  TIMESTAMP WITH TIME ZONE DEFAULT NULL  -- 論理削除
```

### 2.3 テーブル定義参照

各テーブルの詳細定義は、個別のスキーマ定義ファイルを参照してください：

| テーブル名 | 用途 | 詳細定義 |
|-----------|------|----------|
| `users` | ユーザー基本情報・プロフィール管理 | [users.md](./02_database_schemas/users.md) |
| `auth_providers` | OAuth認証プロバイダー情報管理 | [auth_providers.md](./02_database_schemas/auth_providers.md) |
| `sessions` | セッション・JWT管理 | [sessions.md](./02_database_schemas/sessions.md) |

### 2.4 テーブル関係図
全体のER図とテーブル関係については以下を参照：
- [ER図・リレーション定義](.//02_database_schemas/_relations.md)

### 2.4 JSONB活用パターン

#### パターン1: ユーザープロファイル
```sql
-- プロファイルJSONB構造例
{
    "name": {
        "first": "太郎",
        "last": "田中",
        "display": "田中太郎"
    },
    "avatar": "https://example.com/avatar.jpg",
    "bio": "エンジニア",
    "social": {
        "twitter": "@example",
        "github": "example"
    },
    "custom_fields": {
        "department": "開発部",
        "employee_id": "EMP001"
    }
}

-- クエリ例
SELECT * FROM users WHERE profile->>'bio' LIKE '%エンジニア%';
SELECT * FROM users WHERE profile->'social'->>'twitter' IS NOT NULL;
```

#### パターン2: 設定・プリファレンス
```sql
-- プリファレンスJSONB構造例
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
        "grid_view": true
    }
}

-- 更新例
UPDATE users 
SET preferences = jsonb_set(preferences, '{theme}', '"light"')
WHERE id = ?;
```

### 2.5 マイグレーション戦略

#### Alembicによる自動マイグレーション
```python
# alembic.ini
[alembic]
script_location = backend/migrations
sqlalchemy.url = postgresql://user:pass@localhost/myapp

# マイグレーションコマンド
alembic init migrations
alembic revision --autogenerate -m "add user table"
alembic upgrade head
```

#### JSONB利点：スキーマレス変更
```sql
-- カラム追加不要、即座に新フィールド追加可能
UPDATE users 
SET profile = profile || '{"new_field": "value"}'
WHERE id = ?;
```

## 3. Redis設計詳細

### 3.1 キー設計規約
```
{prefix}:{entity}:{identifier}:{suffix}

例：
session:user:123456:data
cache:api:user_profile:123456
queue:task:celery:default
```

### 3.2 用途別設計

#### セッション管理
```python
# キー構造
session:{session_id} → JSON data
user:sessions:{user_id} → Set of session_ids

# TTL設定
24時間（設定可能）
```

#### APIキャッシュ
```python
# キー構造
cache:api:{endpoint}:{params_hash} → Response JSON

# TTL設定
5分〜1時間（エンドポイント別）
```

#### タスクキュー（Celery）
```python
# キー構造
celery:queue:{queue_name} → List of tasks
celery:result:{task_id} → Task result

# TTL設定
結果は1時間保持
```

### 3.3 Redis永続化設定
```conf
# redis.conf
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
```

## 4. データ整合性とトランザクション

### 4.1 トランザクション管理
```python
# SQLAlchemy によるトランザクション
async with async_session() as session:
    async with session.begin():
        user = User(email="test@example.com")
        session.add(user)
        
        auth_provider = AuthProvider(
            user_id=user.id,
            provider="google"
        )
        session.add(auth_provider)
        # 自動コミットまたはロールバック
```

### 4.2 楽観的ロック
```sql
-- version カラムによる楽観的ロック
ALTER TABLE users ADD COLUMN version INTEGER DEFAULT 0;

-- 更新時のバージョンチェック
UPDATE users 
SET data = ?, version = version + 1 
WHERE id = ? AND version = ?;
```

## 5. パフォーマンス最適化

### 5.1 インデックス戦略
```sql
-- 基本インデックス
CREATE INDEX ON table_name (column_name);

-- 複合インデックス
CREATE INDEX ON users (status, created_at DESC);

-- JSONB用GINインデックス
CREATE INDEX ON users USING GIN (profile);

-- 部分インデックス
CREATE INDEX ON users (email) WHERE deleted_at IS NULL;
```

### 5.2 パーティショニング（将来対応）
```sql
-- 時系列データのパーティション例
CREATE TABLE logs (
    id UUID,
    created_at TIMESTAMP,
    data JSONB
) PARTITION BY RANGE (created_at);

CREATE TABLE logs_2024_01 PARTITION OF logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## 6. バックアップとリストア

### 6.1 バックアップ戦略
```bash
# 日次バックアップスクリプト
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -h localhost -U postgres -d myapp | gzip > /backups/myapp_$DATE.sql.gz

# 保持期間：30日
find /backups -name "*.sql.gz" -mtime +30 -delete
```

### 6.2 ポイントインタイムリカバリ
```bash
# WAL アーカイブ設定
archive_mode = on
archive_command = 'cp %p /archive/%f'
```

## 7. 監視とメンテナンス

### 7.1 監視項目
- 接続数
- クエリパフォーマンス
- テーブル/インデックスサイズ
- デッドロック
- レプリケーション遅延

### 7.2 定期メンテナンス
```sql
-- VACUUM（自動実行も設定）
VACUUM ANALYZE;

-- インデックス再構築
REINDEX DATABASE myapp;

-- 統計情報更新
ANALYZE;
```

## 8. セキュリティ

### 8.1 アクセス制御
```sql
-- ロール作成
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE myapp TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

### 8.2 データ暗号化
```sql
-- 機密データの暗号化
CREATE EXTENSION pgcrypto;

-- 暗号化保存
INSERT INTO users (email, secret_data) 
VALUES ('user@example.com', pgp_sym_encrypt('secret', 'password'));

-- 復号化取得
SELECT pgp_sym_decrypt(secret_data, 'password') FROM users;
```

## 9. 機能別テーブル設計への参照

各機能の詳細なテーブル設計は、機能別設計書を参照してください：

- [ログイン機能のDB設計](/dev_tools/spec/kairo/login/design.md#データベース設計)
- [その他機能のDB設計](/dev_tools/spec/kairo/[機能名]/design.md)

**注**: 本書では全体的なデータベース設計方針と共通仕様を定義しています。各機能固有のテーブル定義や詳細な実装は、それぞれの機能別設計書に記載されます。

## 10. 移行計画

### 10.1 既存データからの移行
```python
# 移行スクリプト例
async def migrate_from_old_system():
    # 旧システムからデータ取得
    old_data = fetch_from_old_db()
    
    # 新形式に変換
    for record in old_data:
        user = User(
            email=record['email'],
            profile={
                'name': record['name'],
                'legacy_id': record['id']
            }
        )
        await session.add(user)
```

### 10.2 将来の拡張性
- NoSQL（MongoDB）へのハイブリッド移行
- 時系列データベース（TimescaleDB）統合
- グラフデータベース（Neo4j）連携

---

**最終更新日**: 2025-08-29  
**バージョン**: 2.0.0  
**ステータス**: 確定