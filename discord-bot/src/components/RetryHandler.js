/**
 * Discord API再試行処理ハンドラー
 * Track B先行実装 - エラーハンドリング強化の核心コンポーネント
 * 
 * @author AI Assistant (Track B)
 * @date 2025-08-25
 */

/**
 * 再試行可能エラーのパターン定義
 * @readonly
 * @enum {RegExp}
 */
const RETRYABLE_ERROR_PATTERNS = [
  /network timeout/i,
  /rate limit/i,
  /internal server error/i,
  /service unavailable/i,
  /connection reset/i,
  /socket hang up/i,
  /enotfound/i,
  /timeout/i,
  /500/i,
  /502/i,
  /503/i,
  /504/i
];

/**
 * 非再試行エラーのパターン定義
 * @readonly
 * @enum {RegExp}
 */
const NON_RETRYABLE_ERROR_PATTERNS = [
  /invalid token/i,
  /permission denied/i,
  /unauthorized/i,
  /forbidden/i,
  /bad request/i,
  /not found/i,
  /400/i,
  /401/i,
  /403/i,
  /404/i
];

/**
 * 再試行処理ハンドラークラス
 * Discord APIや外部サービスの一時的な障害に対する再試行戦略を提供
 */
export class RetryHandler {
  constructor(options = {}) {
    /**
     * 最大再試行回数
     * @type {number}
     * @private
     */
    this.maxRetries = options.maxRetries || 3;

    /**
     * 初期遅延時間（ミリ秒）
     * @type {number}
     * @private
     */
    this.baseDelay = options.baseDelay || 1000;

    /**
     * 指数バックオフの倍率
     * @type {number}
     * @private
     */
    this.backoffMultiplier = options.backoffMultiplier || 2;

    /**
     * 最大遅延時間（ミリ秒）
     * @type {number}
     * @private
     */
    this.maxDelay = options.maxDelay || 30000;
  }

  /**
   * 非同期操作を再試行付きで実行
   * @param {Function} asyncOperation - 実行する非同期操作
   * @param {Object} [options={}] - 再試行オプション
   * @returns {Promise<*>} 操作の結果
   */
  async retry(asyncOperation, options = {}) {
    const maxRetries = options.maxRetries || this.maxRetries;
    let lastError = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await asyncOperation();
        
        // 成功時のログ
        if (attempt > 0) {
          console.log(`✅ 再試行成功: ${attempt}回目の試行で成功`);
        }
        
        return result;
      } catch (error) {
        lastError = error;

        // 最終試行の場合は例外を投げる
        if (attempt >= maxRetries) {
          console.error(`❌ 再試行失敗: ${maxRetries}回試行後に諦め`, error.message);
          throw error;
        }

        // 再試行不可能なエラーの場合は即座に失敗
        if (!this.isRetryableError(error)) {
          console.error(`❌ 非再試行エラー: ${error.message}`);
          throw error;
        }

        // 遅延時間を計算
        const delay = this.calculateDelay(attempt);
        
        console.log(`⏳ 再試行予定: ${attempt + 1}/${maxRetries}回目 (${delay}ms後)`);
        
        // 遅延実行
        await this.delay(delay);
      }
    }

    // 理論的にはここに到達しないが、念のため
    throw lastError;
  }

  /**
   * エラーが再試行可能かどうかを判定
   * @param {Error} error - 判定するエラー
   * @returns {boolean} 再試行可能な場合はtrue
   */
  isRetryableError(error) {
    const message = error.message || '';

    // 非再試行エラーパターンに一致する場合は false
    for (const pattern of NON_RETRYABLE_ERROR_PATTERNS) {
      if (pattern.test(message)) {
        return false;
      }
    }

    // 再試行可能エラーパターンに一致する場合は true
    for (const pattern of RETRYABLE_ERROR_PATTERNS) {
      if (pattern.test(message)) {
        return true;
      }
    }

    // デフォルトでは再試行しない（安全側に倒す）
    return false;
  }

  /**
   * 指数バックオフによる遅延時間を計算
   * @param {number} attempt - 試行回数（0から始まる）
   * @returns {number} 遅延時間（ミリ秒）
   */
  calculateDelay(attempt) {
    const delay = this.baseDelay * Math.pow(this.backoffMultiplier, attempt);
    return Math.min(delay, this.maxDelay);
  }

  /**
   * 指定時間だけ遅延
   * @param {number} ms - 遅延時間（ミリ秒）
   * @returns {Promise<void>} 遅延完了Promise
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 再試行統計情報を取得
   * @param {Function} asyncOperation - 実行する非同期操作
   * @returns {Promise<{result: *, attempts: number, totalTime: number}>} 実行結果と統計
   */
  async retryWithStats(asyncOperation) {
    const startTime = Date.now();
    let attempts = 0;

    const wrappedOperation = async () => {
      attempts++;
      return await asyncOperation();
    };

    try {
      const result = await this.retry(wrappedOperation);
      const totalTime = Date.now() - startTime;

      return {
        result,
        attempts,
        totalTime,
        success: true
      };
    } catch (error) {
      const totalTime = Date.now() - startTime;

      return {
        result: null,
        attempts,
        totalTime,
        success: false,
        error: error.message
      };
    }
  }
}

/**
 * デフォルトの再試行ハンドラーインスタンス
 * @type {RetryHandler}
 */
export const defaultRetryHandler = new RetryHandler();