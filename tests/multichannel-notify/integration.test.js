/**
 * Playwright-Discord マルチチャンネル通知システム 統合テスト
 */

import { jest } from '@jest/globals';
import { ChannelConfigManager } from '../../src/multichannel-notify/channel-config-manager.js';
import { SessionDetector } from '../../src/multichannel-notify/session-detector.js';
import { MultiChannelNotifier } from '../../src/multichannel-notify/multi-channel-notifier.js';
import PlaywrightChannelReporter from '../../src/multichannel-notify/playwright-channel-reporter.js';

describe('Multichannel Notify Integration Tests', () => {
  let originalEnv;

  beforeEach(() => {
    originalEnv = process.env;
    
    // テスト用環境変数設定
    process.env = {
      ...originalEnv,
      CC_DISCORD_CHANNEL_ID_001: '1111111111111111111',
      CC_DISCORD_CHANNEL_ID_002: '1405815779198369903',  
      CC_DISCORD_CHANNEL_ID_003: '3333333333333333333',
      CURRENT_SESSION_ID: '002',
      PLAYWRIGHT_CHANNEL_DETECTION_MODE: 'auto',
      PLAYWRIGHT_NOTIFICATION_TIMEOUT: '5000'
    };
  });

  afterEach(() => {
    process.env = originalEnv;
    jest.clearAllMocks();
  });

  describe('コンポーネント統合テスト', () => {
    test('ChannelConfigManager + SessionDetector 統合', async () => {
      const configManager = new ChannelConfigManager();
      const sessionDetector = new SessionDetector();

      // セッション検出
      const currentSession = await sessionDetector.detectCurrentSession();
      expect(currentSession).toBe('002');

      // 対応チャンネル取得
      const channelId = configManager.getChannelBySession(currentSession);
      expect(channelId).toBe('1405815779198369903');
    });

    test('MultiChannelNotifier + ChannelConfigManager 統合', async () => {
      const configManager = new ChannelConfigManager();
      const notifier = new MultiChannelNotifier();

      // モック設定
      const mockSend = jest.fn().mockResolvedValue({ success: true });
      notifier._performSend = mockSend;

      const allChannels = configManager.getAllChannelIds();
      expect(allChannels).toHaveLength(3);

      // 一斉通知テスト
      const message = { content: 'Test broadcast' };
      const results = await notifier.broadcastToChannels(allChannels, message);

      expect(results).toHaveLength(3);
      expect(results.every(r => r.success)).toBe(true);
      expect(mockSend).toHaveBeenCalledTimes(3);
    });
  });

  describe('PlaywrightChannelReporter 統合テスト', () => {
    let reporter;

    beforeEach(() => {
      reporter = new PlaywrightChannelReporter({
        enableVideoAttachment: true,
        enableScreenshotAttachment: true
      });

      // モック設定
      reporter.multiChannelNotifier._performSend = jest.fn().mockResolvedValue({
        success: true,
        messageId: 'mock-message-id'
      });
    });

    test('テスト開始時のセッション・チャンネル検出', async () => {
      const mockSuite = {
        allTests: () => [{ title: 'test1' }, { title: 'test2' }]
      };

      await reporter.onBegin({}, mockSuite);

      expect(reporter.currentSession).toBe('002');
      expect(reporter.targetChannelId).toBe('1405815779198369903');
    });

    test('テスト結果収集と通知送信', async () => {
      // セットアップ
      const mockSuite = { allTests: () => [{ title: 'test1' }] };
      await reporter.onBegin({}, mockSuite);

      // テスト実行シミュレーション
      const mockTest = {
        title: 'sample test',
        location: { file: '/test/sample.spec.js' }
      };

      const mockResult = {
        status: 'passed',
        duration: 1000,
        error: null,
        attachments: []
      };

      reporter.onTestBegin(mockTest);
      await reporter.onTestEnd(mockTest, mockResult);

      // テスト結果確認
      expect(reporter.testResults).toHaveLength(1);
      expect(reporter.testResults[0]).toMatchObject({
        title: 'sample test',
        status: 'passed',
        duration: 1000
      });

      // 終了処理とメッセージ送信
      const mockEndResult = { duration: 2000 };
      await reporter.onEnd(mockEndResult);

      expect(reporter.multiChannelNotifier._performSend).toHaveBeenCalledWith(
        '1405815779198369903',
        expect.objectContaining({
          content: expect.stringContaining('✅ **Playwright テスト結果')
        }),
        []
      );
    });

    test('失敗テスト時の証跡ファイル収集', async () => {
      // セットアップ
      const mockSuite = { allTests: () => [{ title: 'failing test' }] };
      await reporter.onBegin({}, mockSuite);

      // 失敗テスト実行
      const mockTest = {
        title: 'failing test',
        location: { file: '/test/failing.spec.js' }
      };

      const mockResult = {
        status: 'failed',
        duration: 2000,
        error: { message: 'Element not found' },
        attachments: [
          {
            name: 'screenshot',
            path: '/test-results/failing-test/screenshot.png',
            contentType: 'image/png'
          }
        ]
      };

      await reporter.onTestEnd(mockTest, mockResult);

      // 証跡ファイル収集をモック
      const originalCollectArtifacts = reporter._collectFailureArtifacts;
      reporter._collectFailureArtifacts = jest.fn().mockResolvedValue([
        {
          testName: 'failing test',
          files: [
            {
              type: 'screenshot',
              path: '/test-results/failing-test/screenshot.png',
              size: 50000
            }
          ]
        }
      ]);

      await reporter.onEnd({ duration: 3000 });

      expect(reporter._collectFailureArtifacts).toHaveBeenCalled();
      expect(reporter.multiChannelNotifier._performSend).toHaveBeenCalledWith(
        '1405815779198369903',
        expect.objectContaining({
          content: expect.stringContaining('❌ **Playwright テスト結果')
        }),
        expect.arrayContaining([
          expect.objectContaining({
            type: 'screenshot',
            path: '/test-results/failing-test/screenshot.png'
          })
        ])
      );
    });
  });

  describe('エラーハンドリング統合テスト', () => {
    test('セッション検出失敗時のフォールバック動作', async () => {
      // セッション検出を失敗させる
      delete process.env.CURRENT_SESSION_ID;
      
      const sessionDetector = new SessionDetector({
        detectionMethods: ['environment'], // 他の検出方法を無効化
        fallbackSession: '001'
      });

      const currentSession = await sessionDetector.detectCurrentSession();
      expect(currentSession).toBe('001'); // フォールバック値

      // 対応チャンネル確認
      const configManager = new ChannelConfigManager();
      const channelId = configManager.getChannelBySession(currentSession);
      expect(channelId).toBe('1111111111111111111');
    });

    test('通知送信失敗時のリトライ動作', async () => {
      const notifier = new MultiChannelNotifier({
        maxRetryAttempts: 2
      });

      let callCount = 0;
      notifier._performSend = jest.fn().mockImplementation(() => {
        callCount++;
        if (callCount <= 2) {
          throw new Error('Network error');
        }
        return Promise.resolve({ success: true });
      });

      const result = await notifier.retryNotification('1405815779198369903', {
        message: { content: 'Test message' },
        attachments: []
      });

      expect(result.success).toBe(true);
      expect(notifier._performSend).toHaveBeenCalledTimes(3); // 初回 + 2回リトライ
    });

    test('全リトライ失敗時のエラー処理', async () => {
      const notifier = new MultiChannelNotifier({
        maxRetryAttempts: 2,
        baseRetryDelay: 100 // テスト高速化
      });

      notifier._performSend = jest.fn().mockRejectedValue(
        new Error('Persistent network error')
      );

      await expect(
        notifier.retryNotification('1405815779198369903', {
          message: { content: 'Test message' },
          attachments: []
        })
      ).rejects.toThrow('All retry attempts failed');

      expect(notifier._performSend).toHaveBeenCalledTimes(2); // maxRetryAttempts
    });
  });

  describe('設定変更時の動作テスト', () => {
    test('チャンネル設定追加時の動的反映', () => {
      const configManager = new ChannelConfigManager();
      
      // 初期設定確認
      const initialChannels = configManager.getAllChannelIds();
      expect(initialChannels).toHaveLength(3);

      // 新しいチャンネル追加
      process.env.CC_DISCORD_CHANNEL_ID_004 = '4444444444444444444';

      // 強制リロード
      const newConfig = configManager.reloadConfig();
      expect(newConfig).toHaveProperty('004', '4444444444444444444');

      const updatedChannels = configManager.getAllChannelIds();
      expect(updatedChannels).toHaveLength(4);
    });

    test('無効なチャンネル設定の自動除外', () => {
      // 無効な設定を追加
      process.env.CC_DISCORD_CHANNEL_ID_INVALID = 'not-a-channel-id';
      process.env.CC_DISCORD_CHANNEL_ID_EMPTY = '';

      const configManager = new ChannelConfigManager();
      const config = configManager.parseChannelConfig();

      // 無効な設定は除外され、有効な設定のみ残る
      expect(config).toEqual({
        '001': '1111111111111111111',
        '002': '1405815779198369903',
        '003': '3333333333333333333'
      });
      expect(config).not.toHaveProperty('INVALID');
      expect(config).not.toHaveProperty('EMPTY');
    });
  });

  describe('パフォーマンステスト', () => {
    test('大量チャンネル並列通知のパフォーマンス', async () => {
      const notifier = new MultiChannelNotifier();
      
      // 高速モック
      notifier._performSend = jest.fn().mockResolvedValue({ success: true });

      // 10チャンネルの並列通知
      const channels = Array.from({ length: 10 }, (_, i) => 
        `${(i + 1).toString().padStart(18, '0')}` // 18桁のチャンネルID
      );

      const startTime = Date.now();
      const results = await notifier.broadcastToChannels(channels, {
        content: 'Performance test'
      });
      const duration = Date.now() - startTime;

      expect(results).toHaveLength(10);
      expect(results.every(r => r.success)).toBe(true);
      expect(duration).toBeLessThan(5000); // 5秒以内
      expect(notifier._performSend).toHaveBeenCalledTimes(10);
    });

    test('キャッシュ効果による設定読み込み高速化', () => {
      const configManager = new ChannelConfigManager();
      
      const spy = jest.spyOn(configManager, 'parseChannelConfig');

      // 複数回の設定取得
      const startTime = Date.now();
      for (let i = 0; i < 100; i++) {
        configManager.getChannelConfig();
      }
      const duration = Date.now() - startTime;

      // キャッシュにより、パースは1回のみ実行
      expect(spy).toHaveBeenCalledTimes(1);
      expect(duration).toBeLessThan(100); // 100ms以内
    });
  });
});