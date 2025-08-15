import { Client, GatewayIntentBits, ChannelType } from 'discord.js';
import { config } from './config.js';

export class DiscordBot {
  constructor() {
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
      ],
    });
    
    this.targetChannelId = config.discord.channelId;
    this.targetUserId = config.discord.userId;
    this.messageHandler = null;
    this.currentThread = null;
  }

  async start() {
    this.client.on('ready', () => {
      console.log(`Discord bot logged in as ${this.client.user.tag}`);
    });

    this.client.on('messageCreate', async (message) => {
      await this.handleMessage(message);
    });

    await this.client.login(config.discord.token);
  }

  async handleMessage(message) {
    if (message.author.bot) return;
    if (message.author.id !== this.targetUserId) return;
    if (message.channel.id !== this.targetChannelId && message.channel.parentId !== this.targetChannelId) return;

    // Handle !wake command
    if (message.content.trim() === '!wake') {
      await this.handleWakeCommand(message);
      return;
    }

    if (!this.currentThread) {
      await this.createThread(message);
    }

    if (this.messageHandler) {
      await this.messageHandler(message);
    }
  }

  async createThread(message) {
    const channel = message.channel;
    
    if (channel.type === ChannelType.GuildText) {
      this.currentThread = await channel.threads.create({
        name: `Claude Code Session - ${new Date().toLocaleString()}`,
        autoArchiveDuration: 60,
        reason: 'Claude Code Discord Interface',
      });
      
      await this.currentThread.send('🤖 Claude Code Discord Interface が開始されました！');
    } else if (channel.type === ChannelType.PublicThread) {
      this.currentThread = channel;
    }
  }

  setMessageHandler(handler) {
    this.messageHandler = handler;
  }

  async sendMessage(content) {
    if (!this.currentThread) return;
    
    if (content.length > 2000) {
      const chunks = this.splitMessage(content, 2000);
      for (const chunk of chunks) {
        await this.currentThread.send(chunk);
      }
    } else {
      await this.currentThread.send(content);
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

  async handleWakeCommand(message) {
    try {
      await message.react('⏰');
      
      const response = await fetch('https://002-claude-test.vercel.app/api/wake', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: '!wake'
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        await message.reply(`✅ ${result.message}`);
        if (result.codespace_url) {
          await message.reply(`🔗 Codespace URL: ${result.codespace_url}`);
        }
      } else {
        await message.reply(`❌ Error: ${result.error}`);
      }
    } catch (error) {
      console.error('Wake command error:', error);
      await message.reply('❌ Failed to wake up Codespace. Please try again later.');
    }
  }

  async stop() {
    await this.client.destroy();
  }
}