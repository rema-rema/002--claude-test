# 🌐 VPN/DNS Access System - 設計書

## 📋 設計概要

### 設計方針
現状維持を基本とし、再起動耐性に必要な最小限の変更のみを実施。VPN専用アクセスとネットワーク安定性を両立。

### システム構成図

```
[Client Device]
     |
     | (Tailscale VPN)
     v
[Tailscale Network]
     |
     | (100.115.216.73)
     v
[Ubuntu Server]
  ├── dnsmasq (DNS Server :53)
  │     └── home.poco → 100.115.216.73
  ├── nginx (Reverse Proxy :80)
  │     └── proxy_pass → localhost:3000
  └── Python HTTP Server (systemd service :3000)
        └── /home/rema (document root)
```

## 🏛️ アーキテクチャ詳細

### 1. DNS構成設計

#### dnsmasq設定
```conf
# /etc/dnsmasq.d/home.conf
address=/home.poco/100.115.216.73
address=/.poco/100.115.216.73
server=8.8.8.8
server=8.8.4.4
```

**設計ポイント**:
- VPN IP (100.115.216.73) のみ設定
- ローカルIP (192.168.1.13) は削除可能だが現状維持
- DHCP機能は無効（ローカルネットワーク無影響）

### 2. サービス自動起動設計

#### systemdサービス構成

| サービス | 起動順序 | 依存関係 | 自動再起動 |
|---------|---------|---------|-----------|
| dnsmasq | 1 | network.target | Yes |
| nginx | 2 | network.target | Yes |
| home-poco-http | 3 | network.target | Yes |

#### Python HTTPサーバーのsystemd化
```ini
# /etc/systemd/system/home-poco-http.service
[Unit]
Description=Home.poco HTTP Server
After=network.target

[Service]
Type=simple
User=rema
WorkingDirectory=/home/rema
ExecStart=/usr/bin/python3 -m http.server 3000
Restart=always
RestartSec=10
StandardOutput=append:/var/log/home-poco-http.log
StandardError=append:/var/log/home-poco-http.log

[Install]
WantedBy=multi-user.target
```

### 3. 設定ファイル保護設計

#### /etc/resolv.conf保護
```bash
# 内容確保
nameserver 127.0.0.1
nameserver 8.8.8.8

# 書き込み保護
sudo chattr +i /etc/resolv.conf
```

**保護の理由**:
- NetworkManagerの自動書き換え防止
- systemd-resolvedの干渉防止
- 再起動時の設定維持

### 4. ネットワーク設計

#### ポート構成
| サービス | ポート | バインドアドレス | アクセス元 |
|---------|--------|----------------|-----------|
| DNS | 53/tcp,udp | 127.0.0.1 | ローカルのみ |
| HTTP | 80/tcp | 0.0.0.0 | VPN経由のみ |
| Python | 3000/tcp | 0.0.0.0 | nginx経由 |

#### ファイアウォール設定
```bash
# VPN IPからのみHTTPアクセス許可
iptables -A INPUT -p tcp --dport 80 -s 100.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j DROP
```

## 🔧 実装設計

### 1. 初期設定スクリプト

```bash
#!/bin/bash
# setup-vpn-dns.sh

# 1. HTTPサーバーのsystemd化
sudo cp home-poco-http.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable home-poco-http.service
sudo systemctl start home-poco-http.service

# 2. resolv.conf保護
sudo chattr -i /etc/resolv.conf
echo -e "nameserver 127.0.0.1\nnameserver 8.8.8.8" | sudo tee /etc/resolv.conf
sudo chattr +i /etc/resolv.conf

# 3. サービス確認
systemctl status dnsmasq nginx home-poco-http
```

### 2. 監視・ログ設計

#### ログファイル管理
```yaml
ログファイル:
  - /var/log/home-poco-http.log  # HTTPサーバーログ
  - /var/log/nginx/access.log     # nginxアクセスログ
  - /var/log/nginx/error.log      # nginxエラーログ
  - /var/log/syslog               # dnsmasqログ

ローテーション:
  - logrotate設定で自動管理
  - 7日保持、日次ローテーション
```

### 3. 障害復旧設計

#### 自動復旧メカニズム
```yaml
サービス障害時:
  - systemd Restart=always により自動再起動
  - RestartSec=10 で10秒後に再試行
  
ネットワーク障害時:
  - After=network.target でネットワーク復旧待機
  
設定ファイル破損時:
  - chattr +i により書き換え防止
  - バックアップからの手動復旧手順用意
```

## 📊 テスト設計

### 1. 単体テスト

| テスト項目 | 確認内容 | 期待結果 |
|-----------|---------|---------|
| DNS解決 | nslookup home.poco | 100.115.216.73 |
| HTTP応答 | curl -I http://home.poco | 200 OK |
| サービス起動 | systemctl status | active (running) |
| 設定保護 | lsattr /etc/resolv.conf | ----i-------- |

### 2. 統合テスト

```bash
# 再起動テスト
sudo reboot
# 再起動後
curl http://home.poco  # VPN接続で成功
systemctl status home-poco-http  # 自動起動確認
```

### 3. 負荷テスト

```bash
# Apache Bench による負荷テスト
ab -n 1000 -c 10 http://home.poco/
```

## 🚀 デプロイメント計画

### Phase 1: 準備（5分）
1. 一時ファイルから設定ファイルコピー
2. バックアップ作成

### Phase 2: 実装（5分）
1. systemdサービス登録
2. resolv.conf保護
3. サービス再起動

### Phase 3: 検証（5分）
1. 各サービス動作確認
2. VPNアクセステスト
3. 再起動テスト

## 🔐 セキュリティ考慮事項

### アクセス制御
- VPN未接続: home.pocoは解決不可
- ローカルネットワーク: アクセス不可
- ログ記録: すべてのアクセスを記録

### 設定保護
- /etc/resolv.conf: chattr +i で保護
- systemdサービス: root権限必要
- ログファイル: 適切な権限設定

## 📈 パフォーマンス設計

### リソース使用量
```yaml
CPU使用率:
  - dnsmasq: < 1%
  - nginx: < 1%
  - Python HTTP: < 5%

メモリ使用量:
  - dnsmasq: ~10MB
  - nginx: ~50MB
  - Python HTTP: ~20MB

ディスク使用量:
  - ログファイル: ~100MB/週（ローテーション込み）
```

---

## 📝 設計承認事項

**設計完了条件**:
- 現状維持ベースの最小変更設計
- 再起動耐性の技術的実現性確認
- セキュリティ・パフォーマンス要件充足

---
**作成日**: 2025-09-07  
**更新日**: 2025-09-07  
**バージョン**: 1.0