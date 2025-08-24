# エラーハンドリング設計書

## 1. 概要

### 1.1 エラーハンドリング原則
- **ユーザーフレンドリー**: 分かりやすいエラーメッセージ
- **適切な分類**: エラーの種類に応じた処理
- **ログ記録**: デバッグ・監視のための詳細ログ
- **復旧支援**: ユーザーが問題を解決できる情報提供
- **セキュリティ**: 機密情報の漏洩防止

### 1.2 エラー処理レベル
1. **フロントエンド**: UI層でのエラー処理
2. **API層**: バックエンドAPIでのエラー処理
3. **サービス層**: ビジネスロジック層でのエラー処理
4. **インフラ層**: データベース・外部API層でのエラー処理

## 2. エラー分類

### 2.1 エラーカテゴリ

#### 2.1.1 ユーザーエラー（4xx）
ユーザーの操作や入力に起因するエラー

- **バリデーションエラー**: 入力値の形式・範囲エラー
- **認証エラー**: ログイン失敗、トークン無効
- **認可エラー**: 権限不足、アクセス拒否
- **リソースエラー**: 存在しないリソースへのアクセス

#### 2.1.2 システムエラー（5xx）
システム側の問題に起因するエラー

- **内部サーバーエラー**: アプリケーション内部の問題
- **外部サービスエラー**: OpenAI API等の外部依存エラー
- **データベースエラー**: DB接続・クエリエラー
- **ネットワークエラー**: 通信障害

#### 2.1.3 ビジネスエラー
アプリケーション固有のビジネスルールエラー

- **使用量制限エラー**: トークン数・リクエスト数制限
- **サブスクリプションエラー**: 決済・プラン関連
- **コンテンツエラー**: 不適切なコンテンツ検出

## 3. エラーコード体系

### 3.1 エラーコード命名規則
```
[CATEGORY]_[SPECIFIC_ERROR]_[DETAIL]

例:
- AUTH_TOKEN_EXPIRED
- VALIDATION_REQUIRED_FIELD
- OPENAI_RATE_LIMIT_EXCEEDED
```

### 3.2 エラーコード一覧

#### 3.2.1 認証・認可エラー (AUTH_*)
```typescript
enum AuthErrorCode {
  AUTH_TOKEN_MISSING = 'AUTH_TOKEN_MISSING',
  AUTH_TOKEN_INVALID = 'AUTH_TOKEN_INVALID', 
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED',
  AUTH_INSUFFICIENT_PERMISSIONS = 'AUTH_INSUFFICIENT_PERMISSIONS',
  AUTH_LOGIN_FAILED = 'AUTH_LOGIN_FAILED',
  AUTH_LOGOUT_FAILED = 'AUTH_LOGOUT_FAILED'
}
```

#### 3.2.2 バリデーションエラー (VALIDATION_*)
```typescript
enum ValidationErrorCode {
  VALIDATION_REQUIRED_FIELD = 'VALIDATION_REQUIRED_FIELD',
  VALIDATION_INVALID_FORMAT = 'VALIDATION_INVALID_FORMAT',
  VALIDATION_OUT_OF_RANGE = 'VALIDATION_OUT_OF_RANGE',
  VALIDATION_TOO_LONG = 'VALIDATION_TOO_LONG',
  VALIDATION_TOO_SHORT = 'VALIDATION_TOO_SHORT'
}
```

#### 3.2.3 リソースエラー (RESOURCE_*)
```typescript
enum ResourceErrorCode {
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  RESOURCE_ALREADY_EXISTS = 'RESOURCE_ALREADY_EXISTS',
  RESOURCE_LIMIT_EXCEEDED = 'RESOURCE_LIMIT_EXCEEDED',
  RESOURCE_ACCESS_DENIED = 'RESOURCE_ACCESS_DENIED'
}
```

#### 3.2.4 外部サービスエラー (OPENAI_*, STRIPE_*)
```typescript
enum OpenAIErrorCode {
  OPENAI_API_ERROR = 'OPENAI_API_ERROR',
  OPENAI_RATE_LIMIT = 'OPENAI_RATE_LIMIT',
  OPENAI_QUOTA_EXCEEDED = 'OPENAI_QUOTA_EXCEEDED',
  OPENAI_INVALID_KEY = 'OPENAI_INVALID_KEY',
  OPENAI_MODEL_UNAVAILABLE = 'OPENAI_MODEL_UNAVAILABLE'
}

enum StripeErrorCode {
  STRIPE_PAYMENT_FAILED = 'STRIPE_PAYMENT_FAILED',
  STRIPE_CARD_DECLINED = 'STRIPE_CARD_DECLINED',
  STRIPE_SUBSCRIPTION_ERROR = 'STRIPE_SUBSCRIPTION_ERROR'
}
```

#### 3.2.5 システムエラー (SYSTEM_*)
```typescript
enum SystemErrorCode {
  SYSTEM_INTERNAL_ERROR = 'SYSTEM_INTERNAL_ERROR',
  SYSTEM_DATABASE_ERROR = 'SYSTEM_DATABASE_ERROR',
  SYSTEM_NETWORK_ERROR = 'SYSTEM_NETWORK_ERROR',
  SYSTEM_SERVICE_UNAVAILABLE = 'SYSTEM_SERVICE_UNAVAILABLE'
}
```

## 4. エラーレスポンス形式

### 4.1 統一エラーレスポンス
```typescript
interface ErrorResponse {
  success: false
  error: {
    code: string           // エラーコード
    message: string        // ユーザー向けメッセージ
    details?: any         // 詳細情報（開発環境のみ）
    field?: string        // バリデーションエラーの対象フィールド
    retry_after?: number  // リトライ可能な場合の待機時間（秒）
  }
  meta: {
    timestamp: string     // エラー発生時刻
    request_id: string    // リクエストID（トレーシング用）
    version: string       // APIバージョン
  }
}
```

### 4.2 エラーレスポンス例

#### 4.2.1 バリデーションエラー
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_REQUIRED_FIELD",
    "message": "メッセージは必須です",
    "field": "message"
  },
  "meta": {
    "timestamp": "2025-07-22T10:30:00Z",
    "request_id": "req_123456789",
    "version": "1.0"
  }
}
```

#### 4.2.2 OpenAI APIエラー
```json
{
  "success": false,
  "error": {
    "code": "OPENAI_RATE_LIMIT",
    "message": "API利用制限に達しました。しばらく待ってから再度お試しください。",
    "retry_after": 60
  },
  "meta": {
    "timestamp": "2025-07-22T10:30:00Z",
    "request_id": "req_123456789",
    "version": "1.0"
  }
}
```

#### 4.2.3 認証エラー
```json
{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "認証の有効期限が切れています。再度ログインしてください。"
  },
  "meta": {
    "timestamp": "2025-07-22T10:30:00Z",
    "request_id": "req_123456789",
    "version": "1.0"
  }
}
```

## 5. フロントエンドエラーハンドリング

### 5.1 エラー処理アーキテクチャ

#### 5.1.1 エラーバウンダリ
```typescript
class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // エラーログ送信
    this.logError(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />
    }
    return this.props.children
  }
}
```

#### 5.1.2 カスタムフック
```typescript
interface UseErrorHandlerReturn {
  error: string | null
  showError: (error: string) => void
  clearError: () => void
  handleApiError: (error: ApiError) => void
}

export const useErrorHandler = (): UseErrorHandlerReturn => {
  const [error, setError] = useState<string | null>(null)

  const showError = useCallback((errorMessage: string) => {
    setError(errorMessage)
    // トースト通知表示
    toast.error(errorMessage)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const handleApiError = useCallback((apiError: ApiError) => {
    const userMessage = getUserFriendlyMessage(apiError.code)
    showError(userMessage)
    
    // エラーログ送信
    logError(apiError)
  }, [showError])

  return { error, showError, clearError, handleApiError }
}
```

### 5.2 エラーメッセージマッピング

#### 5.2.1 ユーザーフレンドリーメッセージ
```typescript
const ERROR_MESSAGES: Record<string, string> = {
  // 認証エラー
  AUTH_TOKEN_EXPIRED: '認証の有効期限が切れています。再度ログインしてください。',
  AUTH_TOKEN_INVALID: '認証情報が無効です。再度ログインしてください。',
  AUTH_INSUFFICIENT_PERMISSIONS: 'この操作を実行する権限がありません。',

  // バリデーションエラー
  VALIDATION_REQUIRED_FIELD: 'この項目は必須です。',
  VALIDATION_INVALID_FORMAT: '入力形式が正しくありません。',
  VALIDATION_TOO_LONG: '入力が長すぎます。',

  // OpenAI APIエラー
  OPENAI_RATE_LIMIT: 'API利用制限に達しました。しばらく待ってから再度お試しください。',
  OPENAI_QUOTA_EXCEEDED: '月間利用制限に達しました。プランのアップグレードをご検討ください。',
  OPENAI_API_ERROR: 'AI処理中にエラーが発生しました。再度お試しください。',

  // システムエラー
  SYSTEM_NETWORK_ERROR: 'ネットワークエラーが発生しました。接続を確認してください。',
  SYSTEM_INTERNAL_ERROR: 'システムエラーが発生しました。しばらく待ってから再度お試しください。',

  // デフォルト
  UNKNOWN_ERROR: '予期しないエラーが発生しました。'
}

export const getUserFriendlyMessage = (errorCode: string): string => {
  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.UNKNOWN_ERROR
}
```

### 5.3 エラー表示コンポーネント

#### 5.3.1 インラインエラー
```typescript
interface InlineErrorProps {
  error: string | null
  className?: string
}

export const InlineError: React.FC<InlineErrorProps> = ({ error, className }) => {
  if (!error) return null

  return (
    <div className={`inline-error ${className}`} role="alert">
      <Icon name="error" />
      <span>{error}</span>
    </div>
  )
}
```

#### 5.3.2 エラーページ
```typescript
interface ErrorPageProps {
  error: Error
  resetError: () => void
}

export const ErrorPage: React.FC<ErrorPageProps> = ({ error, resetError }) => {
  return (
    <div className="error-page">
      <h1>エラーが発生しました</h1>
      <p>申し訳ございません。予期しないエラーが発生しました。</p>
      <button onClick={resetError}>再試行</button>
      <button onClick={() => window.location.href = '/'}>ホームに戻る</button>
    </div>
  )
}
```

## 6. バックエンドエラーハンドリング

### 6.1 エラーハンドリングミドルウェア

#### 6.1.1 グローバルエラーハンドラー
```python
from flask import Flask, jsonify, request
import traceback
import logging

class ErrorHandler:
    def __init__(self, app: Flask):
        self.app = app
        self.setup_error_handlers()

    def setup_error_handlers(self):
        @self.app.errorhandler(400)
        def bad_request(error):
            return self.create_error_response(
                'VALIDATION_ERROR',
                'リクエストが正しくありません',
                400
            )

        @self.app.errorhandler(401)
        def unauthorized(error):
            return self.create_error_response(
                'AUTH_TOKEN_INVALID',
                '認証が必要です',
                401
            )

        @self.app.errorhandler(403)
        def forbidden(error):
            return self.create_error_response(
                'AUTH_INSUFFICIENT_PERMISSIONS',
                'アクセス権限がありません',
                403
            )

        @self.app.errorhandler(404)
        def not_found(error):
            return self.create_error_response(
                'RESOURCE_NOT_FOUND',
                'リソースが見つかりません',
                404
            )

        @self.app.errorhandler(500)
        def internal_error(error):
            return self.create_error_response(
                'SYSTEM_INTERNAL_ERROR',
                '内部サーバーエラーが発生しました',
                500
            )

    def create_error_response(self, code: str, message: str, status: int):
        response = {
            'success': False,
            'error': {
                'code': code,
                'message': message
            },
            'meta': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': request.headers.get('X-Request-ID', 'unknown'),
                'version': '1.0'
            }
        }
        
        # 開発環境では詳細情報を追加
        if self.app.debug:
            response['error']['details'] = {
                'traceback': traceback.format_exc()
            }
        
        return jsonify(response), status
```

### 6.2 カスタム例外クラス

#### 6.2.1 基底例外クラス
```python
class AppException(Exception):
    """アプリケーション基底例外"""
    def __init__(self, code: str, message: str, status_code: int = 500, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(AppException):
    """バリデーションエラー"""
    def __init__(self, message: str, field: str = None):
        super().__init__(
            code='VALIDATION_ERROR',
            message=message,
            status_code=400,
            details={'field': field} if field else {}
        )

class AuthenticationError(AppException):
    """認証エラー"""
    def __init__(self, code: str = 'AUTH_TOKEN_INVALID', message: str = '認証に失敗しました'):
        super().__init__(code=code, message=message, status_code=401)

class OpenAIError(AppException):
    """OpenAI APIエラー"""
    def __init__(self, original_error: Exception):
        if 'rate_limit' in str(original_error).lower():
            code = 'OPENAI_RATE_LIMIT'
            message = 'API利用制限に達しました'
        elif 'quota' in str(original_error).lower():
            code = 'OPENAI_QUOTA_EXCEEDED'
            message = '月間利用制限に達しました'
        else:
            code = 'OPENAI_API_ERROR'
            message = 'AI処理中にエラーが発生しました'
        
        super().__init__(code=code, message=message, status_code=500)
```

### 6.3 サービス層エラーハンドリング

#### 6.3.1 ChatService例
```python
class ChatService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def process_message(self, message: str, history: List[dict]) -> dict:
        try:
            # 入力値検証
            if not message or not message.strip():
                raise ValidationError('メッセージは必須です', 'message')
            
            if len(message) > 4000:
                raise ValidationError('メッセージが長すぎます', 'message')

            # OpenAI API呼び出し
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=self._build_messages(message, history),
                max_tokens=1000,
                temperature=0.7
            )

            return {
                'response': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model_used': 'gpt-4'
            }

        except openai.RateLimitError as e:
            raise OpenAIError(e)
        except openai.APIError as e:
            raise OpenAIError(e)
        except Exception as e:
            logging.error(f"Unexpected error in ChatService: {str(e)}")
            raise AppException(
                code='SYSTEM_INTERNAL_ERROR',
                message='チャット処理中にエラーが発生しました'
            )
```

## 7. ログ戦略

### 7.1 ログレベル定義
- **DEBUG**: 開発時のデバッグ情報
- **INFO**: 一般的な情報（リクエスト処理等）
- **WARNING**: 警告（非致命的な問題）
- **ERROR**: エラー（処理失敗）
- **CRITICAL**: 致命的エラー（システム停止レベル）

### 7.2 ログ形式

#### 7.2.1 構造化ログ（JSON）
```json
{
  "timestamp": "2025-07-22T10:30:00Z",
  "level": "ERROR",
  "logger": "chat_service",
  "message": "OpenAI API request failed",
  "error": {
    "code": "OPENAI_RATE_LIMIT",
    "message": "Rate limit exceeded",
    "stack_trace": "..."
  },
  "context": {
    "user_id": "user_123",
    "session_id": "session_456",
    "request_id": "req_789"
  },
  "metadata": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "api_version": "1.0"
  }
}
```

### 7.3 ログ記録実装

#### 7.3.1 Python ログ設定
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        if hasattr(record, 'error_code'):
            log_entry['error'] = {
                'code': record.error_code,
                'message': record.error_message
            }
        
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
            
        return json.dumps(log_entry, ensure_ascii=False)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# カスタムロガー
def log_error(error: AppException, context: dict = None):
    logger = logging.getLogger(__name__)
    logger.error(
        f"Application error: {error.message}",
        extra={
            'error_code': error.code,
            'error_message': error.message,
            'context': context or {}
        }
    )
```

## 8. 監視・アラート

### 8.1 エラー監視指標
- **エラー率**: 全リクエストに対するエラーの割合
- **エラー頻度**: 時間あたりのエラー発生数
- **エラー種別**: エラーコード別の発生数
- **復旧時間**: エラー発生から解決までの時間

### 8.2 アラート設定
- **エラー率 > 5%**: 即座にアラート
- **OpenAI APIエラー連続発生**: 5分以内に3回以上
- **システムエラー発生**: 即座にアラート
- **レスポンス時間 > 5秒**: 継続監視

### 8.3 ダッシュボード
- エラー発生状況の可視化
- エラーコード別の統計
- 時系列でのエラー推移
- ユーザー影響度の分析

## 9. テスト戦略

### 9.1 エラーケーステスト

#### 9.1.1 ユニットテスト
```python
def test_chat_service_validation_error():
    service = ChatService(mock_openai_client)
    
    with pytest.raises(ValidationError) as exc_info:
        service.process_message("", [])
    
    assert exc_info.value.code == 'VALIDATION_ERROR'
    assert 'メッセージは必須です' in exc_info.value.message

def test_chat_service_openai_rate_limit():
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = openai.RateLimitError("Rate limit exceeded")
    
    service = ChatService(mock_client)
    
    with pytest.raises(OpenAIError) as exc_info:
        service.process_message("test", [])
    
    assert exc_info.value.code == 'OPENAI_RATE_LIMIT'
```

#### 9.1.2 統合テスト
```python
def test_chat_api_error_response():
    response = client.post('/api/chat', json={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'VALIDATION_ERROR'
```

### 9.2 エラーシナリオテスト
- ネットワーク切断時の動作
- 外部API障害時の動作
- 大量リクエスト時の動作
- 不正なデータ送信時の動作

## 10. 復旧・改善プロセス

### 10.1 インシデント対応フロー
1. **検知**: 監視システムによる自動検知
2. **分析**: ログ・メトリクスによる原因分析
3. **対応**: 緊急対応・修正実施
4. **復旧**: サービス正常化確認
5. **報告**: インシデントレポート作成
6. **改善**: 再発防止策の実施

### 10.2 エラー分析・改善
- 定期的なエラーログ分析
- エラーパターンの特定
- ユーザー影響度の評価
- 改善優先度の決定
- 修正・改善の実施