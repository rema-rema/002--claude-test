# TDD Requirements: TestFailureAnalyzer

## 概要
TestFailureAnalyzerは、Playwrightテスト失敗時の原因分析と修正提案の統合を行う責務を持つコアコンポーネントです。テスト失敗情報から自動的にエラーパターンを識別し、修正提案を生成して、承認フローの基盤データを提供します。

## 機能要件

### 主要機能
1. **テスト失敗分析**: テスト失敗情報の詳細解析
   - 入力: TestFailure型オブジェクト（エラーメッセージ、スタックトレース、テストメタ情報）
   - 出力: AnalysisResult型オブジェクト（エラーパターン + 修正提案 + 信頼度）
   - 制約: 30秒以内で分析完了、不明エラーでも安全に処理

### API仕様
```typescript
interface TestFailureAnalyzer {
  constructor(errorPatternMatcher: ErrorPatternMatcher, fixSuggestionGenerator: FixSuggestionGenerator);
  analyzeFailure(testResult: TestFailure): Promise<AnalysisResult>;
  calculateConfidence(errorPattern: ErrorPattern): number;
}

interface TestFailure {
  testId: string;
  testTitle: string;
  testFile: string;
  projectName: string;
  error: {
    message: string;
    stack?: string;
    location?: { file: string; line: number; column: number; };
  };
  duration: number;
  attachments: Attachment[];
  timestamp: Date;
}

interface AnalysisResult {
  id: string;
  testInfo: TestFailure;
  errorPattern: ErrorPattern;
  fixSuggestions: FixSuggestion[];
  analysisTimestamp: Date;
  confidenceLevel: number;
}
```

## 非機能要件

### パフォーマンス
- 応答時間: 分析処理30秒以内完了（NFR-001準拠）
- メモリ使用量: 512MB以内での動作

### セキュリティ
- 入力検証: TestFailure型の構造検証、不正データの安全な処理
- エラー情報保護: 機密情報を含むスタックトレースの適切な処理

### 保守性
- 単一責任原則: 分析統合機能に責務を限定
- 依存性逆転: インターフェース経由での依存コンポーネント利用

## 受け入れ基準

### 成功条件
- [ ] 有効なTestFailure入力から適切なAnalysisResultを生成できる
- [ ] ErrorPatternMatcherとFixSuggestionGeneratorとの統合が正常動作する
- [ ] 信頼度計算が論理的に妥当な値（0-1範囲）を返す
- [ ] 30秒以内に分析処理が完了する

### 境界値テスト
- [ ] 空のエラーメッセージでも処理継続する
- [ ] 非常に長いエラーメッセージ（10KB以上）を適切に処理する
- [ ] 不完全なTestFailure構造でも安全に処理する
- [ ] 同時複数テスト失敗時の並行処理が正常動作する

### エラー処理
- [ ] ErrorPatternMatcher例外時にデフォルトパターンで継続処理
- [ ] FixSuggestionGenerator例外時に空の修正提案リストで継続処理
- [ ] 不明エラーパターンでもUNKNOWN_ERRORとして安全に処理
- [ ] 分析失敗時でも後続のApprovalRequestManager呼び出しを継続

## テスト戦略

### 単体テスト
- テスト対象: analyzeFailure、calculateConfidence
- テストケース数: 15個（正常系5、異常系5、境界値5）
- モック対象: ErrorPatternMatcher、FixSuggestionGenerator

### 統合テスト  
- テスト範囲: ErrorPatternMatcher + FixSuggestionGenerator連携
- テストシナリオ: UI_ELEMENT、TIMING、ASSERTION各カテゴリでの分析フロー

## 実装上の注意点
- ErrorPatternMatcherとFixSuggestionGeneratorの初期化はコンストラクタで受け取る
- 非同期処理（async/await）を一貫して使用する
- エラーハンドリングはtry-catch + 継続処理パターンを採用
- 分析結果IDは一意性を保証する（UUID等を使用）
- 信頼度計算は複数要素（パターンマッチ精度、修正提案品質等）を統合する

## EARS要件対応
- REQ-002: テスト失敗時の原因分析自動実行
- REQ-101: 失敗の詳細理由分析
- REQ-102: 複数失敗時の個別分析  
- REQ-105: エラー発生時の自動解決試行
- NFR-001: 30秒以内の応答時間制約