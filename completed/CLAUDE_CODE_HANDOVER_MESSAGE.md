# Claude Code 作業引き継ぎ指示

## 🎯 引き継ぎ概要
**AdGuard Home + Nginx によるhome.comアクセス環境構築**の作業を引き継ぎます。
現在Step 7（ローカルテスト段階）まで完了済みです。

## 📋 現在の状況
- **作業ディレクトリ**: `/home/rema/project/002--claude-test`
- **詳細手順書**: `ADGUARD_HOME_SETUP.md`（完全な進捗記録付き）
- **進捗**: Step 7/8 完了（85%完了）

## ✅ 完了済み項目
1. AdGuard Home インストール・起動（ポート53, 3000）
2. home.com → 192.168.1.13 DNS設定
3. Nginx インストール・設定（ポート80リバースプロキシ）
4. 全設定ファイル配置完了

## 🔄 **あなたが実行すべき残りタスク**

### **次に実行すべきコマンド（順番通りに）**
```bash
# 作業ディレクトリに移動
cd /home/rema/project/002--claude-test

# 1. /etc/hostsにテスト用エントリ追加
echo "127.0.0.1 home.com" | sudo tee -a /etc/hosts

# 2. home.comでのアクセステスト
curl -I http://home.com

# 3. DNSテスト（AdGuard Home経由）
nslookup home.com 127.0.0.1

# 4. 動作確認
ss -tln | grep -E ':53|:80|:3000'
ps aux | grep -E "AdGuardHome|nginx" | grep -v grep
```

### **最終目標達成まで**
- ローカルテスト完了
- ルーターDNS設定指示（DHCP: 192.168.1.13）
- 全体動作確認
- 手順書を`completed/`フォルダに移動

## 📁 **重要ファイル**
- `ADGUARD_HOME_SETUP.md` - 完全な手順書（**必ず最初に読んで**）
- `adguard_config.yaml` - AdGuard Home設定
- `nginx_home_config` - Nginx設定
- `install_adguard.sh` - インストールスクリプト

## 🎯 **最終目標**
**http://home.com** で家族全員がポート番号なしでログイン画面にアクセス可能にする

## ⚠️ **注意点**
- 手順書の進捗状況を随時更新すること
- 問題発生時は手順書内の「復旧方法」参照
- 完了時は手順書をアーカイブすること

---

**指示**: 上記の「次に実行すべきコマンド」から開始し、最終目標まで完了させてください。詳細は`ADGUARD_HOME_SETUP.md`を参照してください。