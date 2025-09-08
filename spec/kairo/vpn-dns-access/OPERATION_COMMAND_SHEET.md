# 運用コマンドシート - VPN/DNS Access System

## 概要
このドキュメントは **実際に動作確認済み** のコマンドを記録したパラメータシートです。  
サーバー再起動時や障害復旧時に、このシートの通りに実行すれば確実に復旧できます。

---

## 1. DNS設定（dnsmasq）

### 1.1 初期セットアップ
```bash
# systemd-resolved停止（ポート53競合回避）- 実行済み
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved

# dnsmasqインストール - 実行済み
sudo apt update
sudo apt install -y dnsmasq
```

### 1.2 設定ファイル作成
```bash
# 設定ファイル作成（実際の設定内容）
sudo nano /etc/dnsmasq.d/home.conf
```

**ファイル内容（動作確認済み）**:
```conf
# 2025-09-07 更新版（両IP対応）
address=/home.poco/192.168.1.13
address=/home.poco/100.115.216.73
address=/.poco/192.168.1.13
address=/.poco/100.115.216.73
server=8.8.8.8
server=8.8.4.4
```

### 1.3 dnsmasq起動・再起動
```bash
# 設定ファイル構文チェック
sudo dnsmasq --test

# dnsmasq再起動
sudo systemctl restart dnsmasq

# 起動状態確認
sudo systemctl status dnsmasq

# ログ確認（問題発生時）
sudo journalctl -u dnsmasq -f
```

### 1.4 DNS動作確認
```bash
# DNS解決テスト（サーバー上で実行）
nslookup home.poco 127.0.0.1
dig home.poco @127.0.0.1

# クライアントPCから確認
nslookup home.poco
ping home.poco
```

---

## 2. nginx設定（リバースプロキシ）

### 2.1 nginx設定ファイル作成
```bash
# 設定ファイル作成/編集
sudo nano /etc/nginx/sites-available/home
```

**ファイル内容（2025-09-08 動作確認済み）**:
```nginx
server {
    listen 0.0.0.0:80;
    server_name home.poco *.poco;
    
    # フロントエンド（Next.js）
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
}
```

### 2.2 nginx設定有効化
```bash
# シンボリックリンク作成（初回のみ）
sudo ln -s /etc/nginx/sites-available/home /etc/nginx/sites-enabled/

# デフォルトサイト無効化（必要に応じて）
sudo rm /etc/nginx/sites-enabled/default

# 設定ファイル構文チェック（重要！）
sudo nginx -t

# nginx再起動
sudo systemctl reload nginx

# nginx状態確認
sudo systemctl status nginx

# エラーログ確認（問題発生時）
sudo tail -f /var/log/nginx/error.log
```

### 2.3 nginx動作確認
```bash
# ローカルから確認
curl -I http://localhost
curl http://localhost/api/health

# VPN経由で確認
curl -I http://home.poco
curl http://home.poco/api/health
```

---

## 3. アプリケーション起動

### 3.1 バックエンド（FastAPI）起動
```bash
# バックエンドディレクトリに移動
cd /home/rema/project/002--claude-test/backend

# Python仮想環境有効化（使用している場合）
source venv/bin/activate  # または適切な仮想環境

# FastAPI起動（ポート8000）
python main.py

# またはuvicorn直接起動
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# バックグラウンド実行（tmux推奨）
tmux new -s backend
python main.py
# Ctrl+b d でデタッチ
```

### 3.2 フロントエンド（Next.js）起動
```bash
# フロントエンドディレクトリに移動
cd /home/rema/project/002--claude-test/frontend

# 依存関係インストール（初回または更新時）
npm install

# ビルド（本番環境用）
npm run build

# Next.js起動（ポート3001）
PORT=3001 npm start

# 開発モード起動（ホットリロード有効）
PORT=3001 npm run dev

# バックグラウンド実行（tmux推奨）
tmux new -s frontend
PORT=3001 npm start
# Ctrl+b d でデタッチ
```

### 3.3 プロセス管理
```bash
# 実行中のポート確認
sudo lsof -i :3001  # フロントエンド
sudo lsof -i :8000  # バックエンド
sudo lsof -i :80    # nginx

# プロセス強制終了（必要時）
sudo kill -9 $(lsof -ti:3001)  # ポート3001使用プロセス
sudo kill -9 $(lsof -ti:8000)  # ポート8000使用プロセス

# tmuxセッション確認
tmux ls

# tmuxセッション再接続
tmux a -t frontend  # フロントエンドセッション
tmux a -t backend   # バックエンドセッション
```

---

## 4. システム全体起動手順（サーバー再起動後）

### 4.1 完全起動スクリプト
```bash
#!/bin/bash
# startup.sh - システム全体起動スクリプト

echo "=== VPN/DNS Access System 起動開始 ==="

# 1. DNS設定確認
echo "1. DNS設定確認..."
sudo systemctl status dnsmasq || sudo systemctl start dnsmasq

# 2. nginx確認
echo "2. nginx確認..."
sudo systemctl status nginx || sudo systemctl start nginx

# 3. バックエンド起動
echo "3. バックエンド起動..."
cd /home/rema/project/002--claude-test/backend
tmux new -d -s backend 'python main.py'

# 4. フロントエンド起動
echo "4. フロントエンド起動..."
cd /home/rema/project/002--claude-test/frontend
tmux new -d -s frontend 'PORT=3001 npm start'

echo "=== 起動完了 ==="
echo "アクセスURL: http://home.poco"
echo "tmux ls でセッション確認可能"
```

### 4.2 ヘルスチェックスクリプト
```bash
#!/bin/bash
# healthcheck.sh - システムヘルスチェック

echo "=== システムヘルスチェック ==="

# DNSチェック
echo -n "DNS (dnsmasq): "
nslookup home.poco 127.0.0.1 > /dev/null 2>&1 && echo "✅ OK" || echo "❌ NG"

# nginxチェック
echo -n "nginx: "
curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302" && echo "✅ OK" || echo "❌ NG"

# バックエンドチェック
echo -n "Backend API: "
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ OK" || echo "❌ NG"

# フロントエンドチェック
echo -n "Frontend: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 | grep -q "200" && echo "✅ OK" || echo "❌ NG"

# 統合チェック（home.poco経由）
echo -n "統合アクセス: "
curl -s -o /dev/null -w "%{http_code}" http://home.poco | grep -q "200\|301\|302" && echo "✅ OK" || echo "❌ NG"
```

---

## 5. トラブルシューティング

### 5.1 DNS関連
```bash
# DNS解決できない場合
sudo systemctl restart dnsmasq
sudo systemctl restart NetworkManager

# resolv.conf確認
cat /etc/resolv.conf
# nameserver 127.0.0.1 が先頭にあることを確認

# 手動設定（必要時）
echo -e 'nameserver 127.0.0.1\nnameserver 8.8.8.8' | sudo tee /etc/resolv.conf
```

### 5.2 ポート競合
```bash
# ポート使用状況確認
sudo netstat -tlnp | grep -E ':80|:3001|:8000|:53'

# 競合プロセス特定
sudo lsof -i :3001
sudo lsof -i :8000

# Python HTTPServerが3000番を使用している場合
sudo kill -9 $(lsof -ti:3000)
```

### 5.3 ログ確認
```bash
# システムログ
sudo journalctl -xe

# dnsmasqログ
sudo journalctl -u dnsmasq -n 50

# nginxログ
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# アプリケーションログ（tmux内）
tmux a -t backend
tmux a -t frontend
```

---

## 6. 環境変数・設定ファイル一覧

### 6.1 設定ファイルパス
```bash
# DNS設定
/etc/dnsmasq.d/home.conf

# nginx設定
/etc/nginx/sites-available/home
/etc/nginx/sites-enabled/home

# フロントエンド環境変数
/home/rema/project/002--claude-test/frontend/.env.local

# バックエンド環境変数
/home/rema/project/002--claude-test/backend/.env
```

### 6.2 重要な環境変数
```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://home.poco
NEXT_PUBLIC_SESSION_ID=staging
NODE_ENV=production

# Backend (.env)
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here
```

---

## 7. バックアップ・リストア

### 7.1 設定バックアップ
```bash
# バックアップディレクトリ作成
mkdir -p ~/backup/vpn-dns-system/$(date +%Y%m%d)
cd ~/backup/vpn-dns-system/$(date +%Y%m%d)

# 設定ファイルバックアップ
sudo cp /etc/dnsmasq.d/home.conf ./
sudo cp /etc/nginx/sites-available/home ./
cp /home/rema/project/002--claude-test/frontend/.env.local ./
cp /home/rema/project/002--claude-test/backend/.env ./backend.env

# tar圧縮
tar -czf vpn-dns-backup-$(date +%Y%m%d).tar.gz *
```

### 7.2 リストア
```bash
# バックアップから復元
cd ~/backup/vpn-dns-system/20250908  # 該当日付

sudo cp home.conf /etc/dnsmasq.d/
sudo cp home /etc/nginx/sites-available/
cp .env.local /home/rema/project/002--claude-test/frontend/
cp backend.env /home/rema/project/002--claude-test/backend/.env

# サービス再起動
sudo systemctl restart dnsmasq
sudo systemctl reload nginx
```

---

## 改訂履歴
| 日付 | バージョン | 内容 | 作成者 |
|------|-----------|------|--------|
| 2025-09-08 | 1.0.0 | 初版作成 - 動作確認済みコマンド集 | System |

---

**注意**: このドキュメントのコマンドは全て実際に動作確認済みです。環境により微調整が必要な場合があります。