# Playwright Discord通知システム - 設計書

## 1. システム アーキテクチャ

### 1.1 コンポーネント構成
```
Playwright Test Runner
        ↓
Custom Reporter (PlaywrightDiscordReporter)
        ↓
Discord Notification Service
        ↓
Existing Discord Bot (DiscordBot class)
        ↓
Discord Channel
```

### 1.2 ファイル構成
```
src/
├── reporters/
│   └── playwright-discord-reporter.js    # Playwrightカスタムレポーター
├── services/
│   └── discord-notification-service.js   # Discord通知サービス
└── utils/
    └── capacity-monitor.js               # 容量監視バッチ

test-results/                             # テスト結果格納
├── [test-name]-[browser]/
│   ├── screenshot.png
│   ├── video.webm
│   └── trace.zip

playwright.config.js                     # レポーター設定追加
```

## 2. 詳細設計

### 2.1 PlaywrightDiscordReporter クラス
**責務**: Playwrightテスト完了時のフック処理

```javascript
class PlaywrightDiscordReporter {
  constructor(options = {}) {
    this.discordService = new DiscordNotificationService();
  }

  async onEnd(result) {
    // テスト結果サマリー作成
    const summary = this.createTestSummary(result);
    
    // 失敗時の証跡ファイル収集
    const attachments = await this.collectFailureArtifacts(result);
    
    // Discord通知送信
    await this.discordService.sendTestResult(summary, attachments);
  }

  createTestSummary(result) {
    return {
      total: result.allTests.length,
      passed: result.allTests.filter(t => t.outcome() === 'passed').length,
      failed: result.allTests.filter(t => t.outcome() === 'failed').length,
      duration: result.duration,
      timestamp: new Date().toISOString()
    };
  }

  async collectFailureArtifacts(result) {
    // 失敗したテストのSS・動画を収集
    const failures = result.allTests.filter(t => t.outcome() === 'failed');
    return failures.map(test => ({
      testName: test.title,
      screenshot: this.findScreenshot(test),
      video: this.findVideo(test),
      trace: this.findTrace(test)
    }));
  }
}
```

### 2.2 DiscordNotificationService クラス
**責務**: Discord通知のフォーマット・送信

```javascript
class DiscordNotificationService {
  constructor() {
    this.discordBot = null; // 既存のDiscordBotインスタンス
  }

  async initialize() {
    // 既存DiscordBotクラスのインポート・インスタンス化
    const { DiscordBot } = await import('../discord-bot/src/discord-bot.js');
    this.discordBot = new DiscordBot();
    
    // 既存の設定・認証情報を使用
    if (!this.discordBot.client.readyAt) {
      await this.discordBot.start();
    }
  }

  async sendTestResult(summary, attachments) {
    await this.initialize();

    // 基本通知メッセージ作成
    const message = this.formatSummaryMessage(summary);
    await this.discordBot.sendMessage(message);

    // 失敗時の詳細情報送信
    if (summary.failed > 0) {
      await this.sendFailureDetails(attachments);
    }
  }

  formatSummaryMessage(summary) {
    const status = summary.failed > 0 ? '❌ FAILED' : '✅ PASSED';
    return `
🎭 **Playwright テスト結果** ${status}

📊 **結果サマリー**
• 総テスト数: ${summary.total}
• 成功: ${summary.passed} ✅
• 失敗: ${summary.failed} ❌
• 実行時間: ${Math.round(summary.duration / 1000)}秒

🕒 実行時刻: ${new Date(summary.timestamp).toLocaleString('ja-JP')}
    `.trim();
  }

  async sendFailureDetails(attachments) {
    for (const attachment of attachments) {
      // スクリーンショット添付（25MB制限チェック）
      if (attachment.screenshot && this.isValidFileSize(attachment.screenshot)) {
        await this.discordBot.sendFile(attachment.screenshot, 
          `🖼️ ${attachment.testName} - スクリーンショット`);
      }

      // 動画ファイル情報（サイズが大きい場合はパス表示のみ）
      if (attachment.video) {
        const videoSize = await this.getFileSize(attachment.video);
        if (videoSize < 25 * 1024 * 1024) { // 25MB未満
          await this.discordBot.sendFile(attachment.video, 
            `🎬 ${attachment.testName} - 実行動画`);
        } else {
          await this.discordBot.sendMessage(
            `📹 ${attachment.testName} - 動画ファイル (${Math.round(videoSize/1024/1024)}MB)\n` +
            `パス: \`${attachment.video}\``
          );
        }
      }
    }
  }
}
```

### 2.3 CapacityMonitor クラス
**責務**: テスト結果フォルダの容量監視

```javascript
class CapacityMonitor {
  constructor(targetDir = './test-results') {
    this.targetDir = targetDir;
    this.thresholdGB = 1; // 1GB閾値
  }

  async checkCapacity() {
    const stats = await this.analyzeDirectory();
    
    return {
      currentSize: stats.totalSize,
      currentSizeFormatted: this.formatBytes(stats.totalSize),
      isOverThreshold: stats.totalSize > this.thresholdGB * 1024 * 1024 * 1024,
      fileCount: stats.fileCount,
      oldestFiles: stats.filesByAge.slice(-10), // 古い順で10ファイル
      largestFiles: stats.filesBySize.slice(0, 10) // 大きい順で10ファイル
    };
  }

  async analyzeDirectory() {
    const files = await this.getAllFiles(this.targetDir);
    const fileStats = await Promise.all(
      files.map(async (file) => {
        const stat = await fs.stat(file);
        return {
          path: file,
          size: stat.size,
          createdAt: stat.birthtime,
          modifiedAt: stat.mtime
        };
      })
    );

    return {
      totalSize: fileStats.reduce((sum, file) => sum + file.size, 0),
      fileCount: fileStats.length,
      filesByAge: fileStats.sort((a, b) => a.createdAt - b.createdAt),
      filesBySize: fileStats.sort((a, b) => b.size - a.size)
    };
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // CLI実行用
  async runCLI() {
    console.log('🔍 テスト結果フォルダ容量チェック中...\n');
    
    const result = await this.checkCapacity();
    
    console.log(`📁 対象ディレクトリ: ${this.targetDir}`);
    console.log(`📊 現在の使用量: ${result.currentSizeFormatted} (${result.fileCount}ファイル)`);
    console.log(`⚠️  閾値: ${this.thresholdGB}GB\n`);
    
    if (result.isOverThreshold) {
      console.log('🚨 容量が閾値を超えています！\n');
      console.log('💡 削除推奨ファイル（古い順）:');
      result.oldestFiles.forEach((file, i) => {
        console.log(`  ${i+1}. ${file.path} (${this.formatBytes(file.size)}) - ${file.createdAt.toLocaleDateString()}`);
      });
    } else {
      console.log('✅ 容量は正常範囲内です');
    }
  }
}
```

## 3. 設定・統合

### 3.1 playwright.config.js 修正
```javascript
// 既存設定に追加
export default defineConfig({
  // ... 既存設定
  reporter: [
    ['html'],
    ['./src/reporters/playwright-discord-reporter.js']
  ],
  // ... 既存設定
});
```

### 3.2 package.json スクリプト追加
```json
{
  "scripts": {
    "capacity-check": "node src/utils/capacity-monitor.js"
  }
}
```

## 4. エラーハンドリング

### 4.1 Discord通知失敗時
- 既存Playwrightテストの実行は継続
- エラーログをコンソールに出力
- 再試行は実装しない（シンプル設計）

### 4.2 ファイルアクセス失敗時
- 該当ファイルをスキップ
- 他のファイルの処理は継続
- 失敗したファイル名をログ出力

## 5. テスト戦略

### 5.1 単体テスト（境界値中心）

#### DiscordNotificationService
```javascript
describe('formatSummaryMessage', () => {
  // 境界値：テスト数0件
  it('テスト0件の場合のフォーマット', () => {
    const summary = { total: 0, passed: 0, failed: 0, duration: 0 };
    const result = service.formatSummaryMessage(summary);
    expect(result).toContain('総テスト数: 0');
  });

  // 境界値：全失敗
  it('全テスト失敗の場合のステータス', () => {
    const summary = { total: 3, passed: 0, failed: 3, duration: 5000 };
    const result = service.formatSummaryMessage(summary);
    expect(result).toContain('❌ FAILED');
    expect(result).toContain('失敗: 3');
  });

  // 境界値：実行時間の境界（1秒未満）
  it('1秒未満の実行時間の表示', () => {
    const summary = { total: 1, passed: 1, failed: 0, duration: 500 };
    const result = service.formatSummaryMessage(summary);
    expect(result).toContain('実行時間: 1秒'); // Math.roundで1になる
  });
});

describe('isValidFileSize', () => {
  // 境界値：25MB制限
  it('25MB未満のファイルは有効', () => {
    const result = service.isValidFileSize('/path/to/file', 25 * 1024 * 1024 - 1);
    expect(result).toBe(true);
  });

  it('25MB以上のファイルは無効', () => {
    const result = service.isValidFileSize('/path/to/file', 25 * 1024 * 1024);
    expect(result).toBe(false);
  });
});
```

#### CapacityMonitor
```javascript
describe('formatBytes', () => {
  // 境界値：0バイト
  it('0バイトの表示', () => {
    expect(monitor.formatBytes(0)).toBe('0 Bytes');
  });

  // 境界値：単位変換境界
  it('1024バイト = 1KB', () => {
    expect(monitor.formatBytes(1024)).toBe('1 KB');
  });

  // 境界値：1GB閾値
  it('1GB閾値判定', () => {
    const result = monitor.checkThreshold(1024 * 1024 * 1024);
    expect(result.isOverThreshold).toBe(false);
  });

  it('1GB超過判定', () => {
    const result = monitor.checkThreshold(1024 * 1024 * 1024 + 1);
    expect(result.isOverThreshold).toBe(true);
  });
});
```

### 5.2 結合テスト（ユーザ体験シナリオ）

#### シナリオ1：成功時の完全フロー
```javascript
describe('テスト成功時のユーザ体験', () => {
  it('全テスト成功 → Discord通知確認', async () => {
    // Given: 成功するテストケース
    await writeTestFile('example-success.spec.js', successTestCode);
    
    // When: Playwrightテスト実行
    const result = await exec('npx playwright test example-success.spec.js');
    
    // Then: Discord通知が送信される
    const discordMessages = await getDiscordMessages();
    expect(discordMessages).toHaveLength(1);
    expect(discordMessages[0]).toContain('✅ PASSED');
    expect(discordMessages[0]).toContain('成功: 3');
    expect(discordMessages[0]).toContain('失敗: 0');
    
    // And: 添付ファイルがない（成功時）
    expect(discordMessages[0].attachments).toHaveLength(0);
  });
});
```

#### シナリオ2：失敗時の完全フロー + ファイル添付
```javascript
describe('テスト失敗時のユーザ体験', () => {
  it('テスト失敗 → Discord通知 → スクリーンショット・動画確認', async () => {
    // Given: 失敗するテストケース
    await writeTestFile('example-failure.spec.js', failureTestCode);
    
    // When: Playwrightテスト実行
    await exec('npx playwright test example-failure.spec.js');
    
    // Then: 基本通知が送信される
    const messages = await getDiscordMessages();
    expect(messages[0]).toContain('❌ FAILED');
    expect(messages[0]).toContain('失敗: 1');
    
    // And: スクリーンショットが添付される
    expect(messages).toHaveLength(2); // 基本通知 + SS添付
    expect(messages[1]).toContain('🖼️');
    expect(messages[1].attachments[0].name).toContain('.png');
    
    // And: 動画ファイル情報が送信される
    expect(messages).toHaveLength(3); // 基本通知 + SS + 動画
    expect(messages[2]).toContain('🎬');
    expect(messages[2]).toContain('実行動画');
  });
});
```

#### シナリオ3：大容量ファイル処理
```javascript
describe('大容量ファイル時のユーザ体験', () => {
  it('25MB超過動画 → パス表示のみ', async () => {
    // Given: 大容量動画を生成するテスト
    await writeTestFile('long-test.spec.js', longRunningTestCode);
    
    // When: 長時間テスト実行（大容量動画生成）
    await exec('npx playwright test long-test.spec.js');
    
    // Then: 動画は添付されず、パス表示のみ
    const messages = await getDiscordMessages();
    const videoMessage = messages.find(m => m.content.includes('📹'));
    
    expect(videoMessage.content).toContain('動画ファイル');
    expect(videoMessage.content).toContain('MB'); // サイズ表示
    expect(videoMessage.content).toContain('パス:'); // パス表示
    expect(videoMessage.attachments).toHaveLength(0); // 添付なし
  });
});
```

#### シナリオ4：容量監視バッチの完全利用
```javascript
describe('容量管理のユーザ体験', () => {
  it('テスト蓄積 → 容量チェック → 削除判断', async () => {
    // Given: テスト結果が蓄積されている状態
    await createTestResults([
      { name: 'old-test-1', size: '200MB', age: '10日前' },
      { name: 'recent-test-1', size: '300MB', age: '1日前' },
      { name: 'old-test-2', size: '600MB', age: '20日前' }
    ]);
    
    // When: 容量チェックバッチ実行
    const output = await exec('npm run capacity-check');
    
    // Then: 現在の状況が表示される
    expect(output).toContain('現在の使用量: 1.10 GB');
    expect(output).toContain('🚨 容量が閾値を超えています');
    
    // And: 削除推奨ファイルが古い順で表示される
    expect(output).toContain('削除推奨ファイル');
    const lines = output.split('\n');
    const oldTest2Line = lines.find(l => l.includes('old-test-2'));
    const oldTest1Line = lines.find(l => l.includes('old-test-1'));
    expect(lines.indexOf(oldTest2Line)).toBeLessThan(lines.indexOf(oldTest1Line));
    
    // And: ユーザが手動で削除判断できる情報が揃っている
    expect(output).toContain('600 MB'); // ファイルサイズ
    expect(output).toContain('20日前'); // 作成日時
  });
});
```

#### シナリオ5：エラー耐性の確認
```javascript
describe('エラー発生時のユーザ体験', () => {
  it('Discord接続エラー → テスト実行は継続', async () => {
    // Given: Discordサービスがダウンしている
    await mockDiscordServiceDown();
    
    // When: Playwrightテスト実行
    const result = await exec('npx playwright test example.spec.js');
    
    // Then: テスト自体は正常完了
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain('3 passed');
    
    // And: エラーログが出力される（ユーザが状況把握可能）
    expect(result.stderr).toContain('Discord notification failed');
    
    // And: テスト結果ファイルは正常に保存されている
    expect(fs.existsSync('./test-results/')).toBe(true);
  });
});
```