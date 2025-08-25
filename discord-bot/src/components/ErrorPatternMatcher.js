/**
 * エラーパターンマッチング・分類システム
 * Playwrightテストエラーを分析し、カテゴリ・信頼度を算出
 * 
 * サポートカテゴリ:
 * - UI_ELEMENT: UI要素関連エラー
 * - TIMING: タイムアウト・タイミングエラー  
 * - ASSERTION: アサーション失敗
 * - NETWORK: ネットワーク関連エラー
 * - SECURITY: セキュリティポリシー違反
 * - UNKNOWN: 未分類エラー
 */
export class ErrorPatternMatcher {
  constructor() {
    // エラーパターンのルールを優先度順に定義
    this.patterns = [
      {
        name: 'UI_ELEMENT_NOT_FOUND',
        category: 'UI_ELEMENT',
        matcher: (msg) => msg.includes('locator(') && msg.includes('not found'),
        pattern: /locator\('.+?'\) not found/,
        confidence: 0.9
      },
      {
        name: 'TIMEOUT_EXCEEDED',
        category: 'TIMING',
        matcher: (msg) => msg.includes('Timeout') && msg.includes('ms exceeded'),
        pattern: /Timeout \d+ms exceeded/,
        confidence: 0.85
      },
      {
        name: 'ASSERTION_FAILED',
        category: 'ASSERTION',
        matcher: (msg) => msg.includes('Expected') && msg.includes('but received'),
        pattern: /Expected ".+" but received ".+"/,
        confidence: 0.8
      },
      {
        name: 'MULTIPLE_ISSUES',
        category: 'UI_ELEMENT',
        matcher: (msg) => msg.includes('Multiple issues detected'),
        pattern: /Multiple issues detected/,
        confidence: 0.7
      },
      {
        name: 'NETWORK_CONNECTION_FAILED',
        category: 'NETWORK',
        matcher: (msg) => (msg.includes('Failed to load resource') || msg.includes('ERR_CONNECTION') || msg.includes('net::')),
        pattern: /Failed to load resource|ERR_CONNECTION|net::/,
        confidence: 0.8
      },
      {
        name: 'NETWORK_TIMEOUT',
        category: 'NETWORK',
        matcher: (msg) => msg.includes('ERR_TIMEOUT') || (msg.includes('timeout') && msg.includes('network')),
        pattern: /ERR_TIMEOUT|timeout.*network/i,
        confidence: 0.75
      },
      {
        name: 'CORS_POLICY_ERROR',
        category: 'SECURITY',
        matcher: (msg) => msg.includes('Blocked by CORS policy') || msg.includes('CORS'),
        pattern: /Blocked by CORS policy|CORS/i,
        confidence: 0.85
      },
      {
        name: 'CSP_VIOLATION',
        category: 'SECURITY',
        matcher: (msg) => msg.includes('Content Security Policy') || msg.includes('CSP'),
        pattern: /Content Security Policy|CSP/i,
        confidence: 0.8
      }
    ];
  }

  /**
   * エラーメッセージを分析してパターンを特定
   * @param {string} errorMessage - 分析対象のエラーメッセージ
   * @returns {Promise<{category: string, pattern: RegExp, confidence: number}>}
   */
  async matchPattern(errorMessage) {
    // 入力検証
    if (!errorMessage || typeof errorMessage !== 'string') {
      return this.createUnknownPattern(errorMessage);
    }

    // パフォーマンス最適化: 早期リターン
    if (errorMessage.trim() === '') {
      return this.createUnknownPattern(errorMessage);
    }

    // パターンマッチング実行（優先度順）
    for (const patternRule of this.patterns) {
      if (patternRule.matcher(errorMessage)) {
        return {
          category: patternRule.category,
          pattern: patternRule.pattern,
          confidence: this.calculateDynamicConfidence(patternRule, errorMessage)
        };
      }
    }

    // デフォルト（不明なパターン）
    return this.createUnknownPattern(errorMessage);
  }

  /**
   * エラーメッセージの詳細度に基づく動的信頼度計算
   * @param {Object} patternRule - マッチしたパターンルール
   * @param {string} errorMessage - エラーメッセージ
   * @returns {number} 調整済み信頼度 (0.0 - 1.0)
   */
  calculateDynamicConfidence(patternRule, errorMessage) {
    let baseConfidence = patternRule.confidence;
    
    // エラーメッセージの詳細度による調整
    const detailBonus = Math.min(0.1, errorMessage.length / 1000);
    
    // 複数キーワードマッチによる調整
    const matches = errorMessage.match(patternRule.pattern);
    const matchBonus = matches && matches.length > 1 ? 0.05 : 0;
    
    return Math.min(1.0, baseConfidence + detailBonus + matchBonus);
  }

  createUnknownPattern(errorMessage) {
    // 型チェック: 非文字列の場合は安全に処理
    if (typeof errorMessage !== 'string') {
      return {
        category: 'UNKNOWN',
        pattern: /.*/,
        confidence: 0.0
      };
    }
    
    // 空文字列の場合
    if (!errorMessage || errorMessage.trim() === '') {
      return {
        category: 'UNKNOWN',
        pattern: /.*/,
        confidence: 0.0
      };
    }
    
    // 正常な文字列の場合は正規表現エスケープして処理
    try {
      const safePattern = new RegExp(errorMessage.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
      return {
        category: 'UNKNOWN',
        pattern: safePattern,
        confidence: 0.3
      };
    } catch (error) {
      // 正規表現作成に失敗した場合のフォールバック
      return {
        category: 'UNKNOWN',
        pattern: /.*/,
        confidence: 0.1
      };
    }
  }
}