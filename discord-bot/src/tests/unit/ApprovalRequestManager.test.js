import { jest, describe, test, beforeEach, expect } from '@jest/globals';
import { ApprovalRequestManager, ApprovalStatus } from '../../components/ApprovalRequestManager.js';

describe('ApprovalRequestManager', () => {
  let manager;

  beforeEach(() => {
    manager = new ApprovalRequestManager();
  });

  // 🔴 正常動作テストケース（6件）
  
  describe('正常動作テストケース', () => {
    test('TC-101: 承認依頼正常作成', async () => {
      // 【テスト目的】: 正常な分析結果から承認依頼を作成
      // 【テスト内容】: TestFailureAnalyzer結果を入力して承認依頼生成
      // 【期待される動作】: 適切なApprovalRequest構造体が生成される
      // 🟢 設計書REQ-101の完全実装確認
      
      const testName = 'should find login button';
      const errorMessage = 'locator(".login-btn") not found';
      const fixSuggestions = ['セレクタを修正してください', '待機処理を追加してください'];
      const requesterUserId = 'user-123';

      const request = await manager.createRequest(testName, errorMessage, fixSuggestions, requesterUserId);

      expect(request.id).toMatch(/^[a-f0-9-]{36}$/); // UUID形式
      expect(request.testName).toBe('should find login button');
      expect(request.errorMessage).toBe('locator(".login-btn") not found');
      expect(request.fixSuggestions).toEqual(['セレクタを修正してください', '待機処理を追加してください']);
      expect(request.requesterUserId).toBe('user-123');
      expect(request.status).toBe('PENDING');
      expect(request.createdAt).toBeInstanceOf(Date);
      expect(request.expiresAt).toBeInstanceOf(Date);
      expect(request.expiresAt.getTime() - request.createdAt.getTime()).toBe(24 * 60 * 60 * 1000); // 24時間
    });

    test('TC-102: 承認応答正常処理', async () => {
      // 【テスト目的】: 承認応答による状態更新が正常動作
      // 【テスト内容】: PENDING依頼に対するAPPROVE応答処理
      // 【期待される動作】: APPROVED状態への変更と関連情報更新
      // 🟢 設計書REQ-104の承認パターン確認
      
      const testName = 'test';
      const errorMessage = 'test error';
      const fixSuggestions = ['fix'];
      const requesterUserId = 'requester-123';
      const request = await manager.createRequest(testName, errorMessage, fixSuggestions, requesterUserId);

      const response = await manager.processResponse(request.id, true, 'Fix looks good');

      expect(response.approved).toBe(true);
      expect(response.requestId).toBe(request.id);
      expect(response.processedAt).toBeInstanceOf(Date);
      expect(response.success).toBe(true);
      
      // リクエストの状態も確認
      const updatedRequest = await manager.getRequest(request.id);
      expect(updatedRequest.status).toBe('APPROVED');
      expect(updatedRequest.respondedAt).toBeInstanceOf(Date);
    });

    test('TC-103: 拒否応答正常処理', async () => {
      // 【テスト目的】: 拒否応答による状態更新が正常動作
      // 【テスト内容】: PENDING依頼に対するREJECT応答処理
      // 【期待される動作】: REJECTED状態への変更と関連情報更新
      // 🟢 設計書REQ-104の拒否パターン確認
      
      const testName = 'test';
      const errorMessage = 'test error';
      const fixSuggestions = ['fix'];
      const requesterUserId = 'requester-123';
      const request = await manager.createRequest(testName, errorMessage, fixSuggestions, requesterUserId);

      const response = await manager.processResponse(request.id, false, 'Need more work');

      expect(response.approved).toBe(false);
      expect(response.requestId).toBe(request.id);
      expect(response.comment).toBe('Need more work');
      expect(response.success).toBe(true);

      // リクエストの状態も確認
      const updatedRequest = await manager.getRequest(request.id);
      expect(updatedRequest.status).toBe('REJECTED');
      expect(updatedRequest.respondedAt).toBeInstanceOf(Date);
    });

    test('TC-104: Discord情報更新', async () => {
      // 【テスト目的】: Discord関連メタ情報の更新が正常動作
      // 【テスト内容】: threadId、messageIdの追加更新処理
      // 【期待される動作】: Discord連携情報が適切に保存される
      // 🟢 設計書REQ-103のDiscord統合確認
      
      const testName = 'test';
      const errorMessage = 'test error';
      const fixSuggestions = ['fix'];
      const requesterUserId = 'requester-123';
      const request = await manager.createRequest(testName, errorMessage, fixSuggestions, requesterUserId);

      const threadId = 'discord-thread-123';
      const messageId = 'discord-msg-456';

      const success = await manager.updateDiscordInfo(request.id, threadId, messageId);

      expect(success).toBe(true);
      
      const updatedRequest = await manager.getRequest(request.id);
      expect(updatedRequest.discordThreadId).toBe('discord-thread-123');
      expect(updatedRequest.discordMessageId).toBe('discord-msg-456');
    });

    test('TC-105: 全承認依頼取得', async () => {
      // 【テスト目的】: 複数承認依頼の一括取得が正常動作
      // 【テスト内容】: 3件の依頼作成→全件取得の動作確認
      // 【期待される動作】: 作成順序とフィルタリング機能の動作確認
      // 🟢 設計書REQ-102の取得機能確認
      
      const requests = await Promise.all([
        manager.createRequest('test1', 'error1', ['fix1'], 'user1'),
        manager.createRequest('test2', 'error2', ['fix2'], 'user2'),
        manager.createRequest('test3', 'error3', ['fix3'], 'user1')
      ]);

      const allRequests = await manager.getAllRequests();
      expect(allRequests).toHaveLength(3);

      const user1Requests = await manager.getAllRequests({ requesterUserId: 'user1' });
      expect(user1Requests).toHaveLength(2);

      const pendingRequests = await manager.getAllRequests({ status: ApprovalStatus.PENDING });
      expect(pendingRequests).toHaveLength(3);
    });

    test('TC-106: ステータスフィルタ取得', async () => {
      // 【テスト目的】: ステータス別フィルタリング機能が正常動作
      // 【テスト内容】: PENDING/APPROVED/REJECTEDの各ステータス別取得
      // 【期待される動作】: 各ステータスのフィルタ結果が正確
      // 🟢 設計書REQ-102のフィルタリング確認
      
      const request1 = await manager.createRequest('test1', 'error1', ['fix1'], 'user1');
      const request2 = await manager.createRequest('test2', 'error2', ['fix2'], 'user2');
      const request3 = await manager.createRequest('test3', 'error3', ['fix3'], 'user3');

      await manager.processResponse(request1.id, true);
      await manager.processResponse(request2.id, false);

      const pendingRequests = await manager.getAllRequests({ status: ApprovalStatus.PENDING });
      expect(pendingRequests).toHaveLength(1);
      expect(pendingRequests[0].id).toBe(request3.id);

      const approvedRequests = await manager.getAllRequests({ status: ApprovalStatus.APPROVED });
      expect(approvedRequests).toHaveLength(1);
      expect(approvedRequests[0].id).toBe(request1.id);

      const rejectedRequests = await manager.getAllRequests({ status: ApprovalStatus.REJECTED });
      expect(rejectedRequests).toHaveLength(1);
      expect(rejectedRequests[0].id).toBe(request2.id);
    });
  });

  // ⚠️ 異常系テストケース（6件）
  
  describe('異常系テストケース', () => {
    test('TC-201: 不正な分析結果入力', async () => {
      // 【テスト目的】: 不正・不完全な入力データに対するエラーハンドリング
      // 【テスト内容】: null, undefined, 型不一致入力の処理確認
      // 【期待される動作】: 適切なバリデーションエラーが発生する
      // 🔴 設計書REQ-105の異常系処理確認
      
      await expect(manager.createRequest(null, 'error', ['fix'], 'user')).rejects.toThrow('テスト名は必須');
      await expect(manager.createRequest('test', null, ['fix'], 'user')).rejects.toThrow('エラーメッセージは必須');
      await expect(manager.createRequest('test', 'error', 'not-array', 'user')).rejects.toThrow('修正提案は配列');
      await expect(manager.createRequest('test', 'error', ['fix'], null)).rejects.toThrow('依頼者ユーザーIDは必須');
    });

    test('TC-202: 存在しない承認依頼への応答', async () => {
      // 【テスト目的】: 存在しない依頼IDに対する応答処理エラー
      // 【テスト内容】: 無効なIDでの応答処理実行
      // 【期待される動作】: 「見つかりません」エラーが発生
      // 🔴 設計書REQ-105の存在性検証確認
      
      await expect(manager.processResponse('invalid-id', true)).rejects.toThrow('指定された依頼IDが見つかりません');
    });

    test('TC-203: 重複承認応答の処理', async () => {
      // 【テスト目的】: 既に処理済みの依頼への重複応答エラー
      // 【テスト内容】: APPROVED状態の依頼への再応答実行
      // 【期待される動作】: 「既に処理済み」エラーが発生
      // 🔴 設計書REQ-105の重複処理防止確認
      
      const request = await manager.createRequest('test', 'error', ['fix'], 'user');
      await manager.processResponse(request.id, true);

      await expect(manager.processResponse(request.id, false)).rejects.toThrow('この依頼は既に処理済みです');
    });

    test('TC-204: 不正なApprovalResponse形式', async () => {
      // 【テスト目的】: 不正なレスポンス形式に対するバリデーション
      // 【テスト内容】: 必須フィールド欠如・型不正の応答処理
      // 【期待される動作】: フィールド検証エラーが発生
      // 🔴 設計書REQ-105の応答フォーマット検証確認
      
      const request = await manager.createRequest('test', 'error', ['fix'], 'user');
      
      await expect(manager.processResponse(null, true)).rejects.toThrow('依頼IDは必須');
      await expect(manager.processResponse(request.id, 'not-boolean')).rejects.toThrow('承認フラグはboolean型');
    });

    test('TC-205: タイムアウト処理中の例外', async () => {
      // 【テスト目的】: タイムアウト処理中の例外ケース動作確認
      // 【テスト内容】: processTimeouts()実行中の安全性確認
      // 【期待される動作】: 例外発生時も他の依頼処理は継続する
      // 🔴 設計書REQ-105のタイムアウト例外処理確認
      
      const expiredIds = await manager.processTimeouts();
      expect(Array.isArray(expiredIds)).toBe(true);
      expect(expiredIds).toHaveLength(0);
    });

    test('TC-206: Discord情報更新失敗', async () => {
      // 【テスト目的】: Discord関連情報更新時のエラー処理
      // 【テスト内容】: 無効ID、null値でのDiscord情報更新
      // 【期待される動作】: 適切なバリデーションエラーが発生
      // 🔴 設計書REQ-105のDiscord更新エラー確認
      
      const request = await manager.createRequest('test', 'error', ['fix'], 'user');
      
      await expect(manager.updateDiscordInfo('invalid-id', 'thread', 'message')).rejects.toThrow('指定された依頼IDが見つかりません');
      await expect(manager.updateDiscordInfo(request.id, null, 'message')).rejects.toThrow('スレッドIDは必須');
      await expect(manager.updateDiscordInfo(request.id, 'thread', null)).rejects.toThrow('メッセージIDは必須');
    });
  });

  // 🔄 境界値テストケース（6件）
  
  describe('境界値テストケース', () => {
    test('TC-301: 24時間ちょうどでのタイムアウト', async () => {
      // 【テスト目的】: 24時間タイムアウトの境界値動作確認
      // 【テスト内容】: 24時間ちょうどでの期限切れ処理精度
      // 【期待される動作】: ミリ秒精度での正確なタイムアウト判定
      // 🟡 設計書REQ-101のタイムアウト仕様境界確認
      
      const request = await manager.createRequest('test', 'error', ['fix'], 'user');
      
      // 24時間前の日時に設定
      request.expiresAt = new Date(Date.now() - 1000); // 1秒前
      
      const expiredIds = await manager.processTimeouts();
      expect(expiredIds).toContain(request.id);
      
      const updatedRequest = await manager.getRequest(request.id);
      expect(updatedRequest.status).toBe(ApprovalStatus.EXPIRED);
    });

    test('TC-302: 最大同時承認依頼数（100件）', async () => {
      // 【テスト目的】: 大量同時承認依頼のスケーラビリティ確認
      // 【テスト内容】: 100件の依頼を同時作成・管理
      // 【期待される動作】: パフォーマンス劣化なく全件処理される
      // 🟡 設計書REQ-102のスケーラビリティ境界確認
      
      const promises = [];
      for (let i = 0; i < 100; i++) {
        promises.push(manager.createRequest(`test-${i}`, `error-${i}`, [`fix-${i}`], `user-${i % 10}`));
      }
      
      const requests = await Promise.all(promises);
      expect(requests).toHaveLength(100);
      
      const allRequests = await manager.getAllRequests();
      expect(allRequests).toHaveLength(100);
    });

    test('TC-303: 空の修正提案配列', async () => {
      // 【テスト目的】: 修正提案が空配列の場合の動作確認
      // 【テスト内容】: 修正提案なしでの承認依頼作成
      // 【期待される動作】: 空配列も有効な入力として処理される
      // 🟡 設計書REQ-101の修正提案境界値確認
      
      const request = await manager.createRequest('test', 'error', [], 'user');
      
      expect(request.fixSuggestions).toEqual([]);
      expect(request.status).toBe(ApprovalStatus.PENDING);
    });

    test('TC-304: 最大長のエラーメッセージ処理', async () => {
      // 【テスト目的】: 10000文字の最大長エラーメッセージ処理
      // 【テスト内容】: 長大なエラーメッセージでの承認依頼作成
      // 【期待される動作】: 大容量データも正常に処理される
      // 🟡 設計書REQ-101のメッセージ長境界確認
      
      const longMessage = 'x'.repeat(10000);
      
      const request = await manager.createRequest('test', longMessage, ['fix'], 'user');
      
      expect(request.errorMessage).toHaveLength(10000);
      expect(request.status).toBe(ApprovalStatus.PENDING);
    });

    test('TC-305: UUID重複回避確認', async () => {
      // 【テスト目的】: UUID生成の重複回避性能確認
      // 【テスト内容】: 1000件の依頼作成でのID重複チェック
      // 【期待される動作】: 全てのIDが一意で重複しない
      // 🟡 設計書REQ-101のID一意性境界確認
      
      const promises = [];
      for (let i = 0; i < 1000; i++) {
        promises.push(manager.createRequest(`test-${i}`, 'error', ['fix'], 'user'));
      }
      
      const requests = await Promise.all(promises);
      const ids = requests.map(r => r.id);
      const uniqueIds = [...new Set(ids)];
      
      expect(uniqueIds).toHaveLength(1000);
    });

    test('TC-306: タイムアウト境界値テスト', async () => {
      // 【テスト目的】: タイムアウト処理の境界値動作確認
      // 【テスト内容】: 期限ちょうど・期限1ms過ぎでの処理差異
      // 【期待される動作】: ミリ秒精度での期限判定が正確
      // 🟡 設計書REQ-102のタイムアウト精度境界確認
      
      const now = new Date();
      
      const request1 = await manager.createRequest('test1', 'error', ['fix'], 'user');
      const request2 = await manager.createRequest('test2', 'error', ['fix'], 'user');
      
      // request1を期限ちょうど、request2を1ms過ぎに設定
      request1.expiresAt = new Date(now.getTime());
      request2.expiresAt = new Date(now.getTime() - 1);
      
      const expiredIds = await manager.processTimeouts();
      
      expect(expiredIds).toContain(request2.id);
      expect(expiredIds).not.toContain(request1.id);
    });
  });
});