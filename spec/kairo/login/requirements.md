# Login機能 - 要件定義書

## 1. 機能概要

### 1.1 目的
Google OAuth 2.0を利用したシングルサインオン（SSO）ログイン機能の実装

### 1.2 ユーザーフロー
1. **ログイン画面表示**: ユーザーがアクセス時にログイン画面を表示
2. **Google認証**: Googleアカウントでの認証を実行
3. **トップページ遷移**: 認証成功後、トップページ（index.html）に遷移

## 2. 機能要件

### 2.1 認証機能
- **Google OAuth 2.0統合**: Google Identity Servicesを使用した認証
- **セキュアな認証フロー**: Authorization Code Flow + PKCEによる実装
- **セッション管理**: 認証状態の永続化と管理

### 2.2 UI/UX要件
- **ミニマルデザイン**: 提供されたデザイン仕様に基づく実装
- **レスポンシブ対応**: モバイル・デスクトップ両対応
- **直感的操作**: ワンクリックログインの実現

### 2.3 画面構成
- **ログイン画面** (`login.html`): Google認証ボタンを配置
- **トップページ** (`index.html`): ログイン後の着地ページ
- **画面遷移**: ログイン → Google認証 → トップページ

## 3. 技術要件

### 3.1 フロントエンド
- **HTML5/CSS3**: モダンなマークアップとスタイリング
- **バニラJavaScript**: 軽量で依存関係のない実装
- **Google Identity Services**: 最新のGoogle認証ライブラリ使用

### 3.2 バックエンド
- **Node.js/Express**: サーバーサイド実装
- **Google OAuth 2.0**: 認証プロバイダー
- **セッション管理**: セキュアなセッション保存・管理

### 3.3 ファイル構成
Feature-based Structure（機能別完結型）を採用：
```
/src/features/login/
  /frontend/
    login.html              # ログイン画面
    login.css               # ログイン専用スタイル
    login.js                # ログインUI制御
  /backend/
    google-oauth.js         # Google OAuth実装
    auth-routes.js          # 認証APIエンドポイント
    session-manager.js      # セッション管理
  /config/
    oauth-config.js         # OAuth設定
  /tests/
    login.test.js           # ログインテスト
    test-accounts.json      # テストアカウント
  README.md                 # この機能の説明書

/src/
  index.html                # トップページ（ログイン後の着地ページ）

/tests/login/               # テスト用ディレクトリ
  test-accounts.json        # テストアカウント情報
```

## 4. セキュリティ要件

### 4.1 必須セキュリティ対策
1. **CSRF対策**
   - Stateパラメータ（ランダム値）の実装
   - セッション毎のトークン検証

2. **セッション管理**
   - HTTPOnly Cookieでセッション管理
   - Secure属性（HTTPS必須）
   - SameSite=Strict

3. **トークン管理**
   - Access Tokenはメモリまたはセッション保存
   - Refresh Tokenは暗号化して保存
   - トークン有効期限の管理

4. **通信セキュリティ**
   - HTTPS必須
   - Content Security Policy設定

### 4.2 認証フロー
- **OAuth 2.0 Authorization Code Flow**: 標準的なOAuth認証フロー
- **PKCE実装**: Proof Key for Code Exchange by OAuth Public Clients
- **エラーハンドリング**: セキュリティ情報の最小化

## 5. 非機能要件

### 5.1 パフォーマンス
- **ページロード時間**: 3秒以内
- **認証レスポンス**: 5秒以内
- **UI反応性**: ボタンクリック後即座のフィードバック

### 5.2 ユーザビリティ
- **アクセシビリティ**: WCAG 2.1 AA準拠
- **ブラウザ対応**: Chrome、Firefox、Safari、Edge最新2バージョン
- **エラーメッセージ**: 日本語でのユーザーフレンドリーなメッセージ

### 5.3 保守性
- **コード品質**: ESLint、Prettierによるコード整形
- **テスト網羅率**: 80%以上
- **ドキュメント**: READMEとコメントによる十分な説明

## 6. テスト要件

### 6.1 テストデータ
- **テストアカウント**: `tests/login/test-accounts.json`に格納
  ```json
  {
    "test_user": {
      "email": "bpdy.dev01@gmail.com",
      "password": "c0me1nFr1end",
      "purpose": "開発・テスト用アカウント"
    }
  }
  ```

### 6.2 テストケース
- **正常系**: Google認証成功 → トップページ遷移
- **異常系**: 認証拒否、ネットワークエラー、タイムアウト
- **セキュリティテスト**: CSRF、セッションハイジャック対策

## 7. 制約事項

### 7.1 技術的制約
- **既存プロジェクト構造**: 現在のプロジェクト構造を最大活用
- **Google Cloud Platform**: OAuth 2.0クライアント設定が必要
- **HTTPS環境**: 本番環境でのHTTPS必須

### 7.2 運用制約
- **開発環境**: GitHub Codespaces対応
- **デプロイ**: Vercelとの統合考慮
- **保守**: 既存Discord Bot運用ツールとの共存

## 8. 依存関係

### 8.1 外部サービス
- **Google Cloud Platform**: OAuth 2.0認証プロバイダー
- **Google Identity Services**: 認証ライブラリ

### 8.2 内部システム
- **既存API構造**: `/api/`フォルダとの統合
- **共通コンポーネント**: `/src/shared/`による共通化

## 9. 成功基準

### 9.1 機能的成功基準
- ✅ Googleアカウントでのログイン成功率 99%以上
- ✅ ログイン後のトップページ遷移成功
- ✅ セッション状態の適切な管理

### 9.2 技術的成功基準
- ✅ 全テストケースの合格
- ✅ セキュリティ監査の合格
- ✅ パフォーマンス要件の達成

### 9.3 ユーザー体験成功基準
- ✅ 3クリック以内でのログイン完了
- ✅ エラー時の適切なガイダンス表示
- ✅ レスポンシブデザインでの快適な操作

---

**作成日**: 2025-08-29  
**モード**: REQUIREMENTS  
**次フェーズ**: DESIGN（要件確認完了後）