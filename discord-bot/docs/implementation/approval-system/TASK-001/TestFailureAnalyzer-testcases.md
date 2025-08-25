# TDD Test Cases: TestFailureAnalyzer

## 概要
TestFailureAnalyzerのテストケース定義書。analyzeFailureとcalculateConfidenceメソッドの包括的なテスト戦略。

## テスト環境
- **言語**: JavaScript (ES Modules)
- **フレームワーク**: Jest 29.7.0
- **実行**: `npm test`
- **モック対象**: ErrorPatternMatcher, FixSuggestionGenerator

## 正常系テストケース

### TC001: UI要素エラーの正常分析
```javascript
// 【テスト目的】: UI要素未発見エラーの正常分析処理確認
// 【テスト内容】: locator('#element') not found パターンの分析
// 【期待される動作】: UI_ELEMENTカテゴリでの高精度分析結果生成
// 🟢 設計書UI_ELEMENTパターン例より確実

test('UI要素未発見エラーを正常に分析できる', async () => {
  // 【テストデータ準備】: 典型的なPlaywright UI要素エラーを模擬
  const mockTestFailure = {
    testId: 'ui-test-001',
    testTitle: 'ログインボタンクリック',
    testFile: 'login.spec.js',
    error: { message: "locator('#login-button') not found" },
    duration: 5000,
    timestamp: new Date()
  };

  // 【モック設定】: UI_ELEMENTパターンマッチングとセレクタ更新提案
  mockErrorPatternMatcher.match.mockResolvedValue({
    category: 'UI_ELEMENT', confidence: 0.85
  });
  mockFixSuggestionGenerator.generate.mockResolvedValue([
    { type: 'SELECTOR_UPDATE', priority: 'HIGH' }
  ]);

  // 【実際の処理実行】: analyzeFailureメソッド実行
  const result = await analyzer.analyzeFailure(mockTestFailure);

  // 【結果検証】: 分析結果の正確性確認
  expect(result.errorPattern.category).toBe('UI_ELEMENT'); // 【確認内容】: UI要素カテゴリが正しく識別される
  expect(result.confidenceLevel).toBeGreaterThanOrEqual(0.8); // 【確認内容】: 高信頼度での分析結果
  expect(result.fixSuggestions).toHaveLength(1); // 【確認内容】: 修正提案が適切に統合される
});
```

### TC002: タイムアウトエラーの正常分析
```javascript
// 【テスト目的】: タイムアウトエラーの高精度分析処理確認
// 【テスト内容】: timeout exceeded パターンの分析とduration情報活用
// 【期待される動作】: TIMINGカテゴリでの待機戦略提案生成
// 🟢 設計書TIMING_ERRORパターン例より確実

test('タイムアウトエラーを正常に分析できる', async () => {
  // 【テストデータ準備】: 典型的なPlaywrightタイムアウトエラー
  const mockTestFailure = {
    testId: 'timeout-test-001',
    testTitle: 'ページ読み込みタイムアウト',
    error: { message: "timeout exceeded: page load timeout" },
    duration: 30000
  };

  mockErrorPatternMatcher.match.mockResolvedValue({
    category: 'TIMING', confidence: 0.9
  });
  mockFixSuggestionGenerator.generate.mockResolvedValue([
    { type: 'WAIT_STRATEGY', priority: 'HIGH' }
  ]);

  const result = await analyzer.analyzeFailure(mockTestFailure);

  expect(result.errorPattern.category).toBe('TIMING'); // 【確認内容】: タイミング系エラーとして正確に分類
  expect(result.confidenceLevel).toBeGreaterThanOrEqual(0.85); // 【確認内容】: duration情報で信頼度向上
});
```

### TC003: アサーション失敗の正常分析
```javascript
// 【テスト目的】: アサーション失敗エラーの詳細分析確認
// 【テスト内容】: expect失敗エラーとlocation情報の活用
// 【期待される動作】: ASSERTIONカテゴリでの具体的修正提案
// 🟢 設計書ASSERTION_FAILUREパターン例より確実

test('アサーション失敗エラーを正常に分析できる', async () => {
  const mockTestFailure = {
    testId: 'assertion-test-001',
    testTitle: 'テキスト内容検証',
    error: { 
      message: "expect(locator).toHaveText('Expected') failed: actual 'Actual'",
      location: { file: 'test.spec.js', line: 25, column: 10 }
    }
  };

  mockErrorPatternMatcher.match.mockResolvedValue({
    category: 'ASSERTION', confidence: 0.9
  });

  const result = await analyzer.analyzeFailure(mockTestFailure);

  expect(result.errorPattern.category).toBe('ASSERTION'); // 【確認内容】: アサーション系エラーの正確な識別
});
```

### TC004: 複数修正提案の統合処理
```javascript
// 【テスト目的】: 複数修正提案の適切な統合と優先度計算
// 【テスト内容】: FixSuggestionGeneratorから複数提案受信時の処理
// 【期待される動作】: 優先度順での提案統合と信頼度への反映
// 🟡 複数提案統合ロジックは推測だが妥当

test('複数の修正提案を適切に統合できる', async () => {
  mockFixSuggestionGenerator.generate.mockResolvedValue([
    { type: 'SELECTOR_UPDATE', priority: 'HIGH', effectiveness: 0.9 },
    { type: 'WAIT_STRATEGY', priority: 'MEDIUM', effectiveness: 0.7 }
  ]);

  const result = await analyzer.analyzeFailure(standardTestFailure);

  expect(result.fixSuggestions).toHaveLength(2); // 【確認内容】: 複数提案の適切な統合
  expect(result.fixSuggestions[0].priority).toBe('HIGH'); // 【確認内容】: 優先度順でのソート
});
```

### TC005: 分析結果IDの一意性確保
```javascript
// 【テスト目的】: AnalysisResult.idの一意性確保機能検証
// 【テスト内容】: 同一TestFailureでの複数分析実行
// 【期待される動作】: 各分析で異なるID生成
// 🟡 ID生成方法は推測だが一意性確保は必要

test('分析結果に一意のIDが生成される', async () => {
  const results = await Promise.all([
    analyzer.analyzeFailure(standardTestFailure),
    analyzer.analyzeFailure(standardTestFailure)
  ]);

  expect(results[0].id).not.toBe(results[1].id); // 【確認内容】: 分析結果IDの一意性確保
  expect(results[0].id).toMatch(/^[a-f0-9-]{36}$/); // 【確認内容】: UUID形式での生成確認
});
```

## 異常系テストケース

### TC006: ErrorPatternMatcher例外時の継続処理
```javascript
// 【テスト目的】: 依存コンポーネント例外時のフォールバック処理確認
// 【テスト内容】: ErrorPatternMatcher例外発生時の安全な処理継続
// 【期待される動作】: デフォルトパターンでの処理継続
// 🟢 要件定義のエラーハンドリング要件より確実

test('ErrorPatternMatcher例外時でも分析処理を継続できる', async () => {
  // 【異常条件設定】: ErrorPatternMatcherで例外発生を模擬
  mockErrorPatternMatcher.match.mockRejectedValue(new Error('Pattern matching failed'));

  const result = await analyzer.analyzeFailure(standardTestFailure);

  // 【フォールバック動作確認】: デフォルトパターンでの処理継続
  expect(result.errorPattern.name).toBe('UNKNOWN_ERROR'); // 【確認内容】: デフォルトパターンへのフォールバック
  expect(result.errorPattern.category).toBe('UNKNOWN'); // 【確認内容】: UNKNOWNカテゴリでの安全処理
  expect(result.confidenceLevel).toBe(0.1); // 【確認内容】: 低信頼度での継続処理
});
```

### TC007: FixSuggestionGenerator例外時の継続処理  
```javascript
// 【テスト目的】: 修正提案生成失敗時のgraceful degradation
// 【テスト内容】: FixSuggestionGenerator例外時の部分機能提供
// 【期待される動作】: エラーパターン識別は成功、提案なしで継続
// 🟢 要件定義のエラーハンドリング要件より確実

test('FixSuggestionGenerator例外時でも分析処理を継続できる', async () => {
  mockFixSuggestionGenerator.generate.mockRejectedValue(new Error('Suggestion generation failed'));

  const result = await analyzer.analyzeFailure(standardTestFailure);

  expect(result.errorPattern).toBeDefined(); // 【確認内容】: エラーパターン識別は正常実行
  expect(result.fixSuggestions).toEqual([]); // 【確認内容】: 空配列での安全な継続処理
});
```

### TC008: 不正なTestFailure構造での安全処理
```javascript
// 【テスト目的】: 不完全データ構造への耐性確認
// 【テスト内容】: 必須フィールド欠損TestFailureでの処理
// 【期待される動作】: 例外なしで最低限の分析結果提供
// 🟡 不完全データ処理は推測だが妥当

test('不完全なTestFailure構造でも安全に処理できる', async () => {
  // 【異常データ準備】: 必須フィールドが欠損したTestFailure
  const incompleteTestFailure = {
    testId: 'invalid-test-001',
    error: {}, // message欠損
    duration: null
  };

  const result = await analyzer.analyzeFailure(incompleteTestFailure);

  expect(result).toBeDefined(); // 【確認内容】: 例外なしで結果生成
  expect(result.errorPattern.category).toBe('UNKNOWN'); // 【確認内容】: 不完全データでのUNKNOWN分類
});
```

### TC009: 分析処理タイムアウトの検出と処理
```javascript
// 【テスト目的】: パフォーマンス制約の確実な遵守確認
// 【テスト内容】: 30秒制約での処理タイムアウト検証
// 【期待される動作】: 制限時間内での強制完了
// 🟢 NFR-001の30秒制約より確実

test('30秒制約を超える処理でタイムアウト処理される', async () => {
  // 【重い処理の模擬】: 巨大データでの処理負荷生成
  const heavyTestFailure = {
    ...standardTestFailure,
    error: { 
      message: 'Error: '.repeat(10000), // 巨大エラーメッセージ
      stack: 'stack trace line\n'.repeat(5000) // 巨大スタックトレース
    }
  };

  const startTime = Date.now();
  const result = await analyzer.analyzeFailure(heavyTestFailure);
  const duration = Date.now() - startTime;

  expect(duration).toBeLessThan(30000); // 【確認内容】: 30秒制約の確実な遵守
  expect(result).toBeDefined(); // 【確認内容】: タイムアウト時でも結果生成
}, 35000); // Jest timeout延長
```

### TC010: 同時複数分析処理での競合状態処理
```javascript
// 【テスト目的】: 並行処理安全性の確認
// 【テスト内容】: 同時複数テスト失敗時の分析処理
// 【期待される動作】: データ競合なしでの独立処理
// 🟡 並行処理の詳細は推測だが妥当

test('複数テスト同時失敗時の並行分析処理が安全に動作する', async () => {
  const testFailures = [
    { ...standardTestFailure, testId: 'concurrent-001' },
    { ...standardTestFailure, testId: 'concurrent-002' },
    { ...standardTestFailure, testId: 'concurrent-003' }
  ];

  // 【並行処理実行】: 同時複数分析の実行
  const results = await Promise.all(
    testFailures.map(failure => analyzer.analyzeFailure(failure))
  );

  // 【競合状態検証】: 各分析結果の独立性確認
  const uniqueIds = new Set(results.map(r => r.id));
  expect(uniqueIds.size).toBe(3); // 【確認内容】: 一意ID生成での競合回避
  expect(results).toHaveLength(3); // 【確認内容】: 全分析処理の正常完了
});
```

## 境界値テストケース

### TC011: 空のエラーメッセージでの処理継続
```javascript
// 【テスト目的】: 最小限入力での処理継続性確認
// 【テスト内容】: error.message空文字での分析実行
// 【期待される動作】: 情報不足でもgraceful degradation
// 🟢 境界値処理要件より確実

test('error.messageが空文字列でも分析処理を継続できる', async () => {
  const emptyErrorTestFailure = {
    ...standardTestFailure,
    error: { message: '' }
  };

  const result = await analyzer.analyzeFailure(emptyErrorTestFailure);

  expect(result.errorPattern.name).toBe('UNKNOWN_ERROR'); // 【確認内容】: 空文字でのUNKNOWN分類
  expect(result.confidenceLevel).toBe(0.1); // 【確認内容】: 適切な低信頼度設定
});
```

### TC012: 巨大エラーメッセージでの処理性能
```javascript
// 【テスト目的】: 大量データでのパフォーマンス要件確認
// 【テスト内容】: 10KB+エラーメッセージでの処理時間検証
// 【期待される動作】: 大量データでも30秒以内完了
// 🟡 10KBサイズは推測だが実用的妥当性あり

test('10KB以上の巨大error.messageでも30秒以内に処理完了する', async () => {
  const largeErrorTestFailure = {
    ...standardTestFailure,
    error: { 
      message: 'Error: detailed information '.repeat(500), // 約10KB
      stack: 'at function\n'.repeat(1000) // 追加データ
    }
  };

  const startTime = Date.now();
  const result = await analyzer.analyzeFailure(largeErrorTestFailure);
  const duration = Date.now() - startTime;

  expect(duration).toBeLessThan(30000); // 【確認内容】: パフォーマンス要件の遵守
  expect(result.errorPattern).toBeDefined(); // 【確認内容】: 大量データでも正常分析
}, 35000);
```

### TC013: null/undefined値での安全な処理
```javascript
// 【テスト目的】: JavaScript特有の値欠損への対応確認
// 【テスト内容】: null/undefined値での例外回避
// 【期待される動作】: null安全な処理継続
// 🟢 JavaScript典型的境界値より確実

test('TestFailureの各フィールドがnull/undefinedでも安全に処理できる', async () => {
  const nullTestFailure = {
    testId: null,
    testTitle: undefined,
    error: null,
    duration: undefined,
    attachments: null,
    timestamp: undefined
  };

  // 【例外発生の回避確認】
  await expect(analyzer.analyzeFailure(nullTestFailure)).resolves.toBeDefined();
  
  const result = await analyzer.analyzeFailure(nullTestFailure);
  expect(result.errorPattern.category).toBe('UNKNOWN'); // 【確認内容】: null値での適切なフォールバック
});
```

### TC014: calculateConfidenceメソッドの境界値動作
```javascript
// 【テスト目的】: 信頼度計算の数値範囲確認
// 【テスト内容】: 極端な信頼度パターンでの計算検証  
// 【期待される動作】: 0-1範囲の確実な保証
// 🟡 calculateConfidenceの詳細は推測だが妥当

test('calculateConfidenceが0-1範囲を確実に返す', async () => {
  // 【極端な信頼度パターンでのテスト】
  const highConfidencePattern = { confidence: 0.99, matchQuality: 'PERFECT' };
  const lowConfidencePattern = { confidence: 0.01, matchQuality: 'POOR' };

  const highResult = analyzer.calculateConfidence(highConfidencePattern);
  const lowResult = analyzer.calculateConfidence(lowConfidencePattern);

  expect(highResult).toBeGreaterThanOrEqual(0); // 【確認内容】: 下限値0以上の保証
  expect(highResult).toBeLessThanOrEqual(1);    // 【確認内容】: 上限値1以下の保証
  expect(lowResult).toBeGreaterThanOrEqual(0);  // 【確認内容】: 低信頼度でも0以上
  expect(lowResult).toBeLessThanOrEqual(1);     // 【確認内容】: 低信頼度でも1以下
});
```

### TC015: 最小限TestFailureでの完全分析実行
```javascript
// 【テスト目的】: 最小限情報での分析品質確認
// 【テスト内容】: 必須フィールドのみでの完全分析実行
// 【期待される動作】: 情報制約下でのサービス品質確保
// 🟡 最小限フィールドセットは推測だが妥当

test('必須フィールドのみのTestFailureでも完全な分析結果を生成できる', async () => {
  // 【最小限データ準備】: 必須フィールドのみのTestFailure
  const minimalTestFailure = {
    testId: 'minimal-001',
    testTitle: 'test',
    error: { message: 'error' },
    duration: 0,
    attachments: [],
    timestamp: new Date()
  };

  const result = await analyzer.analyzeFailure(minimalTestFailure);

  expect(result.id).toBeDefined(); // 【確認内容】: 分析結果IDの確実な生成
  expect(result.errorPattern).toBeDefined(); // 【確認内容】: エラーパターン識別の実行
  expect(result.fixSuggestions).toBeDefined(); // 【確認内容】: 修正提案配列の生成
  expect(result.confidenceLevel).toBeGreaterThan(0); // 【確認内容】: 有効な信頼度計算
});
```

## テスト実装の基本構造

### セットアップ・クリーンアップ
```javascript
describe('TestFailureAnalyzer', () => {
  let analyzer;
  let mockErrorPatternMatcher;
  let mockFixSuggestionGenerator;
  let standardTestFailure;

  beforeEach(() => {
    // 【テスト前準備】: 各テスト実行前のクリーンな環境構築
    mockErrorPatternMatcher = {
      match: jest.fn()
    };
    mockFixSuggestionGenerator = {
      generate: jest.fn()
    };
    
    analyzer = new TestFailureAnalyzer(
      mockErrorPatternMatcher,
      mockFixSuggestionGenerator
    );
    
    // 【標準テストデータ】: 共通で使用するTestFailureオブジェクト
    standardTestFailure = {
      testId: 'standard-test-001',
      testTitle: 'Standard Test',
      testFile: 'standard.spec.js',
      projectName: 'chromium',
      error: { message: 'Standard error message' },
      duration: 5000,
      attachments: [],
      timestamp: new Date()
    };
    
    // 【デフォルトモック設定】: 標準的な成功パターンの設定
    mockErrorPatternMatcher.match.mockResolvedValue({
      name: 'STANDARD_ERROR',
      category: 'UI_ELEMENT',
      confidence: 0.8
    });
    mockFixSuggestionGenerator.generate.mockResolvedValue([
      { type: 'STANDARD_FIX', priority: 'MEDIUM' }
    ]);
  });

  afterEach(() => {
    // 【テスト後処理】: 各テスト実行後のクリーンアップ
    jest.clearAllMocks(); // 【状態復元】: モック状態のリセット
  });
});
```

## テストケース実行予定
- **総テストケース数**: 15個
- **正常系**: 5個 (TC001-TC005)
- **異常系**: 5個 (TC006-TC010) 
- **境界値**: 5個 (TC011-TC015)
- **カバレッジ目標**: 95%以上
- **実行時間目標**: 全テスト30秒以内