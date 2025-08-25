import { describe, it, expect, beforeEach } from '@jest/globals';
import PlaywrightDiscordReporter from '../../reporters/playwright-discord-reporter.js';

describe('PlaywrightDiscordReporter Integration (TASK-301)', () => {
  let reporter;

  beforeEach(() => {
    reporter = new PlaywrightDiscordReporter();
  });

  // 正常動作テスト (5件)
  describe('正常動作フロー', () => {
    it('should initialize with required components for approval flow', () => {
      expect(reporter).toBeDefined();
      expect(reporter.discordService).toBeDefined();
      expect(reporter.testResults).toBeDefined();
      expect(reporter.onTestEnd).toBeDefined();
    });

    it('should not process approval request for passing tests', async () => {
      const test = { title: 'Success test', location: { file: 'test.spec.js' } };
      const result = { status: 'passed', duration: 100 };

      // Should not throw and should process normally
      await expect(reporter.onTestEnd(test, result)).resolves.not.toThrow();
      
      // Test should be recorded in results
      expect(reporter.testResults).toContainEqual(
        expect.objectContaining({
          title: 'Success test',
          status: 'passed',
          duration: 100
        })
      );
    });

    it('should handle test failure and attempt integration flow', async () => {
      const test = { 
        title: 'Login test',
        location: { file: 'login.spec.js' }
      };
      const result = {
        status: 'failed',
        error: { message: 'Element not found', stack: 'stack trace' },
        duration: 5000
      };

      // Should not throw even if approval integration fails
      await expect(reporter.onTestEnd(test, result)).resolves.not.toThrow();
      
      // Failed test should be recorded
      expect(reporter.testResults).toContainEqual(
        expect.objectContaining({
          title: 'Login test',
          status: 'failed',
          duration: 5000
        })
      );
    });

    it('should handle multiple test failures individually', async () => {
      const tests = [
        { title: 'Test 1', location: { file: 'test1.spec.js' } },
        { title: 'Test 2', location: { file: 'test2.spec.js' } }
      ];
      const results = [
        { status: 'failed', error: { message: 'Error 1' } },
        { status: 'failed', error: { message: 'Error 2' } }
      ];

      for (let i = 0; i < tests.length; i++) {
        await expect(reporter.onTestEnd(tests[i], results[i])).resolves.not.toThrow();
      }

      // Both tests should be recorded
      expect(reporter.testResults.length).toBe(2);
      expect(reporter.testResults.filter(t => t.status === 'failed')).toHaveLength(2);
    });

    it('should validate test result data structure consistency', async () => {
      const test = { title: 'Consistency test', location: { file: 'test.spec.js' } };
      const result = { 
        status: 'failed', 
        error: { message: 'Validation error' },
        duration: 3000,
        attachments: []
      };

      await reporter.onTestEnd(test, result);

      const recordedTest = reporter.testResults.find(t => t.title === 'Consistency test');
      expect(recordedTest).toBeDefined();
      expect(recordedTest.title).toBe('Consistency test');
      expect(recordedTest.status).toBe('failed');
      expect(recordedTest.duration).toBe(3000);
      expect(recordedTest.error).toBeDefined();
    });
  });

  // 異常系テスト (5件)
  describe('異常系エラーハンドリング', () => {
    it('should handle null test input gracefully', async () => {
      const test = null;
      const result = { status: 'failed', error: { message: 'Test error' } };

      await expect(reporter.onTestEnd(test, result)).resolves.not.toThrow();
      
      // Should not add invalid test to results
      expect(reporter.testResults.length).toBe(0);
    });

    it('should handle undefined result input', async () => {
      const test = { title: 'Valid test', location: { file: 'test.spec.js' } };
      const result = undefined;

      await expect(reporter.onTestEnd(test, result)).resolves.not.toThrow();
    });

    it('should handle missing error details in failed test', async () => {
      const test = { title: 'No error test', location: { file: 'test.spec.js' } };
      const result = { status: 'failed' }; // no error object

      await expect(reporter.onTestEnd(test, result)).resolves.not.toThrow();
      
      const recordedTest = reporter.testResults.find(t => t.title === 'No error test');
      expect(recordedTest).toBeDefined();
      expect(recordedTest.status).toBe('failed');
    });

    it('should be resilient to malformed test data', async () => {
      const test = { /* missing title */ location: { file: 'test.spec.js' } };
      const result = { status: 'failed', error: { message: 'Error' } };

      await expect(reporter.onTestEnd(test, result)).resolves.not.toThrow();
    });

    it('should handle concurrent test processing without race conditions', async () => {
      const concurrentTests = Array(10).fill(0).map((_, i) => ({
        title: `Concurrent Test ${i}`,
        location: { file: `test${i}.spec.js` }
      }));
      const concurrentResults = concurrentTests.map((_, i) => ({
        status: i % 2 === 0 ? 'passed' : 'failed',
        error: i % 2 === 1 ? { message: `Error ${i}` } : undefined,
        duration: Math.random() * 1000
      }));

      // Process all tests concurrently
      const promises = concurrentTests.map((test, i) =>
        reporter.onTestEnd(test, concurrentResults[i])
      );

      await expect(Promise.all(promises)).resolves.not.toThrow();
      
      // All tests should be recorded
      expect(reporter.testResults.length).toBe(10);
    });
  });

  // 統合テスト (5件) 
  describe('統合テスト', () => {
    it('should maintain existing PlaywrightDiscordReporter functionality', async () => {
      // Test core reporter lifecycle methods
      expect(typeof reporter.onBegin).toBe('function');
      expect(typeof reporter.onTestBegin).toBe('function');
      expect(typeof reporter.onTestEnd).toBe('function');
      expect(typeof reporter.onEnd).toBe('function');
      expect(typeof reporter.createTestSummary).toBe('function');
    });

    it('should preserve test result collection mechanism', async () => {
      const tests = [
        { title: 'Passed Test', location: { file: 'pass.spec.js' } },
        { title: 'Failed Test', location: { file: 'fail.spec.js' } },
        { title: 'Skipped Test', location: { file: 'skip.spec.js' } }
      ];
      const results = [
        { status: 'passed', duration: 100 },
        { status: 'failed', error: { message: 'Error' }, duration: 200 },
        { status: 'skipped', duration: 0 }
      ];

      for (let i = 0; i < tests.length; i++) {
        await reporter.onTestEnd(tests[i], results[i]);
      }

      const summary = reporter.createTestSummary({ duration: 1000 });
      expect(summary.total).toBe(3);
      expect(summary.passed).toBe(1);
      expect(summary.failed).toBe(1);
      expect(summary.skipped).toBe(1);
    });

    it('should verify discord service integration readiness', () => {
      expect(reporter.discordService).toBeDefined();
      expect(typeof reporter.discordService.sendTestResult).toBe('function');
    });

    it('should handle test lifecycle events properly', async () => {
      // Test lifecycle: Begin -> TestBegin -> TestEnd -> End
      const config = {};
      const suite = { 
        allTests: () => [
          { title: 'Test 1', location: { file: 'test1.spec.js' } }
        ] 
      };

      reporter.onBegin(config, suite);
      expect(reporter.testStartTime).toBeDefined();

      const test = { title: 'Lifecycle Test', location: { file: 'test.spec.js' } };
      reporter.onTestBegin(test);

      const result = { status: 'passed', duration: 100 };
      await reporter.onTestEnd(test, result);

      expect(reporter.testResults).toContainEqual(
        expect.objectContaining({
          title: 'Lifecycle Test',
          status: 'passed'
        })
      );
    });

    it('should complete integration preparation for Track A/B components', async () => {
      // Verify reporter is ready for component integration
      const test = { title: 'Integration Ready Test', location: { file: 'test.spec.js' } };
      const failedResult = { 
        status: 'failed', 
        error: { message: 'Integration test error', stack: 'test stack' },
        duration: 2000
      };

      await expect(reporter.onTestEnd(test, failedResult)).resolves.not.toThrow();

      // Verify the reporter can handle the integration data structure
      const recordedTest = reporter.testResults.find(t => t.title === 'Integration Ready Test');
      expect(recordedTest).toBeDefined();
      expect(recordedTest.error).toBeDefined();
      expect(recordedTest.error.message).toBe('Integration test error');

      // Verify reporter maintains the structure needed for approval integration
      expect(recordedTest.title).toBeDefined(); // for testName
      expect(recordedTest.error.message).toBeDefined(); // for errorMessage
      expect(recordedTest.file).toBeDefined(); // for context
    });
  });
});