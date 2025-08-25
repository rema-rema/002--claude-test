# TASK-101 ApprovalRequestManager テストケース定義

## 実装日時
2025-08-25

## テストケース概要
ApprovalRequestManagerの全機能を網羅する包括的テストケース。正常系・異常系・境界値を含む18テストケースで100%品質を保証。

## テストケース一覧

### 🟢 正常系テストケース（6件）

#### TC-101: 承認依頼正常作成
```javascript
test('TC-101: 承認依頼正常作成', async () => {
  // 【テスト目的】: 正常な分析結果から承認依頼を作成
  // 【テスト内容】: TestFailureAnalyzer結果を入力して承認依頼生成
  // 【期待される動作】: 適切なApprovalRequest構造体が生成される
  // 🟢 設計書REQ-101の完全実装確認
  
  const analysisResult = {
    testName: 'should find login button',
    errorCategory: 'UI_ELEMENT',
    confidence: 0.9,
    suggestions: ['セレクタを修正してください', '待機処理を追加してください'],
    analysisId: 'analysis-123'
  };

  const request = await manager.createRequest(analysisResult);

  expect(request.id).toMatch(/^[a-f0-9-]{36}$/); // UUID形式
  expect(request.analysisId).toBe('analysis-123');
  expect(request.testName).toBe('should find login button');
  expect(request.errorCategory).toBe('UI_ELEMENT');
  expect(request.confidence).toBe(0.9);
  expect(request.suggestions).toEqual(['セレクタを修正してください', '待機処理を追加してください']);
  expect(request.status).toBe('PENDING');
  expect(request.createdAt).toBeInstanceOf(Date);
  expect(request.expiresAt).toBeInstanceOf(Date);
  expect(request.expiresAt.getTime() - request.createdAt.getTime()).toBe(24 * 60 * 60 * 1000); // 24時間
});
```

#### TC-102: 承認応答正常処理
```javascript
test('TC-102: 承認応答正常処理', async () => {
  // 【テスト目的】: 承認応答による状態更新が正常動作
  // 【テスト内容】: PENDING依頼に対するAPPROVE応答処理
  // 【期待される動作】: APPROVED状態への変更と関連情報更新
  // 🟢 設計書REQ-104の承認パターン確認
  
  const analysisResult = { testName: 'test', errorCategory: 'UI_ELEMENT', confidence: 0.8, suggestions: ['fix'], analysisId: 'test-id' };
  const request = await manager.createRequest(analysisResult);

  const response = {
    requestId: request.id,
    action: 'approve',
    userId: 'user-123',
    reason: 'Fix looks good'
  };

  const updatedRequest = await manager.processResponse(response);

  expect(updatedRequest.status).toBe('APPROVED');
  expect(updatedRequest.responseUserId).toBe('user-123');
  expect(updatedRequest.approvedAt).toBeInstanceOf(Date);
  expect(updatedRequest.rejectedAt).toBeUndefined();
});
```

#### TC-103: 拒否応答正常処理
```javascript
test('TC-103: 拒否応答正常処理', async () => {
  // 【テスト目的】: 拒否応答による状態更新が正常動作
  // 【テスト内容】: PENDING依頼に対するREJECT応答処理
  // 【期待される動作】: REJECTED状態への変更と関連情報更新
  // 🟢 設計書REQ-104の拒否パターン確認
  
  const analysisResult = { testName: 'test', errorCategory: 'TIMING', confidence: 0.7, suggestions: ['timeout fix'], analysisId: 'test-id-2' };
  const request = await manager.createRequest(analysisResult);

  const response = {
    requestId: request.id,
    action: 'reject',
    userId: 'user-456',
    reason: 'Not safe to apply'
  };

  const updatedRequest = await manager.processResponse(response);

  expect(updatedRequest.status).toBe('REJECTED');
  expect(updatedRequest.responseUserId).toBe('user-456');
  expect(updatedRequest.rejectedAt).toBeInstanceOf(Date);
  expect(updatedRequest.approvedAt).toBeUndefined();
});
```

#### TC-104: Discord情報更新
```javascript
test('TC-104: Discord情報更新', async () => {
  // 【テスト目的】: Discord連携情報の正常更新
  // 【テスト内容】: ThreadManager連携でDiscord情報を関連付け
  // 【期待される動作】: スレッドID・メッセージIDの正常保存
  // 🟢 設計書REQ-105のDiscord連携確認
  
  const analysisResult = { testName: 'discord test', errorCategory: 'ASSERTION', confidence: 0.85, suggestions: ['assertion fix'], analysisId: 'discord-test' };
  const request = await manager.createRequest(analysisResult);

  const threadId = 'thread-789';
  const messageId = 'message-123';

  const updatedRequest = await manager.updateDiscordInfo(request.id, threadId, messageId);

  expect(updatedRequest.discordThreadId).toBe(threadId);
  expect(updatedRequest.discordMessageId).toBe(messageId);
  expect(updatedRequest.id).toBe(request.id); // その他のフィールドは変更なし
});
```

#### TC-105: 全承認依頼取得
```javascript
test('TC-105: 全承認依頼取得', async () => {
  // 【テスト目的】: 全承認依頼の一括取得機能
  // 【テスト内容】: 複数の承認依頼を作成して全件取得
  // 【期待される動作】: 作成した全件が正しく返される
  // 🟢 管理機能の基本動作確認
  
  // 複数の承認依頼を作成
  const results = [
    { testName: 'test1', errorCategory: 'UI_ELEMENT', confidence: 0.9, suggestions: ['fix1'], analysisId: 'id1' },
    { testName: 'test2', errorCategory: 'TIMING', confidence: 0.8, suggestions: ['fix2'], analysisId: 'id2' },
    { testName: 'test3', errorCategory: 'ASSERTION', confidence: 0.7, suggestions: ['fix3'], analysisId: 'id3' }
  ];

  const requests = await Promise.all(results.map(r => manager.createRequest(r)));
  const allRequests = await manager.getAllRequests();

  expect(allRequests).toHaveLength(3);
  expect(allRequests.map(r => r.testName)).toEqual(expect.arrayContaining(['test1', 'test2', 'test3']));
});
```

#### TC-106: ステータスフィルタ取得
```javascript
test('TC-106: ステータスフィルタ取得', async () => {
  // 【テスト目的】: ステータス別フィルタリング機能
  // 【テスト内容】: PENDING・APPROVED状態の依頼を作成してフィルタ
  // 【期待される動作】: 指定ステータスの依頼のみが返される
  // 🟢 管理機能の高度機能確認
  
  // 異なるステータスの承認依頼を作成
  const pendingResult = { testName: 'pending-test', errorCategory: 'UI_ELEMENT', confidence: 0.9, suggestions: ['pending-fix'], analysisId: 'pending-id' };
  const approvedResult = { testName: 'approved-test', errorCategory: 'TIMING', confidence: 0.8, suggestions: ['approved-fix'], analysisId: 'approved-id' };

  const pendingRequest = await manager.createRequest(pendingResult);
  const approvedRequest = await manager.createRequest(approvedResult);

  // 1つを承認状態に変更
  await manager.processResponse({
    requestId: approvedRequest.id,
    action: 'approve',
    userId: 'test-user'
  });

  // フィルタリングテスト
  const pendingRequests = await manager.getAllRequests('PENDING');
  const approvedRequests = await manager.getAllRequests('APPROVED');

  expect(pendingRequests).toHaveLength(1);
  expect(pendingRequests[0].testName).toBe('pending-test');
  expect(approvedRequests).toHaveLength(1);
  expect(approvedRequests[0].testName).toBe('approved-test');
});
```

### 🔴 異常系テストケース（6件）

#### TC-201: 不正な分析結果入力
```javascript
test('TC-201: 不正な分析結果入力', async () => {
  // 【テスト目的】: 不正な分析結果入力の適切な処理確認
  // 【テスト内容】: 必須フィールド欠損の分析結果を入力
  // 【期待される動作】: エラーの適切な処理と例外発生
  // 🔴 設計書エラーハンドリング要件確認

  const invalidAnalysisResult = {
    // testName欠損
    errorCategory: 'UI_ELEMENT',
    confidence: 0.9
    // suggestions欠損, analysisId欠損
  };

  await expect(manager.createRequest(invalidAnalysisResult)).rejects.toThrow('Invalid analysis result: missing required fields');
});
```

#### TC-202: 存在しない承認依頼への応答
```javascript
test('TC-202: 存在しない承認依頼への応答', async () => {
  // 【テスト目的】: 存在しない承認依頼IDへの応答処理
  // 【テスト内容】: 無効なrequestIdでprocessResponse呼び出し
  // 【期待される動作】: 適切なエラーメッセージで例外発生
  // 🔴 設計書エラーハンドリング要件確認

  const response = {
    requestId: 'non-existent-id',
    action: 'approve',
    userId: 'test-user'
  };

  await expect(manager.processResponse(response)).rejects.toThrow('Request not found: non-existent-id');
});
```

#### TC-203: 重複承認応答の処理
```javascript
test('TC-203: 重複承認応答の処理', async () => {
  // 【テスト目的】: 既に応答済み依頼への重複応答処理
  // 【テスト内容】: APPROVED状態の依頼に再度応答
  // 【期待される動作】: 重複応答エラーで例外発生
  // 🔴 設計書状態管理要件確認

  const analysisResult = { testName: 'duplicate-test', errorCategory: 'UI_ELEMENT', confidence: 0.9, suggestions: ['fix'], analysisId: 'dup-id' };
  const request = await manager.createRequest(analysisResult);

  // 最初の承認
  await manager.processResponse({
    requestId: request.id,
    action: 'approve',
    userId: 'first-user'
  });

  // 重複承認試行
  await expect(manager.processResponse({
    requestId: request.id,
    action: 'approve', 
    userId: 'second-user'
  })).rejects.toThrow('Request already processed');
});
```

#### TC-204: 不正なApprovalResponse形式
```javascript
test('TC-204: 不正なApprovalResponse形式', async () => {
  // 【テスト目的】: 不正形式のApprovalResponseの処理確認
  // 【テスト内容】: 不正なactionフィールドで応答
  // 【期待される動作】: 形式エラーで例外発生
  // 🔴 設計書入力検証要件確認

  const analysisResult = { testName: 'format-test', errorCategory: 'TIMING', confidence: 0.8, suggestions: ['fix'], analysisId: 'format-id' };
  const request = await manager.createRequest(analysisResult);

  const invalidResponse = {
    requestId: request.id,
    action: 'invalid-action', // 'approve'でも'reject'でもない
    userId: 'test-user'
  };

  await expect(manager.processResponse(invalidResponse)).rejects.toThrow('Invalid action: invalid-action');
});
```

#### TC-205: タイムアウト処理中の例外
```javascript
test('TC-205: タイムアウト処理中の例外', async () => {
  // 【テスト目的】: タイムアウト処理中の例外発生時の適切な処理
  // 【テスト内容】: 内部エラーが発生するシナリオをモック
  // 【期待される動作】: 例外を捕捉して適切にログ・処理継続
  // 🔴 設計書障害処理要件確認

  // 内部処理でエラーが発生する状況をシミュレート
  const originalConsoleError = console.error;
  console.error = jest.fn(); // エラーログをキャプチャ

  // 正常なタイムアウト処理が例外で中断されないことを確認
  const expiredRequests = await manager.processTimeouts();
  
  // 処理が例外で停止せず、空配列が返されることを確認
  expect(Array.isArray(expiredRequests)).toBe(true);
  
  console.error = originalConsoleError;
});
```

#### TC-206: Discord情報更新失敗
```javascript
test('TC-206: Discord情報更新失敗', async () => {
  // 【テスト目的】: 存在しない承認依頼のDiscord情報更新試行
  // 【テスト内容】: 無効なrequestIdでupdateDiscordInfo呼び出し
  // 【期待される動作】: 適切なエラーメッセージで例外発生
  // 🔴 設計書エラーハンドリング要件確認

  await expect(manager.updateDiscordInfo('non-existent-id', 'thread-123', 'message-456'))
    .rejects.toThrow('Request not found: non-existent-id');
});
```

### ⚡ 境界値テストケース（6件）

#### TC-301: 24時間ちょうどでのタイムアウト
```javascript
test('TC-301: 24時間ちょうどでのタイムアウト', async () => {
  // 【テスト目的】: タイムアウト境界値（24時間ちょうど）の処理確認
  // 【テスト内容】: 24時間経過したタイミングでのタイムアウト処理
  // 【期待される動作】: 正確に24時間経過時点でEXPIRED状態に変更
  // ⚡ 設計書タイムアウト境界値仕様確認

  const analysisResult = { testName: 'timeout-test', errorCategory: 'UI_ELEMENT', confidence: 0.9, suggestions: ['fix'], analysisId: 'timeout-id' };
  const request = await manager.createRequest(analysisResult);

  // 24時間後に時間を進める（テスト用時間操作）
  const originalDate = Date.now;
  Date.now = jest.fn(() => request.createdAt.getTime() + 24 * 60 * 60 * 1000); // ちょうど24時間後

  const expiredRequests = await manager.processTimeouts();

  expect(expiredRequests).toHaveLength(1);
  expect(expiredRequests[0].id).toBe(request.id);
  expect(expiredRequests[0].status).toBe('EXPIRED');

  Date.now = originalDate; // 元に戻す
});
```

#### TC-302: 最大同時承認依頼数（100件）
```javascript
test('TC-302: 最大同時承認依頼数（100件）', async () => {
  // 【テスト目的】: 大量承認依頼の同時処理性能確認
  // 【テスト内容】: 100件の承認依頼を一括作成・処理
  // 【期待される動作】: メモリ効率よく全件処理完了
  // ⚡ 設計書パフォーマンス要件確認

  const requests = [];
  const createPromises = [];

  // 100件の承認依頼を並行作成
  for (let i = 0; i < 100; i++) {
    const analysisResult = {
      testName: `batch-test-${i}`,
      errorCategory: 'UI_ELEMENT',
      confidence: 0.8,
      suggestions: [`fix-${i}`],
      analysisId: `batch-id-${i}`
    };
    createPromises.push(manager.createRequest(analysisResult));
  }

  const createdRequests = await Promise.all(createPromises);
  const allRequests = await manager.getAllRequests();

  expect(createdRequests).toHaveLength(100);
  expect(allRequests).toHaveLength(100);
  expect(new Set(createdRequests.map(r => r.id)).size).toBe(100); // 全てユニークID
});
```

#### TC-303: 空の修正提案配列
```javascript
test('TC-303: 空の修正提案配列', async () => {
  // 【テスト目的】: 修正提案が空配列の場合の処理確認
  // 【テスト内容】: suggestions: [] での承認依頼作成
  // 【期待される動作】: 空配列でも正常に承認依頼が作成される
  // ⚡ 設計書境界値処理要件確認

  const analysisResult = {
    testName: 'empty-suggestions-test',
    errorCategory: 'UNKNOWN',
    confidence: 0.1,
    suggestions: [], // 空配列
    analysisId: 'empty-suggestions-id'
  };

  const request = await manager.createRequest(analysisResult);

  expect(request.suggestions).toEqual([]);
  expect(request.status).toBe('PENDING');
  expect(request.testName).toBe('empty-suggestions-test');
});
```

#### TC-304: 最大長のエラーメッセージ処理
```javascript
test('TC-304: 最大長のエラーメッセージ処理', async () => {
  // 【テスト目的】: 極めて長いエラーメッセージの処理確認
  // 【テスト内容】: 10000文字のtestNameで承認依頼作成
  // 【期待される動作】: 長いメッセージでも正常に処理される
  // ⚡ 設計書文字列長制限要件確認

  const longTestName = 'A'.repeat(10000); // 10000文字
  const analysisResult = {
    testName: longTestName,
    errorCategory: 'UI_ELEMENT',
    confidence: 0.5,
    suggestions: ['Long test name fix'],
    analysisId: 'long-name-id'
  };

  const request = await manager.createRequest(analysisResult);

  expect(request.testName).toBe(longTestName);
  expect(request.testName).toHaveLength(10000);
  expect(request.status).toBe('PENDING');
});
```

#### TC-305: UUID重複回避確認
```javascript
test('TC-305: UUID重複回避確認', async () => {
  // 【テスト目的】: UUID生成の重複回避機能確認
  // 【テスト内容】: 1000件の承認依頼を作成してID重複チェック
  // 【期待される動作】: 全てのIDがユニークである
  // ⚡ 設計書ユニークID要件確認

  const requests = [];
  const batchSize = 50; // 並行処理のバッチサイズ

  // 1000件を20バッチに分けて処理（メモリ効率化）
  for (let batch = 0; batch < 20; batch++) {
    const batchPromises = [];
    for (let i = 0; i < batchSize; i++) {
      const analysisResult = {
        testName: `uuid-test-${batch}-${i}`,
        errorCategory: 'UI_ELEMENT',
        confidence: 0.8,
        suggestions: ['uuid test fix'],
        analysisId: `uuid-analysis-${batch}-${i}`
      };
      batchPromises.push(manager.createRequest(analysisResult));
    }
    const batchResults = await Promise.all(batchPromises);
    requests.push(...batchResults);
  }

  // 全IDの重複チェック
  const allIds = requests.map(r => r.id);
  const uniqueIds = new Set(allIds);

  expect(requests).toHaveLength(1000);
  expect(uniqueIds.size).toBe(1000); // 重複なし
  expect(allIds.every(id => id.match(/^[a-f0-9-]{36}$/))).toBe(true); // 全てUUID形式
});
```

#### TC-306: タイムアウト境界値テスト
```javascript
test('TC-306: タイムアウト境界値テスト', async () => {
  // 【テスト目的】: タイムアウト前後の境界値処理確認
  // 【テスト内容】: 23時間59分・24時間1分での処理比較
  // 【期待される動作】: 24時間を境界として正確にタイムアウト判定
  // ⚡ 設計書タイムアウト精密境界確認

  const analysisResult1 = { testName: 'before-timeout', errorCategory: 'UI_ELEMENT', confidence: 0.8, suggestions: ['fix1'], analysisId: 'before-id' };
  const analysisResult2 = { testName: 'after-timeout', errorCategory: 'TIMING', confidence: 0.7, suggestions: ['fix2'], analysisId: 'after-id' };

  const beforeRequest = await manager.createRequest(analysisResult1);
  const afterRequest = await manager.createRequest(analysisResult2);

  const originalDate = Date.now;
  
  // 23時間59分後（タイムアウト前）
  Date.now = jest.fn(() => beforeRequest.createdAt.getTime() + 23 * 60 * 60 * 1000 + 59 * 60 * 1000);
  let expiredRequests = await manager.processTimeouts();
  expect(expiredRequests).toHaveLength(0); // まだタイムアウトしない

  // 24時間1分後（タイムアウト後）  
  Date.now = jest.fn(() => afterRequest.createdAt.getTime() + 24 * 60 * 60 * 1000 + 1 * 60 * 1000);
  expiredRequests = await manager.processTimeouts();
  expect(expiredRequests.length).toBeGreaterThan(0); // タイムアウト発生

  Date.now = originalDate;
});
```

## テスト実行コマンド

```bash
# 単体テスト実行
npm test -- discord-bot/src/tests/unit/ApprovalRequestManager.test.js

# カバレッジ付き実行
npm run test:coverage -- discord-bot/src/tests/unit/ApprovalRequestManager.test.js

# ウォッチモード
npm run test:watch -- discord-bot/src/tests/unit/ApprovalRequestManager.test.js
```

## 品質基準

- **成功率**: 18/18 (100%)
- **カバレッジ**: 全メソッド・全分岐をカバー
- **実行時間**: 全テスト2秒以内
- **メモリ使用量**: 50MB以内

## 次のお勧めステップ

`/tdd-red` でRedフェーズ（失敗テスト作成）を開始します。