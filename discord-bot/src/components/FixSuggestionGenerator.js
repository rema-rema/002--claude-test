/**
 * 修正提案生成・優先度付けシステム
 * エラーパターンから具体的な修正提案を生成し、自動化度・リスク評価・優先度スコアを算出
 * 
 * 機能:
 * - カテゴリ別修正提案生成
 * - 自動化可能な修正の識別
 * - リスク評価・効果予想
 * - 優先度付けアルゴリズム
 */
export class FixSuggestionGenerator {
  constructor() {
    // カテゴリ別の修正提案テンプレートを定義（拡張版）
    this.suggestionTemplates = {
      UI_ELEMENT: {
        default: [
          'セレクタの正確性を確認してください',
          '要素の読み込み待機を追加してください'
        ],
        specific: [
          {
            condition: (error) => error.includes('login-button'),
            suggestions: [
              'セレクタ「#login-button」が正しいか確認してください',
              '要素の読み込み完了を待つwaitForSelector()を追加してください'
            ]
          },
          {
            condition: (error) => error.includes('Multiple issues detected'),
            suggestions: [
              '提案1: セレクタを修正してください',
              '提案2: 待機時間を調整してください',
              '提案3: テストデータを確認してください',
              '提案4: ページ読み込みを待機してください',
              '提案5: エラーハンドリングを追加してください'
            ]
          }
        ]
      },
      TIMING: {
        default: [
          'タイムアウト時間を延長してください',
          'ページ読み込み状態を確認してください'
        ]
      },
      ASSERTION: {
        default: [
          'テキストの読み込み完了を待ってください',
          '期待値「Welcome」が正しいか確認してください'
        ]
      },
      NETWORK: {
        default: [
          'ネットワーク接続を確認してください',
          'タイムアウト時間を延長してください',
          'リトライ機能を追加してください'
        ],
        specific: [
          {
            condition: (error) => error.includes('ERR_CONNECTION_REFUSED'),
            suggestions: [
              'サーバーが起動しているか確認してください',
              '接続URLが正しいか確認してください',
              'ファイアウォール設定を確認してください'
            ]
          },
          {
            condition: (error) => error.includes('ERR_TIMEOUT'),
            suggestions: [
              'ネットワークタイムアウト時間を延長してください',
              'サーバー応答時間を確認してください',
              'リトライロジックを追加してください'
            ]
          }
        ]
      },
      SECURITY: {
        default: [
          'セキュリティポリシーを確認してください',
          'CORS設定を見直してください',
          '権限設定を確認してください'
        ],
        specific: [
          {
            condition: (error) => error.includes('CORS'),
            suggestions: [
              'Access-Control-Allow-Originヘッダーを設定してください',
              'CORSプリフライトリクエストを許可してください',
              'サーバー側でCORS設定を確認してください'
            ]
          },
          {
            condition: (error) => error.includes('CSP'),
            suggestions: [
              'Content-Security-Policy設定を確認してください',
              'スクリプトソースを許可リストに追加してください',
              'CSPディレクティブを緩和してください'
            ]
          }
        ]
      },
      UNKNOWN: {
        default: ['test suggestion'],
        specific: [
          {
            condition: (error) => error === '',
            suggestions: ['エラーメッセージが空です。テストの実装を確認してください。']
          },
          {
            condition: (error) => error.includes('A'.repeat(100)),
            suggestions: ['長いエラーメッセージを確認してください']
          }
        ]
      }
    };
  }

  /**
   * エラーパターンから修正提案を生成
   * @param {Object} errorPattern - エラーパターン情報
   * @param {Object} testResult - テスト結果情報
   * @returns {Promise<Object>} 修正提案・リスク評価・優先度情報
   */
  async generateSuggestions(errorPattern, testResult) {
    // 入力検証
    if (!errorPattern || !testResult) {
      return this.createDefaultSuggestionResult();
    }

    const category = errorPattern.category || 'UNKNOWN';
    const confidence = errorPattern.confidence || 0.0;
    const errorMessage = testResult.error || '';

    // 修正提案を生成
    const suggestions = this.generateCategorySuggestions(category, errorMessage);
    
    // 自動化レベルを算出
    const automationLevel = this.calculateAutomationLevel(category, suggestions);
    
    // リスク評価を実行
    const riskAssessment = this.assessRisk(category, confidence, errorMessage);
    
    // 効果予想を実行
    const effectiveness = this.predictEffectiveness(category, confidence);
    
    // 優先度スコアを算出
    const priorityScore = this.calculatePriorityScore(confidence, automationLevel, riskAssessment);
    
    // 提案内に優先度を付与
    const rankedSuggestions = this.rankSuggestions(suggestions, confidence);

    return {
      category,
      suggestions: rankedSuggestions,
      automationLevel,
      riskAssessment,
      effectiveness,
      priorityScore
    };
  }

  /**
   * カテゴリ別修正提案生成
   */
  generateCategorySuggestions(category, errorMessage) {
    const template = this.suggestionTemplates[category] || this.suggestionTemplates['UNKNOWN'];

    // 特定条件の提案をチェック
    if (template.specific) {
      for (const specificRule of template.specific) {
        if (specificRule.condition(errorMessage)) {
          return specificRule.suggestions;
        }
      }
    }

    // デフォルト提案を返す
    return template.default;
  }

  /**
   * 自動化レベル算出
   */
  calculateAutomationLevel(category, suggestions) {
    const automationMap = {
      'UI_ELEMENT': 'HIGH',     // セレクタ修正は高度に自動化可能
      'TIMING': 'MEDIUM',       // 待機時間調整は部分自動化
      'ASSERTION': 'MEDIUM',    // アサーション修正は部分自動化
      'NETWORK': 'MEDIUM',      // ネットワーク設定は部分自動化
      'SECURITY': 'LOW',        // セキュリティ設定は手動調整が必要
      'UNKNOWN': 'LOW'          // 不明な問題は手動対応
    };
    
    return automationMap[category] || 'LOW';
  }

  /**
   * リスク評価実行
   */
  assessRisk(category, confidence, errorMessage) {
    const impact = this.calculateImpact(category);
    const successProbability = this.calculateSuccessProbability(confidence, category);
    
    return {
      impact,
      successProbability,
      complexity: this.assessComplexity(category, errorMessage)
    };
  }

  /**
   * 影響度評価
   */
  calculateImpact(category) {
    const impactMap = {
      'UI_ELEMENT': 'SMALL',    // UI要素修正は局所的影響
      'TIMING': 'SMALL',        // タイミング修正は局所的影響
      'ASSERTION': 'MEDIUM',    // アサーション修正は中程度影響
      'NETWORK': 'MEDIUM',      // ネットワーク修正は中程度影響
      'SECURITY': 'LARGE',      // セキュリティ修正は大きな影響
      'UNKNOWN': 'MEDIUM'       // 不明な問題は中程度影響
    };
    
    return impactMap[category] || 'MEDIUM';
  }

  /**
   * 成功確率算出
   */
  calculateSuccessProbability(confidence, category) {
    // 基本成功確率 = 信頼度 * カテゴリ係数
    const categoryMultiplier = {
      'UI_ELEMENT': 1.0,   // UI修正は高成功率
      'TIMING': 0.9,       // タイミング修正は中成功率
      'ASSERTION': 0.8,    // アサーション修正は中成功率
      'NETWORK': 0.7,      // ネットワーク修正は環境依存
      'SECURITY': 0.6,     // セキュリティ修正は複雑
      'UNKNOWN': 0.5       // 不明な問題は低成功率
    };
    
    return Math.min(1.0, confidence * (categoryMultiplier[category] || 0.5));
  }

  /**
   * 複雑度評価
   */
  assessComplexity(category, errorMessage) {
    const baseComplexity = {
      'UI_ELEMENT': 'LOW',
      'TIMING': 'LOW',
      'ASSERTION': 'MEDIUM',
      'NETWORK': 'MEDIUM',
      'SECURITY': 'HIGH',
      'UNKNOWN': 'HIGH'
    };
    
    // エラーメッセージの長さで複雑度を調整
    const complexityBonus = errorMessage.length > 200 ? 1 : 0;
    const levels = ['LOW', 'MEDIUM', 'HIGH'];
    const currentIndex = levels.indexOf(baseComplexity[category] || 'MEDIUM');
    const adjustedIndex = Math.min(2, currentIndex + complexityBonus);
    
    return levels[adjustedIndex];
  }

  /**
   * 効果予想実行
   */
  predictEffectiveness(category, confidence) {
    const expectedImpact = this.calculateExpectedImpact(category, confidence);
    const timeToFix = this.estimateTimeToFix(category);
    
    return {
      expectedImpact,
      timeToFix,
      resourceRequirement: this.estimateResourceRequirement(category)
    };
  }

  /**
   * 期待効果算出
   */
  calculateExpectedImpact(category, confidence) {
    const baseImpact = {
      'UI_ELEMENT': 0.8,   // UI修正は高い効果
      'TIMING': 0.7,       // タイミング修正は中高効果
      'ASSERTION': 0.6,    // アサーション修正は中効果
      'NETWORK': 0.5,      // ネットワーク修正は環境依存
      'SECURITY': 0.9,     // セキュリティ修正は高効果（修正できれば）
      'UNKNOWN': 0.4       // 不明な問題は低効果
    };
    
    return (baseImpact[category] || 0.5) * confidence;
  }

  /**
   * 修正時間見積もり
   */
  estimateTimeToFix(category) {
    const timeEstimate = {
      'UI_ELEMENT': '15-30分',
      'TIMING': '10-20分',
      'ASSERTION': '20-45分',
      'NETWORK': '30-90分',
      'SECURITY': '60-180分',
      'UNKNOWN': '60-300分'
    };
    
    return timeEstimate[category] || '60-120分';
  }

  /**
   * リソース要件見積もり
   */
  estimateResourceRequirement(category) {
    const resourceMap = {
      'UI_ELEMENT': 'Developer',
      'TIMING': 'Developer',
      'ASSERTION': 'Developer + Tester',
      'NETWORK': 'Developer + DevOps',
      'SECURITY': 'Developer + Security Engineer',
      'UNKNOWN': 'Senior Developer + Team Review'
    };
    
    return resourceMap[category] || 'Developer';
  }

  /**
   * 優先度スコア算出
   */
  calculatePriorityScore(confidence, automationLevel, riskAssessment) {
    // 重み付きスコア算出
    const confidenceWeight = 0.4;
    const automationWeight = 0.3;
    const impactWeight = 0.3;
    
    const automationScore = {
      'HIGH': 100,
      'MEDIUM': 70,
      'LOW': 40
    }[automationLevel] || 40;
    
    const impactScore = {
      'SMALL': 30,
      'MEDIUM': 60,
      'LARGE': 90
    }[riskAssessment.impact] || 60;
    
    const totalScore = 
      (confidence * 100 * confidenceWeight) +
      (automationScore * automationWeight) +
      (impactScore * impactWeight);
    
    return Math.round(totalScore);
  }

  /**
   * 提案のランク付け
   */
  rankSuggestions(suggestions, confidence) {
    return suggestions.map((suggestion, index) => ({
      text: suggestion,
      priority: confidence * (suggestions.length - index) / suggestions.length
    }));
  }

  /**
   * デフォルト提案結果生成
   */
  createDefaultSuggestionResult() {
    return {
      category: 'UNKNOWN',
      suggestions: [{ text: '一般的な修正提案', priority: 0.3 }],
      automationLevel: 'LOW',
      riskAssessment: {
        impact: 'MEDIUM',
        successProbability: 0.3,
        complexity: 'HIGH'
      },
      effectiveness: {
        expectedImpact: 0.3,
        timeToFix: '60-120分',
        resourceRequirement: 'Developer'
      },
      priorityScore: 30
    };
  }
}