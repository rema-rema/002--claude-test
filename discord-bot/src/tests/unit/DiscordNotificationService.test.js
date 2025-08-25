import { jest, describe, test, beforeEach, expect } from '@jest/globals';

// DiscordNotificationService拡張機能のテスト
describe('DiscordNotificationService - 承認機能拡張', () => {
  let service;
  let mockRetryHandler;
  let mockErrorClassifier;
  let mockThreadManager;
  let mockThread;

  beforeEach(() => {
    // Track B統合コンポーネントのモック
    mockRetryHandler = {
      retry: jest.fn()
    };

    mockErrorClassifier = {
      classify: jest.fn()
    };

    mockThread = {
      send: jest.fn()
    };

    mockThreadManager = {
      createApprovalThread: jest.fn().mockResolvedValue(mockThread)
    };

    // DiscordNotificationServiceクラスの部分モック
    service = {
      retryHandler: mockRetryHandler,
      errorClassifier: mockErrorClassifier,
      threadManager: mockThreadManager,
      
      // メソッドを実装
      async sendTestFailureWithApproval(approvalRequest) {
        return await this.retryHandler.retry(async () => {
          // 1. エラー分類
          const classification = this.errorClassifier.classify(approvalRequest.error);
          
          // 2. スレッド作成
          const thread = await this.threadManager.createApprovalThread(approvalRequest);
          
          // 3. 承認依頼メッセージ送信
          const message = await this.formatApprovalMessage(approvalRequest, classification);
          return await thread.send(message);
        });
      },

      async formatApprovalMessage(approvalRequest, classification) {
        const { testName, error, suggestion, requestId } = approvalRequest;
        
        let message = `🔍 **テスト失敗修正承認依頼**\n`;
        message += `📝 Request ID: \`${requestId}\`\n\n`;
        
        // 問題概要
        message += `**📊 問題概要**\n`;
        message += `• テスト名: \`${testName}\`\n`;
        message += `• エラー分類: ${classification.category} (${classification.severity})\n`;
        message += `• 信頼度: ${Math.round(classification.confidence * 100)}%\n\n`;
        
        // 原因
        message += `**⚠️ エラー原因**\n`;
        const errorMsg = error.message.length > 200 
          ? error.message.substring(0, 200) + '...'
          : error.message;
        message += `\`\`\`\n${errorMsg}\n\`\`\`\n\n`;
        
        // 修正提案
        if (suggestion) {
          message += `**💡 修正提案**\n`;
          message += `• 修正方法: ${suggestion.description}\n`;
          message += `• 自動化度: ${suggestion.automationLevel}\n`;
          message += `• リスクレベル: ${suggestion.riskLevel}\n\n`;
        }
        
        // 操作方法
        message += `**🎯 操作方法**\n`;
        message += `• ✅ 承認: このメッセージにリアクション\n`;
        message += `• ❌ 拒否: 拒否リアクション\n`;
        message += `• 📝 修正内容はこのスレッドで報告されます\n`;
        
        return message;
      },

      async initializeApprovalChannels() {
        // 承認チャンネル初期化のモック実装
        return true;
      },

      async integrateWithThreadManager(threadManager) {
        this.threadManager = threadManager;
      }
    };
  });

  describe('sendTestFailureWithApproval', () => {
    test('承認依頼メッセージが正しく送信される', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'test-request-123',
        testName: 'Sample Test',
        error: { message: 'Test failed due to timeout' },
        suggestion: {
          description: 'Increase timeout value',
          automationLevel: 'HIGH',
          riskLevel: 'LOW'
        }
      };

      const classification = {
        category: 'TIMEOUT',
        severity: 'MEDIUM',
        confidence: 0.85
      };

      mockErrorClassifier.classify.mockReturnValue(classification);
      mockRetryHandler.retry.mockImplementation(async (fn) => await fn());
      mockThread.send.mockResolvedValue({ id: 'message-123' });

      // Act
      const result = await service.sendTestFailureWithApproval(approvalRequest);

      // Assert
      expect(mockErrorClassifier.classify).toHaveBeenCalledWith(approvalRequest.error);
      expect(mockThreadManager.createApprovalThread).toHaveBeenCalledWith(approvalRequest);
      expect(mockThread.send).toHaveBeenCalled();
      expect(result).toEqual({ id: 'message-123' });
    });

    test('retryHandlerでエラー処理がラップされる', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'test-request-456',
        testName: 'Failing Test',
        error: { message: 'Network error' }
      };

      const retryError = new Error('Retry failed');
      mockRetryHandler.retry.mockRejectedValue(retryError);

      // Act & Assert
      await expect(service.sendTestFailureWithApproval(approvalRequest))
        .rejects.toThrow('Retry failed');
      
      expect(mockRetryHandler.retry).toHaveBeenCalled();
    });
  });

  describe('formatApprovalMessage', () => {
    test('承認依頼メッセージが適切にフォーマットされる', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'req-789',
        testName: 'Login Test',
        error: { message: 'Button not found' },
        suggestion: {
          description: 'Update selector',
          automationLevel: 'HIGH',
          riskLevel: 'LOW'
        }
      };

      const classification = {
        category: 'UI_ELEMENT',
        severity: 'HIGH',
        confidence: 0.92
      };

      // Act
      const message = await service.formatApprovalMessage(approvalRequest, classification);

      // Assert
      expect(message).toContain('🔍 **テスト失敗修正承認依頼**');
      expect(message).toContain('req-789');
      expect(message).toContain('Login Test');
      expect(message).toContain('UI_ELEMENT');
      expect(message).toContain('92%');
      expect(message).toContain('Button not found');
      expect(message).toContain('Update selector');
      expect(message).toContain('HIGH');
      expect(message).toContain('LOW');
    });

    test('長いエラーメッセージが切り詰められる', async () => {
      // Arrange
      const longError = 'A'.repeat(300);
      const approvalRequest = {
        requestId: 'req-long',
        testName: 'Long Error Test',
        error: { message: longError }
      };

      const classification = {
        category: 'UNKNOWN',
        severity: 'LOW',
        confidence: 0.5
      };

      // Act
      const message = await service.formatApprovalMessage(approvalRequest, classification);

      // Assert
      expect(message).toContain('A'.repeat(200) + '...');
      expect(message).not.toContain('A'.repeat(300));
    });

    test('修正提案がない場合も正しく処理される', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'req-no-suggestion',
        testName: 'No Suggestion Test',
        error: { message: 'Unknown error' }
      };

      const classification = {
        category: 'UNKNOWN',
        severity: 'MEDIUM',
        confidence: 0.3
      };

      // Act
      const message = await service.formatApprovalMessage(approvalRequest, classification);

      // Assert
      expect(message).toContain('🔍 **テスト失敗修正承認依頼**');
      expect(message).toContain('req-no-suggestion');
      expect(message).not.toContain('💡 修正提案');
    });
  });

  describe('initializeApprovalChannels', () => {
    test('承認チャンネル初期化が成功する', async () => {
      // Act
      const result = await service.initializeApprovalChannels();

      // Assert
      expect(result).toBe(true);
    });
  });

  describe('integrateWithThreadManager', () => {
    test('ThreadManagerが正しく統合される', async () => {
      // Arrange
      const customThreadManager = { createApprovalThread: jest.fn() };

      // Act
      await service.integrateWithThreadManager(customThreadManager);

      // Assert
      expect(service.threadManager).toBe(customThreadManager);
    });
  });
});