/**
 * ChannelConfigManager 単体テスト
 */

import { jest } from '@jest/globals';
import { ChannelConfigManager } from '../../src/multichannel-notify/channel-config-manager.js';

describe('ChannelConfigManager', () => {
  let originalEnv;
  let manager;

  beforeEach(() => {
    // 環境変数をバックアップ
    originalEnv = process.env;
    
    // テスト用環境変数設定
    process.env = {
      ...originalEnv,
      CC_DISCORD_CHANNEL_ID_001: '1111111111111111111',
      CC_DISCORD_CHANNEL_ID_002: '1405815779198369903',
      CC_DISCORD_CHANNEL_ID_003: '3333333333333333333'
    };

    manager = new ChannelConfigManager();
  });

  afterEach(() => {
    // 環境変数を復元
    process.env = originalEnv;
    jest.clearAllMocks();
  });

  describe('parseChannelConfig()', () => {
    test('正常な設定をパースできる', () => {
      const config = manager.parseChannelConfig();
      
      expect(config).toEqual({
        '001': '1111111111111111111',
        '002': '1405815779198369903', 
        '003': '3333333333333333333'
      });
    });

    test('無効なチャンネルIDを除外する', () => {
      process.env.CC_DISCORD_CHANNEL_ID_004 = 'invalid-id';
      process.env.CC_DISCORD_CHANNEL_ID_005 = '';
      
      const config = manager.parseChannelConfig();
      
      expect(config).toEqual({
        '001': '1111111111111111111',
        '002': '1405815779198369903',
        '003': '3333333333333333333'
      });
      expect(config).not.toHaveProperty('004');
      expect(config).not.toHaveProperty('005');
    });

    test('チャンネル設定が存在しない場合は空オブジェクト', () => {
      // 全ての設定をクリア
      Object.keys(process.env).forEach(key => {
        if (key.startsWith('CC_DISCORD_CHANNEL_ID_')) {
          delete process.env[key];
        }
      });

      const config = manager.parseChannelConfig();
      expect(config).toEqual({});
    });
  });

  describe('getChannelBySession()', () => {
    test('数字のセッションIDでチャンネルを取得できる', () => {
      const channelId = manager.getChannelBySession(2);
      expect(channelId).toBe('1405815779198369903');
    });

    test('文字列のセッションIDでチャンネルを取得できる', () => {
      const channelId = manager.getChannelBySession('002');
      expect(channelId).toBe('1405815779198369903');
    });

    test('0埋めされたセッションIDでチャンネルを取得できる', () => {
      const channelId = manager.getChannelBySession('001');
      expect(channelId).toBe('1111111111111111111');
    });

    test('存在しないセッションIDの場合はnullを返す', () => {
      const channelId = manager.getChannelBySession(999);
      expect(channelId).toBeNull();
    });

    test('不正なセッションIDの場合はnullを返す', () => {
      expect(manager.getChannelBySession('')).toBeNull();
      expect(manager.getChannelBySession(null)).toBeNull();
      expect(manager.getChannelBySession(undefined)).toBeNull();
    });
  });

  describe('getAllChannelIds()', () => {
    test('全チャンネルIDを配列で返す', () => {
      const channelIds = manager.getAllChannelIds();
      
      expect(channelIds).toEqual([
        '1111111111111111111',
        '1405815779198369903',
        '3333333333333333333'
      ]);
      expect(channelIds).toHaveLength(3);
    });

    test('設定がない場合は空配列を返す', () => {
      // 設定をクリア
      Object.keys(process.env).forEach(key => {
        if (key.startsWith('CC_DISCORD_CHANNEL_ID_')) {
          delete process.env[key];
        }
      });

      const channelIds = manager.getAllChannelIds();
      expect(channelIds).toEqual([]);
    });
  });

  describe('getSessionByChannel()', () => {
    test('チャンネルIDからセッション番号を取得できる', () => {
      const sessionId = manager.getSessionByChannel('1405815779198369903');
      expect(sessionId).toBe('002');
    });

    test('存在しないチャンネルIDの場合はnullを返す', () => {
      const sessionId = manager.getSessionByChannel('9999999999999999999');
      expect(sessionId).toBeNull();
    });

    test('不正なチャンネルIDの場合はnullを返す', () => {
      expect(manager.getSessionByChannel('')).toBeNull();
      expect(manager.getSessionByChannel(null)).toBeNull();
    });
  });

  describe('hasChannel()', () => {
    test('存在するセッションの場合はtrue', () => {
      expect(manager.hasChannel(1)).toBe(true);
      expect(manager.hasChannel('002')).toBe(true);
      expect(manager.hasChannel('003')).toBe(true);
    });

    test('存在しないセッションの場合はfalse', () => {
      expect(manager.hasChannel(999)).toBe(false);
      expect(manager.hasChannel('999')).toBe(false);
    });
  });

  describe('getDefaultChannelId()', () => {
    test('設定された最初のチャンネルIDを返す', () => {
      const defaultChannel = manager.getDefaultChannelId();
      expect(defaultChannel).toBe('1111111111111111111');
    });

    test('設定がない場合はnullを返す', () => {
      // 設定をクリア
      Object.keys(process.env).forEach(key => {
        if (key.startsWith('CC_DISCORD_CHANNEL_ID_')) {
          delete process.env[key];
        }
      });

      const defaultChannel = manager.getDefaultChannelId();
      expect(defaultChannel).toBeNull();
    });
  });

  describe('キャッシュ機能', () => {
    test('キャッシュが有効な間は同じ結果を返す', () => {
      const spy = jest.spyOn(manager, 'parseChannelConfig');
      
      // 初回呼び出し
      const config1 = manager.getChannelConfig();
      expect(spy).toHaveBeenCalledTimes(1);
      
      // 2回目はキャッシュから取得
      const config2 = manager.getChannelConfig();
      expect(spy).toHaveBeenCalledTimes(1);
      expect(config1).toEqual(config2);
    });

    test('clearCache()でキャッシュがクリアされる', () => {
      const spy = jest.spyOn(manager, 'parseChannelConfig');
      
      // キャッシュ作成
      manager.getChannelConfig();
      expect(spy).toHaveBeenCalledTimes(1);
      
      // キャッシュクリア
      manager.clearCache();
      
      // 再度呼び出しでキャッシュが再作成される
      manager.getChannelConfig();
      expect(spy).toHaveBeenCalledTimes(2);
    });

    test('reloadConfig()で強制リロードできる', () => {
      const spy = jest.spyOn(manager, 'parseChannelConfig');
      
      // 初回読み込み
      const config1 = manager.getChannelConfig();
      expect(spy).toHaveBeenCalledTimes(1);
      
      // 設定変更
      process.env.CC_DISCORD_CHANNEL_ID_004 = '4444444444444444444';
      
      // 強制リロード
      const config2 = manager.reloadConfig();
      expect(spy).toHaveBeenCalledTimes(2);
      expect(config2).toHaveProperty('004', '4444444444444444444');
    });
  });

  describe('getConfigStats()', () => {
    test('統計情報を正しく返す', () => {
      // キャッシュを作成
      manager.getChannelConfig();
      
      const stats = manager.getConfigStats();
      
      expect(stats).toMatchObject({
        totalChannels: 3,
        sessionIds: ['001', '002', '003'],
        channelIds: [
          '1111111111111111111',
          '1405815779198369903',
          '3333333333333333333'
        ],
        isCached: true
      });
      expect(stats.cacheAge).toBeGreaterThanOrEqual(0);
    });
  });

  describe('イベントエミッション', () => {
    test('設定更新時にconfigUpdatedイベントが発火される', (done) => {
      manager.on('configUpdated', (config) => {
        expect(config).toHaveProperty('001');
        expect(config).toHaveProperty('002');
        expect(config).toHaveProperty('003');
        done();
      });

      manager.getChannelConfig();
    });
  });
});