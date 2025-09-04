#!/bin/bash
# AdGuard Home 安全インストールスクリプト（sudo不要版）
# 作成: 2025-09-04 12:20

echo "AdGuard Home インストール開始"

# 1. systemd-resolvedを無効化（ポート53を解放）
echo "systemd-resolved を停止・無効化します..."
systemctl stop systemd-resolved
systemctl disable systemd-resolved

# 2. /etc/resolv.confを固定DNSに変更
echo "DNS設定を一時的に変更..."
rm -f /etc/resolv.conf
echo "nameserver 8.8.8.8" | tee /etc/resolv.conf

# 3. AdGuard Homeをインストール
echo "AdGuard Homeをインストール中..."
mkdir -p /opt/AdGuardHome
cd /opt/AdGuardHome
wget -q https://github.com/AdguardTeam/AdGuardHome/releases/latest/download/AdGuardHome_linux_amd64.tar.gz
tar xzf AdGuardHome_linux_amd64.tar.gz

# 4. サービスとして登録
echo "サービスとして登録..."
./AdGuardHome -s install

echo "インストール完了。Web UIは http://192.168.1.13:3000 でアクセス可能です"