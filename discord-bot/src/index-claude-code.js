import { DiscordBot } from './discord-bot.js';
import { ClaudeCodeService } from './claude-code-service.js';
import { validateConfig } from './config.js';

class DiscordClaudeCodeInterface {
  constructor() {
    this.discordBot = new DiscordBot();
    this.claudeCodeService = new ClaudeCodeService();
  }

  async start() {
    try {
      validateConfig();
      console.log('Configuration validated successfully');
      
      // Start Claude Code service
      await this.claudeCodeService.start();
      await this.claudeCodeService.createWorkingDirectory();
      
      this.discordBot.setMessageHandler(async (message) => {
        await this.handleUserMessage(message);
      });
      
      await this.discordBot.start();
      console.log('Discord Claude Code Interface is running...');
      
    } catch (error) {
      console.error('Failed to start Discord Claude Code Interface:', error);
      process.exit(1);
    }
  }

  async handleUserMessage(message) {
    try {
      console.log(`Received message from ${message.author.username}: ${message.content}`);
      
      if (message.content.startsWith('!files')) {
        const files = await this.claudeCodeService.listFiles();
        const fileList = files.length > 0 
          ? files.map(f => `• ${f.name}`).join('\n')
          : 'No files in working directory';
        await this.discordBot.sendMessage(`📁 **Files in working directory:**\n${fileList}`);
        return;
      }
      
      if (message.content.startsWith('!read ')) {
        const fileName = message.content.substring(6).trim();
        try {
          const content = await this.claudeCodeService.readFile(fileName);
          const truncated = content.length > 1900 ? content.substring(0, 1900) + '...' : content;
          await this.discordBot.sendMessage(`📄 **${fileName}:**\n\`\`\`\n${truncated}\n\`\`\``);
        } catch (error) {
          await this.discordBot.sendMessage(`❌ Error reading file: ${error.message}`);
        }
        return;
      }
      
      if (message.content.startsWith('!help')) {
        const helpMessage = `
**Discord Claude Code Interface コマンド:**
• \`!files\` - 作業ディレクトリのファイル一覧
• \`!read <filename>\` - ファイルの内容を表示
• \`!help\` - このヘルプを表示

その他のメッセージはClaude Codeに送信され、プログラミング支援として処理されます。
Claude Codeはファイルの作成、編集、コード実行などが可能です。
        `;
        await this.discordBot.sendMessage(helpMessage);
        return;
      }

      await this.discordBot.sendMessage('🔧 Claude Codeで処理中...');
      
      try {
        const response = await this.claudeCodeService.executeClaudeCode(message.content);
        await this.discordBot.sendMessage(response || 'No response from Claude Code');
      } catch (error) {
        console.error('Claude Code error:', error);
        await this.discordBot.sendMessage(`❌ Claude Code エラー: ${error.message}`);
      }
      
    } catch (error) {
      console.error('Error handling user message:', error);
      await this.discordBot.sendMessage(`❌ エラーが発生しました: ${error.message}`);
    }
  }

  async stop() {
    await this.claudeCodeService.stop();
    await this.discordBot.stop();
    console.log('Discord Claude Code Interface stopped');
  }
}

const botInterface = new DiscordClaudeCodeInterface();

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