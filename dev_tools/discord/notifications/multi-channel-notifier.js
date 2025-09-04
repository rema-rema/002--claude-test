/**
 * MultiChannelNotifier - マルチチャンネル Discord 通知システム
 * 
 * 機能:
 * - チャンネル固有通知送信
 * - 複数チャンネル一斉通知
 * - 通知失敗時のリトライ機能
 * - Discord APIレート制限対応
 */

import { EventEmitter } from 'events';

export class MultiChannelNotifier extends EventEmitter {
  constructor(options = {}) {
    super();
    
    // 設定
    this.config = {
      maxRetryAttempts: options.maxRetryAttempts || 3,
      baseRetryDelay: options.baseRetryDelay || 1000, // 1秒
      maxRetryDelay: options.maxRetryDelay || 30000,  // 30秒
      requestTimeout: options.requestTimeout || 10000, // 10秒
      rateLimitBuffer: options.rateLimitBuffer || 100, // 100ms
      ...options
    };

    // 状態管理
    this.rateLimitInfo = new Map(); // チャンネル別レート制限情報
    this.pendingRequests = new Map(); // 保留中リクエスト
    this.stats = {
      totalSent: 0,
      successCount: 0,
      failureCount: 0,
      retryCount: 0
    };

    console.log('🚀 MultiChannelNotifier initialized:', this.config);
  }

  /**
   * 特定チャンネルに通知送信（メイン機能）
   * @param {string} channelId Discord チャンネルID
   * @param {Object} message メッセージオブジェクト
   * @param {Array} attachments 添付ファイル配列
   * @returns {Promise<Object>} 送信結果
   */
  async sendToChannel(channelId, message, attachments = []) {
    const startTime = Date.now();
    
    try {
      // 入力検証
      this._validateChannelInput(channelId, message);

      // レート制限チェック
      await this._enforceRateLimit(channelId);

      console.log(`📨 Sending notification to channel ${channelId}:`, {
        messageType: typeof message,
        attachmentCount: attachments.length
      });

      // 通知送信実行
      const result = await this._performSendWithRetry(channelId, message, attachments);

      // 成功統計更新
      this._updateStats('success', Date.now() - startTime);
      
      this.emit('notificationSent', {
        channelId,
        success: true,
        duration: Date.now() - startTime,
        attachmentCount: attachments.length
      });

      return result;

    } catch (error) {
      // 失敗統計更新
      this._updateStats('failure', Date.now() - startTime);
      
      this.emit('notificationFailed', {
        channelId,
        error: error.message,
        duration: Date.now() - startTime
      });

      console.error(`❌ Failed to send notification to channel ${channelId}:`, error);
      throw error;
    }
  }

  /**
   * 複数チャンネルへの一斉通知
   * @param {Array<string>} channelIds チャンネルID配列
   * @param {Object} message メッセージ
   * @param {Array} attachments 添付ファイル配列
   * @returns {Promise<Array>} 各チャンネルの送信結果
   */
  async broadcastToChannels(channelIds, message, attachments = []) {
    if (!Array.isArray(channelIds) || channelIds.length === 0) {
      throw new Error('チャンネルIDの配列が必要です');
    }

    console.log(`📢 Broadcasting to ${channelIds.length} channels:`, channelIds);

    const results = [];
    const concurrentLimit = 3; // 同時並列数制限
    
    // チャンネルを並列処理用にグループ分け
    for (let i = 0; i < channelIds.length; i += concurrentLimit) {
      const batch = channelIds.slice(i, i + concurrentLimit);
      
      // バッチ単位で並列実行
      const batchPromises = batch.map(async (channelId) => {
        try {
          const result = await this.sendToChannel(channelId, message, attachments);
          return { channelId, success: true, result };
        } catch (error) {
          return { channelId, success: false, error: error.message };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // バッチ間の間隔（レート制限対策）
      if (i + concurrentLimit < channelIds.length) {
        await this._sleep(this.config.rateLimitBuffer);
      }
    }

    // 統計情報
    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;
    
    console.log(`📊 Broadcast complete: ${successCount}/${results.length} successful`);

    this.emit('broadcastComplete', {
      totalChannels: channelIds.length,
      successCount,
      failureCount,
      results
    });

    return results;
  }

  /**
   * 通知失敗時のリトライ処理
   * @param {string} channelId チャンネルID
   * @param {Object} payload 送信ペイロード
   * @returns {Promise<Object>} リトライ結果
   */
  async retryNotification(channelId, payload) {
    const maxAttempts = this.config.maxRetryAttempts;
    let lastError = null;

    console.log(`🔄 Starting retry for channel ${channelId}, max attempts: ${maxAttempts}`);

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        // 指数バックオフ遅延
        if (attempt > 1) {
          const delay = this._calculateBackoffDelay(attempt);
          console.log(`⏳ Retry attempt ${attempt}/${maxAttempts} after ${delay}ms delay`);
          await this._sleep(delay);
        }

        // リトライ実行
        const result = await this._performSend(channelId, payload.message, payload.attachments);
        
        console.log(`✅ Retry successful on attempt ${attempt}/${maxAttempts}`);
        this.stats.retryCount++;
        
        return result;

      } catch (error) {
        lastError = error;
        console.warn(`⚠️ Retry attempt ${attempt}/${maxAttempts} failed:`, error.message);
        
        // Discord APIエラーの場合、特定エラーでは早期終了
        if (this._isNonRetryableError(error)) {
          console.error('💥 Non-retryable error encountered, stopping retry');
          break;
        }
      }
    }

    // 全リトライ失敗
    throw new Error(`All retry attempts failed. Last error: ${lastError?.message}`);
  }

  /**
   * 統計情報取得
   * @returns {Object} 統計情報
   */
  getStats() {
    return {
      ...this.stats,
      successRate: this.stats.totalSent > 0 ? 
        (this.stats.successCount / this.stats.totalSent * 100).toFixed(2) + '%' : '0%',
      rateLimitChannels: this.rateLimitInfo.size,
      pendingRequests: this.pendingRequests.size
    };
  }

  /**
   * レート制限情報リセット
   */
  resetRateLimits() {
    this.rateLimitInfo.clear();
    console.log('🧹 Rate limit information cleared');
  }

  /**
   * レート制限強制実行
   * @param {string} channelId チャンネルID
   * @returns {Promise<void>}
   * @private
   */
  async _enforceRateLimit(channelId) {
    const limitInfo = this.rateLimitInfo.get(channelId);
    
    if (limitInfo && limitInfo.resetTime > Date.now()) {
      const waitTime = limitInfo.resetTime - Date.now() + this.config.rateLimitBuffer;
      console.log(`⏳ Rate limit active for channel ${channelId}, waiting ${waitTime}ms`);
      await this._sleep(waitTime);
    }
  }

  /**
   * リトライ付き送信実行
   * @param {string} channelId チャンネルID
   * @param {Object} message メッセージ
   * @param {Array} attachments 添付ファイル
   * @returns {Promise<Object>} 送信結果
   * @private
   */
  async _performSendWithRetry(channelId, message, attachments) {
    try {
      return await this._performSend(channelId, message, attachments);
    } catch (error) {
      // リトライが有効かつ、リトライ可能エラーの場合
      if (this.config.maxRetryAttempts > 1 && !this._isNonRetryableError(error)) {
        console.log(`🔄 Initial send failed, starting retry process: ${error.message}`);
        return await this.retryNotification(channelId, { message, attachments });
      } else {
        throw error;
      }
    }
  }

  /**
   * 実際の送信処理（dp コマンド経由での Discord 送信）
   * @param {string} channelId チャンネルID
   * @param {Object} message メッセージ
   * @param {Array} attachments 添付ファイル
   * @returns {Promise<Object>} 送信結果
   * @private
   */
  async _performSend(channelId, message, attachments) {
    // dp コマンドを使用してDiscordに送信
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    
    try {
      // メッセージ内容を準備
      const messageContent = typeof message === 'string' ? message : message.content;
      
      // 添付ファイルは現在未対応（将来的に実装可能）
      if (attachments && attachments.length > 0) {
        console.log(`📎 Warning: Attachments not yet supported (${attachments.length} files skipped)`);
      }
      
      // エスケープ処理
      const escapedMessage = messageContent
        .replace(/\\/g, '\\\\')  // バックスラッシュをエスケープ
        .replace(/"/g, '\\"')    // ダブルクォートをエスケープ
        .replace(/\n/g, '\\n');  // 改行をエスケープ
      
      // dp コマンド実行（claude-discord-bridge-serverディレクトリから実行）
      const command = `cd /home/rema/project/002--claude-test/claude-discord-bridge-server && echo "${escapedMessage}" | python3 src/discord_post.py ${channelId}`;
      
      console.log(`🔗 Executing dp command for channel ${channelId}`);
      const { stdout, stderr } = await execAsync(command, { 
        timeout: this.config.requestTimeout,
        cwd: '/home/rema/project/002--claude-test/claude-discord-bridge-server'
      });
      
      if (stderr && !stderr.includes('Warning')) {
        throw new Error(`Discord post error: ${stderr}`);
      }
      
      return {
        success: true,
        channelId,
        timestamp: new Date().toISOString(),
        messageId: null, // dp コマンドはメッセージIDを返さない
        stdout: stdout?.trim(),
        stderr: stderr?.trim()
      };
      
    } catch (error) {
      // Discord APIエラーの処理
      if (error.message.includes('status 429') || error.message.includes('rate limit')) {
        // レート制限エラー
        this._handleRateLimitError(channelId, error);
      }
      throw error;
    }
  }

  /**
   * 入力検証
   * @param {string} channelId チャンネルID
   * @param {Object} message メッセージ
   * @private
   */
  _validateChannelInput(channelId, message) {
    if (!channelId || typeof channelId !== 'string') {
      throw new Error('有効なチャンネルIDが必要です');
    }

    if (!message) {
      throw new Error('メッセージが必要です');
    }

    // Discord チャンネルID形式チェック
    if (!/^[0-9]{17,19}$/.test(channelId)) {
      throw new Error(`無効なDiscordチャンネルID形式: ${channelId}`);
    }
  }

  /**
   * 統計更新
   * @param {string} type 'success' | 'failure'
   * @param {number} duration 処理時間
   * @private
   */
  _updateStats(type, duration) {
    this.stats.totalSent++;
    if (type === 'success') {
      this.stats.successCount++;
    } else {
      this.stats.failureCount++;
    }
  }

  /**
   * 指数バックオフ遅延計算
   * @param {number} attempt 試行回数
   * @returns {number} 遅延時間（ミリ秒）
   * @private
   */
  _calculateBackoffDelay(attempt) {
    const baseDelay = this.config.baseRetryDelay;
    const maxDelay = this.config.maxRetryDelay;
    
    // 指数バックオフ + ジッター
    const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
    const jitter = Math.random() * 0.3 * exponentialDelay; // 30%ジッター
    
    return Math.min(exponentialDelay + jitter, maxDelay);
  }

  /**
   * 非リトライ可能エラーの判定
   * @param {Error} error エラーオブジェクト
   * @returns {boolean} 非リトライ可能フラグ
   * @private
   */
  _isNonRetryableError(error) {
    // 400番台エラー（クライアントエラー）は基本的にリトライしない
    if (error.status >= 400 && error.status < 500) {
      // ただし、レート制限(429)とサーバー過負荷(503)はリトライ可能
      return error.status !== 429 && error.status !== 503;
    }
    
    return false;
  }

  /**
   * レート制限情報の更新
   * @param {string} channelId チャンネルID
   * @param {Object} headers レスポンスヘッダー
   * @private
   */
  _updateRateLimitInfo(channelId, headers = {}) {
    if (headers['x-ratelimit-remaining']) {
      const remaining = parseInt(headers['x-ratelimit-remaining']);
      const resetTime = headers['x-ratelimit-reset'] ? 
        new Date(headers['x-ratelimit-reset']).getTime() : Date.now() + 1000;

      this.rateLimitInfo.set(channelId, {
        remaining,
        resetTime,
        updatedAt: Date.now()
      });
    }
  }

  /**
   * レート制限エラー処理
   * @param {string} channelId チャンネルID
   * @param {Error} error レート制限エラー
   * @private
   */
  _handleRateLimitError(channelId, error) {
    const retryAfter = error.retryAfter || 1; // seconds
    const resetTime = Date.now() + (retryAfter * 1000);
    
    this.rateLimitInfo.set(channelId, {
      remaining: 0,
      resetTime,
      updatedAt: Date.now()
    });

    console.warn(`⚠️ Rate limit hit for channel ${channelId}, retry after: ${retryAfter}s`);
  }

  /**
   * Sleep ユーティリティ
   * @param {number} ms ミリ秒
   * @returns {Promise<void>}
   * @private
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}