import { DiscordNotificationService } from '../services/discord-notification-service.js';
import { TestFailureAnalyzer } from '../components/TestFailureAnalyzer.js';
import { ErrorPatternMatcher } from '../components/ErrorPatternMatcher.js';
import { FixSuggestionGenerator } from '../components/FixSuggestionGenerator.js';
import { ApprovalRequestManager } from '../components/ApprovalRequestManager.js';
import { RetryHandler } from '../components/RetryHandler.js';
import { ErrorClassifier } from '../components/ErrorClassifier.js';
import { FailureCounter } from '../components/FailureCounter.js';
import path from 'path';
import fs from 'fs/promises';

/**
 * Playwright Discord Reporter with Approval Integration
 * Track A/B統合: テスト失敗時の自動承認依頼フロー
 */
export default class PlaywrightDiscordReporter {
  constructor(options = {}) {
    this.discordService = new DiscordNotificationService();
    this.options = options;
    
    // テスト結果を収集するための配列
    this.testResults = [];
    this.testStartTime = null;
    
    // Track B基盤コンポーネント統合
    this.errorMatcher = new ErrorPatternMatcher();
    this.suggestionGenerator = new FixSuggestionGenerator();
    this.failureAnalyzer = new TestFailureAnalyzer(
      this.errorMatcher,
      this.suggestionGenerator
    );
    
    // Track A統合コンポーネント
    this.approvalManager = new ApprovalRequestManager();
    
    // TASK-302: エラーハンドリング強化コンポーネント
    this.retryHandler = new RetryHandler();
    this.errorClassifier = new ErrorClassifier();
    this.failureCounter = new FailureCounter();
  }

  async onEnd(result) {
    try {
      console.log('\n🎭 Playwright Discord Reporter: テスト結果を処理中...');
      
      // テスト結果サマリー作成
      const summary = this.createTestSummary(result);
      console.log('📊 テストサマリー作成完了');
      
      // 失敗時の証跡ファイル収集
      const attachments = await this.collectFailureArtifacts(result);
      console.log(`📎 証跡ファイル収集完了: ${attachments.length}件`);
      
      // Discord通知送信
      await this.discordService.sendTestResult(summary, attachments);
      
    } catch (error) {
      console.error('❌ PlaywrightDiscordReporter エラー:', error.message);
      console.error(error.stack);
      
      // エラー時も基本的な情報をログ出力
      console.log('📋 基本テスト情報:');
      console.log(`- 総テスト数: ${result.allTests?.length || 0}`);
      console.log(`- 実行時間: ${Math.round((result.duration || 0) / 1000)}秒`);
    }
  }

  createTestSummary(result) {
    console.log('🔍 createTestSummary: 収集したテスト結果を集計中...');
    console.log(`📊 収集されたテスト数: ${this.testResults.length}`);
    
    // 収集したテスト結果から集計
    let passed = 0;
    let failed = 0;
    let skipped = 0;
    
    for (const test of this.testResults) {
      console.log(`- テスト: "${test.title}" -> ${test.status}`);
      
      if (test.status === 'passed') {
        passed++;
      } else if (test.status === 'failed') {
        failed++;
      } else if (test.status === 'skipped') {
        skipped++;
      }
    }
    
    // 実行時間計算
    const totalDuration = this.testStartTime ? (Date.now() - this.testStartTime) : (result.duration || 0);
    
    const summary = {
      total: this.testResults.length,
      passed: passed,
      failed: failed,
      skipped: skipped,
      duration: totalDuration,
      timestamp: new Date().toISOString(),
      status: failed > 0 ? 'FAILED' : 'PASSED'
    };
    
    console.log('📋 最終サマリー:', summary);
    return summary;
  }

  extractTestsFromSuites(suites) {
    let tests = [];
    
    for (const suite of suites) {
      // 直接のテストがあれば追加
      if (suite.tests) {
        tests.push(...suite.tests);
      }
      
      // ネストされたsuiteがあれば再帰処理
      if (suite.suites && suite.suites.length > 0) {
        tests.push(...this.extractTestsFromSuites(suite.suites));
      }
    }
    
    return tests;
  }

  async collectFailureArtifacts(result) {
    const artifacts = [];
    
    // 収集したテスト結果から失敗したテストを処理
    for (const test of this.testResults) {
      // 失敗したテストのみ処理
      if (test.status === 'failed') {
        try {
          const testArtifacts = await this.collectTestArtifacts(test);
          if (testArtifacts) {
            artifacts.push(testArtifacts);
          }
        } catch (error) {
          console.error(`証跡収集エラー (${test.title}):`, error.message);
        }
      }
    }
    
    return artifacts;
  }

  async collectTestArtifacts(test) {
    const testTitle = test.title || 'Unknown Test';
    
    // テスト結果ディレクトリのパターンを推定
    const testResultsDir = './test-results';
    const testDirPattern = this.sanitizeFileName(testTitle);
    
    const artifacts = {
      testName: testTitle,
      testFile: test.file,
      testProject: test.project,
      error: test.error,
      screenshot: null,
      video: null,
      trace: null
    };

    try {
      // test-resultsディレクトリを探索
      const testResultsDirExists = await this.directoryExists(testResultsDir);
      if (!testResultsDirExists) {
        console.log(`テスト結果ディレクトリが見つかりません: ${testResultsDir}`);
        return artifacts;
      }

      const testDirs = await fs.readdir(testResultsDir, { withFileTypes: true });
      
      // テスト名に関連するディレクトリを検索
      const matchingDirs = testDirs.filter(dir => 
        dir.isDirectory() && 
        dir.name.includes(testDirPattern)
      );

      if (matchingDirs.length === 0) {
        console.log(`テスト ${testTitle} の結果ディレクトリが見つかりません`);
        return artifacts;
      }

      // 最初にマッチしたディレクトリを使用（最新のものを想定）
      const targetDir = path.join(testResultsDir, matchingDirs[0].name);
      const files = await fs.readdir(targetDir);

      // ファイル種別ごとに検索
      for (const file of files) {
        const filePath = path.join(targetDir, file);
        const ext = path.extname(file).toLowerCase();

        if (ext === '.png' || ext === '.jpg' || ext === '.jpeg') {
          artifacts.screenshot = filePath;
        } else if (ext === '.webm' || ext === '.mp4') {
          artifacts.video = filePath;
        } else if (ext === '.zip' && file.includes('trace')) {
          artifacts.trace = filePath;
        }
      }

      console.log(`証跡ファイル収集: ${testTitle} -> ${Object.values(artifacts).filter(v => v).length}件`);
      
    } catch (error) {
      console.error(`証跡収集エラー (${testTitle}):`, error.message);
    }

    return artifacts;
  }

  sanitizeFileName(name) {
    // ファイル名として使用できない文字を除去・置換
    return name
      .replace(/[^\w\s-]/g, '') // 英数字、空白、ハイフン以外を除去
      .replace(/\s+/g, '-')     // 空白をハイフンに置換
      .toLowerCase();
  }

  async directoryExists(dirPath) {
    try {
      const stats = await fs.stat(dirPath);
      return stats.isDirectory();
    } catch (error) {
      return false;
    }
  }

  // Playwrightレポーターインターフェース用メソッド
  onBegin(config, suite) {
    this.testStartTime = Date.now();
    console.log(`🎭 Playwright テスト開始: ${suite.allTests().length}件のテストを実行予定`);
  }

  onTestBegin(test) {
    // 個別テスト開始時の処理
    console.log(`▶️ テスト開始: ${test.title}`);
  }

  async onTestEnd(test, result) {
    // 入力検証
    if (!test || !result) {
      return;
    }
    
    // 個別テスト終了時に結果を収集
    console.log(`✅ テスト終了: ${test.title || 'Unknown'} -> ${result.status || 'Unknown'}`);
    
    // テスト結果記録
    this.testResults.push({
      title: test.title,
      status: result.status,
      duration: result.duration,
      error: result.error,
      attachments: result.attachments || [],
      // テストの詳細情報を追加
      location: test.location,
      project: test.parent?.project()?.name,
      file: test.location?.file
    });
    
    // TASK-302: 成功時の失敗カウンターリセット
    if (result.status === 'passed') {
      this.failureCounter.reset(test.title);
    }
    
    // 失敗時の自動承認依頼フロー
    if (result.status === 'failed') {
      await this.processFailureApprovalWithRetry(test, result);
    }
  }
  
  /**
   * テスト失敗時の承認依頼処理
   * Track A/B統合の核心機能
   */
  async processFailureApproval(test, result) {
    try {
      console.log(`🔍 承認依頼フロー開始: ${test.title}`);
      
      // 1. 失敗分析実行 (Track B基盤)
      const analysis = await this.failureAnalyzer.analyzeFailure({
        testName: test.title,
        error: result.error?.message || 'Unknown error',
        stackTrace: result.error?.stack,
        filePath: test.location?.file,
        duration: result.duration
      });
      
      console.log(`📊 分析完了: カテゴリ=${analysis.errorPattern?.category}, 信頼度=${analysis.confidenceLevel}`);
      
      // 2. 承認依頼作成 (Track A統合)
      const suggestions = this.extractSuggestions(analysis.fixSuggestions);
      const approvalRequest = await this.approvalManager.createRequest(
        test.title,
        result.error?.message || 'Test failed',
        suggestions,
        'playwright-reporter'
      );
      
      console.log(`📝 承認依頼作成: ID=${approvalRequest.id}`);
      
      // 3. Discord承認依頼通知送信
      const discordMessage = await this.sendApprovalNotification({
        testName: test.title,
        error: result.error?.message,
        analysis: analysis,
        approvalRequest: approvalRequest,
        timestamp: new Date().toISOString()
      });
      
      // 4. Discord情報を承認依頼に関連付け
      if (discordMessage?.threadId && discordMessage?.messageId) {
        await this.approvalManager.updateDiscordInfo(
          approvalRequest.id,
          discordMessage.threadId,
          discordMessage.messageId
        );
        console.log(`🔗 Discord情報関連付け完了: thread=${discordMessage.threadId}`);
      }
      
    } catch (error) {
      console.error(`❌ 承認依頼処理エラー (${test.title}):`, error.message);
      await this.fallbackToNormalNotification(test, result);
    }
  }

  onError(error) {
    console.error('Playwright Reporter Error:', error);
  }
  
  /**
   * 修正提案を文字列配列として抽出
   * @param {Array} fixSuggestions - 修正提案配列
   * @returns {string[]} 文字列配列
   */
  extractSuggestions(fixSuggestions) {
    if (!Array.isArray(fixSuggestions)) {
      return [];
    }
    return fixSuggestions.map(s => s.text || s);
  }

  /**
   * Discord承認依頼通知を送信
   * @param {Object} data - 通知データ
   * @returns {Promise<Object>} Discord応答情報
   */
  async sendApprovalNotification(data) {
    if (typeof this.discordService.sendTestFailureWithApproval === 'function') {
      return await this.discordService.sendTestFailureWithApproval(data);
    } else {
      // Track A未実装時の暫定対応
      return await this.mockSendTestFailureWithApproval(data);
    }
  }

  /**
   * 通常のDiscord通知へのフォールバック処理
   * @param {Object} test - テストオブジェクト
   * @param {Object} result - テスト結果
   */
  async fallbackToNormalNotification(test, result) {
    try {
      await this.discordService.sendTestResult({
        testName: test.title,
        error: result.error?.message,
        status: 'FAILED'
      }, []);
    } catch (fallbackError) {
      console.error('❌ フォールバック通知も失敗:', fallbackError.message);
    }
  }

  /**
   * TASK-302: 再試行機能付き承認依頼処理
   * @param {Object} test - テストオブジェクト
   * @param {Object} result - テスト結果
   */
  async processFailureApprovalWithRetry(test, result) {
    try {
      // 失敗回数をカウント
      const errorMessage = result.error?.message || 'Unknown error';
      const failureCount = this.failureCounter.increment(test.title, errorMessage);

      // 10回制限チェック
      if (this.failureCounter.hasReachedLimit(test.title, errorMessage)) {
        console.warn(`🚨 失敗制限到達: ${test.title} - ${failureCount}回失敗`);
        await this.requestHumanJudgment(test, result, failureCount);
        return;
      }

      // 再試行機能付きで承認依頼処理を実行
      await this.retryHandler.retry(async () => {
        await this.processFailureApproval(test, result);
      });

    } catch (error) {
      // エラー分類
      const classification = this.errorClassifier.classify(error);
      console.error(`❌ 承認依頼処理失敗 [${classification.category}:${classification.severity}]:`, error.message);

      // 最終フォールバック
      await this.fallbackToNormalNotification(test, result);
    }
  }

  /**
   * TASK-302: 人間判断への移行
   * @param {Object} test - テストオブジェクト  
   * @param {Object} result - テスト結果
   * @param {number} failureCount - 失敗回数
   */
  async requestHumanJudgment(test, result, failureCount) {
    try {
      console.log(`👥 人間判断依頼: ${test.title} (${failureCount}回失敗)`);

      const humanJudgmentData = {
        testName: test.title,
        error: result.error?.message,
        failureCount: failureCount,
        status: 'HUMAN_JUDGMENT_REQUIRED',
        timestamp: new Date().toISOString(),
        reason: `同一エラーで${failureCount}回連続失敗のため、人間による判断が必要です`,
        recommendations: [
          'テストコードの根本的な見直しを検討',
          'テスト環境・データの確認',
          'プロダクトコードの不具合調査',
          '自動修正の適用範囲外として人間対応を検討'
        ]
      };

      // 人間判断依頼の特別通知
      await this.discordService.sendTestResult(humanJudgmentData, []);

      // 失敗カウンターをリセット（人間判断に移行したため）
      this.failureCounter.reset(test.title, result.error?.message);

    } catch (error) {
      console.error('❌ 人間判断依頼送信失敗:', error.message);
    }
  }

  /**
   * sendTestFailureWithApproval のモック実装
   * 実際のDiscordNotificationServiceに実装されるまでの暫定対応
   */
  async mockSendTestFailureWithApproval(data) {
    // 再試行機能付きでDiscord通知を送信
    return await this.retryHandler.retry(async () => {
      // 既存のsendTestResultを使用してフォールバック
      const summary = {
        testName: data.testName,
        error: data.error,
        status: 'FAILED',
        analysis: data.analysis,
        approval: data.approvalRequest
      };
      
      await this.discordService.sendTestResult(summary, []);
      
      // モック戻り値
      return {
        threadId: `thread-${Date.now()}`,
        messageId: `msg-${Date.now()}`
      };
    });
  }
}