# 🔧 開発ツール・支援システム

プロジェクトの開発・運用を支援するツール群です。製品コードとは完全に分離されています。

## 📁 ディレクトリ構成

### 🌟 **environments/**
セッション別開発環境設定
- `base.env` - 全セッション共通設定
- `sessions/` - セッション別個別設定（A, B, C, D）
- マルチセッション並行開発をサポート

### ⚙️ **scripts/**
開発自動化スクリプト
- `load-session-env.sh` - セッション環境変数読み込み
- `test-session-env.sh` - 環境設定テスト・検証
- その他の開発支援スクリプト

### 📚 **docs/**
設計書・仕様書・計画書
- `spec/` - 技術仕様・設計書
- プロジェクト記録・引継ぎ書
- 計画書・デプロイ記録

### 🧪 **testing/**
テスト関連ツール・結果
- `playwright-tests/` - E2Eテストケース
- `test-results/` - テスト実行結果・レポート
- 自動化テストスクリプト

### 🚀 **services/**
開発支援サービス
- `claude-discord-bridge-server/` - Discord連携開発環境
- `order-management-server/` - タスク管理システム
- その他の開発支援サービス

### 💾 **データディレクトリ**
- `uploads/` - セッション別アップロードファイル
- `logs/` - アプリケーションログ
- `backups/` - データベースバックアップ

## 🎯 使用方法

### セッション環境の起動
```bash
# セッション環境読み込み
source dev_tools/scripts/load-session-env.sh session-a

# データベースサービス起動
docker-compose up postgres-session-a redis-session-a -d

# 開発開始
npm run dev
```

### 環境テスト
```bash
# 全セッション環境テスト
dev_tools/scripts/test-session-env.sh
```

## 📝 ルール

1. **製品コードとの分離**: このディレクトリの内容は製品デプロイには含めない
2. **セッション管理**: A, B, C, D の4セッションで並行開発可能
3. **自動化重視**: 手動作業を最小限に抑える設計

---
**📍 このディレクトリは開発専用です。製品リリース時は除外されます。**