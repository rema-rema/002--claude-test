# Code Style and Conventions

## Language and Module System
- **Language**: JavaScript (Node.js)
- **Module System**: ES Modules (`"type": "module"` in package.json)
- **File Extensions**: `.js` for all JavaScript files

## Import/Export Style
```javascript
// ES module imports
import { Client, GatewayIntentBits, ChannelType } from 'discord.js';
import { config } from './config.js';

// ES module exports
export class DiscordBot {
  // class implementation
}

export default async function handler(req, res) {
  // function implementation
}
```

## Class and Method Conventions
- **Classes**: PascalCase (e.g., `DiscordBot`, `ClaudeService`, `DiscordClaudeInterface`)
- **Methods**: camelCase (e.g., `handleMessage`, `sendMessage`, `processMessage`)
- **Constants**: camelCase for config objects, UPPER_CASE for true constants
- **Variables**: camelCase (e.g., `targetChannelId`, `messageHandler`)

## Error Handling Pattern
```javascript
try {
  // operation
} catch (error) {
  console.error('Error description:', error);
  // appropriate error response
}
```

## Logging Style
- Use `console.log()` for informational messages
- Use `console.error()` for errors with descriptive prefixes
- Include context information in log messages

## Configuration Management
- Environment variables loaded via `dotenv`
- Configuration centralized in `config.js`
- Validation performed at startup via `validateConfig()`

## Async/Await Usage
- Prefer `async/await` over Promises chains
- All async operations properly awaited
- Error handling with try/catch blocks

## Comments and Documentation
- Minimal inline comments (code should be self-documenting)
- JSDoc not used extensively
- README.md provides comprehensive setup instructions
- Comments mainly for complex logic or important notes

## File Organization
```
project-root/
├── discord-bot/src/          # Main application logic
│   ├── index.js             # Entry point and orchestration
│   ├── discord-bot.js       # Discord client handling
│   ├── claude-service.js    # Claude AI integration
│   └── config.js            # Configuration management
├── api/                     # Vercel serverless functions
│   └── wake.js              # Codespace wake endpoint
└── package.json             # Dependencies and scripts
```

## Naming Patterns
- **Files**: kebab-case (e.g., `discord-bot.js`, `claude-service.js`)
- **Classes**: Descriptive names ending with purpose (e.g., `DiscordBot`, `ClaudeService`)
- **Methods**: Action-oriented names (e.g., `handleMessage`, `createThread`, `sendMessage`)
- **Variables**: Descriptive camelCase names (e.g., `currentThread`, `conversationHistory`)