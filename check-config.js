import { config, validateConfig } from './src/config.js';

try {
  validateConfig();
  console.log('✅ 設定OK');
  console.log('Discord Token:', config.discord.token ? '設定済み' : '未設定');
  console.log('Channel ID:', config.discord.channelId ? '設定済み' : '未設定');
  console.log('User ID:', config.discord.userId ? '設定済み' : '未設定');
  console.log('API Key:', config.claude.apiKey ? '設定済み' : '未設定');
} catch (error) {
  console.log('❌', error.message);
}