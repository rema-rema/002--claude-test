# サーバー環境移行記録

## 2025-08-31: GitHub Codespaces から Linux サーバーへ移行

### 移行の経緯
- 当初: GitHub Codespaces 環境で開発
- 現在: 独立した Linux サーバー (Ubuntu) に移行完了

### 現在の環境詳細
- **OS**: Ubuntu Linux (5.15.0-139-generic)
- **ホスト名**: ubuntu
- **作業ディレクトリ**: /home/rema/project/002--claude-test
- **ネットワーク**: 
  - ローカルIP: 192.168.1.13
  - Tailscale IP: 100.115.216.73
  - Tailnet: tailbdc514.ts.net

### 主な変更点
1. **ネットワーク制約の解消**: Codespacesのトンネル制約なし
2. **sudo権限**: 完全な管理者権限利用可能
3. **永続性**: サーバー再起動後もデータ・設定が保持
4. **VPN対応**: Tailscaleの完全な機能が利用可能

### 注意事項
- Codespacesを前提とした設定やスクリプトは見直しが必要
- ローカルサーバーのため、外部公開にはポートフォワーディングやVPNが必要