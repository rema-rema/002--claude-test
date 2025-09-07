# VPN/DNS Access System 設計書

## 1. アーキテクチャ概要

### 1.1 システム構成図
```
[VPN Client PC]
    ↓ (Tailscale VPN: 100.83.213.121)
[Tailscale Network]
    ↓ (MagicDNS + カスタムDNS)
[Ubuntu Server: 100.115.216.73]
    ├─ [dnsmasq:53] → DNS解決 (home.poco → 100.115.216.73)
    ├─ [nginx:80] → リバースプロキシ
    └─ [Python HTTPServer:3000] → Webサービス（仮）
```

### 1.2 ネットワーク構成
- **ローカルネットワーク**: 192.168.1.0/24
  - サーバー: 192.168.1.13
- **Tailscale VPN**: 100.x.x.x/32
  - サーバー: 100.115.216.73
  - クライアント: 動的割り当て（100.83.213.121等）
- **カスタムドメイン**: home.poco

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

### 2.2 Webプロキシ層（nginx）

#### 設定内容
```nginx
# /etc/nginx/sites-available/home
server {
    listen 0.0.0.0:80;
    server_name home.poco *.poco;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 役割
- HTTPリクエストの受付（ポート80）
- バックエンドサービスへのプロキシ
- ヘッダー情報の付加

### 2.3 アプリケーション層

#### 現在の実装
- Python SimpleHTTPServer（ポート3000）
- ディレクトリ一覧表示（テスト用）

#### 将来の拡張
- 実際のWebアプリケーション
- ログイン機能付きダッシュボード
- マルチサービス対応

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

---
## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|------|------------|----------|--------|
| 2025-09-04 | 1.0 | 初版作成（実装済み内容の文書化） | System |
| 2025-09-07 | 1.1 | NetworkManager統合と両IP対応設計追加 | System |