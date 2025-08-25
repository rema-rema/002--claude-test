// Track B統合エクスポート - Track C向け
// エラーハンドリングコンポーネント統合パッケージ

export { RetryHandler } from './RetryHandler.js';
export { ErrorClassifier } from './ErrorClassifier.js';
export { FailureCounter } from './FailureCounter.js';
export { ApprovalRequestManager } from './ApprovalRequestManager.js';
export { ThreadManager } from './ThreadManager.js';

// Track C向け統合設定
export const createErrorHandlingStack = () => ({
  retryHandler: new RetryHandler({
    maxRetries: 3,
    baseDelay: 1000,
    backoffMultiplier: 2
  }),
  errorClassifier: new ErrorClassifier(),
  failureCounter: new FailureCounter()
});

// Quick setup for common use cases
export const createPlaywrightIntegration = () => ({
  ...createErrorHandlingStack(),
  approvalManager: new ApprovalRequestManager(),
  threadManager: new ThreadManager()
});

// Advanced configuration for custom setups
export const createCustomIntegration = (config = {}) => {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    backoffMultiplier = 2,
    failureLimit = 10
  } = config;

  return {
    retryHandler: new RetryHandler({
      maxRetries,
      baseDelay,
      backoffMultiplier
    }),
    errorClassifier: new ErrorClassifier(),
    failureCounter: new FailureCounter({ limit: failureLimit }),
    approvalManager: new ApprovalRequestManager(),
    threadManager: new ThreadManager()
  };
};