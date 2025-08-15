import { DiscordBot } from './discord-bot.js';
import { ClaudeService } from './claude-service.js';
import { validateConfig } from './config.js';

class DiscordClaudeInterface {
  constructor() {
    this.discordBot = new DiscordBot();
    this.claudeService = new ClaudeService();
  }

  async start() {
    try {
      validateConfig();
      console.log('Configuration validated successfully');
      
      this.discordBot.setMessageHandler(async (message) => {
        await this.handleUserMessage(message);
      });
      
      await this.discordBot.start();
      console.log('Discord Claude Interface is running...');
      
    } catch (error) {
      console.error('Failed to start Discord Claude Interface:', error);
      process.exit(1);
    }
  }

  async handleUserMessage(message) {
    try {
      console.log(`Received message from ${message.author.username}: ${message.content}`);
      
      if (message.content.startsWith('!clear')) {
        this.claudeService.clearHistory();
        await this.discordBot.sendMessage('🧹 会話履歴をクリアしました');
        return;
      }
      
      if (message.content.startsWith('!history')) {
        const length = this.claudeService.getHistoryLength();
        await this.discordBot.sendMessage(`📊 会話履歴: ${length} メッセージ`);
        return;
      }
      
      if (message.content.startsWith('!help')) {
        const helpMessage = `
**Discord Claude Interface コマンド:**
• \`!clear\` - 会話履歴をクリア
• \`!history\` - 会話履歴の長さを表示
• \`!help\` - このヘルプを表示

その他のメッセージはClaudeに送信されます。
        `;
        await this.discordBot.sendMessage(helpMessage);
        return;
      }

      await this.discordBot.sendMessage('🤔 思考中...');
      
      const response = await this.claudeService.processMessage(message.content);
      await this.discordBot.sendMessage(response);
      
    } catch (error) {
      console.error('Error handling user message:', error);
      await this.discordBot.sendMessage(`❌ エラーが発生しました: ${error.message}`);
    }
  }

  async stop() {
    await this.discordBot.stop();
    console.log('Discord Claude Interface stopped');
  }
}

const botInterface = new DiscordClaudeInterface();

process.on('SIGINT', async () => {
  console.log('\nShutting down...');
  await botInterface.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\nShutting down...');
  await botInterface.stop();
  process.exit(0);
});

botInterface.start();