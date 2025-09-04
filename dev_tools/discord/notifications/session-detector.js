/**
 * SessionDetector - 現在実行セッションの自動検出
 * 
 * 機能:
 * - Claude Code実行時のセッション情報検出
 * - セッション情報のキャッシュ管理
 * - 検出失敗時のフォールバック処理
 */

import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';

export class SessionDetector extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.config = {
      cacheTimeout: options.cacheTimeout || 30000, // 30秒
      fallbackSession: options.fallbackSession || 'A',
      detectionMethods: options.detectionMethods || [
        'environment',
        'sessionManager',
        'workingDirectory',
        'processArgs'
      ],
      ...options
    };

    this._cachedSession = null;
    this._lastCacheTime = null;
    this._detectionHistory = [];

    console.log('🔍 SessionDetector initialized:', this.config);
  }

  /**
   * 現在実行中のセッション番号を検出（メイン機能）
   * @returns {Promise<string>} セッション番号
   */
  async detectCurrentSession() {
    try {
      // キャッシュチェック
      const cachedSession = this._getCachedSession();
      if (cachedSession) {
        console.log(`📦 Using cached session: ${cachedSession}`);
        return cachedSession;
      }

      console.log('🔍 Starting session detection...');
      
      // 複数の検出方法を順番に試行
      for (const method of this.config.detectionMethods) {
        try {
          const sessionId = await this._detectByMethod(method);
          if (sessionId && this._isValidSession(sessionId)) {
            console.log(`✅ Session detected by ${method}: ${sessionId}`);
            
            // 検出成功をキャッシュ
            this._cacheSession(sessionId, method);
            this._logDetection(method, sessionId, true);
            
            this.emit('sessionDetected', { sessionId, method });
            return sessionId;
          }
        } catch (error) {
          console.warn(`⚠️ Detection method '${method}' failed:`, error.message);
          this._logDetection(method, null, false, error.message);
        }
      }

      // 全ての検出方法が失敗した場合のフォールバック
      console.warn(`🔧 All detection methods failed, using fallback: ${this.config.fallbackSession}`);
      
      this._logDetection('fallback', this.config.fallbackSession, true);
      this.emit('sessionFallback', { sessionId: this.config.fallbackSession });
      
      return this.config.fallbackSession;

    } catch (error) {
      console.error('💥 Critical session detection error:', error);
      
      // 緊急フォールバック
      this.emit('detectionError', { error: error.message });
      return this.config.fallbackSession;
    }
  }

  /**
   * 特定の検出方法を強制実行
   * @param {string} method 検出方法名
   * @returns {Promise<string>} セッション番号
   */
  async forceDetection(method) {
    console.log(`🎯 Force detection using method: ${method}`);
    
    try {
      const sessionId = await this._detectByMethod(method);
      if (sessionId && this._isValidSession(sessionId)) {
        this._cacheSession(sessionId, method);
        return sessionId;
      } else {
        throw new Error(`Invalid session detected: ${sessionId}`);
      }
    } catch (error) {
      console.error(`❌ Force detection failed for method '${method}':`, error);
      throw error;
    }
  }

  /**
   * セッション検出履歴取得
   * @returns {Array} 検出履歴
   */
  getDetectionHistory() {
    return [...this._detectionHistory];
  }

  /**
   * 検出統計情報取得
   * @returns {Object} 統計情報
   */
  getDetectionStats() {
    const history = this._detectionHistory;
    const methodStats = {};
    
    for (const record of history) {
      if (!methodStats[record.method]) {
        methodStats[record.method] = { success: 0, failure: 0 };
      }
      methodStats[record.method][record.success ? 'success' : 'failure']++;
    }

    return {
      totalAttempts: history.length,
      methodStats,
      lastDetection: history[history.length - 1],
      cacheInfo: {
        hasCachedSession: this._cachedSession !== null,
        cacheAge: this._lastCacheTime ? Date.now() - this._lastCacheTime : null
      }
    };
  }

  /**
   * キャッシュクリア
   */
  clearCache() {
    this._cachedSession = null;
    this._lastCacheTime = null;
    console.log('🧹 Session detection cache cleared');
  }

  /**
   * 指定方法によるセッション検出
   * @param {string} method 検出方法
   * @returns {Promise<string>} セッション番号
   * @private
   */
  async _detectByMethod(method) {
    switch (method) {
      case 'environment':
        return this._detectFromEnvironment();
      
      case 'sessionManager':
        return await this._detectFromSessionManager();
      
      case 'workingDirectory':
        return this._detectFromWorkingDirectory();
      
      case 'processArgs':
        return this._detectFromProcessArgs();
      
      default:
        throw new Error(`Unknown detection method: ${method}`);
    }
  }

  /**
   * 環境変数からセッション検出
   * @returns {string} セッション番号
   * @private
   */
  _detectFromEnvironment() {
    // Claude Code実行時に設定される可能性のある環境変数
    const envVars = [
      'CURRENT_SESSION_ID',
      'CLAUDE_SESSION_ID', 
      'DISCORD_SESSION_ID',
      'PLAYWRIGHT_SESSION_ID'
    ];

    for (const envVar of envVars) {
      const value = process.env[envVar];
      if (value && this._isValidSession(value)) {
        console.log(`🎯 Session found in ${envVar}: ${value}`);
        return value;
      }
    }

    throw new Error('No valid session found in environment variables');
  }

  /**
   * SessionManagerからセッション検出
   * @returns {Promise<string>} セッション番号
   * @private
   */
  async _detectFromSessionManager() {
    try {
      // 既存のSessionManagerを動的インポート
      const { SessionManager } = await import('../../claude-discord-bridge-server/src/session_manager.js');
      
      const sessionManager = new SessionManager();
      
      // 現在のアクティブセッションを取得
      const activeSession = sessionManager.getCurrentActiveSession ? 
        sessionManager.getCurrentActiveSession() : 
        sessionManager.getDefaultSession();

      if (activeSession && this._isValidSession(activeSession)) {
        console.log(`🎯 Session from SessionManager: ${activeSession}`);
        return String(activeSession);
      }

      throw new Error('No valid active session found in SessionManager');

    } catch (error) {
      if (error.message.includes('Cannot resolve module')) {
        throw new Error('SessionManager not available');
      }
      throw error;
    }
  }

  /**
   * 作業ディレクトリからセッション推定
   * @returns {string} セッション番号
   * @private
   */
  _detectFromWorkingDirectory() {
    const cwd = process.cwd();
    
    // セッション固有のディレクトリパターンをチェック
    const sessionPatterns = [
      /session[_-]?(\d+)/i,
      /channel[_-]?(\d+)/i,
      /workspace[_-]?(\d+)/i
    ];

    for (const pattern of sessionPatterns) {
      const match = cwd.match(pattern);
      if (match && match[1]) {
        const sessionId = this._normalizeSessionId(match[1]);
        console.log(`🎯 Session inferred from working directory: ${sessionId}`);
        return sessionId;
      }
    }

    throw new Error(`No session pattern found in working directory: ${cwd}`);
  }

  /**
   * プロセス引数からセッション検出
   * @returns {string} セッション番号
   * @private
   */
  _detectFromProcessArgs() {
    const args = process.argv;
    
    // --session, --channel, session= 等のパターンをチェック
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      
      // --session=N 形式
      const sessionMatch = arg.match(/^--(?:session|channel)=(\d+)$/);
      if (sessionMatch) {
        const sessionId = this._normalizeSessionId(sessionMatch[1]);
        console.log(`🎯 Session from process args: ${sessionId}`);
        return sessionId;
      }
      
      // --session N 形式
      if (arg === '--session' || arg === '--channel') {
        const nextArg = args[i + 1];
        if (nextArg && /^\d+$/.test(nextArg)) {
          const sessionId = this._normalizeSessionId(nextArg);
          console.log(`🎯 Session from process args: ${sessionId}`);
          return sessionId;
        }
      }
    }

    throw new Error('No session argument found in process args');
  }

  /**
   * セッション番号の有効性検証
   * @param {string} sessionId セッション番号 (例: "002", "A", "B", "C")
   * @returns {boolean} 有効性フラグ
   * @private
   */
  _isValidSession(sessionId) {
    if (!sessionId || typeof sessionId !== 'string') {
      return false;
    }

    // 数字のみ（1-4桁）、英字のみ（A-Z）、または 数字_英字 形式
    const sessionPattern = /^(?:[0-9]{1,4}(?:_[A-Z]+)?|[A-Z]+)$/;
    return sessionPattern.test(sessionId.trim());
  }

  /**
   * セッション番号の正規化
   * @param {string} sessionId 生のセッション番号 (例: "2", "A", "002_C")
   * @returns {string} 正規化されたセッション番号 (例: "002", "A", "002_C")
   * @private
   */
  _normalizeSessionId(sessionId) {
    // _がある場合（002_C など）または英字のみ（A, B, C など）はそのまま返す
    if (sessionId.includes('_') || /^[A-Z]+$/.test(sessionId)) {
      return sessionId;
    }
    
    // 数字のみの場合は3桁にパディング
    const num = parseInt(sessionId, 10);
    return String(num).padStart(3, '0');
  }

  /**
   * キャッシュからセッション取得
   * @returns {string|null} キャッシュされたセッション番号
   * @private
   */
  _getCachedSession() {
    if (!this._cachedSession || !this._lastCacheTime) {
      return null;
    }

    const cacheAge = Date.now() - this._lastCacheTime;
    if (cacheAge > this.config.cacheTimeout) {
      console.log('⏰ Session cache expired');
      this.clearCache();
      return null;
    }

    return this._cachedSession;
  }

  /**
   * セッション情報をキャッシュ
   * @param {string} sessionId セッション番号
   * @param {string} method 検出方法
   * @private
   */
  _cacheSession(sessionId, method) {
    this._cachedSession = sessionId;
    this._lastCacheTime = Date.now();
    
    console.log(`📦 Session cached: ${sessionId} (detected by: ${method})`);
    this.emit('sessionCached', { sessionId, method });
  }

  /**
   * 検出履歴を記録
   * @param {string} method 検出方法
   * @param {string} sessionId セッション番号
   * @param {boolean} success 成功フラグ
   * @param {string} error エラーメッセージ
   * @private
   */
  _logDetection(method, sessionId, success, error = null) {
    const record = {
      timestamp: new Date().toISOString(),
      method,
      sessionId,
      success,
      error
    };

    this._detectionHistory.push(record);
    
    // 履歴が長くなりすぎた場合は古いものを削除
    if (this._detectionHistory.length > 100) {
      this._detectionHistory = this._detectionHistory.slice(-50);
    }
  }
}