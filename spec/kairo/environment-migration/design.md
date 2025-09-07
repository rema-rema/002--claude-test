# 🏗️ Environment Migration - 設計書

## 📋 設計概要

### 設計方針
物理Linuxサーバー上での検証環境・開発環境分離を**コンテナ・VM分離アーキテクチャ**で実現。現状の開発VM環境を保持しつつ、検証環境を物理サーバー直接実行で構築する。

### アーキテクチャ概念図

```mermaid
graph TB
    subgraph "物理Linuxサーバー (Ubuntu 22.04 LTS)"
        subgraph "検証環境 (物理直接実行)"
            PFE[フロントエンド :3005]
            PBE[バックエンド :8005]
            PDB[(PostgreSQL :5405)]
            PRC[(Redis :6405)]
        end
        
        subgraph "仮想化レイヤー (VMware/VirtualBox)"
            subgraph "開発VM環境 (既存維持)"
                DFE[フロントエンド :3000]
                DBE[バックエンド :8001]
                DSQ[(SQLite)]
            end
        end
        
        subgraph "管理・監視システム"
            MON[統合監視]
            LOG[ログ統合]
            DEP[デプロイ自動化]
        end
    end
    
    PFE -.-> PBE
    PBE -.-> PDB
    PBE -.-> PRC
    DFE -.-> DBE
    DBE -.-> DSQ
    
    MON --> PFE
    MON --> PBE
    MON --> DFE
    MON --> DBE
    
    LOG --> PFE
    LOG --> PBE
    LOG --> DFE
    LOG --> DBE
    
    DEP --> PFE
    DEP --> PBE
```

## 🏛️ システムアーキテクチャ詳細

### 1. 環境分離設計

#### 検証環境（物理サーバー直接実行）
```yaml
環境名: staging-environment
実行方式: Docker Compose + Native Process
リソース配分:
  - CPU: 4コア
  - RAM: 8GB
  - Disk: 100GB (SSD)
ポート構成:
  - Frontend: 3005 (Next.js Production)
  - Backend: 8005 (FastAPI + Uvicorn)
  - PostgreSQL: 5405
  - Redis: 6405
  - Monitoring: 9090 (Prometheus)
```

#### 開発環境（VM内継続）
```yaml
環境名: development-environment  
実行方式: VM Guest OS (既存維持)
リソース配分:
  - CPU: 4コア (VM割り当て)
  - RAM: 8GB (VM割り当て)
  - Disk: 50GB (VM仮想ディスク)
ポート構成:
  - Frontend: 3000 (Next.js Development)
  - Backend: 8001 (FastAPI + Uvicorn)
  - Database: SQLite (test.db)
```

### 2. ネットワーク設計

#### ポート分離マトリックス
| サービス | 検証環境 | 開発環境 | プロトコル | 用途 |
|---------|---------|---------|----------|------|
| Frontend | 3005 | 3000 | HTTP | Web UI |
| Backend API | 8005 | 8001 | HTTP/REST | API Server |
| PostgreSQL | 5405 | - | TCP | Database |
| Redis | 6405 | - | TCP | Cache/Queue |
| Prometheus | 9090 | - | HTTP | Monitoring |
| Grafana | 3001 | - | HTTP | Dashboard |

#### ファイアウォール設計
```bash
# 検証環境アクセス制御
iptables -A INPUT -p tcp --dport 3005 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3005 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8005 -s 127.0.0.1 -j ACCEPT

# VM環境からの検証環境アクセス許可
iptables -A INPUT -p tcp --dport 8005 -s [VM_IP] -j ACCEPT

# 外部からの直接アクセス遮断（開発環境）
iptables -A INPUT -p tcp --dport 3000 -j DROP
iptables -A INPUT -p tcp --dport 8001 -j DROP
```

### 3. データ管理設計

#### データベース分離戦略
```yaml
検証環境データ:
  - Type: PostgreSQL 15
  - Storage: /var/lib/postgresql/staging
  - Backup: Daily @ 02:00 UTC
  - Retention: 7 days local, 30 days remote
  
開発環境データ:
  - Type: SQLite 3
  - Storage: VM内 /home/user/project/test.db
  - Backup: VM snapshot (VMware)
  - Retention: VM管理システムに依存
```

#### ファイルシステム設計
```
物理サーバー構成:
/opt/staging/
├── apps/
│   ├── frontend/          # 検証環境 Next.js
│   └── backend/           # 検証環境 FastAPI
├── data/
│   ├── postgresql/        # DB永続化
│   ├── redis/            # Cache永続化
│   └── logs/             # アプリログ
├── config/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── .env.staging
└── scripts/
    ├── deploy.sh
    ├── backup.sh
    └── monitoring.sh

VM環境構成（既存維持）:
/home/user/project/
├── frontend/             # 開発環境 Next.js
├── backend/             # 開発環境 FastAPI
├── test.db              # SQLite DB
└── .env                 # 開発環境設定
```

## 🔧 技術実装設計

### 1. Docker Compose設計（検証環境）

```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  postgres-staging:
    image: postgres:15-alpine
    container_name: postgres-staging
    ports:
      - "5405:5432"
    environment:
      POSTGRES_DB: staging_db
      POSTGRES_USER: staging_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - /opt/staging/data/postgresql:/var/lib/postgresql/data
    networks:
      - staging-network
      
  redis-staging:
    image: redis:7-alpine
    container_name: redis-staging
    ports:
      - "6405:6379"
    volumes:
      - /opt/staging/data/redis:/data
    networks:
      - staging-network
      
  backend-staging:
    build: ./backend
    container_name: backend-staging
    ports:
      - "8005:8000"
    environment:
      DATABASE_URL: postgresql://staging_user:${POSTGRES_PASSWORD}@postgres-staging:5432/staging_db
      REDIS_URL: redis://redis-staging:6379
    depends_on:
      - postgres-staging
      - redis-staging
    networks:
      - staging-network
      
networks:
  staging-network:
    driver: bridge
```

### 2. Nginx リバースプロキシ設計

```nginx
# /etc/nginx/sites-available/staging
server {
    listen 80;
    server_name staging.local;
    
    # フロントエンド（Next.js）
    location / {
        proxy_pass http://127.0.0.1:3005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # バックエンドAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8005/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. プロセス管理設計

#### systemd サービス定義
```ini
# /etc/systemd/system/staging-environment.service
[Unit]
Description=Staging Environment Services
Requires=docker.service
After=docker.service

[Service]
Type=forking
User=staging
Group=staging
WorkingDirectory=/opt/staging
ExecStart=/usr/local/bin/docker-compose -f docker-compose.staging.yml up -d
ExecReload=/usr/local/bin/docker-compose -f docker-compose.staging.yml restart
ExecStop=/usr/local/bin/docker-compose -f docker-compose.staging.yml down
TimeoutStartSec=0
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## 📊 監視・管理システム設計

### 1. Prometheus監視設定

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'staging-backend'
    static_configs:
      - targets: ['localhost:8005']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'staging-postgres'
    static_configs:
      - targets: ['postgres-staging:5432']
    scrape_interval: 60s
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s
```

### 2. ログ管理設計

```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  fluentd:
    image: fluent/fluentd:v1.14-debian-1
    container_name: fluentd-staging
    ports:
      - "24224:24224"
    volumes:
      - /opt/staging/config/fluentd.conf:/fluentd/etc/fluent.conf
      - /opt/staging/data/logs:/var/log/fluentd
    networks:
      - staging-network
      
  elasticsearch:
    image: elasticsearch:8.8.0
    container_name: elasticsearch-staging
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - /opt/staging/data/elasticsearch:/usr/share/elasticsearch/data
    networks:
      - staging-network
```

## 🚀 デプロイメント自動化設計

### 1. CI/CD パイプライン設計

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [ develop ]
    
jobs:
  deploy-staging:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Backend
        run: |
          cd backend
          docker build -t staging-backend:latest .
          
      - name: Build Frontend
        run: |
          cd frontend
          npm run build
          npm run export
          
      - name: Deploy to Staging
        run: |
          sudo systemctl stop staging-environment
          cp -r frontend/out /opt/staging/apps/frontend/
          docker tag staging-backend:latest staging-backend:$(git rev-parse --short HEAD)
          sudo systemctl start staging-environment
          
      - name: Health Check
        run: |
          sleep 30
          curl -f http://localhost:8005/health || exit 1
          curl -f http://localhost:3005 || exit 1
```

### 2. バックアップ自動化設計

```bash
#!/bin/bash
# /opt/staging/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/staging/backups"

# PostgreSQL バックアップ
docker exec postgres-staging pg_dump -U staging_user staging_db > \
  "$BACKUP_DIR/postgres_staging_$DATE.sql"

# Redis バックアップ  
docker exec redis-staging redis-cli BGSAVE
docker cp redis-staging:/data/dump.rdb \
  "$BACKUP_DIR/redis_staging_$DATE.rdb"

# アプリケーションファイルバックアップ
tar -czf "$BACKUP_DIR/apps_staging_$DATE.tar.gz" \
  /opt/staging/apps/

# 7日経過したバックアップを削除
find "$BACKUP_DIR" -name "*_staging_*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*_staging_*.rdb" -mtime +7 -delete
find "$BACKUP_DIR" -name "*_staging_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

## 🔐 セキュリティ設計

### 1. アクセス制御マトリックス

| アクセス元 | 検証環境 | 開発環境 | 管理ツール | 備考 |
|----------|---------|---------|-----------|------|
| 開発者PC | HTTP:3005 | VM経由 | SSH | VPN必須 |
| 開発VM | API:8005 | 直接 | 制限 | 内部通信のみ |
| CI/CD | 全て | 制限 | 全て | 自動化専用 |
| 外部 | 遮断 | 遮断 | 遮断 | ファイアウォール |

### 2. 認証・認可設計

```yaml
# 検証環境認証設定
Authentication:
  Type: JWT + OAuth 2.0
  Provider: Google Workspace
  Session: 24時間
  Refresh: 30日間
  
Authorization:
  Roles:
    - admin: 全権限
    - developer: 読み取り専用
    - viewer: 画面表示のみ
    
API Security:
  Rate Limiting: 100 req/min per IP
  CORS: staging.local のみ許可
  HTTPS: Let's Encrypt (本番時)
```

## 📈 性能・容量設計

### 1. システム要件
```yaml
最小システム要件:
  CPU: 8コア (物理)
  RAM: 16GB (検証8GB + VM8GB)
  Disk: 200GB SSD
  Network: 1Gbps

推奨システム要件:
  CPU: 12コア (物理)
  RAM: 32GB (検証16GB + VM16GB)
  Disk: 500GB NVMe SSD
  Network: 1Gbps + 予備回線
```

### 2. スケーリング戦略
```yaml
Horizontal Scaling:
  検証環境: Docker Swarm / Kubernetes移行準備
  開発環境: VM複製による複数開発者対応
  
Vertical Scaling:  
  CPU: 最大16コア対応
  RAM: 最大64GB対応
  Disk: NVMe SSD RAID構成
```

## 🔄 運用・保守設計

### 1. 監視アラート設定

```yaml
Critical Alerts:
  - サービス停止 (>30秒)
  - CPU使用率 (>90% for 5分)
  - メモリ使用率 (>95% for 2分)
  - ディスク使用率 (>90%)
  
Warning Alerts:
  - API応答時間 (>500ms)
  - CPU使用率 (>70% for 10分)
  - メモリ使用率 (>80% for 5分)
  - ディスク使用率 (>70%)
```

### 2. 定期メンテナンス計画

```yaml
Daily (自動):
  - システムログローテーション
  - データベースバックアップ
  - ヘルスチェック実行
  
Weekly (自動):
  - セキュリティアップデート確認
  - パフォーマンス分析レポート
  - 古いバックアップファイル削除
  
Monthly (手動):
  - 容量プランニング見直し
  - セキュリティ監査実施
  - ドキュメント更新
```

## 🎯 移行実装計画

### Phase 1: インフラ準備 (3日)
1. **物理サーバー環境構築**
   - Ubuntu 22.04 LTS インストール
   - Docker & Docker Compose インストール
   - 基本セキュリティ設定

2. **ネットワーク設定**
   - ファイアウォール設定
   - ポート分離設定
   - VM-物理サーバー通信確認

### Phase 2: 検証環境構築 (5日)
1. **Docker環境構築**
   - PostgreSQL/Redis コンテナ設定
   - アプリケーション用Dockerfile作成
   - docker-compose.staging.yml 設定

2. **アプリケーションデプロイ**
   - バックエンドAPI配置・設定
   - フロントエンドビルド・配置
   - 動作確認・テスト実行

### Phase 3: 監視・自動化 (4日)
1. **監視システム構築**
   - Prometheus/Grafana設定
   - ログ収集システム構築
   - アラート設定・テスト

2. **自動化スクリプト作成**
   - デプロイスクリプト作成
   - バックアップスクリプト作成
   - 運用スクリプト作成

### Phase 4: テスト・調整 (3日)
1. **統合テスト実行**
   - 機能テスト実行
   - パフォーマンステスト実行
   - セキュリティテスト実行

2. **最適化・調整**
   - パフォーマンスチューニング
   - 設定値調整・最適化
   - ドキュメント整備

---

## 📝 設計承認事項

**設計完了条件**:
- 100回仮想会議レビューによる品質確認
- アーキテクチャ・技術選定の妥当性確認
- 実装計画の実現可能性確認

**承認者**:
- システムアーキテクト
- インフラエンジニア
- プロジェクトマネージャー

---
**作成日**: 2025-09-05  
**承認予定**: 設計レビュー完了後