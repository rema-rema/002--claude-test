# TASK-102: ThreadManager要件定義書

## 📋 **基本情報**

- **タスクID**: TASK-102
- **タスク名**: ThreadManager実装
- **担当トラック**: Track A (Discord統合トラック)
- **依存関係**: MS-A1 (TASK-101: ApprovalRequestManager) ✅ 完了
- **実装日**: 2025-08-25
- **TDDアプローチ**: Requirements → Testcases → Red → Green → Refactor

## 🎯 **概要**

Discord.js v14を活用したスレッド管理システムを実装し、承認依頼専用のスレッドを作成・管理する。ApprovalRequestManagerと密結合し、24時間自動アーカイブとライフサイクル管理を提供する。

## 📚 **要件仕様**

### **REQ-102-001: コアスレッド管理機能**

Discord.js v14 Thread APIを活用したスレッド管理機能を実装する。

```typescript
interface ThreadManagerOptions {
  client: Client;              // Discord.js Client instance
  channelId: string;          // 親チャンネルID
  autoArchiveDuration: number; // 自動アーカイブ時間（分）
}

interface ApprovalThread {
  id: string;                 // Discord Thread ID
  parentId: string;           // 親チャンネルID
  name: string;               // スレッド名
  ownerId: string;            // スレッド作成者ID
  createdAt: Date;            // 作成日時
  expiresAt: Date;            // 自動アーカイブ予定日時
  archived: boolean;          // アーカイブ状態
  locked: boolean;            // ロック状態
  approvalRequestId?: string; // 関連承認依頼ID（MS-A1統合）
}
```

### **REQ-102-002: 承認依頼専用スレッド作成**

ApprovalRequestManagerからの承認依頼データを基に専用スレッドを作成する。

```typescript
interface CreateThreadRequest {
  approvalRequestId: string;    // MS-A1: ApprovalRequestManager.id
  testName: string;            // テスト名
  errorSummary: string;        // エラー概要
  fixSuggestions: string[];    // 修正提案
  requesterUserId: string;     // 依頼者ID
  urgency?: 'LOW' | 'MEDIUM' | 'HIGH'; // 緊急度
}

interface CreateThreadResponse {
  threadId: string;           // 作成されたスレッドID
  messageId: string;          // 初期メッセージID
  threadUrl: string;          // スレッドURL
  success: boolean;           // 作成成功フラグ
  createdAt: Date;           // 作成日時
}
```

### **REQ-102-003: スレッドライフサイクル管理**

24時間自動アーカイブとスレッド状態管理を実装する。

**自動アーカイブ仕様**:
- **アーカイブ時間**: 24時間（1440分）
- **アーカイブ条件**: 最後のメッセージから24時間経過
- **手動アーカイブ**: 承認完了時に即座にアーカイブ可能
- **再オープン**: アーカイブ後も再オープン可能

**スレッド状態管理**:
```typescript
enum ThreadStatus {
  ACTIVE = 'ACTIVE',           // アクティブ状態
  ARCHIVED = 'ARCHIVED',       // アーカイブ状態
  LOCKED = 'LOCKED',           // ロック状態
  DELETED = 'DELETED'          // 削除状態
}
```

### **REQ-102-004: ApprovalRequestManager統合**

MS-A1で実装されたApprovalRequestManagerとの完全統合を実現する。

**統合ポイント**:
1. **スレッド作成時**: ApprovalRequestに`threadId`を関連付け
2. **メッセージ投稿時**: ApprovalRequestに`messageId`を関連付け
3. **承認完了時**: スレッドを自動アーカイブ
4. **タイムアウト時**: 承認期限切れと連動してスレッド処理

```typescript
// MS-A1統合例
async createApprovalThread(approvalRequest: ApprovalRequest): Promise<CreateThreadResponse> {
  // 1. Discord スレッド作成
  const thread = await this.createThread({...});
  
  // 2. ApprovalRequestManager に threadId を関連付け
  await this.approvalManager.updateDiscordInfo(
    approvalRequest.id,
    thread.id,
    initialMessage.id
  );
  
  return response;
}
```

### **REQ-102-005: メッセージテンプレート**

スレッド内メッセージの統一フォーマットを定義する。

**初期メッセージテンプレート**:
```
🔧 **テスト修正依頼** - #{approvalRequestId}

**テスト名**: `{testName}`
**エラー概要**: {errorSummary}

**修正提案**:
{fixSuggestions.map(s => `• ${s}`).join('\n')}

**操作方法**:
✅ 承認: `!approve {approvalRequestId} [コメント]`
❌ 拒否: `!reject {approvalRequestId} [理由]`
📝 進捗: このスレッド内で作業進捗を報告してください

⏰ **自動期限**: {expiresAt} (24時間後)
🎯 **依頼者**: <@{requesterUserId}>
```

**完了メッセージテンプレート**:
```
🎉 **修正作業完了** - #{approvalRequestId}

**結果**: {approved ? '✅ 承認' : '❌ 拒否'}
**処理時間**: {processTime}
**完了理由**: {comment || 'コメントなし'}

このスレッドは自動的にアーカイブされます。
```

### **REQ-102-006: エラーハンドリング**

Discord API制限とネットワークエラーに対する堅牢な処理を実装する。

**Discord API制限対応**:
- **Rate Limit**: 自動リトライ機能
- **Permission**: 権限エラー時の適切な処理
- **Channel Limit**: チャンネル内スレッド数制限対応

**エラー分類**:
```typescript
enum ThreadError {
  DISCORD_API_ERROR = 'DISCORD_API_ERROR',           // Discord API エラー
  PERMISSION_DENIED = 'PERMISSION_DENIED',           // 権限エラー
  CHANNEL_NOT_FOUND = 'CHANNEL_NOT_FOUND',          // チャンネル未発見
  THREAD_LIMIT_EXCEEDED = 'THREAD_LIMIT_EXCEEDED',  // スレッド数制限
  NETWORK_ERROR = 'NETWORK_ERROR',                  // ネットワークエラー
  VALIDATION_ERROR = 'VALIDATION_ERROR'             // 入力値エラー
}
```

## 🏗️ **実装設計**

### **クラス構造**

```typescript
export class ThreadManager {
  private client: Client;
  private channelId: string;
  private autoArchiveDuration: number;
  private approvalManager: ApprovalRequestManager;  // MS-A1統合
  private activeThreads: Map<string, ApprovalThread>;

  constructor(options: ThreadManagerOptions);
  
  // コア機能
  async createApprovalThread(request: CreateThreadRequest): Promise<CreateThreadResponse>;
  async archiveThread(threadId: string, reason?: string): Promise<boolean>;
  async deleteThread(threadId: string): Promise<boolean>;
  
  // スレッド管理
  async getThread(threadId: string): Promise<ApprovalThread | null>;
  async getAllThreads(options?: ThreadFilterOptions): Promise<ApprovalThread[]>;
  async updateThreadStatus(threadId: string, status: ThreadStatus): Promise<boolean>;
  
  // メッセージ管理
  async sendMessage(threadId: string, content: string): Promise<Message>;
  async editMessage(threadId: string, messageId: string, content: string): Promise<Message>;
  
  // イベント処理
  async onApprovalCompleted(approvalRequestId: string): Promise<void>;
  async onApprovalExpired(approvalRequestId: string): Promise<void>;
  
  // 内部メソッド
  private buildThreadName(testName: string): string;
  private buildInitialMessage(request: CreateThreadRequest): string;
  private buildCompletionMessage(approval: ApprovalResponse): string;
  private validateThreadPermissions(channelId: string): Promise<boolean>;
}
```

### **統合インターフェース**

```typescript
// ApprovalRequestManager イベント連携
interface ApprovalEventListener {
  onApprovalCreated(approval: ApprovalRequest): Promise<void>;
  onApprovalCompleted(approval: ApprovalRequest, response: ApprovalResponse): Promise<void>;
  onApprovalExpired(approval: ApprovalRequest): Promise<void>;
}

// ThreadManager が ApprovalRequestManager のイベントを監視
export class ThreadManager implements ApprovalEventListener {
  async onApprovalCreated(approval: ApprovalRequest): Promise<void> {
    // 承認依頼作成時に自動でスレッド作成
    const thread = await this.createApprovalThread({
      approvalRequestId: approval.id,
      testName: approval.testName,
      errorSummary: approval.errorMessage,
      fixSuggestions: approval.fixSuggestions,
      requesterUserId: approval.requesterUserId
    });
  }
  
  async onApprovalCompleted(approval: ApprovalRequest, response: ApprovalResponse): Promise<void> {
    // 承認完了時にスレッドをアーカイブ
    await this.archiveThread(approval.discordThreadId!, response.comment);
  }
}
```

## 🧪 **テスト要件**

### **単体テスト (6テストケース)**

1. **TC-102-001**: スレッド正常作成
   - Discord.js v14 Thread API 正常動作確認
   - ApprovalRequest統合確認

2. **TC-102-002**: 承認完了時自動アーカイブ  
   - 承認完了イベント受信時の自動アーカイブ
   - 完了メッセージ送信確認

3. **TC-102-003**: 24時間自動アーカイブ
   - 24時間後の自動アーカイブ動作
   - タイムアウト精度確認

4. **TC-102-004**: メッセージテンプレート生成
   - 初期メッセージフォーマット確認
   - 動的データ挿入確認

5. **TC-102-005**: ApprovalRequestManager統合
   - threadId/messageId 関連付け確認
   - 双方向同期確認

6. **TC-102-006**: スレッド状態管理
   - ACTIVE/ARCHIVED/LOCKED状態遷移
   - 状態変更イベント処理

### **異常系テスト (6テストケース)**

1. **TC-102-101**: Discord API エラー処理
2. **TC-102-102**: 権限不足エラー処理  
3. **TC-102-103**: チャンネル未発見エラー
4. **TC-102-104**: スレッド数制限エラー
5. **TC-102-105**: ネットワークエラー処理
6. **TC-102-106**: 不正入力値エラー

### **統合テスト (6テストケース)**

1. **TC-102-201**: ApprovalRequestManager完全統合
2. **TC-102-202**: Discord.js v14統合テスト
3. **TC-102-203**: 承認フロー E2E テスト
4. **TC-102-204**: 複数スレッド同時管理
5. **TC-102-205**: 長期間スレッド管理
6. **TC-102-206**: エラー復旧・再試行テスト

## 📁 **成果物構成**

```
docs/implementation/TASK-102/
├── ThreadManager-requirements.md     # 本ファイル
├── ThreadManager-testcases.md        # テストケース設計
└── ThreadManager-integration.md      # ApprovalRequestManager統合仕様

discord-bot/src/components/
└── ThreadManager.js                  # 実装ファイル

discord-bot/src/tests/unit/
└── ThreadManager.test.js             # テストファイル
```

## 🔗 **依存関係**

### **入力依存 (MS-A1成果物)**
- `ApprovalRequestManager.js` ✅ 完成
- `ApprovalRequest`型定義 ✅ 完成  
- `ApprovalStatus`列挙型 ✅ 完成
- `ApprovalResponse`型定義 ✅ 完成

### **外部依存**
- **Discord.js v14**: Thread API
- **Node.js**: 18+ (ES Modules対応)
- **Jest**: テストフレームワーク

### **出力成果物 (MS-A3向け)**
- ThreadManager統合インターフェース
- スレッドライフサイクルイベント
- Discord関連メタデータ管理

---

**実装準備完了**: MS-A1 (ApprovalRequestManager) 完成により、TASK-102実装開始可能