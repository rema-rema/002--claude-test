import { randomUUID } from 'crypto';

export class TestFailureAnalyzer {
  // Constants for error handling
  static UNKNOWN_CATEGORY = 'UNKNOWN';
  static UNKNOWN_TEST_NAME = 'Unknown Test';
  static MIN_CONFIDENCE = 0.0;
  static DEFAULT_MESSAGES = {
    EMPTY_ERROR: 'エラーメッセージが空です。テストの実装を確認してください。',
    MALFORMED_INPUT: '入力データが不正です。必須フィールドを確認してください。',
    NULL_UNDEFINED: '入力データにnull/undefined値が含まれています。データを確認してください。',
    ANALYSIS_ERROR: '分析エラーが発生しました。手動での確認をお願いします。',
    RESOURCE_ERROR: 'システムリソースが不足しています。しばらく待ってから再試行してください。',
    TIMEOUT_ERROR: '処理がタイムアウトしました。後で再試行してください。'
  };

  constructor(errorPatternMatcher, fixSuggestionGenerator) {
    this.errorPatternMatcher = errorPatternMatcher;
    this.fixSuggestionGenerator = fixSuggestionGenerator;
  }

  async analyzeFailure(testResult) {
    try {
      // 入力データ検証フロー
      const validationResult = this.validateInput(testResult);
      if (validationResult) {
        return validationResult;
      }

      // 正常化された入力データを取得
      const normalizedInput = this.normalizeInput(testResult);
      
      // 空エラーメッセージの処理
      if (normalizedInput.errorMessage === '') {
        return this.createSuccessResponse(
          normalizedInput.testName,
          TestFailureAnalyzer.UNKNOWN_CATEGORY,
          TestFailureAnalyzer.MIN_CONFIDENCE,
          [TestFailureAnalyzer.DEFAULT_MESSAGES.EMPTY_ERROR]
        );
      }

      // エラーパターンマッチングと修正提案生成
      const errorPattern = await this.errorPatternMatcher.matchPattern(normalizedInput.errorMessage);
      const suggestions = await this.fixSuggestionGenerator.generateSuggestions(errorPattern, testResult);

      // 分析結果生成
      return this.createSuccessResponse(
        normalizedInput.testName,
        errorPattern.category,
        errorPattern.confidence,
        suggestions
      );

    } catch (error) {
      // エラーハンドリング
      return this.createErrorResponse(
        testResult?.testName || TestFailureAnalyzer.UNKNOWN_TEST_NAME, 
        this.getErrorMessage(error),
        error.message
      );
    }
  }

  validateInput(testResult) {
    // null/undefined testResult
    if (!testResult) {
      return this.createErrorResponse(
        TestFailureAnalyzer.UNKNOWN_TEST_NAME, 
        TestFailureAnalyzer.DEFAULT_MESSAGES.MALFORMED_INPUT
      );
    }

    // null/undefined値の処理
    if (testResult.testName === null || testResult.error === undefined) {
      return this.createErrorResponse(
        TestFailureAnalyzer.UNKNOWN_TEST_NAME, 
        TestFailureAnalyzer.DEFAULT_MESSAGES.NULL_UNDEFINED
      );
    }

    // 不正形式入力の処理（必須フィールド欠損）
    if (!testResult.testName) {
      return this.createErrorResponse(
        TestFailureAnalyzer.UNKNOWN_TEST_NAME, 
        TestFailureAnalyzer.DEFAULT_MESSAGES.MALFORMED_INPUT, 
        '不正な入力形式'
      );
    }

    return null; // 検証成功
  }

  normalizeInput(testResult) {
    return {
      testName: testResult.testName || TestFailureAnalyzer.UNKNOWN_TEST_NAME,
      errorMessage: testResult.error || ''
    };
  }

  createSuccessResponse(testName, category, confidence, suggestions) {
    return {
      testName: testName,
      errorCategory: category,
      confidence: confidence,
      suggestions: suggestions,
      analysisId: randomUUID()
    };
  }

  createErrorResponse(testName, defaultMessage, originalError = null) {
    const suggestions = [this.getSpecificErrorMessage(originalError) || defaultMessage];
    
    const result = {
      testName: testName,
      errorCategory: TestFailureAnalyzer.UNKNOWN_CATEGORY,
      confidence: TestFailureAnalyzer.MIN_CONFIDENCE,
      suggestions: suggestions,
      analysisId: randomUUID()
    };

    if (originalError) {
      result.error = originalError;
    }

    return result;
  }

  getSpecificErrorMessage(originalError) {
    if (!originalError) return null;
    
    if (originalError.includes('ENOMEM')) {
      return TestFailureAnalyzer.DEFAULT_MESSAGES.RESOURCE_ERROR;
    }
    if (originalError.includes('タイムアウト')) {
      return TestFailureAnalyzer.DEFAULT_MESSAGES.TIMEOUT_ERROR;
    }
    return null;
  }

  getErrorMessage(error) {
    if (error.message.includes('ErrorPatternMatcher internal error')) {
      return TestFailureAnalyzer.DEFAULT_MESSAGES.ANALYSIS_ERROR;
    }
    if (error.message.includes('ENOMEM')) {
      return TestFailureAnalyzer.DEFAULT_MESSAGES.RESOURCE_ERROR;
    }
    if (error.message.includes('タイムアウト')) {
      return TestFailureAnalyzer.DEFAULT_MESSAGES.TIMEOUT_ERROR;
    }
    return TestFailureAnalyzer.DEFAULT_MESSAGES.ANALYSIS_ERROR;
  }

  calculateConfidence(errorPattern) {
    return errorPattern.confidence;
  }
}