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
    console.log(`Message received: ${message.content} from ${message.author.id} in ${message.channel.id}`);
    
    if (message.author.bot) return;
    if (message.author.id !== this.targetUserId) {
      console.log(`User ID mismatch: ${message.author.id} !== ${this.targetUserId}`);
      return;
    }
    if (message.channel.id !== this.targetChannelId && message.channel.parentId !== this.targetChannelId) {
      console.log(`Channel ID mismatch: ${message.channel.id} !== ${this.targetChannelId}`);
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


  async stop() {
    await this.client.destroy();
  }
}