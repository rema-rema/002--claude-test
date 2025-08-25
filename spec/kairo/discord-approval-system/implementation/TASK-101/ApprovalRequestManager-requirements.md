# TASK-101 ApprovalRequestManager TDD要件定義

## 実装日時
2025-08-25

## コンポーネント概要
ApprovalRequestManagerは、テスト失敗時の承認依頼ワークフローを管理する中核コンポーネントです。承認依頼の作成、状態管理、タイムアウト処理、承認応答処理を統合的に提供します。

## API仕様

### TypeScriptインターフェース定義

```typescript
// 承認依頼データ型
interface ApprovalRequest {
  id: string;                    // ユニークID (UUID)
  analysisId: string;            // TestFailureAnalyzer生成のID
  testName: string;              // 失敗したテスト名
  testFile: string;              // テストファイルパス
  errorMessage: string;          // エラーメッセージ
  errorCategory: string;         // エラーカテゴリ（UI_ELEMENT, TIMING等）
  confidence: number;            // 分析信頼度 (0.0-1.0)
  suggestions: string[];         // 修正提案リスト
  status: ApprovalStatus;        // 承認状態
  createdAt: Date;              // 作成日時
  expiresAt: Date;              // 有効期限（24時間後）
  discordThreadId?: string;     // DiscordスレッドID
  discordMessageId?: string;    // Discord承認依頼メッセージID
  approvedAt?: Date;            // 承認日時
  rejectedAt?: Date;            // 拒否日時
  responseUserId?: string;      // 承認/拒否したユーザーID
}

// 承認状態
enum ApprovalStatus {
  PENDING = 'PENDING',          // 承認待ち
  APPROVED = 'APPROVED',        // 承認済み
  REJECTED = 'REJECTED',        // 拒否済み
  EXPIRED = 'EXPIRED'           // タイムアウト
}

// 承認応答データ
interface ApprovalResponse {
  requestId: string;            // 承認依頼ID
  action: 'approve' | 'reject'; // アクション
  userId: string;               // 応答ユーザーID
  reason?: string;              // 承認/拒否理由（オプション）
}

// メインクラス
interface ApprovalRequestManager {
  // 承認依頼作成
  createRequest(analysisResult: AnalysisResult): Promise<ApprovalRequest>;
  
  // 承認依頼取得
  getRequest(requestId: string): Promise<ApprovalRequest | null>;
  
  // 全承認依頼取得（オプション：ステータスフィルタ）
  getAllRequests(status?: ApprovalStatus): Promise<ApprovalRequest[]>;
  
  // 承認応答処理
  processResponse(response: ApprovalResponse): Promise<ApprovalRequest>;
  
  // タイムアウト処理（期限切れ承認依頼の自動処理）
  processTimeouts(): Promise<ApprovalRequest[]>;
  
  // 承認依頼削除（クリーンアップ用）
  deleteRequest(requestId: string): Promise<boolean>;
  
  // Discord情報更新
  updateDiscordInfo(requestId: string, threadId: string, messageId: string): Promise<ApprovalRequest>;
}
```

## 機能要件

### REQ-101: 承認依頼作成機能
**Given**: TestFailureAnalyzerの分析結果を受け取る  
**When**: createRequest()を呼び出す  
**Then**: 以下を満たす承認依頼を生成する
- ユニークなID（UUID）を生成
- 24時間後の有効期限を設定
- 初期状態をPENDINGに設定
- 分析結果の全データを保持

### REQ-102: 承認依頼状態管理機能
**Given**: 作成済みの承認依頼  
**When**: 承認・拒否・タイムアウトが発生する  
**Then**: 状態を適切に更新し、関連データを記録する
- 承認時: APPROVED状態、承認日時、ユーザーID記録
- 拒否時: REJECTED状態、拒否日時、ユーザーID記録  
- タイムアウト時: EXPIRED状態に自動変更

### REQ-103: タイムアウト管理機能
**Given**: 24時間経過した承認依頼  
**When**: processTimeouts()を実行する  
**Then**: 期限切れの依頼をEXPIRED状態に変更する
- 期限チェック: expiresAt < 現在時刻
- 一括処理: 複数のタイムアウト依頼を同時処理
- 結果返却: 処理された依頼のリストを返す

### REQ-104: 承認応答処理機能  
**Given**: Discord経由の承認・拒否応答  
**When**: processResponse()を呼び出す  
**Then**: 承認依頼の状態を更新する
- 承認: PENDING → APPROVED
- 拒否: PENDING → REJECTED
- 応答者情報: ユーザーID、応答日時を記録
- 理由記録: オプションの承認/拒否理由を保存

### REQ-105: Discord連携情報管理
**Given**: Discord通知システムとの連携  
**When**: updateDiscordInfo()を呼び出す  
**Then**: Discord関連情報を承認依頼に関連付ける
- スレッドID: 承認用スレッドのID
- メッセージID: 承認依頼メッセージのID
- 後続処理: Claude Code連携での利用に備える

## 非機能要件

### NFR-101: パフォーマンス要件
- **応答時間**: 全API呼び出しが100ms以内で完了
- **同時処理**: 10件の承認依頼を並行処理可能  
- **メモリ使用量**: 1000件の承認依頼データを効率的に管理

### NFR-102: 信頼性要件
- **データ永続化**: メモリ内管理（将来DB拡張可能な設計）
- **エラー処理**: 全ての異常系で適切なエラー応答
- **ログ出力**: 重要な状態変更をログに記録

### NFR-103: 拡張性要件  
- **プラガブル設計**: 通知システム（Discord以外）への拡張対応
- **ストレージ抽象化**: メモリからDB移行への対応
- **承認フロー拡張**: 複数段階承認への拡張可能性

## テスト要件

### 正常系テストケース（5-7件）
- TC-101: 承認依頼正常作成
- TC-102: 承認応答正常処理
- TC-103: 拒否応答正常処理  
- TC-104: Discord情報更新
- TC-105: 全承認依頼取得
- TC-106: ステータスフィルタ取得
- TC-107: タイムアウト正常処理

### 異常系テストケース（5-7件）
- TC-201: 不正な分析結果入力
- TC-202: 存在しない承認依頼への応答
- TC-203: 重複承認応答の処理
- TC-204: 不正なApprovalResponse形式
- TC-205: タイムアウト処理中の例外
- TC-206: Discord情報更新失敗
- TC-207: メモリ不足時の処理

### 境界値テストケース（3-5件）
- TC-301: 24時間ちょうどでのタイムアウト
- TC-302: 最大同時承認依頼数（1000件）
- TC-303: 空の修正提案配列
- TC-304: 最大長のエラーメッセージ処理
- TC-305: UUID重複回避確認

## 実装制約

### 依存関係
- **必須**: crypto（UUID生成）
- **必須**: TestFailureAnalyzer（AnalysisResult型）
- **オプション**: logging（将来追加）

### ファイル配置
- **実装**: `discord-bot/src/components/ApprovalRequestManager.js`
- **テスト**: `discord-bot/src/tests/unit/ApprovalRequestManager.test.js`
- **型定義**: JSDocコメントで疑似TypeScript型定義

### 設計原則
- **単一責任**: 承認ワークフロー管理のみに特化
- **依存注入**: 外部サービス（Discord, Logger）は注入可能に設計
- **テスト容易性**: 全メソッドをモック・テスト可能に実装

## 次のステップ

この要件定義完了後、以下の順序で進行：
1. **testcases**: 詳細テストケース作成（15-20件目標）
2. **tdd-red**: 失敗テスト実装
3. **tdd-green**: 最小実装でテスト成功
4. **tdd-refactor**: コード品質向上

**目標**: TASK-001と同等の高品質実装（100%テスト成功率）を達成する。