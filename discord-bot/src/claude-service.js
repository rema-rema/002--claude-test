import Anthropic from '@anthropic-ai/sdk';
import { config } from './config.js';

export class ClaudeService {
  constructor() {
    this.workingDirectory = '/workspaces/002--claude-test';
    this.conversationHistory = [];
    this.anthropic = new Anthropic({
      apiKey: config.claude.apiKey,
    });
  }

  async processMessage(userMessage) {
    try {
      console.log(`Processing message: "${userMessage}"`);
      console.log(`Working directory: ${this.workingDirectory}`);
      
      this.conversationHistory.push({
        role: 'user',
        content: userMessage
      });

      // Use Claude SDK with tools (Claude Code approach)
      const response = await this.anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4000,
        messages: this.conversationHistory.slice(-10),
        system: `あなたはDiscord経由でClaude Codeを使用しているユーザーとやり取りしています。
作業ディレクトリは ${this.workingDirectory} です。

利用可能なツール:
- ファイル読み書き (readFile, writeFile, listDirectory)
- bashコマンド実行 (executeBash) 
- プロジェクト管理機能

ファイル操作やコマンド実行が必要な場合は、適切なツール関数を呼び出してください。
簡潔で分かりやすい回答を心がけ、必要に応じてコードブロックやマークダウン記法を使用してください。`,
        tools: [
          {
            name: 'listDirectory',
            description: 'ディレクトリの内容を一覧表示する',
            input_schema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'リストするディレクトリパス（省略時は作業ディレクトリ）'
                }
              }
            }
          },
          {
            name: 'readFile',
            description: 'ファイルの内容を読み込む',
            input_schema: {
              type: 'object',
              properties: {
                filepath: {
                  type: 'string',
                  description: '読み込むファイルパス'
                }
              },
              required: ['filepath']
            }
          },
          {
            name: 'writeFile',
            description: 'ファイルに内容を書き込む',
            input_schema: {
              type: 'object',
              properties: {
                filepath: {
                  type: 'string',
                  description: '書き込むファイルパス'
                },
                content: {
                  type: 'string',
                  description: '書き込む内容'
                }
              },
              required: ['filepath', 'content']
            }
          },
          {
            name: 'executeBash',
            description: 'bashコマンドを実行する',
            input_schema: {
              type: 'object',
              properties: {
                command: {
                  type: 'string',
                  description: '実行するbashコマンド'
                }
              },
              required: ['command']
            }
          }
        ]
      });

      let assistantMessage = '';

      // Handle tool use and text responses
      for (const contentBlock of response.content) {
        if (contentBlock.type === 'text') {
          assistantMessage += contentBlock.text + '\n';
        } else if (contentBlock.type === 'tool_use') {
          const toolResult = await this.executeToolFunction(contentBlock);
          assistantMessage += toolResult + '\n';
        }
      }

      const finalMessage = assistantMessage.trim();
      
      this.conversationHistory.push({
        role: 'assistant',
        content: finalMessage
      });

      return finalMessage;

    } catch (error) {
      console.error('Claude SDK Error:', error);
      return `❌ エラーが発生しました: ${error.message}`;
    }
  }

  async executeToolFunction(toolUse) {
    const { name, input } = toolUse;
    
    try {
      console.log(`Executing tool: ${name} with input:`, input);
      
      switch (name) {
        case 'listDirectory':
          return await this.listDirectory(input.path || this.workingDirectory);
        
        case 'readFile':
          return await this.readFile(input.filepath);
        
        case 'writeFile':
          return await this.writeFile(input.filepath, input.content);
        
        case 'executeBash':
          return await this.executeBash(input.command);
        
        default:
          return `❌ 未知のツール: ${name}`;
      }
    } catch (error) {
      console.error(`Tool execution error (${name}):`, error);
      return `❌ ツール実行エラー (${name}): ${error.message}`;
    }
  }

  async listDirectory(dirPath = this.workingDirectory) {
    const fs = await import('fs');
    const path = await import('path');
    
    try {
      if (!fs.existsSync(dirPath)) {
        return `❌ ディレクトリが見つかりません: ${dirPath}`;
      }
      
      const items = fs.readdirSync(dirPath);
      const dirs = [];
      const files = [];
      
      items.forEach(item => {
        const fullPath = path.join(dirPath, item);
        const stats = fs.statSync(fullPath);
        
        if (stats.isDirectory()) {
          dirs.push(item);
        } else {
          files.push(item);
        }
      });
      
      let response = `📁 **ディレクトリ構成** (${dirPath})\n\n`;
      
      if (dirs.length > 0) {
        response += '**📂 ディレクトリ:**\n';
        dirs.sort().forEach(dir => {
          response += `- \`${dir}/\`\n`;
        });
        response += '\n';
      }
      
      if (files.length > 0) {
        response += '**📄 ファイル:**\n';
        files.sort().forEach(file => {
          response += `- \`${file}\`\n`;
        });
      }
      
      return response;
    } catch (error) {
      return `❌ ディレクトリ読み込みエラー: ${error.message}`;
    }
  }

  async readFile(filepath) {
    const fs = await import('fs');
    const path = await import('path');
    
    try {
      const fullPath = path.isAbsolute(filepath) ? filepath : path.join(this.workingDirectory, filepath);
      
      if (!fs.existsSync(fullPath)) {
        return `❌ ファイルが見つかりません: ${filepath}`;
      }
      
      const content = fs.readFileSync(fullPath, 'utf-8');
      return `📄 **ファイル内容** (${filepath}):\n\`\`\`\n${content}\n\`\`\``;
    } catch (error) {
      return `❌ ファイル読み込みエラー: ${error.message}`;
    }
  }

  async writeFile(filepath, content) {
    const fs = await import('fs');
    const path = await import('path');
    
    try {
      const fullPath = path.isAbsolute(filepath) ? filepath : path.join(this.workingDirectory, filepath);
      
      // Create directory if it doesn't exist
      const dir = path.dirname(fullPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      fs.writeFileSync(fullPath, content, 'utf-8');
      return `✅ ファイルを書き込みました: ${filepath}`;
    } catch (error) {
      return `❌ ファイル書き込みエラー: ${error.message}`;
    }
  }

  async executeBash(command) {
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    
    try {
      console.log(`Executing bash command: ${command}`);
      const { stdout, stderr } = await execAsync(command, {
        cwd: this.workingDirectory,
        timeout: 30000 // 30 second timeout
      });
      
      let result = `🔧 **コマンド実行**: \`${command}\`\n\n`;
      
      if (stdout) {
        result += `**出力:**\n\`\`\`\n${stdout}\n\`\`\`\n`;
      }
      
      if (stderr) {
        result += `**エラー出力:**\n\`\`\`\n${stderr}\n\`\`\`\n`;
      }
      
      return result;
    } catch (error) {
      return `❌ コマンド実行エラー: ${error.message}`;
    }
  }

  clearHistory() {
    this.conversationHistory = [];
  }

  getHistoryLength() {
    return this.conversationHistory.length;
  }
}