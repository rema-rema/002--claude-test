import { describe, it, expect, beforeEach } from '@jest/globals';
import { FixSuggestionGenerator } from '../../components/FixSuggestionGenerator.js';

describe('FixSuggestionGenerator', () => {
  let generator;

  beforeEach(() => {
    generator = new FixSuggestionGenerator();
  });

  // 正常系テスト (1-6)
  describe('正常系修正提案生成', () => {
    it('should generate UI_ELEMENT suggestions', async () => {
      const errorPattern = { category: 'UI_ELEMENT', confidence: 0.9 };
      const testResult = { error: "locator('#login-btn') not found", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
      expect(result.suggestions.length).toBeGreaterThan(0);
      expect(result.category).toBe('UI_ELEMENT');
    });

    it('should generate TIMING suggestions', async () => {
      const errorPattern = { category: 'TIMING', confidence: 0.85 };
      const testResult = { error: "Timeout 5000ms exceeded", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
      expect(result.category).toBe('TIMING');
    });

    it('should generate ASSERTION suggestions', async () => {
      const errorPattern = { category: 'ASSERTION', confidence: 0.8 };
      const testResult = { error: 'Expected "Welcome" but received "Loading"', filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
      expect(result.category).toBe('ASSERTION');
    });

    it('should generate NETWORK suggestions', async () => {
      const errorPattern = { category: 'NETWORK', confidence: 0.8 };
      const testResult = { error: "Failed to load resource: net::ERR_CONNECTION_REFUSED", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
      expect(result.category).toBe('NETWORK');
      expect(result.suggestions.some(s => s.text.includes('接続'))).toBe(true);
    });

    it('should generate SECURITY suggestions', async () => {
      const errorPattern = { category: 'SECURITY', confidence: 0.85 };
      const testResult = { error: "Blocked by CORS policy", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
      expect(result.category).toBe('SECURITY');
      expect(result.suggestions.some(s => s.text.includes('CORS'))).toBe(true);
    });

    it('should identify automatable fixes', async () => {
      const errorPattern = { category: 'UI_ELEMENT', confidence: 0.9 };
      const testResult = { error: "locator('#old-selector') not found", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.automationLevel).toBeDefined();
      expect(['HIGH', 'MEDIUM', 'LOW']).toContain(result.automationLevel);
    });
  });

  // 異常系テスト (7-9)
  describe('異常系エラーハンドリング', () => {
    it('should handle unknown category gracefully', async () => {
      const errorPattern = { category: 'UNKNOWN_CATEGORY', confidence: 0.3 };
      const testResult = { error: "Unknown error", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
      expect(result.suggestions.length).toBeGreaterThan(0);
    });

    it('should handle null inputs gracefully', async () => {
      const result = await generator.generateSuggestions(null, null);
      
      expect(result.suggestions).toBeDefined();
      expect(result.suggestions.length).toBeGreaterThan(0);
    });

    it('should handle malformed error patterns', async () => {
      const errorPattern = { confidence: 0.5 }; // categoryなし
      const testResult = { error: "Some error", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions).toBeDefined();
    });
  });

  // リスク評価・効果予想テスト (10-12)
  describe('リスク評価・効果予想', () => {
    it('should calculate risk assessment', async () => {
      const errorPattern = { category: 'UI_ELEMENT', confidence: 0.9 };
      const testResult = { error: "locator('.btn') not found", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.riskAssessment).toBeDefined();
      expect(['SMALL', 'MEDIUM', 'LARGE']).toContain(result.riskAssessment.impact);
      expect(result.riskAssessment.successProbability).toBeGreaterThanOrEqual(0);
      expect(result.riskAssessment.successProbability).toBeLessThanOrEqual(1);
    });

    it('should predict fix effectiveness', async () => {
      const errorPattern = { category: 'TIMING', confidence: 0.8 };
      const testResult = { error: "Timeout exceeded", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.effectiveness).toBeDefined();
      expect(result.effectiveness.expectedImpact).toBeDefined();
      expect(result.effectiveness.timeToFix).toBeDefined();
    });

    it('should assess impact scope correctly', async () => {
      const errorPattern = { category: 'SECURITY', confidence: 0.9 };
      const testResult = { error: "CSP violation", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.riskAssessment.impact).toBe('LARGE'); // セキュリティは影響大
    });
  });

  // 優先度付けアルゴリズムテスト (13-15)
  describe('優先度付けアルゴリズム', () => {
    it('should calculate priority scores', async () => {
      const errorPattern = { category: 'UI_ELEMENT', confidence: 0.9 };
      const testResult = { error: "locator('.critical') not found", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.priorityScore).toBeDefined();
      expect(result.priorityScore).toBeGreaterThanOrEqual(0);
      expect(result.priorityScore).toBeLessThanOrEqual(100);
    });

    it('should prioritize high-confidence suggestions', async () => {
      const highConfPattern = { category: 'UI_ELEMENT', confidence: 0.95 };
      const lowConfPattern = { category: 'UI_ELEMENT', confidence: 0.3 };
      const testResult = { error: "locator('.btn') not found", filePath: 'test.spec.js' };
      
      const highResult = await generator.generateSuggestions(highConfPattern, testResult);
      const lowResult = await generator.generateSuggestions(lowConfPattern, testResult);
      
      expect(highResult.priorityScore).toBeGreaterThan(lowResult.priorityScore);
    });

    it('should rank suggestions within categories', async () => {
      const errorPattern = { category: 'UI_ELEMENT', confidence: 0.8 };
      const testResult = { error: "locator('.multiple') not found", filePath: 'test.spec.js' };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      if (result.suggestions.length > 1) {
        expect(result.suggestions[0].priority).toBeGreaterThanOrEqual(result.suggestions[1].priority);
      }
    });
  });

  // 統合テスト (16-18)
  describe('統合テスト', () => {
    it('should integrate with ErrorPatternMatcher results', async () => {
      const errorPattern = { 
        category: 'UI_ELEMENT', 
        confidence: 0.9,
        pattern: /locator\('.+?'\) not found/
      };
      const testResult = { 
        error: "locator('.test-button') not found", 
        filePath: 'integration.spec.js',
        testName: 'should click button'
      };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result).toHaveProperty('suggestions');
      expect(result).toHaveProperty('automationLevel');
      expect(result).toHaveProperty('riskAssessment');
      expect(result).toHaveProperty('priorityScore');
    });

    it('should handle complex error scenarios', async () => {
      const errorPattern = { category: 'NETWORK', confidence: 0.75 };
      const testResult = { 
        error: "Failed to load resource: net::ERR_TIMEOUT after 30000ms", 
        filePath: 'network.spec.js',
        testName: 'should load API data'
      };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions.length).toBeGreaterThan(2);
      expect(result.riskAssessment.impact).toBeDefined();
      expect(result.automationLevel).toBe('MEDIUM'); // ネットワークエラーは部分自動化
    });

    it('should provide comprehensive fix strategies', async () => {
      const errorPattern = { category: 'ASSERTION', confidence: 0.85 };
      const testResult = { 
        error: 'Expected text "Success" but received "Error: Failed to process"', 
        filePath: 'assertion.spec.js',
        testName: 'should show success message'
      };
      
      const result = await generator.generateSuggestions(errorPattern, testResult);
      
      expect(result.suggestions.length).toBeGreaterThanOrEqual(2);
      expect(result.effectiveness.expectedImpact).toBeGreaterThan(0.5);
      expect(result.priorityScore).toBeGreaterThan(50); // 中程度以上の優先度
    });
  });
});