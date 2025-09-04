/**
 * EnvParser - 環境変数解析ユーティリティ
 * 
 * 機能:
 * - .env環境変数の構造化解析
 * - 設定値検証とエラーハンドリング
 * - 型安全な設定値取得
 */

export class EnvParser {
  /**
   * Discord チャンネル設定の解析
   * @returns {Object} 解析結果
   */
  static parseDiscordChannels() {
    const result = {
      channels: {},
      errors: [],
      warnings: []
    };

    try {
      // CC_DISCORD_CHANNEL_ID_* パターンのキーを収集
      const channelKeys = Object.keys(process.env)
        .filter(key => key.startsWith('CC_DISCORD_CHANNEL_ID_'))
        .sort(); // セッション順でソート

      console.log(`🔍 Found ${channelKeys.length} potential channel configurations`);

      for (const key of channelKeys) {
        try {
          const sessionId = this._extractSessionId(key);
          const channelId = process.env[key];

          // セッションID検証
          if (!this._isValidSessionId(sessionId)) {
            result.warnings.push(`Invalid session ID format: ${sessionId} (from ${key})`);
            continue;
          }

          // チャンネルID検証
          const channelValidation = this._validateChannelId(channelId, sessionId);
          if (!channelValidation.isValid) {
            result.errors.push(channelValidation.error);
            continue;
          }

          // 正常な設定として追加
          result.channels[sessionId] = channelId.trim();
          
        } catch (error) {
          result.errors.push(`Error parsing ${key}: ${error.message}`);
        }
      }

      // 解析結果サマリー
      const totalFound = channelKeys.length;
      const validConfigs = Object.keys(result.channels).length;
      const errorCount = result.errors.length;
      const warningCount = result.warnings.length;

      console.log(`📊 Channel parsing summary:`, {
        totalFound,
        validConfigs,
        errorCount,
        warningCount
      });

      // エラーがある場合はログ出力
      if (result.errors.length > 0) {
        console.error('❌ Channel configuration errors:', result.errors);
      }
      
      if (result.warnings.length > 0) {
        console.warn('⚠️ Channel configuration warnings:', result.warnings);
      }

      return result;

    } catch (error) {
      result.errors.push(`Critical parsing error: ${error.message}`);
      console.error('💥 Failed to parse Discord channel configuration:', error);
      return result;
    }
  }

  /**
   * Playwright 専用設定の解析
   * @returns {Object} Playwright設定
   */
  static parsePlaywrightConfig() {
    const config = {
      channelDetectionMode: process.env.PLAYWRIGHT_CHANNEL_DETECTION_MODE || 'auto',
      notificationTimeout: this._parseInteger(
        process.env.PLAYWRIGHT_NOTIFICATION_TIMEOUT, 
        5000, 
        'PLAYWRIGHT_NOTIFICATION_TIMEOUT'
      ),
      enableVideoAttachment: this._parseBoolean(
        process.env.PLAYWRIGHT_ENABLE_VIDEO_ATTACHMENT, 
        true
      ),
      enableScreenshotAttachment: this._parseBoolean(
        process.env.PLAYWRIGHT_ENABLE_SCREENSHOT_ATTACHMENT, 
        true
      ),
      maxRetryAttempts: this._parseInteger(
        process.env.PLAYWRIGHT_MAX_RETRY_ATTEMPTS, 
        3, 
        'PLAYWRIGHT_MAX_RETRY_ATTEMPTS'
      )
    };

    console.log('⚙️ Playwright configuration:', config);
    return config;
  }

  /**
   * 全体設定の統合解析
   * @returns {Object} 統合設定オブジェクト
   */
  static parseAllConfigurations() {
    const channelResult = this.parseDiscordChannels();
    const playwrightConfig = this.parsePlaywrightConfig();

    const result = {
      channels: channelResult.channels,
      playwright: playwrightConfig,
      errors: channelResult.errors,
      warnings: channelResult.warnings,
      isValid: channelResult.errors.length === 0,
      stats: {
        totalChannels: Object.keys(channelResult.channels).length,
        hasErrors: channelResult.errors.length > 0,
        hasWarnings: channelResult.warnings.length > 0
      }
    };

    // 設定が空の場合の警告
    if (Object.keys(result.channels).length === 0) {
      result.warnings.push('No valid Discord channel configurations found');
    }

    return result;
  }

  /**
   * 環境変数キーからセッションIDを抽出
   * @param {string} envKey 環境変数キー
   * @returns {string} セッションID
   * @private
   */
  static _extractSessionId(envKey) {
    return envKey.replace('CC_DISCORD_CHANNEL_ID_', '');
  }

  /**
   * セッションID形式の検証
   * @param {string} sessionId セッションID
   * @returns {boolean} 有効性
   * @private
   */
  static _isValidSessionId(sessionId) {
    if (!sessionId || typeof sessionId !== 'string') {
      return false;
    }

    // 3桁の数字パターン、または1-4桁の数字
    const sessionPattern = /^(?:[0-9]{3}|[0-9]{1,4})$/;
    return sessionPattern.test(sessionId);
  }

  /**
   * チャンネルIDの詳細検証
   * @param {string} channelId チャンネルID
   * @param {string} sessionId セッションID（エラー用）
   * @returns {Object} 検証結果
   * @private
   */
  static _validateChannelId(channelId, sessionId) {
    if (!channelId) {
      return {
        isValid: false,
        error: `Empty channel ID for session ${sessionId}`
      };
    }

    if (typeof channelId !== 'string') {
      return {
        isValid: false,
        error: `Channel ID for session ${sessionId} must be a string, got ${typeof channelId}`
      };
    }

    const trimmedId = channelId.trim();
    
    // Discord チャンネルIDは17-19桁の数字
    const discordIdPattern = /^[0-9]{17,19}$/;
    if (!discordIdPattern.test(trimmedId)) {
      return {
        isValid: false,
        error: `Invalid Discord channel ID format for session ${sessionId}: ${channelId}`
      };
    }

    return {
      isValid: true,
      channelId: trimmedId
    };
  }

  /**
   * 整数型環境変数のパース
   * @param {string} value 環境変数値
   * @param {number} defaultValue デフォルト値
   * @param {string} varName 変数名（エラー用）
   * @returns {number} パース結果
   * @private
   */
  static _parseInteger(value, defaultValue, varName) {
    if (!value) {
      return defaultValue;
    }

    const parsed = parseInt(value, 10);
    if (isNaN(parsed)) {
      console.warn(`⚠️ Invalid integer value for ${varName}: ${value}, using default: ${defaultValue}`);
      return defaultValue;
    }

    return parsed;
  }

  /**
   * 真偽値型環境変数のパース
   * @param {string} value 環境変数値
   * @param {boolean} defaultValue デフォルト値
   * @returns {boolean} パース結果
   * @private
   */
  static _parseBoolean(value, defaultValue) {
    if (!value) {
      return defaultValue;
    }

    const lowerValue = value.toLowerCase().trim();
    return lowerValue === 'true' || lowerValue === '1' || lowerValue === 'yes';
  }
}