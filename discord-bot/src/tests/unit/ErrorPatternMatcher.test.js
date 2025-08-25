import { describe, it, expect, beforeEach } from '@jest/globals';
import { ErrorPatternMatcher } from '../../components/ErrorPatternMatcher.js';

describe('ErrorPatternMatcher', () => {
  let matcher;

  beforeEach(() => {
    matcher = new ErrorPatternMatcher();
  });

  // 正常系テスト (1-7)
  describe('正常系パターンマッチング', () => {
    it('should match UI_ELEMENT_NOT_FOUND pattern', async () => {
      const error = "locator('#button').click() not found";
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('UI_ELEMENT');
      expect(result.confidence).toBeGreaterThan(0.8);
    });

    it('should match TIMEOUT_EXCEEDED pattern', async () => {
      const error = "Timeout 30000ms exceeded waiting for element";
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('TIMING');
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    it('should match ASSERTION_FAILED pattern', async () => {
      const error = 'Expected "Hello" but received "World"';
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('ASSERTION');
      expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    });

    it('should match NETWORK_ERROR pattern', async () => {
      const error = "Failed to load resource: net::ERR_CONNECTION_REFUSED";
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('NETWORK');
      expect(result.confidence).toBeGreaterThan(0.7);
    });

    it('should match SECURITY_ERROR pattern', async () => {
      const error = "Blocked by CORS policy: Cross origin requests are only supported for protocol schemes";
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('SECURITY');
      expect(result.confidence).toBeGreaterThan(0.7);
    });

    it('should match MULTIPLE_ISSUES pattern', async () => {
      const error = "Multiple issues detected in test execution";
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('UI_ELEMENT');
      expect(result.confidence).toBeGreaterThanOrEqual(0.7);
    });

    it('should calculate appropriate confidence levels', async () => {
      const highConfidenceError = "locator('.specific-selector').click() not found";
      const result = await matcher.matchPattern(highConfidenceError);
      
      expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    });
  });

  // 異常系テスト (8-12)
  describe('異常系エラーハンドリング', () => {
    it('should handle null input gracefully', async () => {
      const result = await matcher.matchPattern(null);
      
      expect(result.category).toBe('UNKNOWN');
      expect(result.confidence).toBe(0.0);
    });

    it('should handle undefined input gracefully', async () => {
      const result = await matcher.matchPattern(undefined);
      
      expect(result.category).toBe('UNKNOWN');
      expect(result.confidence).toBe(0.0);
    });

    it('should handle empty string input', async () => {
      const result = await matcher.matchPattern('');
      
      expect(result.category).toBe('UNKNOWN');
      expect(result.confidence).toBe(0.0);
    });

    it('should handle non-string input', async () => {
      const result = await matcher.matchPattern(123);
      
      expect(result.category).toBe('UNKNOWN');
      expect(result.confidence).toBe(0.0);
    });

    it('should handle special characters safely', async () => {
      const error = "Error with special chars: []{}.?*+^$|\\()";
      const result = await matcher.matchPattern(error);
      
      expect(result.category).toBe('UNKNOWN');
      expect(result.pattern).toBeDefined();
    });
  });

  // 境界値テスト (13-16)
  describe('境界値テスト', () => {
    it('should handle very long error messages', async () => {
      const longError = "locator('.test') not found".repeat(1000);
      const start = Date.now();
      
      const result = await matcher.matchPattern(longError);
      const duration = Date.now() - start;
      
      expect(result.category).toBe('UI_ELEMENT');
      expect(duration).toBeLessThan(100); // 100ms以内で処理
    });

    it('should handle minimal matching patterns', async () => {
      const minimalError = "not found";
      const result = await matcher.matchPattern(minimalError);
      
      expect(result).toBeDefined();
      expect(result.category).toBeDefined();
    });

    it('should handle complex nested patterns', async () => {
      const complexError = "locator('div[data-testid=\"complex-component\"]').locator('button').click() not found after timeout";
      const result = await matcher.matchPattern(complexError);
      
      expect(result.category).toBe('UI_ELEMENT');
      expect(result.confidence).toBeGreaterThan(0.8);
    });

    it('should handle unicode characters', async () => {
      const unicodeError = "locator('テスト要素').click() not found 🚫";
      const result = await matcher.matchPattern(unicodeError);
      
      expect(result.category).toBe('UI_ELEMENT');
      expect(result.pattern).toBeDefined();
    });
  });

  // パフォーマンステスト (17-20)
  describe('パフォーマンステスト', () => {
    it('should process multiple error messages efficiently', async () => {
      const errors = Array(100).fill(0).map((_, i) => `locator('#test${i}') not found`);
      const start = Date.now();
      
      const results = await Promise.all(errors.map(error => matcher.matchPattern(error)));
      const duration = Date.now() - start;
      
      expect(results.length).toBe(100);
      expect(duration).toBeLessThan(1000); // 1秒以内で100件処理
      expect(results.every(r => r.category === 'UI_ELEMENT')).toBe(true);
    });

    it('should maintain performance with different pattern types', async () => {
      const mixedErrors = [
        "locator('.test') not found",
        "Timeout 5000ms exceeded",
        'Expected "test" but received "fail"',
        "Failed to load resource: net::ERR_TIMEOUT",
        "Blocked by CORS policy"
      ];
      
      const start = Date.now();
      const results = await Promise.all(mixedErrors.map(error => matcher.matchPattern(error)));
      const duration = Date.now() - start;
      
      expect(results.length).toBe(5);
      expect(duration).toBeLessThan(50); // 50ms以内で5件処理
    });

    it('should handle memory efficiently with large datasets', async () => {
      const memoryStart = process.memoryUsage().heapUsed;
      const largeErrors = Array(1000).fill(0).map((_, i) => `Error ${i}: locator('#element${i}') not found with details`.repeat(10));
      
      const results = await Promise.all(largeErrors.map(error => matcher.matchPattern(error)));
      const memoryEnd = process.memoryUsage().heapUsed;
      const memoryIncrease = (memoryEnd - memoryStart) / 1024 / 1024; // MB
      
      expect(results.length).toBe(1000);
      expect(memoryIncrease).toBeLessThan(100); // 100MB以下のメモリ増加
    });

    it('should maintain confidence accuracy under load', async () => {
      const highConfidenceErrors = Array(50).fill("locator('.specific-selector').click() not found");
      const lowConfidenceErrors = Array(50).fill("Unknown error occurred");
      const allErrors = [...highConfidenceErrors, ...lowConfidenceErrors];
      
      const results = await Promise.all(allErrors.map(error => matcher.matchPattern(error)));
      
      const highConfidenceResults = results.slice(0, 50);
      const lowConfidenceResults = results.slice(50);
      
      expect(highConfidenceResults.every(r => r.confidence > 0.8)).toBe(true);
      expect(lowConfidenceResults.every(r => r.confidence <= 0.3)).toBe(true);
    });
  });

  // ヘルパーメソッドテスト
  describe('ヘルパーメソッド', () => {
    it('should create unknown pattern correctly', () => {
      const error = "Custom error message";
      const result = matcher.createUnknownPattern(error);
      
      expect(result.category).toBe('UNKNOWN');
      expect(result.pattern).toBeDefined();
      expect(result.confidence).toBe(0.3);
    });
  });
});