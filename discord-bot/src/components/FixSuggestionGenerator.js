export class FixSuggestionGenerator {
  constructor() {
    // カテゴリ別の修正提案テンプレートを定義
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

  async generateSuggestions(errorPattern, testResult) {
    const category = errorPattern.category;
    const template = this.suggestionTemplates[category];

    if (!template) {
      return ['一般的な修正提案'];
    }

    // 特定条件の提案をチェック
    if (template.specific) {
      for (const specificRule of template.specific) {
        if (specificRule.condition(testResult.error)) {
          return specificRule.suggestions;
        }
      }
    }

    // デフォルト提案を返す
    return template.default;
  }
}