import { DiscordNotificationService } from '../services/discord-notification-service.js';
import path from 'path';
import fs from 'fs/promises';

export default class PlaywrightDiscordReporter {
  constructor(options = {}) {
    this.discordService = new DiscordNotificationService();
    this.options = options;
    
    // テスト結果を収集するための配列
    this.testResults = [];
    this.testStartTime = null;
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

  onTestEnd(test, result) {
    // 個別テスト終了時に結果を収集
    console.log(`✅ テスト終了: ${test.title} -> ${result.status}`);
    
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
  }

  onError(error) {
    console.error('Playwright Reporter Error:', error);
  }
}