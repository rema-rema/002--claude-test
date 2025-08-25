import { jest, describe, test, beforeEach, expect } from '@jest/globals';
import { TestFailureAnalyzer } from '../../components/TestFailureAnalyzer.js';
import { ErrorPatternMatcher } from '../../components/ErrorPatternMatcher.js';
import { FixSuggestionGenerator } from '../../components/FixSuggestionGenerator.js';

describe('TestFailureAnalyzer', () => {
  let analyzer;
  let mockErrorPatternMatcher;
  let mockFixSuggestionGenerator;

  beforeEach(() => {
    mockErrorPatternMatcher = {
      matchPattern: jest.fn()
    };
    mockFixSuggestionGenerator = {
      generateSuggestions: jest.fn()
    };
    analyzer = new TestFailureAnalyzer(mockErrorPatternMatcher, mockFixSuggestionGenerator);
  });

  // 🔴 正常動作テストケース（5件）
  
  describe('正常動作テストケース', () => {
    test('TC-01: UI要素未発見エラーの分析', async () => {
      // 【テスト目的】: UI要素未発見エラーの正常分析処理確認
      // 【テスト内容】: locator('#element') not found パターンの分析
      // 【期待される動作】: UI_ELEMENTカテゴリでの高精度分析結果生成
      // 🟢 設計書UI_ELEMENTパターン例より確実
      
      const testResult = {
        testName: 'should find login button',
        error: "locator('#login-button') not found",
        stackTrace: 'at page.locator (test.spec.js:15:20)',
        testFile: 'login.test.js'
      };

      const mockErrorPattern = {
        category: 'UI_ELEMENT',
        pattern: /locator\('.+?'\) not found/,
        confidence: 0.9
      };

      const mockSuggestions = [
        'セレクタ「#login-button」が正しいか確認してください',
        '要素の読み込み完了を待つwaitForSelector()を追加してください'
      ];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'should find login button',
        errorCategory: 'UI_ELEMENT',
        confidence: 0.9,
        suggestions: mockSuggestions,
        analysisId: expect.any(String)
      });
      expect(mockErrorPatternMatcher.matchPattern).toHaveBeenCalledWith(testResult.error);
      expect(mockFixSuggestionGenerator.generateSuggestions).toHaveBeenCalledWith(mockErrorPattern, testResult);
    });

    test('TC-02: タイムアウトエラーの分析', async () => {
      // 【テスト目的】: タイムアウトエラーの正常分析処理確認  
      // 【テスト内容】: Timeout 30000ms exceeded パターンの分析
      // 【期待される動作】: TIMINGカテゴリでの分析結果生成
      // 🟢 設計書TIMINGパターン例より確実
      
      const testResult = {
        testName: 'should load page within timeout',
        error: 'Timeout 30000ms exceeded',
        stackTrace: 'at waitForLoadState (test.spec.js:10:15)',
        testFile: 'navigation.test.js'
      };

      const mockErrorPattern = {
        category: 'TIMING',
        pattern: /Timeout \d+ms exceeded/,
        confidence: 0.85
      };

      const mockSuggestions = [
        'タイムアウト時間を延長してください',
        'ページ読み込み状態を確認してください'
      ];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'should load page within timeout',
        errorCategory: 'TIMING',
        confidence: 0.85,
        suggestions: mockSuggestions,
        analysisId: expect.any(String)
      });
    });

    test('TC-03: アサーション失敗の分析', async () => {
      // 【テスト目的】: アサーション失敗の正常分析処理確認
      // 【テスト内容】: expect().toHaveText() 失敗パターンの分析
      // 【期待される動作】: ASSERTIONカテゴリでの分析結果生成
      // 🟢 設計書ASSERTIONパターン例より確実
      
      const testResult = {
        testName: 'should display correct title',
        error: 'Expected "Welcome" but received "Loading..."',
        stackTrace: 'at expect.toHaveText (test.spec.js:20:25)',
        testFile: 'title.test.js'
      };

      const mockErrorPattern = {
        category: 'ASSERTION',
        pattern: /Expected ".+" but received ".+"/,
        confidence: 0.8
      };

      const mockSuggestions = [
        'テキストの読み込み完了を待ってください',
        '期待値「Welcome」が正しいか確認してください'
      ];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'should display correct title',
        errorCategory: 'ASSERTION',
        confidence: 0.8,
        suggestions: mockSuggestions,
        analysisId: expect.any(String)
      });
    });

    test('TC-04: 複数修正提案の生成', async () => {
      // 【テスト目的】: 複数の修正提案が正しく生成される確認
      // 【テスト内容】: 5つの提案を生成するパターンの処理
      // 【期待される動作】: 全ての提案が結果に含まれる
      // 🟢 設計書の最大5つルールより確実
      
      const testResult = {
        testName: 'complex test with multiple issues',
        error: 'Multiple issues detected',
        stackTrace: 'complex stack trace',
        testFile: 'complex.test.js'
      };

      const mockErrorPattern = {
        category: 'UI_ELEMENT',
        pattern: /Multiple issues detected/,
        confidence: 0.7
      };

      const mockSuggestions = [
        '提案1: セレクタを修正してください',
        '提案2: 待機時間を調整してください',
        '提案3: テストデータを確認してください',
        '提案4: ページ読み込みを待機してください',
        '提案5: エラーハンドリングを追加してください'
      ];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result = await analyzer.analyzeFailure(testResult);

      expect(result.suggestions).toHaveLength(5);
      expect(result.suggestions).toEqual(mockSuggestions);
    });

    test('TC-05: 分析IDのユニーク性確認', async () => {
      // 【テスト目的】: 各分析結果のIDがユニークである確認
      // 【テスト内容】: 同一テスト結果を複数回分析してID重複確認
      // 【期待される動作】: 異なる分析IDが生成される
      // 🟢 設計書のユニークID要件より確実
      
      const testResult = {
        testName: 'unique id test',
        error: 'test error',
        stackTrace: 'test stack',
        testFile: 'test.js'
      };

      const mockErrorPattern = {
        category: 'UI_ELEMENT',
        pattern: /test error/,
        confidence: 0.8
      };

      const mockSuggestions = ['test suggestion'];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result1 = await analyzer.analyzeFailure(testResult);
      const result2 = await analyzer.analyzeFailure(testResult);

      expect(result1.analysisId).not.toEqual(result2.analysisId);
      expect(result1.analysisId).toMatch(/^[a-f0-9-]{36}$/); // UUID形式
      expect(result2.analysisId).toMatch(/^[a-f0-9-]{36}$/); // UUID形式
    });
  });

  // 🔴 エラーハンドリングテストケース（5件）

  describe('エラーハンドリングテストケース', () => {
    test('TC-06: 依存コンポーネント例外の処理', async () => {
      // 【テスト目的】: 依存コンポーネントでの例外発生時の適切な処理確認
      // 【テスト内容】: ErrorPatternMatcher.matchPattern()での例外発生
      // 【期待される動作】: エラーレスポンスの適切な返却
      // 🟢 設計書エラーハンドリング要件より確実
      
      const testResult = {
        testName: 'error test',
        error: 'test error',
        stackTrace: 'test stack',
        testFile: 'test.js'
      };

      mockErrorPatternMatcher.matchPattern.mockRejectedValue(
        new Error('ErrorPatternMatcher internal error')
      );

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'error test',
        errorCategory: 'UNKNOWN',
        confidence: 0.0,
        suggestions: ['分析エラーが発生しました。手動での確認をお願いします。'],
        analysisId: expect.any(String),
        error: 'ErrorPatternMatcher internal error'
      });
    });

    test('TC-07: 不正形式入力の処理', async () => {
      // 【テスト目的】: 不正形式のテスト結果入力への適切な処理確認
      // 【テスト内容】: 必須フィールド欠損入力の処理
      // 【期待される動作】: エラーレスポンスの適切な返却
      // 🟢 設計書入力検証要件より確実
      
      const malformedTestResult = {
        // testName欠損
        error: 'test error',
        stackTrace: 'test stack'
        // testFile欠損
      };

      const result = await analyzer.analyzeFailure(malformedTestResult);

      expect(result).toEqual({
        testName: 'Unknown Test',
        errorCategory: 'UNKNOWN',
        confidence: 0.0,
        suggestions: ['入力データが不正です。必須フィールドを確認してください。'],
        analysisId: expect.any(String),
        error: '不正な入力形式'
      });
    });

    test('TC-08: タイムアウト処理', async () => {
      // 【テスト目的】: 処理タイムアウト時の適切な処理確認
      // 【テスト内容】: 長時間処理のタイムアウト発生
      // 【期待される動作】: タイムアウトエラーレスポンスの返却
      // 🟢 設計書パフォーマンス要件より確実
      
      const testResult = {
        testName: 'timeout test',
        error: 'test error',
        stackTrace: 'test stack',
        testFile: 'test.js'
      };

      // 30秒でタイムアウトする長時間処理をシミュレート
      mockErrorPatternMatcher.matchPattern.mockImplementation(
        () => new Promise((resolve, reject) => {
          setTimeout(() => reject(new Error('処理がタイムアウトしました')), 100);
        })
      );

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'timeout test',
        errorCategory: 'UNKNOWN',
        confidence: 0.0,
        suggestions: ['処理がタイムアウトしました。後で再試行してください。'],
        analysisId: expect.any(String),
        error: '処理がタイムアウトしました'
      });
    });

    test('TC-09: 同時実行処理の確認', async () => {
      // 【テスト目的】: 複数分析要求の同時実行処理確認
      // 【テスト内容】: 3つの分析要求を同時実行
      // 【期待される動作】: 全ての要求が適切に処理される
      // 🟢 設計書同時実行要件より確実
      
      const testResults = [
        { testName: 'test1', error: 'error1', stackTrace: 'stack1', testFile: 'test1.js' },
        { testName: 'test2', error: 'error2', stackTrace: 'stack2', testFile: 'test2.js' },
        { testName: 'test3', error: 'error3', stackTrace: 'stack3', testFile: 'test3.js' }
      ];

      const mockErrorPattern = {
        category: 'UI_ELEMENT',
        pattern: /error\d/,
        confidence: 0.8
      };

      const mockSuggestions = ['test suggestion'];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const promises = testResults.map(testResult => analyzer.analyzeFailure(testResult));
      const results = await Promise.all(promises);

      expect(results).toHaveLength(3);
      results.forEach((result, index) => {
        expect(result.testName).toBe(`test${index + 1}`);
        expect(result.errorCategory).toBe('UI_ELEMENT');
        expect(result.confidence).toBe(0.8);
        expect(result.analysisId).toMatch(/^[a-f0-9-]{36}$/);
      });

      // 各分析IDがユニークであることを確認
      const analysisIds = results.map(r => r.analysisId);
      const uniqueIds = new Set(analysisIds);
      expect(uniqueIds.size).toBe(3);
    });

    test('TC-10: メモリ不足例外の処理', async () => {
      // 【テスト目的】: システムリソース不足時の適切な処理確認
      // 【テスト内容】: メモリ不足例外の発生シミュレーション
      // 【期待される動作】: リソースエラーレスポンスの返却
      // 🟢 設計書リソース管理要件より確実
      
      const testResult = {
        testName: 'memory test',
        error: 'test error',
        stackTrace: 'test stack',
        testFile: 'test.js'
      };

      mockErrorPatternMatcher.matchPattern.mockRejectedValue(
        new Error('ENOMEM: not enough memory')
      );

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'memory test',
        errorCategory: 'UNKNOWN',
        confidence: 0.0,
        suggestions: ['システムリソースが不足しています。しばらく待ってから再試行してください。'],
        analysisId: expect.any(String),
        error: 'ENOMEM: not enough memory'
      });
    });
  });

  // 🔴 境界値テストケース（5件）

  describe('境界値テストケース', () => {
    test('TC-11: 空エラーメッセージの処理', async () => {
      // 【テスト目的】: 空または最小エラーメッセージの処理確認
      // 【テスト内容】: 空文字列エラーメッセージの分析
      // 【期待される動作】: 適切なデフォルト処理の実行
      // 🟢 設計書境界値処理要件より確実
      
      const testResult = {
        testName: 'empty error test',
        error: '',
        stackTrace: '',
        testFile: 'test.js'
      };

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'empty error test',
        errorCategory: 'UNKNOWN',
        confidence: 0.0,
        suggestions: ['エラーメッセージが空です。テストの実装を確認してください。'],
        analysisId: expect.any(String)
      });
    });

    test('TC-12: 最大長エラーメッセージの処理', async () => {
      // 【テスト目的】: 最大長エラーメッセージの処理確認
      // 【テスト内容】: 10000文字のエラーメッセージ分析
      // 【期待される動作】: 正常な分析処理の実行
      // 🟢 設計書最大長制限要件より確実
      
      const longError = 'A'.repeat(10000);
      const testResult = {
        testName: 'long error test',
        error: longError,
        stackTrace: 'stack trace',
        testFile: 'test.js'
      };

      const mockErrorPattern = {
        category: 'UI_ELEMENT',
        pattern: /A+/,
        confidence: 0.5
      };

      const mockSuggestions = ['長いエラーメッセージを確認してください'];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result = await analyzer.analyzeFailure(testResult);

      expect(result.errorCategory).toBe('UI_ELEMENT');
      expect(result.confidence).toBe(0.5);
      expect(result.suggestions).toEqual(mockSuggestions);
      expect(result.testName).toBe('long error test');
    });

    test('TC-13: null/undefined値の処理', async () => {
      // 【テスト目的】: null/undefined値入力の適切な処理確認
      // 【テスト内容】: null値を含むテスト結果の処理
      // 【期待される動作】: 適切なデフォルト値での処理実行
      // 🟢 設計書null安全性要件より確実
      
      const testResult = {
        testName: null,
        error: undefined,
        stackTrace: null,
        testFile: 'test.js'
      };

      const result = await analyzer.analyzeFailure(testResult);

      expect(result).toEqual({
        testName: 'Unknown Test',
        errorCategory: 'UNKNOWN',
        confidence: 0.0,
        suggestions: ['入力データにnull/undefined値が含まれています。データを確認してください。'],
        analysisId: expect.any(String)
      });
    });

    test('TC-14: 信頼度計算の境界値確認', async () => {
      // 【テスト目的】: 信頼度計算の境界値（0.0, 1.0）確認
      // 【テスト内容】: 最小・最大信頼度での計算処理
      // 【期待される動作】: 境界値が適切に処理される
      // 🟢 設計書信頼度計算仕様より確実
      
      const testResult = {
        testName: 'confidence boundary test',
        error: 'boundary error',
        stackTrace: 'stack',
        testFile: 'test.js'
      };

      // 最小信頼度のテスト
      const minErrorPattern = {
        category: 'UNKNOWN',
        pattern: /boundary error/,
        confidence: 0.0
      };

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(minErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(['最小信頼度提案']);

      const minResult = await analyzer.analyzeFailure(testResult);
      expect(minResult.confidence).toBe(0.0);

      // 最大信頼度のテスト
      const maxErrorPattern = {
        category: 'UI_ELEMENT',
        pattern: /boundary error/,
        confidence: 1.0
      };

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(maxErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(['最大信頼度提案']);

      const maxResult = await analyzer.analyzeFailure(testResult);
      expect(maxResult.confidence).toBe(1.0);
    });

    test('TC-15: 最小限入力での処理', async () => {
      // 【テスト目的】: 必須フィールドのみの最小限入力処理確認
      // 【テスト内容】: testName, errorのみの入力処理
      // 【期待される動作】: 欠損フィールドの適切なデフォルト処理
      // 🟢 設計書最小入力要件より確実
      
      const minimalTestResult = {
        testName: 'minimal test',
        error: 'minimal error'
        // stackTrace, testFile は省略
      };

      const mockErrorPattern = {
        category: 'UNKNOWN',
        pattern: /minimal error/,
        confidence: 0.3
      };

      const mockSuggestions = ['最小入力での提案'];

      mockErrorPatternMatcher.matchPattern.mockResolvedValue(mockErrorPattern);
      mockFixSuggestionGenerator.generateSuggestions.mockResolvedValue(mockSuggestions);

      const result = await analyzer.analyzeFailure(minimalTestResult);

      expect(result).toEqual({
        testName: 'minimal test',
        errorCategory: 'UNKNOWN',
        confidence: 0.3,
        suggestions: mockSuggestions,
        analysisId: expect.any(String)
      });
    });
  });
});