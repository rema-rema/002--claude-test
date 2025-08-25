/**
 * テスト失敗回数管理コンポーネント
 * Track B先行実装 - 同一エラー10回制限処理
 * 
 * @author AI Assistant (Track B)
 * @date 2025-08-25
 */

/**
 * 失敗回数制限の定数定義
 */
const DEFAULT_FAILURE_LIMIT = 10;
const CLEANUP_INTERVAL_MS = 60 * 60 * 1000; // 1時間
const MAX_ENTRY_AGE_MS = 24 * 60 * 60 * 1000; // 24時間

/**
 * テスト失敗カウンター管理クラス
 * 同一テスト・同一エラーパターンの失敗回数を追跡し、制限到達時に人間判断へ移行
 */
export class FailureCounter {
  constructor(options = {}) {
    /**
     * 失敗回数制限
     * @type {number}
     * @private
     */
    this.failureLimit = options.failureLimit || DEFAULT_FAILURE_LIMIT;

    /**
     * 失敗カウンター（テスト名+エラーパターン別）
     * Key: testName:errorPattern, Value: {count, firstSeen, lastSeen, errors}
     * @type {Map<string, Object>}
     * @private
     */
    this.failureCounts = new Map();

    /**
     * クリーンアップタイマー
     * @type {NodeJS.Timeout|null}
     * @private
     */
    this.cleanupTimer = null;

    // 定期クリーンアップを開始
    this._startCleanupTimer();
  }

  /**
   * 失敗回数をインクリメント
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @returns {number} 現在の失敗回数
   */
  increment(testName, errorMessage) {
    const key = this._createKey(testName, errorMessage);
    const now = new Date();

    if (this.failureCounts.has(key)) {
      const entry = this.failureCounts.get(key);
      entry.count++;
      entry.lastSeen = now;
      entry.errors.push({
        message: errorMessage,
        timestamp: now
      });

      console.log(`📊 失敗カウント更新: ${testName} - ${entry.count}/${this.failureLimit}`);
    } else {
      const entry = {
        count: 1,
        firstSeen: now,
        lastSeen: now,
        errors: [{
          message: errorMessage,
          timestamp: now
        }]
      };
      this.failureCounts.set(key, entry);

      console.log(`🆕 新規失敗カウント開始: ${testName} - 1/${this.failureLimit}`);
    }

    const currentCount = this.failureCounts.get(key).count;

    // 制限に近づいた場合の警告
    if (currentCount >= this.failureLimit * 0.8) {
      console.warn(`⚠️ 失敗制限接近: ${testName} - ${currentCount}/${this.failureLimit}`);
    }

    return currentCount;
  }

  /**
   * 指定されたテスト・エラーパターンの失敗回数を取得
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @returns {number} 失敗回数
   */
  getCount(testName, errorMessage) {
    const key = this._createKey(testName, errorMessage);
    const entry = this.failureCounts.get(key);
    return entry ? entry.count : 0;
  }

  /**
   * 制限に達しているかを確認
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @returns {boolean} 制限に達している場合はtrue
   */
  hasReachedLimit(testName, errorMessage) {
    const count = this.getCount(testName, errorMessage);
    return count >= this.failureLimit;
  }

  /**
   * 指定されたテストの失敗カウンターをリセット
   * @param {string} testName - テスト名
   * @param {string} [errorMessage] - エラーメッセージ（指定時は該当パターンのみリセット）
   */
  reset(testName, errorMessage = null) {
    if (errorMessage) {
      // 特定のエラーパターンのみリセット
      const key = this._createKey(testName, errorMessage);
      if (this.failureCounts.has(key)) {
        this.failureCounts.delete(key);
        console.log(`🔄 失敗カウンターリセット: ${testName} - ${errorMessage}`);
      }
    } else {
      // 該当テストのすべてのエラーパターンをリセット
      const keysToDelete = [];
      for (const key of this.failureCounts.keys()) {
        if (key.startsWith(`${testName}:`)) {
          keysToDelete.push(key);
        }
      }

      keysToDelete.forEach(key => this.failureCounts.delete(key));
      
      if (keysToDelete.length > 0) {
        console.log(`🔄 失敗カウンター全リセット: ${testName} - ${keysToDelete.length}パターン`);
      }
    }
  }

  /**
   * すべての失敗カウンターをリセット
   */
  resetAll() {
    const totalCount = this.failureCounts.size;
    this.failureCounts.clear();
    console.log(`🔄 全失敗カウンターリセット: ${totalCount}エントリ`);
  }

  /**
   * 失敗統計情報を取得
   * @returns {Object} 統計情報
   */
  getStatistics() {
    const stats = {
      totalEntries: this.failureCounts.size,
      entriesNearLimit: 0,
      entriesAtLimit: 0,
      byTestName: {},
      oldestEntry: null,
      newestEntry: null
    };

    let oldestTime = null;
    let newestTime = null;

    for (const [key, entry] of this.failureCounts.entries()) {
      const [testName] = key.split(':');

      // テスト名別統計
      if (!stats.byTestName[testName]) {
        stats.byTestName[testName] = {
          patterns: 0,
          totalFailures: 0,
          maxCount: 0
        };
      }

      stats.byTestName[testName].patterns++;
      stats.byTestName[testName].totalFailures += entry.count;
      stats.byTestName[testName].maxCount = Math.max(
        stats.byTestName[testName].maxCount,
        entry.count
      );

      // 制限関連統計
      if (entry.count >= this.failureLimit) {
        stats.entriesAtLimit++;
      } else if (entry.count >= this.failureLimit * 0.8) {
        stats.entriesNearLimit++;
      }

      // 時刻統計
      if (!oldestTime || entry.firstSeen < oldestTime) {
        oldestTime = entry.firstSeen;
        stats.oldestEntry = { key, firstSeen: entry.firstSeen };
      }

      if (!newestTime || entry.lastSeen > newestTime) {
        newestTime = entry.lastSeen;
        stats.newestEntry = { key, lastSeen: entry.lastSeen };
      }
    }

    return stats;
  }

  /**
   * 制限に達したエントリの詳細を取得
   * @returns {Array<Object>} 制限到達エントリリスト
   */
  getLimitReachedEntries() {
    const entries = [];

    for (const [key, entry] of this.failureCounts.entries()) {
      if (entry.count >= this.failureLimit) {
        const [testName, errorPattern] = key.split(':', 2);
        entries.push({
          testName,
          errorPattern,
          count: entry.count,
          firstSeen: entry.firstSeen,
          lastSeen: entry.lastSeen,
          duration: entry.lastSeen - entry.firstSeen,
          recentErrors: entry.errors.slice(-3) // 最新3件のエラー
        });
      }
    }

    return entries.sort((a, b) => b.count - a.count); // 失敗回数降順
  }

  /**
   * 古いエントリをクリーンアップ
   */
  cleanup() {
    const now = new Date();
    const cutoffTime = new Date(now.getTime() - MAX_ENTRY_AGE_MS);
    let cleanedCount = 0;

    for (const [key, entry] of this.failureCounts.entries()) {
      if (entry.lastSeen < cutoffTime) {
        this.failureCounts.delete(key);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      console.log(`🧹 失敗カウンタークリーンアップ: ${cleanedCount}エントリ削除`);
    }

    return cleanedCount;
  }

  /**
   * リソースを解放
   */
  destroy() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
    this.failureCounts.clear();
  }

  /**
   * キーを生成（テスト名とエラーパターンから）
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @returns {string} キー
   * @private
   */
  _createKey(testName, errorMessage) {
    // エラーメッセージから主要パターンを抽出（最初の50文字）
    const errorPattern = this._extractErrorPattern(errorMessage);
    return `${testName}:${errorPattern}`;
  }

  /**
   * エラーメッセージから主要パターンを抽出
   * @param {string} errorMessage - エラーメッセージ
   * @returns {string} エラーパターン
   * @private
   */
  _extractErrorPattern(errorMessage) {
    // 数値や時間などの動的部分を正規化
    let pattern = errorMessage
      .replace(/\d+/g, 'N') // 数値をNに置換
      .replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/g, 'TIMESTAMP') // タイムスタンプ
      .substring(0, 50); // 50文字で切る

    return pattern;
  }

  /**
   * 定期クリーンアップタイマーを開始
   * @private
   */
  _startCleanupTimer() {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, CLEANUP_INTERVAL_MS);
  }
}

/**
 * デフォルトの失敗カウンターインスタンス
 * @type {FailureCounter}
 */
export const defaultFailureCounter = new FailureCounter();