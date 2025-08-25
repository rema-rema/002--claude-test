import { defaultRetryHandler } from '../components/RetryHandler.js';
import { defaultErrorClassifier } from '../components/ErrorClassifier.js';

export class ClaudeCodeIntegrator {
  constructor(options = {}) {
    this.retryHandler = options.retryHandler || defaultRetryHandler;
    this.errorClassifier = options.errorClassifier || defaultErrorClassifier;
    this.claudeService = options.claudeService || null;
    this.discordNotificationService = options.discordNotificationService || null;
  }

  async sendModificationRequest(approvalRequest) {
    return await this.retryHandler.retry(async () => {
      // Claude Service設定チェック
      if (!this.claudeService) {
        throw new Error('Claude Service未設定: ClaudeCodeIntegratorを適切に初期化してください');
      }
      
      // 1. エラー分類とリスク評価
      const classification = this.errorClassifier.classify(approvalRequest.error);
      
      // 2. Claude Code修正依頼メッセージ構築
      const modificationMessage = await this.buildModificationMessage(approvalRequest, classification);
      
      // 3. Claude Serviceに修正依頼を送信
      const response = await this.claudeService.sendMessage(modificationMessage);
      
      // 4. 進捗通知
      await this.notifyProgress(approvalRequest, 'MODIFICATION_REQUESTED', {
        requestId: approvalRequest.requestId,
        claudeResponse: response
      });

      return response;
    });
  }

  async processClaudeResponse(response) {
    try {
      // 1. Claude応答の解析
      const analysis = await this.analyzeClaudeResponse(response);
      
      // 2. 適用判定
      const applicationDecision = await this.evaluateApplication(analysis);
      
      // 3. Discord通知サービス連携: 結果通知
      if (this.discordNotificationService) {
        await this.discordNotificationService.sendMessage(
          this.formatResponseSummary(analysis, applicationDecision)
        );
      }

      return {
        analysis,
        applicationDecision,
        processedAt: new Date()
      };
    } catch (error) {
      const classification = this.errorClassifier.classify(error);
      
      await this.notifyProgress(null, 'PROCESSING_ERROR', {
        error: error.message,
        classification
      });
      
      throw error;
    }
  }

  async buildModificationMessage(approvalRequest, classification) {
    const { testName, error, suggestion, requestId } = approvalRequest;
    
    let message = `🔧 **Claude Code修正依頼**\n`;
    message += `Request ID: ${requestId}\n\n`;
    
    // テスト情報
    message += `**📋 テスト詳細**\n`;
    message += `- テスト名: ${testName}\n`;
    message += `- エラー分類: ${classification.category}\n`;
    message += `- 重要度: ${classification.severity}\n`;
    message += `- 信頼度: ${Math.round(classification.confidence * 100)}%\n\n`;
    
    // エラー内容
    message += `**⚠️ エラー内容**\n`;
    message += `\`\`\`\n${error.message}\n\`\`\`\n\n`;
    
    // 修正提案
    if (suggestion) {
      message += `**💡 推奨修正方法**\n`;
      message += `- 修正内容: ${suggestion.description}\n`;
      message += `- 自動化レベル: ${suggestion.automationLevel}\n`;
      message += `- リスクレベル: ${suggestion.riskLevel}\n\n`;
    }
    
    // 作業指示
    message += `**🎯 作業指示**\n`;
    message += `以下のテストを修正してください：\n`;
    message += `1. エラーの根本原因を特定\n`;
    message += `2. 適切な修正を実施\n`;
    message += `3. 修正内容をスレッドで報告\n`;
    message += `4. テストが成功することを確認\n\n`;
    message += `**重要**: 修正完了後、このスレッドで作業内容をご報告ください。`;
    
    return message;
  }

  async analyzeClaudeResponse(response) {
    // Claude応答の構造解析
    const analysis = {
      hasCodeChanges: this.detectCodeChanges(response.content),
      hasFileModifications: this.detectFileModifications(response.content),
      hasTestUpdates: this.detectTestUpdates(response.content),
      confidenceLevel: this.calculateResponseConfidence(response),
      extractedChanges: this.extractChanges(response.content)
    };

    return analysis;
  }

  async evaluateApplication(analysis) {
    // 適用判定ロジック
    const decision = {
      shouldApply: analysis.hasCodeChanges && analysis.confidenceLevel > 0.7,
      reason: this.generateApplicationReason(analysis),
      riskLevel: this.assessApplicationRisk(analysis),
      priority: this.calculateApplicationPriority(analysis)
    };

    return decision;
  }

  detectCodeChanges(content) {
    // コード変更検出の簡易実装
    const codePatterns = [
      /```[\s\S]*?```/g,
      /\bfunction\s+\w+/g,
      /\bclass\s+\w+/g,
      /\bconst\s+\w+\s*=/g,
      /\blet\s+\w+\s*=/g
    ];
    
    return codePatterns.some(pattern => pattern.test(content));
  }

  detectFileModifications(content) {
    // ファイル修正検出
    const filePatterns = [
      /file\s*[:：]\s*[^\s]+\.(js|ts|json|md)/gi,
      /path\s*[:：]\s*[^\s]+/gi,
      /修正.*ファイル/gi
    ];
    
    return filePatterns.some(pattern => pattern.test(content));
  }

  detectTestUpdates(content) {
    // テスト更新検出
    const testPatterns = [
      /test\s*\(/gi,
      /describe\s*\(/gi,
      /expect\s*\(/gi,
      /\.spec\.|\.test\./gi
    ];
    
    return testPatterns.some(pattern => pattern.test(content));
  }

  calculateResponseConfidence(response) {
    // 応答信頼度計算の簡易実装
    let confidence = 0.5; // ベース信頼度
    
    if (response.content.length > 100) confidence += 0.1;
    if (this.detectCodeChanges(response.content)) confidence += 0.3; // より高い重み
    if (this.detectFileModifications(response.content)) confidence += 0.1;
    if (response.content.includes('テスト') || response.content.includes('test')) confidence += 0.1;
    
    return Math.min(confidence, 1.0);
  }

  extractChanges(content) {
    // 変更内容抽出の簡易実装
    const changes = [];
    
    // コードブロックを抽出
    const codeBlocks = content.match(/```[\s\S]*?```/g) || [];
    codeBlocks.forEach((block, index) => {
      changes.push({
        type: 'code',
        content: block,
        index: index + 1
      });
    });
    
    return changes;
  }

  generateApplicationReason(analysis) {
    if (!analysis.hasCodeChanges) {
      return 'コード変更が検出されませんでした';
    }
    
    if (analysis.confidenceLevel < 0.7) {
      return `信頼度が低すぎます (${Math.round(analysis.confidenceLevel * 100)}%)`;
    }
    
    return `適用可能: 信頼度${Math.round(analysis.confidenceLevel * 100)}%、変更内容${analysis.extractedChanges.length}件`;
  }

  assessApplicationRisk(analysis) {
    if (!analysis.hasCodeChanges) return 'NONE';
    if (analysis.hasTestUpdates) return 'HIGH';
    if (analysis.extractedChanges.length > 3) return 'MEDIUM';
    return 'LOW';
  }

  calculateApplicationPriority(analysis) {
    if (analysis.confidenceLevel > 0.8) return 'HIGH'; // 閾値を下げる
    if (analysis.confidenceLevel > 0.6) return 'MEDIUM';
    return 'LOW';
  }

  async notifyProgress(approvalRequest, status, details = {}) {
    try {
      if (!this.discordNotificationService) {
        console.warn('Discord通知サービス未設定: 進捗通知をスキップ');
        return;
      }

      const message = this.formatProgressMessage(approvalRequest, status, details);
      await this.discordNotificationService.sendMessage(message);
    } catch (error) {
      console.error('進捗通知エラー:', error.message);
    }
  }

  formatProgressMessage(approvalRequest, status, details) {
    const timestamp = new Date().toLocaleString('ja-JP');
    
    let message = `🔄 **Claude Code統合進捗**\n`;
    message += `時刻: ${timestamp}\n`;
    
    if (approvalRequest) {
      message += `Request ID: ${approvalRequest.requestId}\n`;
      message += `テスト: ${approvalRequest.testName}\n`;
    }
    
    switch (status) {
      case 'MODIFICATION_REQUESTED':
        message += `状態: 修正依頼送信完了 ✅\n`;
        if (details.claudeResponse) {
          message += `応答受信: ${details.claudeResponse.content.length}文字\n`;
        }
        break;
        
      case 'PROCESSING_ERROR':
        message += `状態: 処理エラー ❌\n`;
        message += `エラー: ${details.error}\n`;
        if (details.classification) {
          message += `分類: ${details.classification.category}\n`;
        }
        break;
        
      default:
        message += `状態: ${status}\n`;
    }
    
    return message;
  }

  formatResponseSummary(analysis, applicationDecision) {
    let message = `📊 **Claude応答分析結果**\n\n`;
    
    // 分析結果
    message += `**🔍 分析内容**\n`;
    message += `• コード変更: ${analysis.hasCodeChanges ? '✅' : '❌'}\n`;
    message += `• ファイル修正: ${analysis.hasFileModifications ? '✅' : '❌'}\n`;
    message += `• テスト更新: ${analysis.hasTestUpdates ? '✅' : '❌'}\n`;
    message += `• 信頼度: ${Math.round(analysis.confidenceLevel * 100)}%\n`;
    message += `• 変更件数: ${analysis.extractedChanges.length}件\n\n`;
    
    // 適用判定
    message += `**⚖️ 適用判定**\n`;
    message += `• 適用可否: ${applicationDecision.shouldApply ? '✅ 適用推奨' : '❌ 適用非推奨'}\n`;
    message += `• 理由: ${applicationDecision.reason}\n`;
    message += `• リスクレベル: ${applicationDecision.riskLevel}\n`;
    message += `• 優先度: ${applicationDecision.priority}\n`;
    
    return message;
  }
}