import { jest, describe, test, beforeEach, expect } from '@jest/globals';
import { ClaudeCodeIntegrator } from '../../services/claude-code-integrator.js';

describe('ClaudeCodeIntegrator', () => {
  let integrator;
  let mockRetryHandler;
  let mockErrorClassifier;
  let mockClaudeService;
  let mockDiscordNotificationService;

  beforeEach(() => {
    mockRetryHandler = {
      retry: jest.fn()
    };

    mockErrorClassifier = {
      classify: jest.fn()
    };

    mockClaudeService = {
      sendMessage: jest.fn()
    };

    mockDiscordNotificationService = {
      sendMessage: jest.fn()
    };

    integrator = new ClaudeCodeIntegrator({
      retryHandler: mockRetryHandler,
      errorClassifier: mockErrorClassifier,
      claudeService: mockClaudeService,
      discordNotificationService: mockDiscordNotificationService
    });
  });

  describe('sendModificationRequest', () => {
    test('修正依頼が正しく送信される', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'req-123',
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
        confidence: 0.9
      };

      const claudeResponse = {
        content: 'ボタンセレクタを修正しました。',
        timestamp: new Date()
      };

      mockErrorClassifier.classify.mockReturnValue(classification);
      mockRetryHandler.retry.mockImplementation(async (fn) => await fn());
      mockClaudeService.sendMessage.mockResolvedValue(claudeResponse);
      mockDiscordNotificationService.sendMessage.mockResolvedValue();

      // Act
      const result = await integrator.sendModificationRequest(approvalRequest);

      // Assert
      expect(mockErrorClassifier.classify).toHaveBeenCalledWith(approvalRequest.error);
      expect(mockClaudeService.sendMessage).toHaveBeenCalled();
      expect(mockDiscordNotificationService.sendMessage).toHaveBeenCalled();
      expect(result).toBe(claudeResponse);
    });

    test('Claude Service未設定時にエラーを投げる', async () => {
      // Arrange
      integrator.claudeService = null;
      
      const approvalRequest = {
        requestId: 'req-456',
        testName: 'Test',
        error: { message: 'Error' }
      };

      mockRetryHandler.retry.mockImplementation(async (fn) => await fn());

      // Act & Assert
      await expect(integrator.sendModificationRequest(approvalRequest))
        .rejects.toThrow('Claude Service未設定');
    });
  });

  describe('processClaudeResponse', () => {
    test('Claude応答が正しく解析される', async () => {
      // Arrange
      const response = {
        content: '```javascript\nconst button = await page.locator(".login-button");\n```\nボタンセレクタを修正しました。',
        timestamp: new Date()
      };

      mockDiscordNotificationService.sendMessage.mockResolvedValue();

      // Act
      const result = await integrator.processClaudeResponse(response);

      // Assert
      expect(result.analysis).toBeDefined();
      expect(result.analysis.hasCodeChanges).toBe(true);
      expect(result.analysis.confidenceLevel).toBeGreaterThan(0.5);
      expect(result.applicationDecision).toBeDefined();
      expect(result.applicationDecision.shouldApply).toBe(true);
      expect(result.processedAt).toBeInstanceOf(Date);
    });

    test('応答処理エラー時にエラー分類と通知を行う', async () => {
      // Arrange
      const response = { content: 'Invalid response' };
      const processingError = new Error('Processing failed');
      
      // analyzeClaudeResponseでエラーを発生させる
      integrator.analyzeClaudeResponse = jest.fn().mockRejectedValue(processingError);
      
      const classification = {
        category: 'PROCESSING_ERROR',
        severity: 'HIGH',
        confidence: 0.8
      };
      
      mockErrorClassifier.classify.mockReturnValue(classification);
      mockDiscordNotificationService.sendMessage.mockResolvedValue();

      // Act & Assert
      await expect(integrator.processClaudeResponse(response))
        .rejects.toThrow('Processing failed');
      
      expect(mockErrorClassifier.classify).toHaveBeenCalledWith(processingError);
      expect(mockDiscordNotificationService.sendMessage).toHaveBeenCalled();
    });
  });

  describe('buildModificationMessage', () => {
    test('修正依頼メッセージが適切に構築される', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'req-789',
        testName: 'Navigation Test',
        error: { message: 'Page load timeout' },
        suggestion: {
          description: 'Increase wait time',
          automationLevel: 'MEDIUM',
          riskLevel: 'LOW'
        }
      };

      const classification = {
        category: 'TIMEOUT',
        severity: 'MEDIUM',
        confidence: 0.85
      };

      // Act
      const message = await integrator.buildModificationMessage(approvalRequest, classification);

      // Assert
      expect(message).toContain('🔧 **Claude Code修正依頼**');
      expect(message).toContain('req-789');
      expect(message).toContain('Navigation Test');
      expect(message).toContain('TIMEOUT');
      expect(message).toContain('MEDIUM');
      expect(message).toContain('85%');
      expect(message).toContain('Page load timeout');
      expect(message).toContain('Increase wait time');
      expect(message).toContain('作業指示');
    });
  });

  describe('analyzeClaudeResponse', () => {
    test('コード変更を含む応答が正しく解析される', async () => {
      // Arrange
      const response = {
        content: '```javascript\nconst element = await page.waitForSelector(".button");\n```\nセレクタを修正しました。',
        timestamp: new Date()
      };

      // Act
      const analysis = await integrator.analyzeClaudeResponse(response);

      // Assert
      expect(analysis.hasCodeChanges).toBe(true);
      expect(analysis.hasFileModifications).toBe(false);
      expect(analysis.hasTestUpdates).toBe(false);
      expect(analysis.confidenceLevel).toBeGreaterThan(0.5);
      expect(analysis.extractedChanges).toHaveLength(1);
      expect(analysis.extractedChanges[0].type).toBe('code');
    });

    test('ファイル修正を含む応答が正しく解析される', async () => {
      // Arrange
      const response = {
        content: 'file: test.spec.js を修正しました。新しいテストケースを追加。',
        timestamp: new Date()
      };

      // Act
      const analysis = await integrator.analyzeClaudeResponse(response);

      // Assert
      expect(analysis.hasFileModifications).toBe(true);
      expect(analysis.confidenceLevel).toBeGreaterThan(0.5);
    });
  });

  describe('evaluateApplication', () => {
    test('高信頼度でコード変更ありの場合に適用推奨される', async () => {
      // Arrange
      const analysis = {
        hasCodeChanges: true,
        hasFileModifications: true,
        hasTestUpdates: false,
        confidenceLevel: 0.85,
        extractedChanges: [{ type: 'code', content: '```js\ncode\n```' }]
      };

      // Act
      const decision = await integrator.evaluateApplication(analysis);

      // Assert
      expect(decision.shouldApply).toBe(true);
      expect(decision.reason).toContain('適用可能');
      expect(decision.riskLevel).toBe('LOW');
      expect(decision.priority).toBe('HIGH');
    });

    test('低信頼度の場合に適用非推奨される', async () => {
      // Arrange
      const analysis = {
        hasCodeChanges: true,
        hasFileModifications: false,
        hasTestUpdates: false,
        confidenceLevel: 0.3,
        extractedChanges: []
      };

      // Act
      const decision = await integrator.evaluateApplication(analysis);

      // Assert
      expect(decision.shouldApply).toBe(false);
      expect(decision.reason).toContain('信頼度が低すぎます');
      expect(decision.priority).toBe('LOW');
    });
  });

  describe('formatResponseSummary', () => {
    test('応答サマリーが適切にフォーマットされる', async () => {
      // Arrange
      const analysis = {
        hasCodeChanges: true,
        hasFileModifications: true,
        hasTestUpdates: false,
        confidenceLevel: 0.85,
        extractedChanges: [{ type: 'code' }, { type: 'file' }]
      };

      const applicationDecision = {
        shouldApply: true,
        reason: '適用可能: 信頼度85%',
        riskLevel: 'LOW',
        priority: 'HIGH'
      };

      // Act
      const summary = integrator.formatResponseSummary(analysis, applicationDecision);

      // Assert
      expect(summary).toContain('📊 **Claude応答分析結果**');
      expect(summary).toContain('✅ 適用推奨');
      expect(summary).toContain('85%');
      expect(summary).toContain('2件');
      expect(summary).toContain('LOW');
      expect(summary).toContain('HIGH');
    });
  });

  describe('notifyProgress', () => {
    test('進捗通知が正しく送信される', async () => {
      // Arrange
      const approvalRequest = {
        requestId: 'req-notify',
        testName: 'Progress Test'
      };

      const details = {
        claudeResponse: { content: 'Test response' }
      };

      mockDiscordNotificationService.sendMessage.mockResolvedValue();

      // Act
      await integrator.notifyProgress(approvalRequest, 'MODIFICATION_REQUESTED', details);

      // Assert
      expect(mockDiscordNotificationService.sendMessage).toHaveBeenCalled();
      const sentMessage = mockDiscordNotificationService.sendMessage.mock.calls[0][0];
      expect(sentMessage).toContain('🔄 **Claude Code統合進捗**');
      expect(sentMessage).toContain('req-notify');
      expect(sentMessage).toContain('Progress Test');
      expect(sentMessage).toContain('修正依頼送信完了');
    });

    test('Discord通知サービス未設定時にワーニングログを出力', async () => {
      // Arrange
      integrator.discordNotificationService = null;
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      // Act
      await integrator.notifyProgress(null, 'TEST_STATUS');

      // Assert
      expect(consoleSpy).toHaveBeenCalledWith('Discord通知サービス未設定: 進捗通知をスキップ');
      
      consoleSpy.mockRestore();
    });
  });
});