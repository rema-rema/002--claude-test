# Project Overview: Discord Claude Code Interface

## Purpose
This project is a Discord bot that enables interaction with Claude AI through Discord messages. Users can communicate with Claude AI directly via Discord channels, with conversations managed through Discord threads.

## Tech Stack
- **Runtime**: Node.js with ES modules
- **Main Language**: JavaScript
- **Key Dependencies**:
  - `discord.js` v14.21.0 - Discord bot framework
  - `@anthropic-ai/sdk` v0.60.0 - Claude AI integration
  - `dotenv` v17.2.1 - Environment variable management
  - `express` v5.1.0 - Web server (for Vercel API endpoints)

## Architecture
The project consists of two main components:

### 1. Discord Bot Component (`discord-bot/src/`)
- **Main entry point**: `discord-bot/src/index.js`
- **Core classes**:
  - `DiscordClaudeInterface`: Main orchestrator class
  - `DiscordBot`: Discord client and message handling
  - `ClaudeService`: Claude AI integration and conversation management
  - Configuration management in `config.js`

### 2. Vercel API Component (`api/`)
- **Wake endpoint**: `api/wake.js` - Serverless function for GitHub Codespace management
- Handles both POST and GET requests for codespace wake functionality

## Key Features
- Thread-based conversations in Discord
- Conversation history management (keeps last 10 messages)
- Bot commands: `!clear`, `!history`, `!help`, `!wake`
- Automatic message splitting for Discord's 2000 character limit
- GitHub Codespace integration via wake endpoint

## Deployment
- Discord bot: Direct Node.js execution
- API endpoints: Vercel serverless functions
- Environment: GitHub Codespaces compatible