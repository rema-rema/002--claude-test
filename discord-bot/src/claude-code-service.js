import { spawn } from 'child_process';
import express from 'express';
import fs from 'fs/promises';
import path from 'path';

export class ClaudeCodeService {
  constructor() {
    this.app = express();
    this.server = null;
    this.port = 3000;
    this.sessionId = null;
    this.workingDirectory = process.cwd();
  }

  async start() {
    this.app.use(express.json());
    
    this.app.post('/api/chat', async (req, res) => {
      try {
        const { message } = req.body;
        const response = await this.executeClaudeCode(message);
        res.json({ response });
      } catch (error) {
        console.error('Claude Code execution error:', error);
        res.status(500).json({ error: error.message });
      }
    });

    this.server = this.app.listen(this.port, () => {
      console.log(`Claude Code server running on port ${this.port}`);
    });
  }

  async executeClaudeCode(message) {
    console.log(`Executing Claude Code with message: "${message}"`);
    console.log(`Working directory: ${this.workingDirectory}`);
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        claudeProcess.kill();
        reject(new Error('Claude Code execution timed out after 30 seconds'));
      }, 30000);

      const claudeProcess = spawn('claude', [
        '--print',
        '--dangerously-skip-permissions'
      ], {
        cwd: this.workingDirectory,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let output = '';
      let errorOutput = '';

      claudeProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        console.log('Claude stdout:', chunk);
        output += chunk;
      });

      claudeProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        console.log('Claude stderr:', chunk);
        errorOutput += chunk;
      });

      claudeProcess.on('close', (code) => {
        clearTimeout(timeout);
        console.log(`Claude Code process closed with code: ${code}`);
        console.log('Final output:', output);
        console.log('Final error:', errorOutput);
        
        if (code === 0) {
          const result = this.parseClaudeOutput(output);
          resolve(result || 'Claude Code executed successfully but returned no output');
        } else {
          reject(new Error(`Claude Code exited with code ${code}: ${errorOutput}`));
        }
      });

      claudeProcess.on('error', (error) => {
        clearTimeout(timeout);
        console.log('Claude Code process error:', error);
        reject(new Error(`Failed to start Claude Code: ${error.message}`));
      });

      // Send the message to Claude Code via stdin
      claudeProcess.stdin.write(message + '\n');
      claudeProcess.stdin.end();
    });
  }

  parseClaudeOutput(output) {
    // Basic parsing of Claude Code output
    // In a real implementation, you would parse the structured output
    const lines = output.split('\n').filter(line => line.trim());
    
    // Look for actual response content, filtering out system messages
    const responseLines = lines.filter(line => 
      !line.includes('Loading Claude Code') &&
      !line.includes('Authenticating') &&
      !line.includes('Ready to assist')
    );

    return responseLines.join('\n') || output;
  }

  async createWorkingDirectory() {
    const tempDir = path.join(process.cwd(), 'temp_claude_sessions');
    try {
      await fs.mkdir(tempDir, { recursive: true });
      this.workingDirectory = tempDir;
      return tempDir;
    } catch (error) {
      console.error('Failed to create working directory:', error);
      throw error;
    }
  }

  async listFiles() {
    try {
      const files = await fs.readdir(this.workingDirectory);
      return files.map(file => ({
        name: file,
        path: path.join(this.workingDirectory, file)
      }));
    } catch (error) {
      throw new Error(`Failed to list files: ${error.message}`);
    }
  }

  async readFile(fileName) {
    try {
      const filePath = path.join(this.workingDirectory, fileName);
      const content = await fs.readFile(filePath, 'utf-8');
      return content;
    } catch (error) {
      throw new Error(`Failed to read file ${fileName}: ${error.message}`);
    }
  }

  async stop() {
    if (this.server) {
      await new Promise((resolve) => {
        this.server.close(resolve);
      });
      console.log('Claude Code server stopped');
    }
  }
}