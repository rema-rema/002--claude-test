# Task Completion Workflow

## When a Task is Completed

### 1. Code Quality Checks
Since this project doesn't have formal linting/formatting tools configured, perform manual checks:

```bash
# Check for syntax errors
node --check discord-bot/src/index.js
node --check discord-bot/src/discord-bot.js
node --check discord-bot/src/claude-service.js
node --check api/wake.js
```

### 2. Testing
No formal testing framework is configured, but perform these manual tests:

#### Discord Bot Testing
```bash
# Start the bot in development mode
npm run dev

# Test in Discord:
# - Send a message to trigger thread creation
# - Test !clear command
# - Test !history command  
# - Test !help command
# - Test !wake command (if GitHub integration is set up)
```

#### API Endpoint Testing
```bash
# Test wake endpoint
curl -X GET "https://your-app.vercel.app/api/wake?wake=true"
curl -X POST "https://your-app.vercel.app/api/wake" \
  -H "Content-Type: application/json" \
  -d '{"content": "!wake"}'
```

### 3. Environment Variable Validation
```bash
# Ensure all required environment variables are set
node -e "
const config = require('./discord-bot/src/config.js');
try {
  config.validateConfig();
  console.log('✅ Configuration valid');
} catch (error) {
  console.error('❌ Configuration error:', error.message);
}
"
```

### 4. Process Management
```bash
# Stop any running instances
pkill -f "discord-bot"

# Clean up PID files
rm -f bot.pid

# Start fresh instance
npm start
```

### 5. Version Control
```bash
# Check status
git status

# Stage relevant changes (avoid committing secrets)
git add discord-bot/
git add api/
git add package.json
git add README.md

# Commit with descriptive message
git commit -m "feat: describe the changes made"

# Push to repository
git push
```

### 6. Deployment Considerations

#### For Discord Bot:
- Ensure bot is running in production environment
- Verify environment variables are set correctly
- Monitor logs for any startup errors

#### For Vercel API:
- Changes to `api/` directory are automatically deployed
- Verify environment variables in Vercel dashboard
- Test endpoints after deployment

### 7. Documentation Updates
Update relevant documentation:
- README.md if setup process changed
- Add comments for complex logic
- Update environment variable examples if needed

## Rollback Process
If issues are discovered after deployment:

```bash
# Revert to previous commit
git revert HEAD

# Or reset to specific commit
git reset --hard <commit-hash>

# Restart services
npm start

# Push rollback
git push
```

## Health Checks
After completion, verify:
- ✅ Bot responds to Discord messages
- ✅ Claude AI integration working
- ✅ Thread creation functioning
- ✅ All bot commands working
- ✅ API endpoints responding correctly
- ✅ No error messages in logs
- ✅ Environment variables secure