import { Client, GatewayIntentBits } from 'discord.js';
import { config } from '../config.js';
import fs from 'fs/promises';
import path from 'path';

// Track B統合コンポーネント
import { RetryHandler, defaultRetryHandler } from '../components/RetryHandler.js';
import { ErrorClassifier, defaultErrorClassifier } from '../components/ErrorClassifier.js';
import { ThreadManager } from '../components/ThreadManager.js';

export class DiscordNotificationService {
  constructor(options = {}) {
    this.client = null;
    this.targetChannel = null;
    this.mainChannel = null;
    this.maxFileSize = 25 * 1024 * 1024; // 25MB制限
    
    // Track B統合コンポーネント
    this.retryHandler = options.retryHandler || defaultRetryHandler;
    this.errorClassifier = options.errorClassifier || defaultErrorClassifier;
    this.threadManager = options.threadManager || null;
  }

  async initialize() {
    try {
      // Discord Clientの作成・初期化
      this.client = new Client({
        intents: [
          GatewayIntentBits.Guilds,
          GatewayIntentBits.GuildMessages,
        ],
      });

      // Discord Botログイン
      await this.client.login(config.discord.token);
      
      // 接続完了まで待機
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Discord接続タイムアウト'));
        }, 10000); // 10秒でタイムアウト

        this.client.once('ready', () => {
          clearTimeout(timeout);
          console.log(`Discord通知サービス準備完了: ${this.client.user.tag}`);
          resolve();
        });

        this.client.once('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

      // テスト結果専用チャンネルの取得
      this.targetChannel = await this.client.channels.fetch(config.discord.resultChannelId);
      
      if (!this.targetChannel) {
        throw new Error(`指定されたテスト結果チャンネル(${config.discord.resultChannelId})が見つかりません`);
      }

      console.log(`テスト結果チャンネル設定完了: ${this.targetChannel.name}`);

      // 承認チャンネル初期化
      await this.initializeApprovalChannels();

    } catch (error) {
      console.error('Discord通知サービス初期化エラー:', error.message);
      throw error;
    }
  }

  async sendTestResult(summary, attachments = []) {
    try {
      await this.initialize();

      // 基本通知メッセージ作成・送信
      const message = this.formatSummaryMessage(summary);
      await this.sendMessage(message);

      // 失敗時の詳細情報送信
      if (summary.failed > 0 && attachments.length > 0) {
        await this.sendFailureDetails(attachments);
      }

      console.log('✅ Discord通知送信完了');
    } catch (error) {
      // エラーが発生してもPlaywrightテストの実行は継続させる
      console.error('❌ Discord通知送信に失敗:', error.message);
      console.error('📋 テスト結果サマリー:', JSON.stringify(summary, null, 2));
    } finally {
      // リソース解放
      await this.cleanup();
    }
  }

  async sendTestFailureWithApproval(approvalRequest) {
    return await this.retryHandler.retry(async () => {
      // 1. エラー分類
      const classification = this.errorClassifier.classify(approvalRequest.error);
      
      // 2. スレッド作成
      const thread = await this.threadManager.createApprovalThread(approvalRequest);
      
      // 3. 承認依頼メッセージ送信
      const message = await this.formatApprovalMessage(approvalRequest, classification);
      return await thread.send(message);
    });
  }

  async initializeApprovalChannels() {
    try {
      if (!this.client) {
        await this.initialize();
      }

      // RESULT vs MAIN チャンネル分離設定
      if (config.discord.mainChannelId) {
        this.mainChannel = await this.client.channels.fetch(config.discord.mainChannelId);
        
        if (!this.mainChannel) {
          throw new Error(`メインチャンネル(${config.discord.mainChannelId})が見つかりません`);
        }
        
        console.log(`メインチャンネル設定完了: ${this.mainChannel.name}`);
      }

      // ThreadManagerとの統合
      if (!this.threadManager) {
        this.threadManager = new ThreadManager({
          client: this.client,
          parentChannel: this.mainChannel || this.targetChannel
        });
      }

      console.log('承認チャンネル初期化完了');
    } catch (error) {
      console.error('承認チャンネル初期化エラー:', error.message);
      throw error;
    }
  }

  async integrateWithThreadManager(threadManager) {
    this.threadManager = threadManager;
  }

  async formatApprovalMessage(approvalRequest, classification) {
    const { testName, error, suggestion, requestId } = approvalRequest;
    
    let message = `🔍 **テスト失敗修正承認依頼**\n`;
    message += `📝 Request ID: \`${requestId}\`\n\n`;
    
    // 問題概要
    message += `**📊 問題概要**\n`;
    message += `• テスト名: \`${testName}\`\n`;
    message += `• エラー分類: ${classification.category} (${classification.severity})\n`;
    message += `• 信頼度: ${Math.round(classification.confidence * 100)}%\n\n`;
    
    // 原因
    message += `**⚠️ エラー原因**\n`;
    const errorMsg = error.message.length > 200 
      ? error.message.substring(0, 200) + '...'
      : error.message;
    message += `\`\`\`\n${errorMsg}\n\`\`\`\n\n`;
    
    // 修正提案
    if (suggestion) {
      message += `**💡 修正提案**\n`;
      message += `• 修正方法: ${suggestion.description}\n`;
      message += `• 自動化度: ${suggestion.automationLevel}\n`;
      message += `• リスクレベル: ${suggestion.riskLevel}\n\n`;
    }
    
    // 操作方法
    message += `**🎯 操作方法**\n`;
    message += `• ✅ 承認: このメッセージにリアクション\n`;
    message += `• ❌ 拒否: 拒否リアクション\n`;
    message += `• 📝 修正内容はこのスレッドで報告されます\n`;
    
    return message;
  }

  async cleanup() {
    try {
      if (this.client && this.client.readyAt) {
        console.log('Discord接続をクリーンアップ中...');
        await this.client.destroy();
        this.client = null;
        this.targetChannel = null;
      }
    } catch (error) {
      console.error('Discord接続クリーンアップエラー:', error.message);
    }
  }

  formatSummaryMessage(summary) {
    const status = summary.failed > 0 ? '❌ FAILED' : '✅ PASSED';
    const duration = Math.round(summary.duration / 1000);
    
    let message = `
🎭 **Playwright テスト結果** ${status}

📊 **結果サマリー**
• 総テスト数: ${summary.total}
• 成功: ${summary.passed} ✅
• 失敗: ${summary.failed} ❌`;

    if (summary.skipped > 0) {
      message += `\n• スキップ: ${summary.skipped} ⏭️`;
    }

    message += `\n• 実行時間: ${duration}秒

🕒 実行時刻: ${new Date(summary.timestamp).toLocaleString('ja-JP')}`;

    // 失敗時には詳細へのヒントを追加
    if (summary.failed > 0) {
      message += '\n\n💡 各失敗テストの詳細は以下をご確認ください ⬇️';
    }

    return message.trim();
  }

  async sendFailureDetails(attachments) {
    for (const attachment of attachments) {
      try {
        // テスト名のヘッダーと詳細情報送信
        if (attachment.testName) {
          let detailMessage = `\n🔍 **${attachment.testName}** の詳細:`;
          
          // ファイル名を追加
          if (attachment.testFile) {
            const fileName = attachment.testFile.split('/').pop();
            detailMessage += `\n📂 ファイル: \`${fileName}\``;
          }
          
          // プロジェクト名を追加
          if (attachment.testProject) {
            detailMessage += `\n🌐 ブラウザ: ${attachment.testProject}`;
          }
          
          // エラーメッセージを追加
          if (attachment.error && attachment.error.message) {
            const errorMsg = attachment.error.message.length > 300 
              ? attachment.error.message.substring(0, 300) + '...'
              : attachment.error.message;
            detailMessage += `\n❌ エラー: \`${errorMsg}\``;
          }
          
          await this.sendMessage(detailMessage);
        }

        // スクリーンショット添付
        if (attachment.screenshot && await this.fileExists(attachment.screenshot)) {
          if (await this.isValidFileSize(attachment.screenshot)) {
            await this.sendFileWithErrorHandling(
              attachment.screenshot, 
              `🖼️ スクリーンショット`
            );
          } else {
            const size = await this.getFileSize(attachment.screenshot);
            await this.sendMessage(
              `🖼️ スクリーンショット (${this.formatFileSize(size)}) - サイズ制限により表示できません\n` +
              `📍 パス: \`${attachment.screenshot}\``
            );
          }
        }

        // 動画ファイル情報
        if (attachment.video && await this.fileExists(attachment.video)) {
          const videoSize = await this.getFileSize(attachment.video);
          
          if (videoSize < this.maxFileSize) {
            await this.sendFileWithErrorHandling(
              attachment.video, 
              `🎬 実行動画`
            );
          } else {
            await this.sendMessage(
              `📹 実行動画 (${this.formatFileSize(videoSize)})\n` +
              `📍 パス: \`${attachment.video}\``
            );
          }
        }

        // トレースファイル情報
        if (attachment.trace && await this.fileExists(attachment.trace)) {
          const traceSize = await this.getFileSize(attachment.trace);
          await this.sendMessage(
            `📋 トレースファイル (${this.formatFileSize(traceSize)})\n` +
            `📍 パス: \`${attachment.trace}\``
          );
        }
      } catch (error) {
        console.error(`❌ 添付ファイル送信エラー (${attachment.testName}):`, error.message);
        
        // エラー時も基本情報は送信
        await this.sendMessage(
          `⚠️ ${attachment.testName} の詳細情報送信に失敗しました`
        );
      }
    }
  }

  async sendMessage(content) {
    if (!this.targetChannel) {
      throw new Error('Discord チャンネルが初期化されていません');
    }

    try {
      // メッセージ長制限対応（Discord: 2000文字）
      if (content.length > 2000) {
        const chunks = this.splitMessage(content, 2000);
        for (const chunk of chunks) {
          await this.targetChannel.send(chunk);
        }
      } else {
        await this.targetChannel.send(content);
      }
    } catch (error) {
      console.error('メッセージ送信エラー:', error.message);
      throw error;
    }
  }

  splitMessage(text, maxLength) {
    const chunks = [];
    let current = '';
    
    const lines = text.split('\n');
    
    for (const line of lines) {
      if (current.length + line.length + 1 > maxLength) {
        if (current) {
          chunks.push(current);
          current = '';
        }
        
        if (line.length > maxLength) {
          let remaining = line;
          while (remaining.length > maxLength) {
            chunks.push(remaining.substring(0, maxLength));
            remaining = remaining.substring(maxLength);
          }
          current = remaining;
        } else {
          current = line;
        }
      } else {
        if (current) current += '\n';
        current += line;
      }
    }
    
    if (current) {
      chunks.push(current);
    }
    
    return chunks;
  }

  async sendFileWithErrorHandling(filePath, caption) {
    try {
      if (!this.targetChannel) {
        throw new Error('Discord チャンネルが初期化されていません');
      }

      // ファイル添付送信
      await this.targetChannel.send({
        content: caption,
        files: [filePath]
      });

    } catch (error) {
      console.error(`ファイル送信エラー: ${filePath}`, error.message);
      
      // ファイル送信に失敗した場合は、ファイル情報のみ送信
      const size = await this.getFileSize(filePath);
      await this.sendMessage(
        `${caption} (${this.formatFileSize(size)}) - 添付送信失敗\n` +
        `📍 パス: \`${filePath}\``
      );
    }
  }

  async isValidFileSize(filePath) {
    try {
      const stats = await fs.stat(filePath);
      return stats.size <= this.maxFileSize;
    } catch (error) {
      console.error(`ファイルサイズチェックエラー: ${filePath}`, error.message);
      return false;
    }
  }

  async getFileSize(filePath) {
    try {
      const stats = await fs.stat(filePath);
      return stats.size;
    } catch (error) {
      console.error(`ファイルサイズ取得エラー: ${filePath}`, error.message);
      return 0;
    }
  }

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch (error) {
      return false;
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}