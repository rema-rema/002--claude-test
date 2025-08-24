# API設計書

## 1. 概要

### 1.1 現在の実装状況
本APIは基本的なAIチャット機能を提供する最小限の実装です。将来的な拡張を考慮した設計方針を含みます。

### 1.2 ベースURL
```
開発環境: http://localhost:5000
本番環境: https://ai-chat-proto.fly.dev
```

### 1.3 認証方式（現在実装済み）
- **Access Token**: 環境変数ACCESS_TOKENによる簡易認証（オプション）
- **OpenAI API Key**: サーバーサイドで管理

## 2. 現在の実装仕様

### 2.1 リクエストヘッダー
```http
Content-Type: application/json
Authorization: Bearer <access_token>  # オプション（ACCESS_TOKEN設定時のみ）
```

### 2.2 レスポンス形式（現在の実装）

#### 2.2.1 成功レスポンス例
```json
{
  "response": "AI応答内容",
  "status": "success"
}
```

#### 2.2.2 エラーレスポンス例
```json
{
  "error": "エラーメッセージ"
}
```

### 2.3 HTTPステータスコード（現在使用中）
- `200 OK`: 成功
- `400 Bad Request`: リクエストエラー
- `401 Unauthorized`: 認証エラー
- `404 Not Found`: エンドポイント未発見
- `429 Too Many Requests`: OpenAI APIレート制限
- `500 Internal Server Error`: サーバーエラー

## 3. 現在実装済みエンドポイント

### 3.1 ヘルスチェック

#### GET /health
システムの稼働状況を確認

**リクエスト**
```http
GET /health
```

**レスポンス（実際の形式）**
```json
{
  "status": "healthy",
  "service": "AI Chat Backend"
}
```

### 3.2 チャット機能

#### POST /api/chat
AIとのチャット処理（メイン機能）

**リクエスト（実際の形式）**
```http
POST /api/chat
Authorization: Bearer <access_token>  # ACCESS_TOKEN設定時のみ必須
Content-Type: application/json

{
  "message": "こんにちは",
  "history": [
    {
      "role": "user",
      "content": "前回の質問"
    },
    {
      "role": "assistant", 
      "content": "前回の回答"
    }
  ]
}
```

**レスポンス（実際の形式）**
```json
{
  "response": "こんにちは！何かお手伝いできることはありますか？",
  "status": "success"
}
```

**エラーレスポンス例（実際の形式）**
```json
{
  "error": "OpenAI API rate limit exceeded"
}
```

### 3.3 静的ファイル配信

#### GET / および GET /<path:path>
Next.js静的ファイルの配信（SPA対応）

**機能**
- Next.jsビルド結果の配信
- 存在しないパスは全てindex.htmlにフォールバック
- SPA（Single Page Application）ルーティング対応

## 4. 将来拡張予定のエンドポイント

### 4.1 認証機能（フェーズ2予定）
- `POST /api/auth/login` - OAuth認証
- `POST /api/auth/refresh` - トークンリフレッシュ
- `POST /api/auth/logout` - ログアウト

### 4.2 セッション管理（フェーズ3予定）
- `GET /api/sessions` - セッション一覧
- `POST /api/sessions` - セッション作成
- `GET /api/sessions/{id}` - セッション詳細
- `PUT /api/sessions/{id}` - セッション更新
- `DELETE /api/sessions/{id}` - セッション削除

### 4.3 メッセージ管理（フェーズ3予定）
- `GET /api/sessions/{id}/messages` - メッセージ履歴
- `POST /api/sessions/{id}/messages` - メッセージ送信

### 4.4 ユーザー管理（フェーズ4予定）
- `GET /api/user/profile` - プロフィール取得
- `PUT /api/user/profile` - プロフィール更新
- `GET /api/user/usage` - 使用量統計

## 5. 現在のエラーハンドリング

### 5.1 実装済みエラー処理
- **400 Bad Request**: `{"error": "Message is required"}`
- **401 Unauthorized**: `{"error": "Unauthorized"}` または `{"error": "Invalid OpenAI API key"}`
- **404 Not Found**: `{"error": "Endpoint not found"}`
- **429 Too Many Requests**: `{"error": "OpenAI API rate limit exceeded"}`
- **500 Internal Server Error**: `{"error": "OpenAI API error: ..."}`または`{"error": "Internal server error: ..."}`

### 5.2 リファクタリング予定
- エラーレスポンス形式の統一
- エラーコード体系の導入
- 詳細なエラー情報の提供

## 6. 将来拡張予定機能

### 6.1 レート制限（フェーズ2予定）
- アプリケーションレベルでのレート制限実装
- ユーザー別・IP別制限
- レート制限ヘッダーの追加

### 6.2 ページネーション（フェーズ3予定）
- セッション一覧・メッセージ履歴での実装
- 標準的なページネーション形式

### 6.3 検索・フィルタリング（フェーズ4予定）
- セッション検索機能
- メッセージ内容検索
- 日付範囲フィルタ

### 6.4 WebSocket API（フェーズ5予定）
- リアルタイムチャット
- ストリーミング応答
- 接続状態管理

## 7. 現在の技術的制約

### 7.1 制約事項
- セッション管理なし（ブラウザ内のみ）
- ユーザー認証なし（ACCESS_TOKENのみ）
- データ永続化なし
- レート制限なし（OpenAI API依存）

### 7.2 リファクタリング・改善タスク

#### 7.2.1 コード整理タスク
- [ ] エラーレスポンス形式の統一
- [ ] バリデーション処理の共通化
- [ ] OpenAI API呼び出しの関数化
- [ ] 設定値の外部化（モデル、温度等）

#### 7.2.2 機能改善タスク
- [ ] リクエストログの詳細化
- [ ] エラーハンドリングの強化
- [ ] レスポンス時間の監視
- [ ] ヘルスチェックの詳細化

#### 7.2.3 セキュリティ強化タスク
- [ ] 入力値検証の強化
- [ ] CORS設定の最適化
- [ ] セキュリティヘッダーの追加
- [ ] APIキー管理の改善