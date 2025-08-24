# Suggested Commands for Discord Claude Code Interface

## Development Commands

### Installation & Setup
```bash
npm install                    # Install dependencies
```

### Running the Application
```bash
npm start                     # Start the Discord bot (production)
npm run dev                   # Start in development mode with auto-reload
```

### Environment Setup
Create `.env` file with required variables:
```bash
CC_DISCORD_TOKEN=your-discord-bot-token
CC_DISCORD_CHANNEL_ID=your-channel-id
CC_DISCORD_USER_ID=your-user-id
ANTHROPIC_API_KEY=your-anthropic-api-key

# For Codespace wake functionality:
GITHUB_TOKEN=your-github-token
GITHUB_USERNAME=your-github-username
GITHUB_REPO_NAME=your-repo-name
```

## Bot Commands (Discord)
- `!clear` - Clear conversation history
- `!history` - Show conversation history length
- `!help` - Display help information
- `!wake` - Wake up GitHub Codespace

## System Commands (Linux)
```bash
# Process management
ps aux | grep node           # Find running Node processes
pkill -f "discord-bot"       # Kill discord bot processes

# Log monitoring
tail -f discord-bot.log      # Monitor bot logs
journalctl -f               # System logs

# Git operations
git status                  # Check repository status
git add .                   # Stage changes
git commit -m "message"     # Commit changes
git push                    # Push to remote

# File operations
ls -la                      # List files with details
find . -name "*.js"         # Find JavaScript files
grep -r "pattern" .         # Search for patterns in files
```

## Vercel Development
```bash
# For API endpoint testing
curl -X GET "https://your-app.vercel.app/api/wake?wake=true"
curl -X POST "https://your-app.vercel.app/api/wake" -d '{"content": "!wake"}'
```

## Debugging & Monitoring
```bash
# Check bot status
cat bot.pid                 # Get bot process ID
kill -0 $(cat bot.pid)      # Check if bot is running

# Network debugging
netstat -tlnp | grep :3000  # Check port usage
lsof -i :3000              # Check what's using port 3000
```