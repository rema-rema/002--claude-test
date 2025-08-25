# Track C向け統合サンプル集

## TASK-302 エラーハンドリング強化コンポーネント統合ガイド

### 🎯 概要

Track Bで開発されたエラーハンドリング強化コンポーネント群をTrack Cで活用するためのサンプルコード集です。

### 📦 利用可能コンポーネント

```javascript
import {
  RetryHandler,
  ErrorClassifier,
  FailureCounter,
  createErrorHandlingStack,
  createPlaywrightIntegration,
  createCustomIntegration
} from '../discord-bot/src/components/index.js';
```

### 🚀 クイックスタート

#### 1. 基本的なエラーハンドリング

```javascript
import { createErrorHandlingStack } from '../discord-bot/src/components/index.js';

// エラーハンドリングスタックを作成
const { retryHandler, errorClassifier, failureCounter } = createErrorHandlingStack();

// Discord API呼び出しを再試行付きで実行
async function sendNotificationWithRetry(message) {
  try {
    await retryHandler.retry(async () => {
      // Discord API呼び出し
      return await discordClient.send(message);
    });
  } catch (error) {
    // 再試行失敗後のフォールバック処理
    const classification = errorClassifier.classify(error);
    console.error(`通知送信失敗 [${classification.category}]:`, error.message);
  }
}
```

#### 2. Playwright統合

```javascript
import { createPlaywrightIntegration } from '../discord-bot/src/components/index.js';

// Playwright用統合セットを作成
const integration = createPlaywrightIntegration();

// テスト失敗時の処理
async function handleTestFailure(test, result) {
  const errorPattern = result.error?.message || 'Unknown error';
  
  // 失敗回数をカウント
  const failureCount = integration.failureCounter.increment(test.title, errorPattern);
  
  // 制限到達チェック
  if (integration.failureCounter.hasReachedLimit(test.title, errorPattern)) {
    console.log(`⚠️  制限到達: ${test.title} (${failureCount}/10)`);
    // 人間の判断を要求
    await requestHumanApproval(test, result);
    return;
  }

  // Discord通知を再試行付きで送信
  await integration.retryHandler.retry(async () => {
    await sendDiscordNotification(test, result);
  });
}
```

#### 3. カスタム設定

```javascript
import { createCustomIntegration } from '../discord-bot/src/components/index.js';

// カスタム設定でエラーハンドリングを作成
const customIntegration = createCustomIntegration({
  maxRetries: 5,           // 最大5回再試行
  baseDelay: 2000,         // 初回遅延2秒
  backoffMultiplier: 1.5,  // 1.5倍バックオフ
  failureLimit: 15         // 失敗制限15回
});

// E2Eテストでの使用例
class CustomPlaywrightReporter {
  constructor() {
    this.integration = customIntegration;
  }

  async onTestEnd(test, result) {
    if (result.status === 'failed') {
      await this.handleFailure(test, result);
    } else if (result.status === 'passed') {
      // 成功時は失敗カウンタをリセット
      this.integration.failureCounter.reset(test.title);
    }
  }

  async handleFailure(test, result) {
    const { retryHandler, errorClassifier, failureCounter } = this.integration;
    
    try {
      await retryHandler.retry(async () => {
        // 承認依頼処理
        await this.processApprovalRequest(test, result);
      });
    } catch (error) {
      // 分類してログ出力
      const classification = errorClassifier.classify(error);
      console.error(`処理失敗 [${classification.category}]:`, error.message);
    }
  }
}
```

### 🔧 個別コンポーネント使用例

#### RetryHandler - 再試行制御

```javascript
import { RetryHandler } from '../discord-bot/src/components/index.js';

const retryHandler = new RetryHandler({
  maxRetries: 3,
  baseDelay: 1000,
  backoffMultiplier: 2
});

// 非同期操作の再試行
async function reliableOperation() {
  return await retryHandler.retry(async () => {
    // 失敗する可能性のある処理
    const result = await fetchDataFromAPI();
    if (!result) {
      throw new Error('Data fetch failed');
    }
    return result;
  });
}
```

#### ErrorClassifier - エラー分類

```javascript
import { ErrorClassifier } from '../discord-bot/src/components/index.js';

const classifier = new ErrorClassifier();

function handleError(error) {
  const classification = classifier.classify(error);
  
  console.log(`エラー分類: ${classification.category}`);
  console.log(`重要度: ${classification.severity}`);
  console.log(`再試行可能: ${classification.retryable ? 'Yes' : 'No'}`);
  
  // 分類に基づく処理
  switch (classification.category) {
    case 'RATE_LIMIT':
      console.log('レート制限 - 待機後再試行');
      break;
    case 'AUTHENTICATION':
      console.log('認証エラー - トークン更新が必要');
      break;
    case 'NETWORK':
      console.log('ネットワークエラー - 接続確認');
      break;
    default:
      console.log('その他のエラー');
  }
}
```

#### FailureCounter - 失敗回数管理

```javascript
import { FailureCounter } from '../discord-bot/src/components/index.js';

const counter = new FailureCounter();

function trackTestFailures(testName, errorPattern) {
  // 失敗回数を増加
  const count = counter.increment(testName, errorPattern);
  
  console.log(`${testName}: ${count}回目の失敗`);
  
  // 制限チェック
  if (counter.hasReachedLimit(testName, errorPattern)) {
    console.log(`⚠️  制限到達: ${testName}`);
    // エスカレーション処理
    escalateToHuman(testName, errorPattern, count);
  }
}

function handleTestSuccess(testName) {
  // 成功時はリセット
  counter.reset(testName);
  console.log(`✅ ${testName}: 失敗カウンタをリセット`);
}
```

### 💡 ベストプラクティス

#### 1. コンポーネント初期化

```javascript
// アプリケーション起動時に一度だけ初期化
const errorHandling = createErrorHandlingStack();

// グローバルに利用可能にする
global.errorHandling = errorHandling;

// または依存性注入パターン
class ServiceManager {
  constructor() {
    this.errorHandling = createErrorHandlingStack();
  }
  
  getRetryHandler() {
    return this.errorHandling.retryHandler;
  }
}
```

#### 2. エラーログの構造化

```javascript
async function structuredErrorHandling(operation, context = {}) {
  const { retryHandler, errorClassifier } = global.errorHandling;
  
  try {
    return await retryHandler.retry(operation);
  } catch (error) {
    const classification = errorClassifier.classify(error);
    
    // 構造化ログ出力
    console.error('Operation failed:', {
      operation: operation.name,
      context: context,
      error: {
        message: error.message,
        category: classification.category,
        severity: classification.severity,
        retryable: classification.retryable
      },
      timestamp: new Date().toISOString()
    });
    
    throw error;
  }
}
```

#### 3. 設定の外部化

```javascript
// config.js
export const errorHandlingConfig = {
  retry: {
    maxRetries: process.env.MAX_RETRIES || 3,
    baseDelay: parseInt(process.env.BASE_DELAY) || 1000,
    backoffMultiplier: parseFloat(process.env.BACKOFF_MULTIPLIER) || 2
  },
  failure: {
    limit: parseInt(process.env.FAILURE_LIMIT) || 10
  }
};

// main.js
import { createCustomIntegration } from '../discord-bot/src/components/index.js';
import { errorHandlingConfig } from './config.js';

const integration = createCustomIntegration({
  maxRetries: errorHandlingConfig.retry.maxRetries,
  baseDelay: errorHandlingConfig.retry.baseDelay,
  backoffMultiplier: errorHandlingConfig.retry.backoffMultiplier,
  failureLimit: errorHandlingConfig.failure.limit
});
```

### 🧪 テスト統合例

#### Jest テスト

```javascript
import { createErrorHandlingStack } from '../discord-bot/src/components/index.js';

describe('Error Handling Integration', () => {
  let errorHandling;
  
  beforeEach(() => {
    errorHandling = createErrorHandlingStack();
  });
  
  test('should retry failed operations', async () => {
    const mockOperation = jest.fn()
      .mockRejectedValueOnce(new Error('First failure'))
      .mockRejectedValueOnce(new Error('Second failure'))
      .mockResolvedValueOnce('Success');
    
    const result = await errorHandling.retryHandler.retry(mockOperation);
    
    expect(result).toBe('Success');
    expect(mockOperation).toHaveBeenCalledTimes(3);
  });
});
```

### 📚 関連ドキュメント

- [RetryHandler API仕様](../../../components/RetryHandler.js)
- [ErrorClassifier API仕様](../../../components/ErrorClassifier.js)
- [FailureCounter API仕様](../../../components/FailureCounter.js)
- [Track B実装完了レポート](./export-interface.md)

### 🔗 次のステップ

1. Track Cプロジェクトに統合コンポーネントをインストール
2. 既存のエラーハンドリングを段階的に置換
3. パフォーマンスメトリクスの監視実装
4. 本番環境でのA/Bテスト実施