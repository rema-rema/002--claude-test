# VPN/DNS Access System 設計書

## 1. アーキテクチャ概要

### 1.1 システム構成図（2025-09-08更新: モバイル対応アーキテクチャ）
```
[VPN Client PC/Mobile]
    ↓ (Tailscale VPN: 100.x.x.x)
[Tailscale Network]
    ↓ (MagicDNS + カスタムDNS)
[Ubuntu Server: 100.115.216.73]
    ├─ [dnsmasq:53] → DNS解決 (home.poco → 100.115.216.73)
    ├─ [nginx:80] → リバースプロキシ
    │   ├─ location / → Frontend (Next.js:3001)
    │   └─ location /api/ → Backend API (FastAPI:8000)
    ├─ [Next.js:3001] → フロントエンド（ログイン・ダッシュボード）
    └─ [FastAPI:8000] → バックエンドAPI（認証・データ処理）
```

### 1.2 ネットワーク構成（モバイル対応拡張）
- **ローカルネットワーク**: 192.168.1.0/24
  - サーバー: 192.168.1.13
- **Tailscale VPN**: 100.x.x.x/32
  - サーバー: 100.115.216.73
  - デスクトップPC: 動的割り当て（100.83.213.121等）
  - **モバイル端末**: 動的割り当て（Tailscale VPN経由でアクセス可能）
- **カスタムドメイン**: home.poco（全デバイス統一アクセス）

### 1.3 アプリケーション層構成
- **フロントエンド**: Next.js (Port 3001)
  - ログインページ (`/login`)
  - ダッシュボードページ (`/dashboard`)
  - APIクライアント（相対パス `/api/` でバックエンド連携）
- **バックエンド**: FastAPI (Port 8000)
  - 認証API (`/api/auth/mock-login`, `/api/auth/mock-logout`, `/api/auth/mock-me`)
  - ヘルスチェック (`/health`)
  - HTTPOnly Cookie によるセッション管理

## 2. コンポーネント設計

### 2.1 DNS解決層（dnsmasq）

#### 設定内容
```conf
# /etc/dnsmasq.d/home.conf
# 2025-09-07 更新: 両IP対応
address=/home.poco/192.168.1.13
address=/home.poco/100.115.216.73
address=/.poco/192.168.1.13
address=/.poco/100.115.216.73
server=8.8.8.8
server=8.8.4.4
```

#### 役割
- カスタムドメイン（.poco）の解決（VPN/ローカル両対応）
- 外部DNSへのフォワーディング
- キャッシュ管理
- 両IP登録によるVPN/ローカル環境での統一アクセス

### 2.2 Webプロキシ層（nginx）- 2025-09-08更新

#### 設定内容（モバイル対応リバースプロキシ）
```nginx
# /etc/nginx/sites-available/home - モバイル対応設定
server {
    listen 0.0.0.0:80;
    server_name home.poco *.poco;
    
    # フロントエンド（Next.js）へのプロキシ
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # バックエンドAPI（FastAPI）へのプロキシ
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

#### 役割（モバイル対応拡張）
- HTTPリクエストの受付（ポート80、全IP対応）
- **フロントエンド・バックエンドの分離プロキシ**
  - `/` → Next.js (3001) フロントエンド
  - `/api/` → FastAPI (8000) バックエンドAPI
- モバイル端末からの相対パスAPI呼び出し対応
- ヘッダー情報の付加・転送

### 2.3 アプリケーション層（2025-09-08実装完了）

#### フロントエンド実装（Next.js - Port 3001）
- **ログインページ** (`/login`)
  - Google OAuth風 UI デザイン
  - Mock認証システム連携
  - 認証状態チェック・自動リダイレクト
  - モバイル対応レスポンシブデザイン
- **ダッシュボードページ** (`/dashboard`) 
  - ユーザー情報表示
  - システム状態表示
  - 認証済みユーザーのみアクセス可能
- **API クライアント設計**
  - 相対パス (`/api/`) でバックエンド呼び出し
  - **重要**: `localhost:8000` hardcode を完全除去
  - モバイル端末でのlocalhost問題を解決

#### バックエンド実装（FastAPI - Port 8000）
- **認証API エンドポイント**
  - `POST /api/auth/mock-login` - ログイン処理
  - `POST /api/auth/mock-logout` - ログアウト処理  
  - `GET /api/auth/mock-me` - 認証状態確認
- **セッション管理**
  - HTTPOnly Cookie による安全なセッション管理
  - JWT トークンベース認証
- **ヘルスチェック** (`GET /health`)

#### 環境設定（モバイル対応）
- **`.env.local`**: `NEXT_PUBLIC_API_URL=http://home.poco`
- 全デバイス共通ドメインでの統一アクセス実現

## 3. データフロー設計

### 3.1 DNS解決フロー
```
1. VPN PC: http://home.poco アクセス
2. Tailscale DNS: home.poco解決要求
3. dnsmasq: home.poco → 100.115.216.73 返却
4. VPN PC: 100.115.216.73:80 にHTTP接続
```

### 3.2 HTTPリクエストフロー
```
1. VPN PC → 100.115.216.73:80 (HTTP GET)
2. nginx: リクエスト受信
3. nginx → localhost:3000 プロキシ
4. Python HTTPServer: レスポンス生成
5. nginx → VPN PC: レスポンス返却
```

## 4. セキュリティ設計

### 4.1 アクセス制御
- VPNネットワーク内のみアクセス可能
- ファイアウォール設定は現状なし（将来検討）

### 4.2 認証・認可
- 現在: 認証なし
- 将来: Basic認証 or OAuth2実装予定

## 5. エラーハンドリング設計

### 5.1 DNS障害時
- プライマリ: dnsmasq (127.0.0.1)
- セカンダリ: Google DNS (8.8.8.8)
- フォールバック自動切り替え

### 5.2 サービス障害時
- nginx: 502 Bad Gateway返却
- 自動復旧: systemdによる自動再起動

## 6. 運用設計

### 6.1 起動順序
```bash
1. systemd-resolved 停止（ポート53競合回避）
2. dnsmasq 起動
3. nginx 起動
4. アプリケーションサービス起動
```

### 6.2 設定変更手順
```bash
# DNS設定変更
sudo nano /etc/dnsmasq.d/home.conf
sudo systemctl restart dnsmasq

# nginx設定変更
sudo nano /etc/nginx/sites-available/home
sudo nginx -t
sudo systemctl reload nginx

# NetworkManager DNS管理無効化（2025-09-07追加）
sudo nano /etc/NetworkManager/NetworkManager.conf
# [main]セクションに dns=none を追加
sudo systemctl restart NetworkManager

# resolv.conf設定（永続化対応）
echo -e 'nameserver 127.0.0.1\nnameserver 8.8.8.8' | sudo tee /etc/resolv.conf
```

### 6.3 ログ管理
- dnsmasq: `/var/log/syslog`
- nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- アプリケーション: 標準出力

## 7. 拡張性設計

### 7.1 マルチドメイン対応
```nginx
server_name home.poco app.poco service.poco;
```

### 7.2 マルチサービス対応
```nginx
location /app1 { proxy_pass http://localhost:3001; }
location /app2 { proxy_pass http://localhost:3002; }
```

### 7.3 HTTPS対応（将来）
- Let's Encrypt証明書
- nginx SSL設定追加

## 8. 制約事項
- Claude Code API接続維持のため、システムDNSは慎重に変更
- Tailscale VPNの設定は変更不可
- ポート80, 53の競合に注意

## 9. 承認
- 作成日: 2025-09-04
- 作成者: System
- ステータス: 実装済み内容の文書化

## 10. 🚨 重要修正記録: モバイルネットワークエラー解決（2025-09-08）

### 10.1 発生した問題
**問題**: VPN経由でモバイル端末から `http://home.poco` でログインボタンを押すとネットワークエラー
```
エラーメッセージ: "ネットワークエラーが発生しました。接続を確認してください。"
```

### 10.2 原因分析（小学生でもわかる説明）

#### 🎯 根本原因: 「localhost問題」
**簡単に言うと**: 
- コンピューター用語で「localhost」= 「自分自身」という意味
- PC から見た「localhost」= PC自身
- スマホから見た「localhost」= スマホ自身  
- **問題**: スマホが「localhost:8000」にアクセス → スマホ自身を探す → サーバーが見つからない

#### 🔍 具体的な技術原因
1. **フロントエンドJavaScript内にhardcoded URL問題**
   ```javascript
   // 問題のあったコード（login/page.tsx, dashboard/page.tsx）
   const apiUrl = `http://${currentHost}:8000`;
   fetch(`${apiUrl}/api/auth/mock-me`, ...); // ❌ モバイルでlocalhost:8000になる
   ```

2. **環境変数の設定不備**
   ```bash
   # 問題のあった設定
   NEXT_PUBLIC_API_URL=http://localhost:8000 # ❌ モバイルでアクセス不可
   ```

### 10.3 解決手順と修正内容

#### ステップ1: 環境変数修正
```bash
# Before: localhost指定（モバイルアクセス不可）
NEXT_PUBLIC_API_URL=http://localhost:8000

# After: home.pocoドメイン統一（全デバイスアクセス可能）
NEXT_PUBLIC_API_URL=http://home.poco
```

#### ステップ2: JavaScript コード修正
**修正ファイル**: `src/app/login/page.tsx`
```javascript
// Before: hardcoded URL（モバイルでlocalhost:8000 = エラー）
const response = await fetch(`http://${currentHost}:8000/api/auth/mock-me`, {

// After: 相対パス（nginxが正しく8000にプロキシ）
const response = await fetch(`/api/auth/mock-me`, {
```

**修正ファイル**: `src/app/dashboard/page.tsx`  
```javascript
// Before: hardcoded URL
const response = await fetch(`http://${currentHost}:8000/api/auth/mock-me`, {
await fetch(`http://${currentHost}:8000/api/auth/mock-logout`, {

// After: 相対パス  
const response = await fetch(`/api/auth/mock-me`, {
await fetch(`/api/auth/mock-logout`, {
```

#### ステップ3: フロントエンド再構築
```bash
cd frontend
rm -rf .next          # キャッシュ削除
npm run build         # 修正内容で再ビルド  
PORT=3001 npm start   # 再起動
```

### 10.4 修正の仕組み（小学生でもわかる図解）

#### 修正前（エラーが起きる仕組み）
```
[モバイル端末] 
    ↓ JavaScriptが「localhost:8000」にアクセス試行
[モバイル端末自身] ← localhost = 自分自身を探す
    ↓ サーバーが見つからない
[❌ ネットワークエラー]
```

#### 修正後（正常に動く仕組み）
```
[モバイル端末]
    ↓ JavaScriptが「/api/auth/mock-me」にアクセス
[home.poco (nginx)] ← 相対パスはcurrent domainに送られる  
    ↓ nginxが /api/ を localhost:8000 にプロキシ
[FastAPI Server :8000]
    ↓ 正常なレスポンス
[✅ ログイン成功]
```

### 10.5 なぜこの修正で全てのデバイスで動作するのか

#### nginx リバースプロキシの仕組み
```nginx
# /etc/nginx/sites-available/home
server {
    listen 0.0.0.0:80;
    server_name home.poco *.poco;
    
    location / {          # フロントエンド
        proxy_pass http://localhost:3001;  
    }
    
    location /api/ {      # バックエンドAPI ← 重要！
        proxy_pass http://localhost:8000;  # 相対パス /api/ を 8000番ポートに転送
    }
}
```

#### すべてのデバイスで統一アクセス
- **PC**: `http://home.poco/api/auth/mock-me` → nginx → localhost:8000 
- **モバイル**: `http://home.poco/api/auth/mock-me` → nginx → localhost:8000
- **全デバイス共通**: 相対パス `/api/` → nginx が適切にプロキシ → 正常動作

### 10.6 今後の安定性について

#### ✅ 永続化済み（再起動でも壊れない）
- nginx設定ファイル保存済み
- 環境変数設定保存済み  
- JavaScriptコード修正済み

#### ⚠️ 再起動時の必要作業（サービス起動のみ）
```bash
# フロントエンド起動
cd frontend && PORT=3001 npm start

# バックエンド起動  
cd backend && python main.py
```

### 10.7 学習ポイント（開発者向け）

#### モバイル開発で避けるべき罠
1. **hardcoded localhost URL**: モバイルで必ず失敗
2. **デバイス固有設定**: 全デバイス共通設計にすべき
3. **絶対パス使用**: 相対パスでプロキシ活用すべき

#### ベストプラクティス
1. **相対パス API呼び出し**: `/api/endpoint` 形式
2. **nginx リバースプロキシ活用**: 複数サービス統一アクセス
3. **統一ドメイン設計**: 全デバイスで同じURL

---
## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|------|------------|----------|--------|
| 2025-09-04 | 1.0 | 初版作成（実装済み内容の文書化） | System |
| 2025-09-07 | 1.1 | NetworkManager統合と両IP対応設計追加 | System |
| 2025-09-08 | 2.0 | モバイル対応アーキテクチャ拡張・ネットワークエラー修正記録追加 | System |