/**
 * ChannelConfigManager - Discord チャンネル設定の動的管理
 * 
 * 機能:
 * - .env環境変数からチャンネル設定を動的に解析
 * - セッション番号 → チャンネルID変換
 * - 設定情報のキャッシュ管理
 * - 設定変更の自動検出
 */

import { EventEmitter } from 'events';

export class ChannelConfigManager extends EventEmitter {
  constructor() {
    super();
    this._channelCache = null;
    this._lastCacheTime = null;
    this.cacheTimeout = 5 * 60 * 1000; // 5分キャッシュ
  }

  /**
   * .env環境変数からチャンネル設定をパース
   * @returns {Object} セッション → チャンネルID のマッピング
   */
  parseChannelConfig() {
    const channels = {};
    
    // CC_DISCORD_CHANNEL_ID_* パターンを検索
    Object.keys(process.env).forEach(key => {
      if (key.startsWith('CC_DISCORD_CHANNEL_ID_')) {
        const sessionNum = key.replace('CC_DISCORD_CHANNEL_ID_', '');
        const channelId = process.env[key];
        
        // 設定値検証
        if (this._isValidChannelId(channelId)) {
          channels[sessionNum] = channelId;
        } else {
          console.warn(`Invalid channel ID for session ${sessionNum}: ${channelId}`);
        }
      }
    });

    // デバッグ情報
    console.log(`🔍 Parsed ${Object.keys(channels).length} channel configurations:`, channels);
    
    return channels;
  }

  /**
   * セッション番号からチャンネルID取得（キャッシュ付き）
   * @param {string|number} sessionId セッション番号 (例: "002", "002_B", "002_C")
   * @returns {string|null} Discord チャンネルID
   */
  getChannelBySession(sessionId) {
    const channels = this.getChannelConfig();
    const sessionStr = String(sessionId);
    
    // まず完全一致を試行 (002_C など)
    let channelId = channels[sessionStr];
    
    // 完全一致しない場合、パディングを試行 ("1" -> "001")
    if (!channelId && /^\d+$/.test(sessionStr)) {
      const sessionKey = sessionStr.padStart(3, '0');
      channelId = channels[sessionKey];
    }
    
    if (!channelId) {
      console.warn(`⚠️ No channel configured for session: ${sessionId}`);
      console.warn(`Available sessions: ${Object.keys(channels).join(', ')}`);
      return null;
    }

    console.log(`✅ Session ${sessionId} -> Channel ${channelId}`);
    return channelId;
  }

  /**
   * 全チャンネル設定取得（キャッシュ機能付き）
   * @returns {Object} 全チャンネル設定
   */
  getChannelConfig() {
    const now = Date.now();
    
    // キャッシュが有効な場合はキャッシュを返す
    if (this._channelCache && 
        this._lastCacheTime && 
        (now - this._lastCacheTime) < this.cacheTimeout) {
      return this._channelCache;
    }

    // 設定を新規取得してキャッシュ
    this._channelCache = this.parseChannelConfig();
    this._lastCacheTime = now;
    
    this.emit('configUpdated', this._channelCache);
    return this._channelCache;
  }

  /**
   * 全チャンネルID一覧取得
   * @returns {Array<string>} チャンネルID配列
   */
  getAllChannelIds() {
    const channels = this.getChannelConfig();
    return Object.values(channels);
  }

  /**
   * 全セッション番号一覧取得
   * @returns {Array<string>} セッション番号配列
   */
  getAllSessionIds() {
    const channels = this.getChannelConfig();
    return Object.keys(channels);
  }

  /**
   * 特定チャンネルのセッション番号取得（逆引き）
   * @param {string} channelId Discord チャンネルID
   * @returns {string|null} セッション番号
   */
  getSessionByChannel(channelId) {
    const channels = this.getChannelConfig();
    
    for (const [sessionId, cId] of Object.entries(channels)) {
      if (cId === channelId) {
        return sessionId;
      }
    }
    
    return null;
  }

  /**
   * チャンネル設定の存在確認
   * @param {string|number} sessionId セッション番号
   * @returns {boolean} 設定存在フラグ
   */
  hasChannel(sessionId) {
    return this.getChannelBySession(sessionId) !== null;
  }

  /**
   * 設定キャッシュクリア
   */
  clearCache() {
    this._channelCache = null;
    this._lastCacheTime = null;
    console.log('🧹 Channel config cache cleared');
  }

  /**
   * 設定強制リロード
   * @returns {Object} 新しい設定
   */
  reloadConfig() {
    this.clearCache();
    const newConfig = this.getChannelConfig();
    console.log('🔄 Channel config reloaded:', newConfig);
    return newConfig;
  }

  /**
   * デフォルトチャンネルID取得
   * 設定された最初のチャンネルを返す
   * @returns {string|null} デフォルトチャンネルID
   */
  getDefaultChannelId() {
    const channels = this.getChannelConfig();
    const channelIds = Object.values(channels);
    
    if (channelIds.length === 0) {
      console.warn('⚠️ No channels configured');
      return null;
    }

    const defaultChannel = channelIds[0];
    console.log(`🔧 Using default channel: ${defaultChannel}`);
    return defaultChannel;
  }

  /**
   * 設定統計情報取得
   * @returns {Object} 統計情報
   */
  getConfigStats() {
    const channels = this.getChannelConfig();
    
    return {
      totalChannels: Object.keys(channels).length,
      sessionIds: Object.keys(channels),
      channelIds: Object.values(channels),
      cacheAge: this._lastCacheTime ? Date.now() - this._lastCacheTime : null,
      isCached: this._channelCache !== null
    };
  }

  /**
   * Discord チャンネルID形式の検証
   * @param {string} channelId チャンネルID
   * @returns {boolean} 有効性フラグ
   * @private
   */
  _isValidChannelId(channelId) {
    if (!channelId || typeof channelId !== 'string') {
      return false;
    }

    // Discord チャンネルIDは通常18-19桁の数字
    const discordIdPattern = /^[0-9]{17,19}$/;
    return discordIdPattern.test(channelId.trim());
  }
}