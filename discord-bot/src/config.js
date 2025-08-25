import dotenv from 'dotenv';

dotenv.config();

export const config = {
  discord: {
    token: process.env.CC_DISCORD_TOKEN,
    channelId: process.env.CC_DISCORD_CHANNEL_ID_002,
    resultChannelId: process.env.CC_DISCORD_CHANNEL_ID_002_RESULT,
    userId: process.env.CC_DISCORD_USER_ID,
  },
  claude: {
    apiKey: process.env.ANTHROPIC_API_KEY,
  }
};

export function validateConfig() {
  const required = [
    'CC_DISCORD_TOKEN',
    'CC_DISCORD_CHANNEL_ID_002', 
    'CC_DISCORD_CHANNEL_ID_002_RESULT',
    'CC_DISCORD_USER_ID',
    'ANTHROPIC_API_KEY'
  ];
  
  const missing = required.filter(key => !process.env[key]);
  
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
}