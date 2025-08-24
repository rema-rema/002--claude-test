# Codebase Structure and Architecture

## Directory Structure
```
002--claude-test/
├── discord-bot/src/          # Core Discord bot implementation
│   ├── index.js             # Main entry point and orchestration
│   ├── discord-bot.js       # Discord client management
│   ├── claude-service.js    # Claude AI service integration
│   └── config.js            # Configuration and validation
├── api/                     # Vercel serverless functions
│   └── wake.js              # GitHub Codespace wake endpoint
├── node_modules/            # NPM dependencies
├── package.json             # Project configuration and dependencies
├── package-lock.json        # Dependency lock file
├── vercel.json              # Vercel deployment configuration
├── README.md                # Project documentation
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── .mcp.json                # MCP server configuration (Serena)
└── bot.pid                  # Process ID file (runtime)
```

## Core Classes and Their Responsibilities

### 1. DiscordClaudeInterface (index.js)
**Purpose**: Main orchestrator that coordinates between Discord and Claude services
- **Methods**:
  - `start()`: Initialize and start the bot
  - `handleUserMessage()`: Process incoming Discord messages
  - `stop()`: Gracefully shutdown the bot
- **Key Features**:
  - Message routing between Discord and Claude
  - Command processing (!clear, !history, !help, !wake)
  - Error handling and user feedback

### 2. DiscordBot (discord-bot.js)
**Purpose**: Manages Discord client connection and message handling
- **Key Properties**:
  - `client`: Discord.js client instance
  - `currentThread`: Active conversation thread
  - `messageHandler`: Callback for message processing
- **Methods**:
  - `start()`: Connect to Discord
  - `handleMessage()`: Process incoming messages
  - `createThread()`: Create conversation threads
  - `sendMessage()`: Send responses with auto-splitting
  - `splitMessage()`: Handle Discord's 2000 character limit
- **Features**:
  - User and channel validation
  - Automatic thread creation
  - Message chunking for long responses

### 3. ClaudeService (claude-service.js)
**Purpose**: Interface with Anthropic's Claude AI API
- **Key Properties**:
  - `anthropic`: Anthropic SDK client
  - `conversationHistory`: Message history (last 10 messages)
- **Methods**:
  - `processMessage()`: Send message to Claude and get response
  - `clearHistory()`: Reset conversation context
  - `getHistoryLength()`: Return conversation length
- **Features**:
  - Context management (10 message sliding window)
  - Japanese language system prompt
  - Error handling with user-friendly messages

### 4. Configuration System (config.js)
**Purpose**: Centralized configuration and environment validation
- **Exports**:
  - `config`: Configuration object with Discord and Claude settings
  - `validateConfig()`: Ensures all required environment variables are present
- **Required Environment Variables**:
  - `CC_DISCORD_TOKEN`: Discord bot token
  - `CC_DISCORD_CHANNEL_ID`: Target Discord channel
  - `CC_DISCORD_USER_ID`: Authorized user ID
  - `ANTHROPIC_API_KEY`: Claude AI API key

## API Layer (api/wake.js)
**Purpose**: Vercel serverless function for GitHub Codespace management
- **HTTP Methods**: GET and POST
- **Functionality**: 
  - Start GitHub Codespaces via GitHub API
  - Handle wake commands from Discord bot
  - Support direct browser access with wake=true parameter

## Message Flow Architecture
1. **User sends Discord message** → `DiscordBot.handleMessage()`
2. **Message validation** → Check user/channel permissions
3. **Thread management** → Create thread if needed
4. **Command processing** → Handle bot commands or route to Claude
5. **Claude integration** → `ClaudeService.processMessage()`
6. **Response handling** → Split long messages and send via Discord

## Key Design Patterns
- **Dependency Injection**: Services injected into main orchestrator
- **Event-Driven**: Discord events drive message processing
- **Separation of Concerns**: Clear boundaries between Discord, Claude, and orchestration logic
- **Configuration Pattern**: Centralized config with validation
- **Error Boundary**: Comprehensive error handling at each layer

## Threading Model
- **Main Thread**: Discord event handling and message routing
- **Async Operations**: All I/O operations use async/await
- **No Worker Threads**: Single-threaded Node.js event loop model

## Security Considerations
- User ID validation prevents unauthorized access
- Channel ID validation restricts bot to specific channels
- Environment variables for sensitive data
- No persistent data storage (conversation history is in-memory)