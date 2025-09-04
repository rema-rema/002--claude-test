/**
 * PlaywrightChannelReporter - Playwright統合マルチチャンネルレポーター
 * 
 * 機能:
 * - Playwrightテスト結果のチャンネル固有ルーティング
 * - セッション自動検出によるターゲットチャンネル決定
 * - 失敗時の包括的通知処理
 * - 既存レポーターとの後方互換性
 */

import { EventEmitter } from 'events';
import path from 'path';
import { ChannelConfigManager } from './channel-config-manager.js';
import { SessionDetector } from './session-detector.js';
import { MultiChannelNotifier } from './multi-channel-notifier.js';

export default class PlaywrightChannelReporter extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.options = {
      enableVideoAttachment: options.enableVideoAttachment !== false,
      enableScreenshotAttachment: options.enableScreenshotAttachment !== false,
      maxRetryAttempts: options.maxRetryAttempts || 3,
      notificationTimeout: options.notificationTimeout || 5000,
      ...options
    };

    // コアコンポーネント初期化
    this.channelManager = new ChannelConfigManager();
    this.sessionDetector = new SessionDetector();
    this.multiChannelNotifier = new MultiChannelNotifier({
      maxRetryAttempts: this.options.maxRetryAttempts,
      requestTimeout: this.options.notificationTimeout
    });

    // テスト結果収集用
    this.testResults = [];
    this.testStartTime = null;
    this.currentSession = null;
    this.targetChannelId = null;

    // イベントリスナー設定
    this._setupEventListeners();

    console.log('🎭 PlaywrightChannelReporter initialized:', this.options);
  }

  /**
   * Playwright テスト開始時のコールバック
   * @param {Object} config Playwright設定
   * @param {Object} suite テストスイート
   */
  async onBegin(config, suite) {
    this.testStartTime = Date.now();
    const totalTests = suite.allTests().length;
    
    console.log(`🎭 Playwright テスト開始: ${totalTests}件のテストを実行予定`);

    try {
      // セッション検出とチャンネル決定
      this.currentSession = await this.sessionDetector.detectCurrentSession();
      this.targetChannelId = this.channelManager.getChannelBySession(this.currentSession);
      
      if (this.targetChannelId) {
        console.log(`📍 Target channel determined: ${this.targetChannelId} (Session: ${this.currentSession})`);
        
        // テスト開始通知（オプション）
        if (this.options.notifyOnStart) {
          await this._sendTestStartNotification(totalTests);
        }
        
      } else {
        console.warn(`⚠️ No channel configured for session ${this.currentSession}, using fallback`);
        this.targetChannelId = this.channelManager.getDefaultChannelId();
      }

    } catch (error) {
      console.error('❌ Failed to initialize session and channel detection:', error);
      // フォールバック設定
      this.targetChannelId = this.channelManager.getDefaultChannelId();
    }

    this.emit('testingBegin', {
      session: this.currentSession,
      channelId: this.targetChannelId,
      totalTests
    });
  }

  /**
   * 個別テスト開始時のコールバック
   * @param {Object} test テストケース
   */
  onTestBegin(test) {
    console.log(`▶️ テスト開始: ${test.title}`);
    
    this.emit('testBegin', {
      testTitle: test.title,
      testFile: test.location?.file
    });
  }

  /**
   * 個別テスト終了時のコールバック
   * @param {Object} test テストケース
   * @param {Object} result テスト結果
   */
  async onTestEnd(test, result) {
    console.log(`✅ テスト終了: ${test.title || 'Unknown'} -> ${result.status || 'Unknown'}`);

    // テスト結果を収集
    const testResult = {
      title: test.title,
      status: result.status,
      duration: result.duration,
      error: result.error,
      attachments: result.attachments || [],
      location: test.location,
      project: test.parent?.project()?.name,
      file: test.location?.file,
      timestamp: new Date().toISOString()
    };

    this.testResults.push(testResult);

    // 失敗時の即座通知処理（オプション）
    if (result.status === 'failed' && this.options.notifyOnFailure) {
      await this._handleIndividualTestFailure(test, result);
    }

    this.emit('testEnd', { test: testResult, channelId: this.targetChannelId });
  }

  /**
   * 全テスト終了時のコールバック（メイン処理）
   * @param {Object} result 全体テスト結果
   */
  async onEnd(result) {
    try {
      console.log('\n🎭 Playwright Discord Reporter: テスト結果を処理中...');
      
      // テスト結果サマリー作成
      const summary = this._createTestSummary(result);
      console.log('📊 テストサマリー作成完了');
      
      // 失敗時の証跡ファイル収集
      const attachments = await this._collectFailureArtifacts(result);
      console.log(`📎 証跡ファイル収集完了: ${attachments.length}件`);
      
      // ターゲットチャンネルへの通知送信
      if (this.targetChannelId) {
        await this._sendComprehensiveTestResult(summary, attachments);
      } else {
        console.error('❌ No target channel available for notification');
      }
      
      // 統計情報出力
      this._logFinalStats();

    } catch (error) {
      console.error('❌ PlaywrightChannelReporter エラー:', error.message);
      console.error(error.stack);
      
      // エラー時のフォールバック通知
      await this._sendErrorNotification(error);
    }
  }

  /**
   * レポーターエラー時のコールバック
   * @param {Error} error エラーオブジェクト
   */
  onError(error) {
    console.error('💥 Playwright Reporter Error:', error);
    this.emit('reporterError', { error: error.message });
  }

  /**
   * テスト結果サマリー作成
   * @param {Object} result Playwright結果オブジェクト
   * @returns {Object} サマリーオブジェクト
   * @private
   */
  _createTestSummary(result) {
    console.log('🔍 createTestSummary: 収集したテスト結果を集計中...');
    console.log(`📊 収集されたテスト数: ${this.testResults.length}`);
    
    // 収集したテスト結果から集計
    let passed = 0;
    let failed = 0;
    let skipped = 0;
    let timedOut = 0;

    for (const test of this.testResults) {
      console.log(`- テスト: "${test.title}" -> ${test.status}`);
      
      switch (test.status) {
        case 'passed':
          passed++;
          break;
        case 'failed':
          failed++;
          break;
        case 'skipped':
          skipped++;
          break;
        case 'timedOut':
          timedOut++;
          break;
      }
    }

    // 実行時間計算
    const totalDuration = this.testStartTime ? (Date.now() - this.testStartTime) : (result.duration || 0);
    
    const summary = {
      session: this.currentSession,
      channelId: this.targetChannelId,
      total: this.testResults.length,
      passed,
      failed,
      skipped,
      timedOut,
      duration: totalDuration,
      timestamp: new Date().toISOString(),
      status: failed > 0 || timedOut > 0 ? 'FAILED' : 'PASSED'
    };

    console.log('📋 最終サマリー:', summary);
    return summary;
  }

  /**
   * 失敗時証跡ファイル収集
   * @param {Object} result テスト結果
   * @returns {Promise<Array>} 証跡ファイル配列
   * @private
   */
  async _collectFailureArtifacts(result) {
    const artifacts = [];
    
    // 失敗したテストの証跡を収集
    for (const testResult of this.testResults) {
      if (testResult.status === 'failed' || testResult.status === 'timedOut') {
        try {
          const testArtifacts = await this._collectTestArtifacts(testResult);
          if (testArtifacts && testArtifacts.files.length > 0) {
            artifacts.push(testArtifacts);
            console.log(`証跡ファイル収集: ${testResult.title} -> ${testArtifacts.files.length}件`);
          }
        } catch (error) {
          console.error(`証跡収集エラー (${testResult.title}):`, error.message);
        }
      }
    }

    return artifacts;
  }

  /**
   * 個別テストの証跡ファイル収集
   * @param {Object} testResult テスト結果
   * @returns {Promise<Object>} 証跡オブジェクト
   * @private
   */
  async _collectTestArtifacts(testResult) {
    const testTitle = testResult.title || 'Unknown Test';
    const artifacts = {
      testName: testTitle,
      files: [],
      metadata: {
        duration: testResult.duration,
        error: testResult.error?.message,
        timestamp: testResult.timestamp
      }
    };

    try {
      // テスト結果ディレクトリのパターンを推定
      const testResultsDir = './test-results';
      const sanitizedTestName = this._sanitizeFileName(testTitle);
      
      // 可能な証跡ファイルパスを生成
      const possiblePaths = [
        `${testResultsDir}/${sanitizedTestName}`,
        `${testResultsDir}/${sanitizedTestName}-chromium`,
        `${testResultsDir}/${sanitizedTestName}-webkit`,
        `${testResultsDir}/${sanitizedTestName}-firefox`
      ];

      for (const dirPath of possiblePaths) {
        const artifactFiles = await this._scanArtifactDirectory(dirPath);
        artifacts.files.push(...artifactFiles);
      }

      // Playwrightの添付ファイル情報も確認
      if (testResult.attachments) {
        for (const attachment of testResult.attachments) {
          if (attachment.path) {
            artifacts.files.push({
              type: attachment.name || 'attachment',
              path: attachment.path,
              contentType: attachment.contentType
            });
          }
        }
      }

    } catch (error) {
      console.error(`証跡収集エラー (${testTitle}):`, error.message);
    }

    return artifacts;
  }

  /**
   * 証跡ディレクトリスキャン
   * @param {string} dirPath ディレクトリパス
   * @returns {Promise<Array>} ファイル情報配列
   * @private
   */
  async _scanArtifactDirectory(dirPath) {
    const files = [];
    
    try {
      const fs = await import('fs/promises');
      const stats = await fs.stat(dirPath);
      
      if (stats.isDirectory()) {
        const entries = await fs.readdir(dirPath);
        
        for (const entry of entries) {
          const fullPath = path.join(dirPath, entry);
          const fileStats = await fs.stat(fullPath);
          
          if (fileStats.isFile()) {
            const fileType = this._determineFileType(entry);
            
            files.push({
              type: fileType,
              path: fullPath,
              name: entry,
              size: fileStats.size
            });
          }
        }
      }
    } catch (error) {
      // ディレクトリが存在しない場合は無視
      if (error.code !== 'ENOENT') {
        console.warn(`警告: ディレクトリスキャンエラー ${dirPath}:`, error.message);
      }
    }

    return files;
  }

  /**
   * 包括的なテスト結果通知送信
   * @param {Object} summary テストサマリー
   * @param {Array} attachments 添付ファイル配列
   * @returns {Promise<void>}
   * @private
   */
  async _sendComprehensiveTestResult(summary, attachments) {
    try {
      // 通知メッセージ構築
      const message = this._buildTestResultMessage(summary, attachments);
      
      // 添付ファイル準備
      const attachmentFiles = this._prepareAttachmentFiles(attachments);
      
      console.log(`📨 Sending test results to channel: ${this.targetChannelId}`);
      
      // マルチチャンネルノーティファイヤーで送信
      const result = await this.multiChannelNotifier.sendToChannel(
        this.targetChannelId,
        message,
        attachmentFiles
      );
      
      console.log('✅ Test result notification sent successfully');
      
      this.emit('notificationSent', {
        channelId: this.targetChannelId,
        summary,
        attachmentCount: attachmentFiles.length
      });
      
      return result;
      
    } catch (error) {
      console.error('❌ Failed to send test result notification:', error);
      this.emit('notificationFailed', { error: error.message });
      throw error;
    }
  }

  /**
   * テスト結果メッセージ構築
   * @param {Object} summary テストサマリー
   * @param {Array} attachments 添付ファイル
   * @returns {Object} メッセージオブジェクト
   * @private
   */
  _buildTestResultMessage(summary, attachments) {
    const statusEmoji = summary.status === 'PASSED' ? '✅' : '❌';
    const durationSeconds = Math.round(summary.duration / 1000);
    
    let content = `${statusEmoji} **Playwright テスト結果 - Session ${summary.session}**\n\n`;
    
    content += `📊 **テストサマリー:**\n`;
    content += `• 総数: ${summary.total}件\n`;
    content += `• ✅ 成功: ${summary.passed}件\n`;
    content += `• ❌ 失敗: ${summary.failed}件\n`;
    content += `• ⏭️ スキップ: ${summary.skipped}件\n`;
    if (summary.timedOut > 0) {
      content += `• ⏰ タイムアウト: ${summary.timedOut}件\n`;
    }
    content += `• ⏱️ 実行時間: ${durationSeconds}秒\n\n`;

    // 失敗詳細
    if (summary.failed > 0 || summary.timedOut > 0) {
      content += `🔍 **失敗テスト詳細:**\n`;
      
      const failedTests = this.testResults.filter(t => 
        t.status === 'failed' || t.status === 'timedOut'
      );
      
      for (const test of failedTests.slice(0, 5)) { // 最大5件
        content += `• ${test.title}\n`;
        if (test.error) {
          const errorMsg = test.error.message || test.error;
          const shortError = errorMsg.length > 100 ? 
            errorMsg.substring(0, 100) + '...' : errorMsg;
          content += `  エラー: ${shortError}\n`;
        }
      }
      
      if (failedTests.length > 5) {
        content += `• ... 他 ${failedTests.length - 5}件\n`;
      }
      content += `\n`;
    }

    // 添付ファイル情報
    if (attachments.length > 0) {
      content += `📎 **証跡ファイル:** ${attachments.length}件のテストで証跡を収集\n`;
      
      const totalVideoFiles = attachments.reduce((sum, a) => 
        sum + a.files.filter(f => f.type === 'video').length, 0
      );
      const totalScreenshots = attachments.reduce((sum, a) => 
        sum + a.files.filter(f => f.type === 'screenshot').length, 0
      );
      
      if (totalVideoFiles > 0) {
        content += `• 🎥 動画ファイル: ${totalVideoFiles}件\n`;
      }
      if (totalScreenshots > 0) {
        content += `• 📸 スクリーンショット: ${totalScreenshots}件\n`;
      }
    }

    content += `\n⏰ 実行時刻: ${new Date().toLocaleString('ja-JP')}`;

    return { content };
  }

  /**
   * 添付ファイル準備
   * @param {Array} attachments 証跡ファイル配列
   * @returns {Array} 送信用添付ファイル配列
   * @private
   */
  _prepareAttachmentFiles(attachments) {
    const files = [];
    
    for (const artifact of attachments) {
      for (const file of artifact.files) {
        // ファイルタイプフィルター
        if (file.type === 'video' && this.options.enableVideoAttachment) {
          files.push(file);
        } else if (file.type === 'screenshot' && this.options.enableScreenshotAttachment) {
          files.push(file);
        }
        
        // ファイルサイズ制限（8MB）
        if (file.size && file.size > 8 * 1024 * 1024) {
          console.warn(`⚠️ File too large for Discord: ${file.name} (${file.size} bytes)`);
          continue;
        }
      }
    }

    return files.slice(0, 10); // Discord制限: 最大10ファイル
  }

  /**
   * 個別テスト失敗時の即座通知
   * @param {Object} test テストケース
   * @param {Object} result テスト結果
   * @returns {Promise<void>}
   * @private
   */
  async _handleIndividualTestFailure(test, result) {
    try {
      const message = {
        content: `⚠️ **テスト失敗通知 - Session ${this.currentSession}**\n\n` +
                `📋 **テスト名:** ${test.title}\n` +
                `❌ **ステータス:** ${result.status}\n` +
                `⏱️ **実行時間:** ${Math.round(result.duration / 1000)}秒\n` +
                `🔍 **エラー:** ${result.error?.message || 'Unknown error'}\n\n` +
                `📎 詳細な証跡ファイルは全テスト完了後に送信されます。`
      };

      await this.multiChannelNotifier.sendToChannel(this.targetChannelId, message);
      
    } catch (error) {
      console.error('❌ Failed to send individual failure notification:', error);
    }
  }

  /**
   * エラー時のフォールバック通知
   * @param {Error} error エラーオブジェクト
   * @returns {Promise<void>}
   * @private
   */
  async _sendErrorNotification(error) {
    try {
      const channelId = this.targetChannelId || this.channelManager.getDefaultChannelId();
      
      if (channelId) {
        const message = {
          content: `💥 **Playwright レポーターエラー - Session ${this.currentSession}**\n\n` +
                  `❌ **エラー:** ${error.message}\n` +
                  `⏰ **発生時刻:** ${new Date().toLocaleString('ja-JP')}\n\n` +
                  `テスト結果の通知に失敗しました。ログを確認してください。`
        };

        await this.multiChannelNotifier.sendToChannel(channelId, message);
      }
    } catch (fallbackError) {
      console.error('❌ Failed to send error notification:', fallbackError);
    }
  }

  /**
   * 最終統計情報ログ出力
   * @private
   */
  _logFinalStats() {
    const notifierStats = this.multiChannelNotifier.getStats();
    const sessionStats = this.sessionDetector.getDetectionStats();
    
    console.log('\n📊 PlaywrightChannelReporter 最終統計:');
    console.log('- セッション:', this.currentSession);
    console.log('- ターゲットチャンネル:', this.targetChannelId);
    console.log('- 収集テスト数:', this.testResults.length);
    console.log('- 通知統計:', notifierStats);
    console.log('- セッション検出:', sessionStats.lastDetection);
  }

  /**
   * イベントリスナー設定
   * @private
   */
  _setupEventListeners() {
    // マルチチャンネルノーティファイヤーイベント
    this.multiChannelNotifier.on('notificationSent', (data) => {
      console.log(`📨 Notification sent to ${data.channelId}`);
    });

    this.multiChannelNotifier.on('notificationFailed', (data) => {
      console.error(`❌ Notification failed to ${data.channelId}:`, data.error);
    });

    // セッション検出イベント  
    this.sessionDetector.on('sessionDetected', (data) => {
      console.log(`🎯 Session detected: ${data.sessionId} (${data.method})`);
    });

    this.sessionDetector.on('sessionFallback', (data) => {
      console.warn(`🔧 Using fallback session: ${data.sessionId}`);
    });
  }

  /**
   * ファイル名サニタイズ
   * @param {string} name ファイル名
   * @returns {string} サニタイズ済みファイル名
   * @private
   */
  _sanitizeFileName(name) {
    return name
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .toLowerCase();
  }

  /**
   * ファイル種別判定
   * @param {string} filename ファイル名
   * @returns {string} ファイル種別
   * @private
   */
  _determineFileType(filename) {
    const ext = path.extname(filename).toLowerCase();
    
    if (ext === '.webm' || ext === '.mp4') {
      return 'video';
    } else if (ext === '.png' || ext === '.jpg' || ext === '.jpeg') {
      return 'screenshot';
    } else if (ext === '.zip' || ext === '.har') {
      return 'trace';
    } else {
      return 'other';
    }
  }
}