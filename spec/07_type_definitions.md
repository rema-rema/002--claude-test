# TypeScript型定義設計書

## 1. 概要

### 1.1 現在の型定義状況
現在はChatInterface.tsxに基本的なMessage型のみ定義されています。将来の拡張を見据えた型定義戦略を含みます。

### 1.2 型定義戦略
- **段階的拡張**: 現在の実装から将来の拡張まで対応
- **厳密モード**: TypeScript strict設定での開発
- **共通化**: 再利用可能な型の定義
- **実装ベース**: 実際のコードに基づいた型定義

## 2. 現在実装済みの型定義

### 2.1 基本Message型（ChatInterface.tsx）
```typescript
// 現在実装済み
interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
}
```

### 2.2 リファクタリング予定の型定義

#### 2.2.1 基本型エイリアス
```typescript
// 将来の共通化予定
export type MessageId = string
export type Timestamp = Date // 現在はDate型使用

// 将来拡張予定
export type UserId = string
export type SessionId = string
```

#### 2.2.2 メッセージロール型
```typescript
// 現在: 'user' | 'assistant'
// 将来拡張予定: 'system'も追加
export type MessageRole = 'user' | 'assistant' | 'system'
```

## 3. API通信関連型定義

### 3.1 現在実装済みのAPI型

#### 3.1.1 チャットAPI型（実装済み）
```typescript
// POST /api/chat リクエスト型
export interface ChatRequest {
  message: string
  history: Message[]  // 現在のMessage型を使用
}

// POST /api/chat レスポンス型
export interface ChatResponse {
  response: string
  status: 'success'
}

// エラーレスポンス型
export interface ChatErrorResponse {
  error: string
}
```

#### 3.1.2 ヘルスチェックAPI型（実装済み）
```typescript
// GET /health レスポンス型
export interface HealthResponse {
  status: 'healthy'
  service: 'AI Chat Backend'
}
```

### 3.2 将来拡張予定の型定義

#### 3.2.1 拡張Message型（将来）
```typescript
// 現在のMessage型を拡張予定
export interface ExtendedMessage extends Message {
  sessionId?: SessionId
  metadata?: MessageMetadata
  tokenCount?: number
}

export interface MessageMetadata {
  model?: string  // 'gpt-4'等
  temperature?: number
  maxTokens?: number
  cost?: number
  processingTime?: number // ミリ秒
}
```

#### 3.2.2 セッション管理型（将来）
```typescript
export interface ChatSession {
  id: SessionId
  title: string
  createdAt: Timestamp
  updatedAt: Timestamp
  isArchived: boolean
  settings: ChatSettings
  messageCount?: number
}

export interface ChatSettings {
  model: string  // 'gpt-4'等
  temperature: number
  maxTokens: number
  systemPrompt: string
}
```

### 3.3 サブスクリプション関連型

#### 3.3.1 Subscription型
```typescript
export interface UserSubscription {
  id: string
  userId: UserId
  stripeSubscriptionId?: string
  status: SubscriptionStatus
  planType: PlanType
  currentPeriodStart?: Timestamp
  currentPeriodEnd?: Timestamp
  createdAt: Timestamp
  updatedAt: Timestamp
}

export interface SubscriptionPlan {
  type: PlanType
  name: string
  description: string
  price: Amount
  currency: Currency
  features: PlanFeature[]
  limits: PlanLimits
}

export interface PlanFeature {
  name: string
  description: string
  included: boolean
}

export interface PlanLimits {
  monthlyTokens: number
  maxSessions: number
  maxMessagesPerSession: number
  supportLevel: 'basic' | 'priority' | 'premium'
}
```

#### 3.3.2 使用量関連型
```typescript
export interface UsageLog {
  id: string
  userId: UserId
  sessionId?: SessionId
  messageId?: MessageId
  tokensUsed: number
  cost: number
  createdAt: Timestamp
  modelUsed: OpenAIModel
}

export interface UserUsage {
  period: string // YYYY-MM形式
  totalTokens: number
  totalCost: number
  sessionCount: number
  messageCount: number
  dailyBreakdown: DailyUsage[]
}

export interface DailyUsage {
  date: string // YYYY-MM-DD形式
  tokens: number
  cost: number
  sessions: number
}

export interface UsageLimits {
  monthlyTokenLimit: number
  remainingTokens: number
  resetDate: Timestamp
}
```

## 4. API関連型定義

### 4.1 共通API型

#### 4.1.1 レスポンス型
```typescript
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: ApiError
  meta: ApiMeta
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
  field?: string
  retryAfter?: number
}

export interface ApiMeta {
  timestamp: Timestamp
  requestId: RequestId
  version: string
}

// 成功レスポンス型
export interface SuccessResponse<T> extends ApiResponse<T> {
  success: true
  data: T
}

// エラーレスポンス型
export interface ErrorResponse extends ApiResponse {
  success: false
  error: ApiError
}
```

#### 4.1.2 ページネーション型
```typescript
export interface PaginationParams {
  page: number
  limit: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface PaginationMeta {
  page: number
  limit: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: PaginationMeta
}
```

### 4.2 エンドポイント別型定義

#### 4.2.1 チャットAPI型
```typescript
// POST /api/chat
export type ChatApiRequest = ChatRequest
export type ChatApiResponse = SuccessResponse<ChatResponse>

// POST /api/sessions/{sessionId}/messages
export interface SessionChatRequest {
  content: string
  settings?: Partial<ChatSettings>
}

export interface SessionChatResponse {
  userMessage: Message
  assistantMessage: Message
  usage: TokenUsage
}
```

#### 4.2.2 セッションAPI型
```typescript
// GET /api/sessions
export interface GetSessionsParams extends PaginationParams {
  archived?: boolean
  search?: string
}

export type GetSessionsResponse = SuccessResponse<PaginatedResponse<ChatSession>>

// POST /api/sessions
export type CreateSessionResponse = SuccessResponse<{ session: ChatSession }>

// GET /api/sessions/{id}
export type GetSessionResponse = SuccessResponse<{ session: ChatSession }>

// PUT /api/sessions/{id}
export type UpdateSessionResponse = SuccessResponse<{ session: ChatSession }>

// DELETE /api/sessions/{id}
export type DeleteSessionResponse = SuccessResponse<{ message: string }>
```

#### 4.2.3 メッセージAPI型
```typescript
// GET /api/sessions/{sessionId}/messages
export interface GetMessagesParams extends PaginationParams {
  before?: Timestamp
  after?: Timestamp
}

export type GetMessagesResponse = SuccessResponse<PaginatedResponse<Message>>
```

#### 4.2.4 ユーザーAPI型
```typescript
// GET /api/user/profile
export type GetProfileResponse = SuccessResponse<{ user: UserProfile }>

// PUT /api/user/profile
export type UpdateProfileResponse = SuccessResponse<{ user: User }>

// GET /api/user/usage
export interface GetUsageParams {
  period?: string // YYYY-MM
  year?: number
  month?: number
}

export type GetUsageResponse = SuccessResponse<{
  usage: UserUsage
  limits: UsageLimits
}>
```

## 4. フロントエンド型定義

### 4.1 現在実装済みのコンポーネント型

#### 4.1.1 ChatInterface型（実装済み）
```typescript
// 現在のChatInterfaceコンポーネント
// Props型は現在未定義（将来のリファクタリング対象）
export interface ChatInterfaceProps {
  // 将来の拡張予定
  initialMessages?: Message[]
  onMessageSend?: (message: string) => void
  className?: string
}
```

### 4.2 リファクタリング予定の型定義

#### 4.2.1 コンポーネント分離予定
```typescript
// MessageList コンポーネント（分離予定）
export interface MessageListProps {
  messages: Message[]
  isLoading?: boolean
  className?: string
}

// MessageInput コンポーネント（分離予定）
export interface MessageInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (message: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

// LoadingIndicator コンポーネント（分離予定）
export interface LoadingIndicatorProps {
  className?: string
}
```

### 4.3 現在の状態管理型

#### 4.3.1 ChatInterface内部状態（実装済み）
```typescript
// 現在のChatInterfaceコンポーネント内で使用
interface ChatState {
  messages: Message[]
  input: string
  isLoading: boolean
}
```

### 4.4 将来のカスタムフック型（拡張予定）

#### 4.4.1 useChat フック（分離予定）
```typescript
// ChatInterfaceからロジックを分離予定
export interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  error: string | null
  sendMessage: (message: string) => Promise<void>
  clearMessages: () => void
}
```

#### 4.4.2 useApi フック（共通化予定）
```typescript
// API通信の共通化予定
export interface UseApiReturn<T> {
  data: T | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}
```

## 6. バリデーション型定義

### 6.1 入力値検証型
```typescript
// Zod スキーマ型
import { z } from 'zod'

export const MessageSchema = z.object({
  content: z.string().min(1, 'メッセージは必須です').max(4000, 'メッセージが長すぎます'),
  role: z.nativeEnum(MessageRole),
  sessionId: z.string().uuid().optional()
})

export const ChatRequestSchema = z.object({
  message: z.string().min(1).max(4000),
  history: z.array(MessageSchema).max(10).optional(),
  settings: z.object({
    model: z.nativeEnum(OpenAIModel).optional(),
    temperature: z.number().min(0).max(2).optional(),
    maxTokens: z.number().min(1).max(4000).optional()
  }).optional()
})

export const UserProfileSchema = z.object({
  displayName: z.string().min(1).max(100),
  avatarUrl: z.string().url().optional()
})

// 型推論
export type MessageInput = z.infer<typeof MessageSchema>
export type ChatRequestInput = z.infer<typeof ChatRequestSchema>
export type UserProfileInput = z.infer<typeof UserProfileSchema>
```

### 6.2 フォーム型定義
```typescript
// React Hook Form用型
export interface LoginFormData {
  email: string
  password: string
  rememberMe: boolean
}

export interface ProfileFormData {
  displayName: string
  avatarUrl: string
}

export interface ChatSettingsFormData {
  model: OpenAIModel
  temperature: number
  maxTokens: number
  systemPrompt: string
}
```

## 7. ユーティリティ型定義

### 7.1 共通ユーティリティ型
```typescript
// 部分的な更新型
export type PartialUpdate<T> = Partial<T> & { id: string }

// 作成時に不要なフィールドを除外
export type CreateInput<T> = Omit<T, 'id' | 'createdAt' | 'updatedAt'>

// 更新時に変更可能なフィールドのみ
export type UpdateInput<T> = Partial<Omit<T, 'id' | 'createdAt' | 'updatedAt'>>

// APIレスポンスからデータ部分を抽出
export type ExtractData<T> = T extends SuccessResponse<infer U> ? U : never

// 配列の要素型を取得
export type ArrayElement<T> = T extends (infer U)[] ? U : never

// 非null型
export type NonNull<T> = T extends null ? never : T

// 深い部分型
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}
```

### 7.2 条件型・マップ型
```typescript
// 必須フィールドのみ抽出
export type RequiredFields<T> = {
  [K in keyof T as T[K] extends Required<T>[K] ? K : never]: T[K]
}

// オプショナルフィールドのみ抽出
export type OptionalFields<T> = {
  [K in keyof T as T[K] extends Required<T>[K] ? never : K]: T[K]
}

// 特定の型のフィールドのみ抽出
export type FieldsOfType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K]
}

// 文字列リテラル型からUnion型を生成
export type StringToUnion<T extends string> = T extends `${infer U},${infer V}`
  ? U | StringToUnion<V>
  : T
```

## 8. 型ガード・型述語

### 8.1 型ガード関数
```typescript
// User型ガード
export function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'email' in obj &&
    'displayName' in obj
  )
}

// Message型ガード
export function isMessage(obj: unknown): obj is Message {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'role' in obj &&
    'content' in obj &&
    Object.values(MessageRole).includes((obj as any).role)
  )
}

// APIエラー型ガード
export function isApiError(obj: unknown): obj is ApiError {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'code' in obj &&
    'message' in obj
  )
}

// 成功レスポンス型ガード
export function isSuccessResponse<T>(
  response: ApiResponse<T>
): response is SuccessResponse<T> {
  return response.success === true && 'data' in response
}
```

### 8.2 型述語ユーティリティ
```typescript
// 配列の型ガード
export function isArrayOf<T>(
  arr: unknown[],
  guard: (item: unknown) => item is T
): arr is T[] {
  return arr.every(guard)
}

// オブジェクトのキー存在チェック
export function hasKey<T extends object, K extends string>(
  obj: T,
  key: K
): obj is T & Record<K, unknown> {
  return key in obj
}

// null/undefined チェック
export function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined
}
```

## 9. 型定義の組織化

### 9.1 ファイル構成
```
src/types/
├── index.ts              # 全型定義のエクスポート
├── common.ts             # 共通型定義
├── api.ts                # API関連型
├── auth.ts               # 認証関連型
├── chat.ts               # チャット関連型
├── user.ts               # ユーザー関連型
├── subscription.ts       # サブスクリプション関連型
├── ui.ts                 # UI関連型
├── forms.ts              # フォーム関連型
├── utils.ts              # ユーティリティ型
└── guards.ts             # 型ガード関数
```

### 9.2 型定義のエクスポート戦略
```typescript
// types/index.ts
// 共通型
export * from './common'
export * from './api'

// ドメイン型
export * from './auth'
export * from './chat'
export * from './user'
export * from './subscription'

// UI型
export * from './ui'
export * from './forms'

// ユーティリティ
export * from './utils'
export * from './guards'

// デフォルトエクスポート（主要型のみ）
export type {
  User,
  Message,
  ChatSession,
  ApiResponse,
  SuccessResponse,
  ErrorResponse
} from './common'
```

## 5. 型定義リファクタリングタスク

### 5.1 即座に実行すべきタスク

#### 5.1.1 基本型定義の分離
- [ ] `src/types/index.ts` 作成
- [ ] Message型を共通ファイルに移動
- [ ] API関連型の定義
- [ ] 基本型エイリアスの定義

#### 5.1.2 コンポーネント型の整理
- [ ] ChatInterfaceProps型の定義
- [ ] コンポーネント分離時の型定義準備
- [ ] Props型の明示的定義

### 5.2 段階的リファクタリングタスク

#### 5.2.1 フェーズ1: 基本整理
- [ ] 現在のMessage型の拡張
- [ ] API通信型の統一
- [ ] エラー型の定義

#### 5.2.2 フェーズ2: コンポーネント分離対応
- [ ] 分離予定コンポーネントの型定義
- [ ] カスタムフックの型定義
- [ ] 状態管理型の整理

#### 5.2.3 フェーズ3: 将来拡張対応
- [ ] セッション管理型の準備
- [ ] ユーザー管理型の準備
- [ ] 認証関連型の準備

### 5.3 型定義ファイル構成（目標）

```
src/types/
├── index.ts              # 全型定義のエクスポート
├── common.ts             # 基本型・共通型
├── api.ts                # API関連型
├── chat.ts               # チャット関連型
├── components.ts         # コンポーネント型
└── hooks.ts              # カスタムフック型
```

### 5.4 実装優先度

#### 高優先度（即座に実行）
- Message型の共通化
- API型の定義
- 基本的なProps型定義

#### 中優先度（コンポーネント分離時）
- 分離コンポーネントの型定義
- カスタムフック型定義

#### 低優先度（将来拡張時）
- セッション・ユーザー管理型
- 高度な型ユーティリティ