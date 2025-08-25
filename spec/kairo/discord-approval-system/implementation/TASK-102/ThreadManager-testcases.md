# TASK-102: ThreadManager テストケース設計書

## 📋 **テスト設計概要**

- **総テストケース数**: 18ケース
- **テスト分類**: 正常動作6件 + 異常系6件 + 統合6件
- **実装アプローチ**: TDD (Test-Driven Development)
- **テストフレームワーク**: Jest + ES Modules
- **モック対象**: Discord.js Client, ApprovalRequestManager

## 🟢 **正常動作テストケース (6件)**

### **TC-102-001: 承認依頼スレッド正常作成**

```javascript
test('TC-102-001: 承認依頼スレッド正常作成', async () => {
  // 【テスト目的】: ApprovalRequest基盤でスレッドが正常作成される
  // 【テスト内容】: createApprovalThread()による完全なスレッド作成フロー
  // 【期待される動作】: Discord.js v14 Thread API統合とApprovalRequestManager連携動作
  // 🟢 REQ-102-001, REQ-102-002の基本機能確認

  const mockApprovalRequest = {
    id: 'approval-123',
    testName: 'should validate login form',
    errorMessage: 'locator("input#email") not found',
    fixSuggestions: ['セレクタを修正してください', '要素の待機処理を追加してください'],
    requesterUserId: 'user-456'
  };

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440 // 24時間
  });

  const result = await threadManager.createApprovalThread({
    approvalRequestId: mockApprovalRequest.id,
    testName: mockApprovalRequest.testName,
    errorSummary: mockApprovalRequest.errorMessage,
    fixSuggestions: mockApprovalRequest.fixSuggestions,
    requesterUserId: mockApprovalRequest.requesterUserId
  });

  // Discord Thread作成確認
  expect(result.success).toBe(true);
  expect(result.threadId).toMatch(/^[0-9]+$/); // Discord ID形式
  expect(result.messageId).toMatch(/^[0-9]+$/);
  expect(result.threadUrl).toContain('discord.com/channels');
  expect(result.createdAt).toBeInstanceOf(Date);

  // ApprovalRequestManager統合確認
  expect(mockApprovalManager.updateDiscordInfo).toHaveBeenCalledWith(
    mockApprovalRequest.id,
    result.threadId,
    result.messageId
  );

  // スレッド名フォーマット確認
  expect(mockDiscordClient.channels.threads.create).toHaveBeenCalledWith(
    expect.objectContaining({
      name: '🔧 修正作業: should validate login form',
      autoArchiveDuration: 1440,
      type: 'GUILD_PUBLIC_THREAD'
    })
  );
});
```

### **TC-102-002: 承認完了時自動アーカイブ**

```javascript
test('TC-102-002: 承認完了時自動アーカイブ', async () => {
  // 【テスト目的】: 承認完了時にスレッドが自動的にアーカイブされる
  // 【テスト内容】: onApprovalCompleted()イベント処理での自動アーカイブ
  // 【期待される動作】: 完了メッセージ送信後にスレッドアーカイブ実行
  // 🟢 REQ-102-003のライフサイクル管理確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  const mockApprovalRequest = {
    id: 'approval-123',
    testName: 'test name',
    discordThreadId: 'thread-456',
    status: 'APPROVED'
  };

  const mockApprovalResponse = {
    requestId: 'approval-123',
    approved: true,
    comment: '修正提案が適切です',
    processedAt: new Date(),
    success: true
  };

  // 承認完了イベント処理
  await threadManager.onApprovalCompleted(mockApprovalRequest, mockApprovalResponse);

  // 完了メッセージ送信確認
  expect(mockDiscordClient.channels.threads.send).toHaveBeenCalledWith(
    'thread-456',
    expect.stringContaining('🎉 **修正作業完了**')
  );
  expect(mockDiscordClient.channels.threads.send).toHaveBeenCalledWith(
    'thread-456',
    expect.stringContaining('✅ 承認')
  );
  expect(mockDiscordClient.channels.threads.send).toHaveBeenCalledWith(
    'thread-456',
    expect.stringContaining('修正提案が適切です')
  );

  // スレッドアーカイブ確認
  expect(mockDiscordClient.channels.threads.setArchived).toHaveBeenCalledWith(
    'thread-456',
    true,
    '承認完了のため自動アーカイブ'
  );
});
```

### **TC-102-003: 24時間自動アーカイブ設定**

```javascript
test('TC-102-003: 24時間自動アーカイブ設定', async () => {
  // 【テスト目的】: 24時間後のDiscord自動アーカイブ設定が正確
  // 【テスト内容】: autoArchiveDuration設定とDiscord API連携
  // 【期待される動作】: 1440分（24時間）での自動アーカイブ設定
  // 🟢 REQ-102-003の自動アーカイブ仕様確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440  // 24時間
  });

  await threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  });

  // Discord Thread作成時の自動アーカイブ設定確認
  expect(mockDiscordClient.channels.threads.create).toHaveBeenCalledWith(
    expect.objectContaining({
      autoArchiveDuration: 1440  // 24時間 = 1440分
    })
  );

  // 作成されたスレッドの設定確認
  const createdThread = await threadManager.getThread('thread-123');
  expect(createdThread.expiresAt.getTime() - createdThread.createdAt.getTime())
    .toBe(24 * 60 * 60 * 1000); // 24時間 = ミリ秒
});
```

### **TC-102-004: メッセージテンプレート生成**

```javascript
test('TC-102-004: メッセージテンプレート生成', async () => {
  // 【テスト目的】: スレッド初期メッセージのテンプレート生成確認
  // 【テスト内容】: buildInitialMessage()による動的メッセージ構築
  // 【期待される動作】: 承認依頼データを基にした適切なフォーマット生成
  // 🟢 REQ-102-005のメッセージテンプレート確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  const request = {
    approvalRequestId: 'approval-123',
    testName: 'should validate login form',
    errorSummary: 'locator("input#email") not found',
    fixSuggestions: [
      'セレクタを修正してください',
      '要素の待機処理を追加してください',
      'データテストIDを使用してください'
    ],
    requesterUserId: 'user-456'
  };

  const message = threadManager.buildInitialMessage(request);

  // メッセージフォーマット確認
  expect(message).toContain('🔧 **テスト修正依頼** - #approval-123');
  expect(message).toContain('**テスト名**: `should validate login form`');
  expect(message).toContain('**エラー概要**: locator("input#email") not found');
  
  // 修正提案リスト確認
  expect(message).toContain('• セレクタを修正してください');
  expect(message).toContain('• 要素の待機処理を追加してください');
  expect(message).toContain('• データテストIDを使用してください');
  
  // 操作方法確認
  expect(message).toContain('✅ 承認: `!approve approval-123 [コメント]`');
  expect(message).toContain('❌ 拒否: `!reject approval-123 [理由]`');
  
  // 依頼者メンション確認
  expect(message).toContain('🎯 **依頼者**: <@user-456>');
  
  // 期限表示確認
  expect(message).toContain('⏰ **自動期限**:');
  expect(message).toContain('(24時間後)');
});
```

### **TC-102-005: ApprovalRequestManager統合**

```javascript
test('TC-102-005: ApprovalRequestManager統合', async () => {
  // 【テスト目的】: MS-A1 ApprovalRequestManagerとの完全統合確認
  // 【テスト内容】: threadId/messageId双方向関連付け動作
  // 【期待される動作】: 両システム間での一貫したデータ同期
  // 🟢 REQ-102-004のApprovalRequestManager統合確認

  const mockApprovalManager = {
    updateDiscordInfo: jest.fn().mockResolvedValue(true),
    getRequest: jest.fn().mockResolvedValue({
      id: 'approval-123',
      testName: 'test',
      status: 'PENDING',
      discordThreadId: null,
      discordMessageId: null
    })
  };

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440,
    approvalManager: mockApprovalManager
  });

  // スレッド作成
  const result = await threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  });

  // ApprovalRequestManager統合確認
  expect(mockApprovalManager.updateDiscordInfo).toHaveBeenCalledWith(
    'approval-123',
    result.threadId,
    result.messageId
  );
  expect(mockApprovalManager.updateDiscordInfo).toHaveBeenCalledTimes(1);

  // ThreadManagerからApprovalRequestManagerのデータ取得確認
  const approvalRequest = await threadManager.getLinkedApprovalRequest('thread-456');
  expect(mockApprovalManager.getRequest).toHaveBeenCalledWith('approval-123');
  expect(approvalRequest.id).toBe('approval-123');
});
```

### **TC-102-006: スレッド状態管理**

```javascript
test('TC-102-006: スレッド状態管理', async () => {
  // 【テスト目的】: スレッド状態遷移とステータス管理の動作確認
  // 【テスト内容】: ACTIVE → ARCHIVED → LOCKED状態遷移
  // 【期待される動作】: 各状態での適切な操作制限と状態変更
  // 🟢 REQ-102-003のスレッドライフサイクル管理確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  // スレッド作成（ACTIVE状態）
  const result = await threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  });

  // 初期状態確認
  let thread = await threadManager.getThread(result.threadId);
  expect(thread.status).toBe('ACTIVE');
  expect(thread.archived).toBe(false);
  expect(thread.locked).toBe(false);

  // アーカイブ状態に変更
  await threadManager.updateThreadStatus(result.threadId, 'ARCHIVED');
  thread = await threadManager.getThread(result.threadId);
  expect(thread.status).toBe('ARCHIVED');
  expect(thread.archived).toBe(true);

  // ロック状態に変更
  await threadManager.updateThreadStatus(result.threadId, 'LOCKED');
  thread = await threadManager.getThread(result.threadId);
  expect(thread.status).toBe('LOCKED');
  expect(thread.locked).toBe(true);

  // Discord API呼び出し確認
  expect(mockDiscordClient.channels.threads.setArchived).toHaveBeenCalledWith(
    result.threadId,
    true
  );
  expect(mockDiscordClient.channels.threads.setLocked).toHaveBeenCalledWith(
    result.threadId,
    true
  );
});
```

## ⚠️ **異常系テストケース (6件)**

### **TC-102-101: Discord API エラー処理**

```javascript
test('TC-102-101: Discord API エラー処理', async () => {
  // 【テスト目的】: Discord API呼び出し失敗時のエラーハンドリング確認
  // 【テスト内容】: Rate Limit、Network Error時の適切なエラー処理
  // 【期待される動作】: 適切なエラーメッセージとリトライ機能
  // 🔴 REQ-102-006のエラーハンドリング確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  // Discord API エラーをモック
  mockDiscordClient.channels.threads.create.mockRejectedValue(
    new Error('Discord API Rate Limit Exceeded')
  );

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  })).rejects.toThrow('Discord API Rate Limit Exceeded');

  // エラーログ確認
  expect(console.error).toHaveBeenCalledWith(
    'Discord API エラー:',
    expect.any(Error)
  );
});
```

### **TC-102-102: 権限不足エラー処理**

```javascript
test('TC-102-102: 権限不足エラー処理', async () => {
  // 【テスト目的】: Discord権限不足時のエラーハンドリング
  // 【テスト内容】: CREATE_THREADS権限なし時の処理
  // 【期待される動作】: 権限エラーの適切な処理と代替手段提示
  // 🔴 REQ-102-006の権限エラー処理確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  mockDiscordClient.channels.threads.create.mockRejectedValue(
    new Error('Missing Permissions: CREATE_PUBLIC_THREADS')
  );

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  })).rejects.toThrow('Missing Permissions');
});
```

### **TC-102-103: チャンネル未発見エラー**

```javascript
test('TC-102-103: チャンネル未発見エラー', async () => {
  // 【テスト目的】: 指定チャンネルが存在しない場合のエラー処理
  // 【テスト内容】: 無効なchannelIdでのスレッド作成試行
  // 【期待される動作】: チャンネル存在チェックとエラーメッセージ
  // 🔴 REQ-102-006のチャンネル検証確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'invalid-channel-id',
    autoArchiveDuration: 1440
  });

  mockDiscordClient.channels.cache.get.mockReturnValue(null);

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  })).rejects.toThrow('チャンネルが見つかりません');
});
```

### **TC-102-104: スレッド数制限エラー**

```javascript
test('TC-102-104: スレッド数制限エラー', async () => {
  // 【テスト目的】: チャンネル内スレッド数上限到達時の処理
  // 【テスト内容】: Discordのスレッド数制限に達した場合
  // 【期待される動作】: 制限エラーの検出と古いスレッドのアーカイブ提案
  // 🔴 REQ-102-006のスレッド制限処理確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  mockDiscordClient.channels.threads.create.mockRejectedValue(
    new Error('Maximum number of threads reached')
  );

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  })).rejects.toThrow('Maximum number of threads reached');
});
```

### **TC-102-105: ネットワークエラー処理**

```javascript
test('TC-102-105: ネットワークエラー処理', async () => {
  // 【テスト目的】: ネットワーク接続エラー時の堅牢性確認
  // 【テスト内容】: ネットワーク切断時のリトライ機能
  // 【期待される動作】: 自動リトライとタイムアウト処理
  // 🔴 REQ-102-006のネットワークエラー処理確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  mockDiscordClient.channels.threads.create.mockRejectedValue(
    new Error('ENOTFOUND discord.com')
  );

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  })).rejects.toThrow('ENOTFOUND discord.com');
});
```

### **TC-102-106: 不正入力値エラー**

```javascript
test('TC-102-106: 不正入力値エラー', async () => {
  // 【テスト目的】: 入力パラメータ検証とバリデーションエラー
  // 【テスト内容】: null、undefined、型不整合の入力値処理
  // 【期待される動作】: 適切なバリデーションエラーメッセージ
  // 🔴 REQ-102-006の入力値検証確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  // 必須フィールド欠如テスト
  await expect(threadManager.createApprovalThread({
    approvalRequestId: null,
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  })).rejects.toThrow('承認依頼IDは必須です');

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: null,
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'  
  })).rejects.toThrow('テスト名は必須です');

  await expect(threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: 'not-array',
    requesterUserId: 'user-456'
  })).rejects.toThrow('修正提案は配列である必要があります');
});
```

## 🔗 **統合テストケース (6件)**

### **TC-102-201: ApprovalRequestManager完全統合**

```javascript
test('TC-102-201: ApprovalRequestManager完全統合', async () => {
  // 【テスト目的】: MS-A1 ApprovalRequestManagerとの完全統合動作確認
  // 【テスト内容】: 承認依頼作成→スレッド作成→承認完了の全フロー
  // 【期待される動作】: 両システム間でのデータ一貫性とイベント連携
  // 🟡 REQ-102-004の統合機能確認

  // ApprovalRequestManagerの実インスタンス使用
  const realApprovalManager = new ApprovalRequestManager();
  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440,
    approvalManager: realApprovalManager
  });

  // 1. 承認依頼作成
  const approvalRequest = await realApprovalManager.createRequest(
    'should validate login form',
    'locator("input#email") not found',
    ['セレクタを修正してください'],
    'user-456'
  );

  // 2. スレッド作成
  const threadResult = await threadManager.createApprovalThread({
    approvalRequestId: approvalRequest.id,
    testName: approvalRequest.testName,
    errorSummary: approvalRequest.errorMessage,
    fixSuggestions: approvalRequest.fixSuggestions,
    requesterUserId: approvalRequest.requesterUserId
  });

  // 3. ApprovalRequestManagerでのDiscord情報更新確認
  const updatedRequest = await realApprovalManager.getRequest(approvalRequest.id);
  expect(updatedRequest.discordThreadId).toBe(threadResult.threadId);
  expect(updatedRequest.discordMessageId).toBe(threadResult.messageId);

  // 4. 承認処理
  const approvalResponse = await realApprovalManager.processResponse(
    approvalRequest.id,
    true,
    '修正提案が適切です'
  );

  // 5. スレッド自動アーカイブ確認
  await threadManager.onApprovalCompleted(updatedRequest, approvalResponse);
  expect(mockDiscordClient.channels.threads.setArchived).toHaveBeenCalledWith(
    threadResult.threadId,
    true,
    expect.any(String)
  );
});
```

### **TC-102-202: Discord.js v14統合テスト**

```javascript
test('TC-102-202: Discord.js v14統合テスト', async () => {
  // 【テスト目的】: Discord.js v14の最新Thread API統合確認
  // 【テスト内容】: 実際のDiscord.js APIとの互換性テスト
  // 【期待される動作】: v14 Thread機能の完全利用
  // 🟡 REQ-102-001のDiscord.js統合確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  await threadManager.createApprovalThread({
    approvalRequestId: 'approval-123',
    testName: 'test',
    errorSummary: 'error',
    fixSuggestions: ['fix'],
    requesterUserId: 'user-456'
  });

  // Discord.js v14 API呼び出し確認
  expect(mockDiscordClient.channels.threads.create).toHaveBeenCalledWith(
    expect.objectContaining({
      name: expect.any(String),
      autoArchiveDuration: 1440,
      type: 'GUILD_PUBLIC_THREAD',
      reason: expect.stringContaining('承認依頼スレッド作成')
    })
  );

  // Thread.send API使用確認
  expect(mockDiscordClient.channels.threads.send).toHaveBeenCalledWith(
    expect.any(String),
    expect.stringContaining('🔧 **テスト修正依頼**')
  );
});
```

### **TC-102-203: 承認フロー E2E テスト**

```javascript
test('TC-102-203: 承認フロー E2E テスト', async () => {
  // 【テスト目的】: 承認依頼からスレッド完了までの完全E2Eフロー
  // 【テスト内容】: 実際のユーザー操作シナリオでの動作確認
  // 【期待される動作】: 全ステップでの適切なユーザー体験
  // 🟡 全REQの統合動作確認

  const realApprovalManager = new ApprovalRequestManager();
  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440,
    approvalManager: realApprovalManager
  });

  // E2Eシナリオ: テスト失敗 → 承認依頼 → スレッド作成 → 議論 → 承認 → 完了
  
  // Step 1: 承認依頼作成
  const request = await realApprovalManager.createRequest(
    'should validate user registration',
    'Element not found: button[type="submit"]',
    ['CSSセレクタの修正', 'データテストIDの追加', '待機処理の改善'],
    'dev-user-123'
  );

  // Step 2: スレッド作成
  const thread = await threadManager.createApprovalThread({
    approvalRequestId: request.id,
    testName: request.testName,
    errorSummary: request.errorMessage,
    fixSuggestions: request.fixSuggestions,
    requesterUserId: request.requesterUserId
  });

  // Step 3: スレッド内での議論シミュレーション
  await threadManager.sendMessage(
    thread.threadId,
    'セレクタを `button[data-testid="submit-btn"]` に変更しました。'
  );
  
  await threadManager.sendMessage(
    thread.threadId,
    '変更確認済み。承認をお願いします。'
  );

  // Step 4: 承認処理
  const response = await realApprovalManager.processResponse(
    request.id,
    true,
    'セレクタ修正により問題解決確認済み'
  );

  // Step 5: スレッド自動完了
  const updatedRequest = await realApprovalManager.getRequest(request.id);
  await threadManager.onApprovalCompleted(updatedRequest, response);

  // E2E結果確認
  expect(updatedRequest.status).toBe('APPROVED');
  expect(response.success).toBe(true);
  expect(mockDiscordClient.channels.threads.setArchived).toHaveBeenCalled();
});
```

### **TC-102-204: 複数スレッド同時管理**

```javascript
test('TC-102-204: 複数スレッド同時管理', async () => {
  // 【テスト目的】: 複数の承認依頼スレッドの同時管理能力確認
  // 【テスト内容】: 10件の同時承認依頼でのスレッド管理
  // 【期待される動作】: 各スレッドの独立した状態管理
  // 🟡 REQ-102-003のスケーラビリティ確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  // 10件の同時承認依頼スレッド作成
  const promises = [];
  for (let i = 0; i < 10; i++) {
    promises.push(threadManager.createApprovalThread({
      approvalRequestId: `approval-${i}`,
      testName: `test-${i}`,
      errorSummary: `error-${i}`,
      fixSuggestions: [`fix-${i}`],
      requesterUserId: `user-${i}`
    }));
  }

  const results = await Promise.all(promises);

  // 全スレッド作成成功確認
  expect(results).toHaveLength(10);
  results.forEach((result, index) => {
    expect(result.success).toBe(true);
    expect(result.threadId).toBeTruthy();
  });

  // 各スレッドの独立性確認
  const allThreads = await threadManager.getAllThreads();
  expect(allThreads).toHaveLength(10);
  
  const threadIds = results.map(r => r.threadId);
  const uniqueIds = [...new Set(threadIds)];
  expect(uniqueIds).toHaveLength(10); // 重複なし確認
});
```

### **TC-102-205: 長期間スレッド管理**

```javascript
test('TC-102-205: 長期間スレッド管理', async () => {
  // 【テスト目的】: 24時間を超える長期スレッド管理の安定性
  // 【テスト内容】: タイムアウト境界での状態管理確認
  // 【期待される動作】: 長期間にわたる安定したスレッド状態保持
  // 🟡 REQ-102-003の長期管理確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440
  });

  const result = await threadManager.createApprovalThread({
    approvalRequestId: 'approval-long-term',
    testName: 'long term test',
    errorSummary: 'complex error',
    fixSuggestions: ['complex fix'],
    requesterUserId: 'user-456'
  });

  // 時間経過シミュレーション（23時間55分後）
  const almostExpired = new Date(Date.now() + 23 * 60 * 60 * 1000 + 55 * 60 * 1000);
  jest.setSystemTime(almostExpired);

  let thread = await threadManager.getThread(result.threadId);
  expect(thread.status).toBe('ACTIVE'); // まだアクティブ

  // 時間経過シミュレーション（24時間5分後）
  const expired = new Date(Date.now() + 24 * 60 * 60 * 1000 + 5 * 60 * 1000);
  jest.setSystemTime(expired);

  // Discordの自動アーカイブシミュレーション
  await threadManager.processExpiredThreads();

  thread = await threadManager.getThread(result.threadId);
  expect(thread.status).toBe('ARCHIVED'); // 自動アーカイブ済み
});
```

### **TC-102-206: エラー復旧・再試行テスト**

```javascript
test('TC-102-206: エラー復旧・再試行テスト', async () => {
  // 【テスト目的】: 一時的エラーからの自動復旧とリトライ機能
  // 【テスト内容】: ネットワーク障害からの復旧シナリオ
  // 【期待される動作】: 自動リトライによる処理継続
  // 🟡 REQ-102-006のエラー復旧確認

  const threadManager = new ThreadManager({
    client: mockDiscordClient,
    channelId: 'channel-789',
    autoArchiveDuration: 1440,
    retryAttempts: 3,
    retryDelay: 1000
  });

  // 最初の2回は失敗、3回目で成功のシナリオ
  let attempt = 0;
  mockDiscordClient.channels.threads.create.mockImplementation(() => {
    attempt++;
    if (attempt <= 2) {
      return Promise.reject(new Error('Temporary network error'));
    }
    return Promise.resolve({
      id: 'thread-456',
      name: '🔧 修正作業: test',
      send: jest.fn().mockResolvedValue({ id: 'message-789' })
    });
  });

  const result = await threadManager.createApprovalThread({
    approvalRequestId: 'approval-retry-test',
    testName: 'retry test',
    errorSummary: 'test error',
    fixSuggestions: ['test fix'],
    requesterUserId: 'user-456'
  });

  // リトライ成功確認
  expect(result.success).toBe(true);
  expect(result.threadId).toBe('thread-456');
  expect(attempt).toBe(3); // 3回目で成功

  // リトライログ確認
  expect(console.warn).toHaveBeenCalledWith(
    'スレッド作成リトライ中 (1/3):',
    expect.any(Error)
  );
  expect(console.warn).toHaveBeenCalledWith(
    'スレッド作成リトライ中 (2/3):',
    expect.any(Error)
  );
});
```

## 📁 **テスト環境設定**

### **Jest設定ファイル**

```javascript
// jest.setup.js 追加設定
import { jest } from '@jest/globals';

// Discord.js モック設定
const mockDiscordClient = {
  channels: {
    cache: {
      get: jest.fn(),
    },
    threads: {
      create: jest.fn(),
      send: jest.fn(),
      setArchived: jest.fn(),
      setLocked: jest.fn(),
      fetch: jest.fn()
    }
  }
};

global.mockDiscordClient = mockDiscordClient;

// ApprovalRequestManager モック
const mockApprovalManager = {
  updateDiscordInfo: jest.fn(),
  getRequest: jest.fn(),
  processResponse: jest.fn()
};

global.mockApprovalManager = mockApprovalManager;

// 時間操作用
global.jest = jest;

beforeEach(() => {
  jest.clearAllMocks();
  jest.useRealTimers();
});
```

### **テストデータファクトリー**

```javascript
// test-factories.js
export const createMockApprovalRequest = (overrides = {}) => ({
  id: 'approval-test-123',
  testName: 'should validate form',
  errorMessage: 'Element not found',
  fixSuggestions: ['Fix selector', 'Add wait'],
  requesterUserId: 'user-456',
  status: 'PENDING',
  createdAt: new Date(),
  expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
  discordThreadId: null,
  discordMessageId: null,
  ...overrides
});

export const createMockThreadResponse = (overrides = {}) => ({
  threadId: 'thread-456',
  messageId: 'message-789',
  threadUrl: 'https://discord.com/channels/guild/channel/thread',
  success: true,
  createdAt: new Date(),
  ...overrides
});
```

---

**テストケース設計完了**: 18テストケース（正常6 + 異常6 + 統合6）でThreadManager完全テストを実現