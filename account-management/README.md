# Account Management - 認証情報管理システム

## 📋 概要
このディレクトリは、002 Claude Testプロジェクトの認証情報・アカウント情報を**Git管理対象外**で安全に管理するために作成されています。

## 🚨 重要な注意事項
- **Git管理対象外**: このディレクトリ内のファイルは `.gitignore` で除外されています
- **機密情報専用**: データベース認証情報、API キー、OAuth シークレットなどを保管
- **本番運用対応**: 開発・ステージング・本番環境ごとに分離管理

## 📁 ディレクトリ構造
```
account-management/
├── README.md                    # このファイル（Git管理対象）
├── development/                 # 開発環境認証情報
│   ├── database-accounts.md
│   ├── oauth-credentials.md
│   └── api-keys.md
├── staging/                     # ステージング環境認証情報  
│   ├── database-accounts.md
│   ├── oauth-credentials.md
│   └── api-keys.md
├── production/                  # 本番環境認証情報
│   ├── database-accounts.md
│   ├── oauth-credentials.md
│   └── api-keys.md
└── templates/                   # テンプレートファイル
    ├── database-template.md
    ├── oauth-template.md
    └── api-keys-template.md
```

## 🔐 セキュリティ原則

### 1. Git除外設定
```bash
# .gitignore に以下を追加済み
account-management/development/
account-management/staging/
account-management/production/
```

### 2. ファイルアクセス権限
```bash
# 認証情報ファイルは所有者のみ読み書き可能
chmod 600 account-management/*/database-accounts.md
chmod 600 account-management/*/oauth-credentials.md
chmod 600 account-management/*/api-keys.md
```

### 3. 環境変数連携
```bash
# 認証情報ファイルから環境変数を生成
source account-management/staging/load-env.sh
```

## 🛠️ 使用方法

### 新環境セットアップ
1. 該当環境ディレクトリ作成
2. テンプレートからファイルをコピー
3. 実際の認証情報を記入
4. ファイル権限設定（600）

### 認証情報の更新
1. 該当環境の `.md` ファイルを編集
2. 必要に応じて `load-env.sh` を再実行
3. アプリケーション再起動

### バックアップ
- 定期的に暗号化バックアップを作成
- クラウドストレージとローカルストレージの両方に保存

## 📝 業界標準プラクティス

### 一般的な管理手法
1. **環境変数ファイル**: `.env` ファイル（Git除外）
2. **専用管理ツール**: HashiCorp Vault, AWS Secrets Manager
3. **暗号化ファイル**: GPG暗号化されたファイル
4. **設定管理ツール**: Ansible Vault, Chef Data Bags

### 推奨運用フロー
1. **開発**: ローカル `.env` ファイル
2. **ステージング**: CI/CD環境変数または Secrets Manager
3. **本番**: 専用 Secrets Management Service
4. **緊急時**: 暗号化バックアップファイル

## ⚠️ 禁止事項
- 認証情報の平文での Git コミット
- Slack, メール等での認証情報共有
- 開発環境認証情報の本番流用
- アクセス権限の過度な付与

## 🔄 ライフサイクル管理
- **定期ローテーション**: 90日ごとに認証情報更新
- **アクセス監査**: 月次でアクセスログ確認
- **廃止処理**: プロジェクト終了時の完全削除

---

**最終更新**: 2025-08-29  
**管理者**: Claude Code AI Assistant  
**承認者**: プロジェクト責任者