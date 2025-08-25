/**
 * エラー分類・分析コンポーネント
 * Track B先行実装 - エラーハンドリング強化の分析エンジン
 * 
 * @author AI Assistant (Track B)
 * @date 2025-08-25
 */

/**
 * エラー重要度レベル
 * @readonly
 * @enum {string}
 */
export const ErrorSeverity = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL'
};

/**
 * エラーカテゴリ
 * @readonly
 * @enum {string}
 */
export const ErrorCategory = {
  NETWORK: 'NETWORK',
  AUTHENTICATION: 'AUTHENTICATION',
  PERMISSION: 'PERMISSION',
  RATE_LIMIT: 'RATE_LIMIT',
  SERVER_ERROR: 'SERVER_ERROR',
  CLIENT_ERROR: 'CLIENT_ERROR',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
};

/**
 * エラー分類パターン定義
 * @type {Array<{pattern: RegExp, category: string, severity: string, transient: boolean}>}
 */
const ERROR_CLASSIFICATION_RULES = [
  // ネットワーク関連エラー
  {
    pattern: /network timeout|connection reset|socket hang up|enotfound/i,
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.MEDIUM,
    transient: true
  },

  // 認証エラー
  {
    pattern: /invalid token|unauthorized|authentication failed/i,
    category: ErrorCategory.AUTHENTICATION,
    severity: ErrorSeverity.HIGH,
    transient: false
  },

  // 権限エラー
  {
    pattern: /permission denied|forbidden|access denied/i,
    category: ErrorCategory.PERMISSION,
    severity: ErrorSeverity.HIGH,
    transient: false
  },

  // レート制限
  {
    pattern: /rate limit|too many requests|429/i,
    category: ErrorCategory.RATE_LIMIT,
    severity: ErrorSeverity.MEDIUM,
    transient: true
  },

  // サーバーエラー (5xx)
  {
    pattern: /internal server error|service unavailable|bad gateway|500|502|503|504/i,
    category: ErrorCategory.SERVER_ERROR,
    severity: ErrorSeverity.HIGH,
    transient: true
  },

  // クライアントエラー (4xx)
  {
    pattern: /bad request|not found|400|404/i,
    category: ErrorCategory.CLIENT_ERROR,
    severity: ErrorSeverity.MEDIUM,
    transient: false
  },

  // タイムアウト
  {
    pattern: /timeout|timed out/i,
    category: ErrorCategory.TIMEOUT,
    severity: ErrorSeverity.MEDIUM,
    transient: true
  }
];

/**
 * エラー分類・分析クラス
 * エラーメッセージを解析し、カテゴリ、重要度、一時性を判定
 */
export class ErrorClassifier {
  constructor() {
    /**
     * 分類統計情報
     * @type {Map<string, number>}
     * @private
     */
    this.classificationStats = new Map();
  }

  /**
   * エラーを分類・分析
   * @param {Error|string} error - 分析するエラーまたはエラーメッセージ
   * @returns {Object} 分析結果
   */
  classify(error) {
    const message = typeof error === 'string' ? error : (error.message || '');
    const stack = typeof error === 'object' ? error.stack : '';

    // 分類ルールに基づいて判定
    const classification = this._findMatchingRule(message);

    // 統計情報更新
    this._updateStats(classification.category);

    const result = {
      category: classification.category,
      severity: classification.severity,
      transient: classification.transient,
      message: message.substring(0, 200), // メッセージを200文字で制限
      timestamp: new Date().toISOString(),
      id: this._generateErrorId()
    };

    // スタックトレースがある場合は追加情報を抽出
    if (stack) {
      result.stackTrace = this._extractStackInfo(stack);
    }

    return result;
  }

  /**
   * エラーが一時的（再試行可能）かどうかを判定
   * @param {Error|string} error - 判定するエラー
   * @returns {boolean} 一時的エラーの場合はtrue
   */
  isTransient(error) {
    const classification = this.classify(error);
    return classification.transient;
  }

  /**
   * エラーの重要度を取得
   * @param {Error|string} error - 判定するエラー
   * @returns {string} 重要度レベル
   */
  getSeverity(error) {
    const classification = this.classify(error);
    return classification.severity;
  }

  /**
   * 分類統計情報を取得
   * @returns {Object} カテゴリ別統計
   */
  getClassificationStats() {
    const stats = Object.fromEntries(this.classificationStats);
    const total = Object.values(stats).reduce((sum, count) => sum + count, 0);

    return {
      byCategory: stats,
      total,
      mostCommon: this._getMostCommonCategory()
    };
  }

  /**
   * 統計情報をリセット
   */
  resetStats() {
    this.classificationStats.clear();
  }

  /**
   * メッセージに一致する分類ルールを検索
   * @param {string} message - エラーメッセージ
   * @returns {Object} 分類結果
   * @private
   */
  _findMatchingRule(message) {
    for (const rule of ERROR_CLASSIFICATION_RULES) {
      if (rule.pattern.test(message)) {
        return {
          category: rule.category,
          severity: rule.severity,
          transient: rule.transient
        };
      }
    }

    // デフォルト分類
    return {
      category: ErrorCategory.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      transient: false
    };
  }

  /**
   * 統計情報を更新
   * @param {string} category - エラーカテゴリ
   * @private
   */
  _updateStats(category) {
    const currentCount = this.classificationStats.get(category) || 0;
    this.classificationStats.set(category, currentCount + 1);
  }

  /**
   * エラー一意IDを生成
   * @returns {string} エラーID
   * @private
   */
  _generateErrorId() {
    return `err_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
  }

  /**
   * スタックトレースから有用な情報を抽出
   * @param {string} stack - スタックトレース
   * @returns {Object} 抽出された情報
   * @private
   */
  _extractStackInfo(stack) {
    const lines = stack.split('\n');
    const relevantLines = lines.slice(0, 5); // 上位5行のみ

    return {
      topLevel: lines[0] || '',
      frames: relevantLines.map(line => line.trim()),
      depth: lines.length
    };
  }

  /**
   * 最も多いエラーカテゴリを取得
   * @returns {string|null} 最も多いカテゴリ
   * @private
   */
  _getMostCommonCategory() {
    if (this.classificationStats.size === 0) {
      return null;
    }

    let maxCount = 0;
    let mostCommon = null;

    for (const [category, count] of this.classificationStats.entries()) {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = category;
      }
    }

    return mostCommon;
  }
}

/**
 * デフォルトのエラー分類器インスタンス
 * @type {ErrorClassifier}
 */
export const defaultErrorClassifier = new ErrorClassifier();