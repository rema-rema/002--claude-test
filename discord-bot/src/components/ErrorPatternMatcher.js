export class ErrorPatternMatcher {
  constructor() {
    // エラーパターンのルールを定義
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
      }
    ];
  }

  async matchPattern(errorMessage) {
    // 入力検証
    if (!errorMessage || typeof errorMessage !== 'string') {
      return this.createUnknownPattern(errorMessage);
    }

    // パターンマッチング実行
    for (const patternRule of this.patterns) {
      if (patternRule.matcher(errorMessage)) {
        return {
          category: patternRule.category,
          pattern: patternRule.pattern,
          confidence: patternRule.confidence
        };
      }
    }

    // デフォルト（不明なパターン）
    return this.createUnknownPattern(errorMessage);
  }

  createUnknownPattern(errorMessage) {
    const safePattern = errorMessage 
      ? new RegExp(errorMessage.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      : /.*/;
    
    return {
      category: 'UNKNOWN',
      pattern: safePattern,
      confidence: errorMessage ? 0.3 : 0.0
    };
  }
}