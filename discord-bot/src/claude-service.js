import Anthropic from '@anthropic-ai/sdk';
import { config } from './config.js';

export class ClaudeService {
  constructor() {
    this.anthropic = new Anthropic({
      apiKey: config.claude.apiKey,
    });
    this.conversationHistory = [];
  }

  async processMessage(userMessage) {
    try {
      this.conversationHistory.push({
        role: 'user',
        content: userMessage
      });

      const response = await this.anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4000,
        messages: this.conversationHistory.slice(-10), // Keep last 10 messages for context
        system: `あなたはDiscord経由でClaude Codeを使用しているユーザーとやり取りしています。
        簡潔で分かりやすい回答を心がけてください。
        必要に応じて、コードブロックやマークダウン記法を使用してください。`
      });

      const assistantMessage = response.content[0].text;
      
      this.conversationHistory.push({
        role: 'assistant',
        content: assistantMessage
      });

      return assistantMessage;
    } catch (error) {
      console.error('Claude API Error:', error);
      return `エラーが発生しました: ${error.message}`;
    }
  }

  clearHistory() {
    this.conversationHistory = [];
  }

  getHistoryLength() {
    return this.conversationHistory.length;
  }
}