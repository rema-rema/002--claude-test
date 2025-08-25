/**
 * Discord スレッド管理システム
 * 承認依頼専用スレッドの作成・管理・ライフサイクル制御
 * 
 * ApprovalRequestManager (MS-A1) との統合により、
 * 24時間自動アーカイブとDiscord連携を実現
 * 
 * @author AI Assistant  
 * @date 2025-08-25
 */

import { ApprovalRequestManager } from './ApprovalRequestManager.js';

/**
 * スレッドステータス列挙型
 * @readonly
 * @enum {string}
 */
export const ThreadStatus = {
  ACTIVE: 'ACTIVE',
  ARCHIVED: 'ARCHIVED', 
  LOCKED: 'LOCKED',
  DELETED: 'DELETED'
};

/**
 * 時間関連定数
 * @constant {number}
 */
const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;
const DEFAULT_RETRY_ATTEMPTS = 3;
const DEFAULT_RETRY_DELAY = 1000;
const DEFAULT_AUTO_ARCHIVE_DURATION = 1440; // 24時間（分）

/**
 * Discord Thread 管理クラス
 * 承認依頼専用のスレッド作成・管理・自動アーカイブを提供
 */
export class ThreadManager {
  /**
   * ThreadManager コンストラクタ
   * @param {Object} options - 設定オプション
   * @param {Client} options.client - Discord.js Client インスタンス
   * @param {string} options.channelId - 親チャンネルID
   * @param {number} options.autoArchiveDuration - 自動アーカイブ時間（分）
   * @param {ApprovalRequestManager} [options.approvalManager] - ApprovalRequestManager インスタンス
   * @param {number} [options.retryAttempts=3] - リトライ回数
   * @param {number} [options.retryDelay=1000] - リトライ間隔（ミリ秒）
   */
  constructor(options) {
    // 必須パラメータ検証
    this._validateConstructorOptions(options);
    
    this.client = options.client;
    this.channelId = options.channelId;
    this.autoArchiveDuration = options.autoArchiveDuration || DEFAULT_AUTO_ARCHIVE_DURATION;
    this.approvalManager = options.approvalManager;
    this.retryAttempts = options.retryAttempts || DEFAULT_RETRY_ATTEMPTS;
    this.retryDelay = options.retryDelay || DEFAULT_RETRY_DELAY;
    
    /**
     * アクティブなスレッドの管理Map
     * @type {Map<string, ApprovalThread>}
     * @private
     */
    this.activeThreads = new Map();
  }

  /**
   * コンストラクタオプションの検証
   * @param {Object} options - 検証対象オプション
   * @private
   */
  _validateConstructorOptions(options) {
    if (!options) {
      throw new Error('ThreadManager options は必須です');
    }
    if (!options.client) {
      throw new Error('Discord Client インスタンスは必須です');
    }
    if (!options.channelId || typeof options.channelId !== 'string') {
      throw new Error('有効なチャンネルIDは必須です');
    }
  }

  /**
   * 承認依頼専用スレッドを作成
   * @param {Object} request - スレッド作成リクエスト
   * @param {string} request.approvalRequestId - 承認依頼ID
   * @param {string} request.testName - テスト名
   * @param {string} request.errorSummary - エラー概要
   * @param {string[]} request.fixSuggestions - 修正提案配列
   * @param {string} request.requesterUserId - 依頼者ユーザーID
   * @param {string} [request.urgency='MEDIUM'] - 緊急度
   * @returns {Promise<CreateThreadResponse>} スレッド作成結果
   */
  async createApprovalThread(request) {
    // 入力値検証
    this._validateCreateThreadRequest(request);

    // チャンネル存在確認
    await this._validateChannelExists();

    try {
      // Discord スレッド作成フロー
      const thread = await this._executeThreadCreation(request);
      
      // ApprovalRequestManager統合
      const message = await this._integrateWithApprovalManager(thread, request);

      // スレッド情報をローカルで管理
      const approvalThread = this._createApprovalThread(thread, request);
      this.activeThreads.set(thread.id, approvalThread);

      return this._buildCreateThreadResponse(thread, message);

    } catch (error) {
      console.error('スレッド作成エラー:', error);
      throw error;
    }
  }

  /**
   * Discord スレッド作成フローを実行
   * @param {Object} request - スレッド作成リクエスト
   * @returns {Promise<Thread>} 作成されたスレッド
   * @private
   */
  async _executeThreadCreation(request) {
    const threadName = this._buildThreadName(request.testName);
    return await this._createDiscordThread(threadName);
  }

  /**
   * ApprovalRequestManager との統合処理
   * @param {Thread} thread - 作成されたスレッド
   * @param {Object} request - スレッド作成リクエスト
   * @returns {Promise<Message>} 送信されたメッセージ
   * @private
   */
  async _integrateWithApprovalManager(thread, request) {
    // 初期メッセージ送信
    const initialMessage = this._buildInitialMessage(request);
    const message = await thread.send(initialMessage);

    // ApprovalRequestManager に Discord 情報を関連付け
    if (this.approvalManager) {
      await this.approvalManager.updateDiscordInfo(
        request.approvalRequestId,
        thread.id,
        message.id
      );
    }

    return message;
  }

  /**
   * スレッド作成レスポンスを構築
   * @param {Thread} thread - 作成されたスレッド
   * @param {Message} message - 送信されたメッセージ
   * @returns {CreateThreadResponse} レスポンス
   * @private
   */
  _buildCreateThreadResponse(thread, message) {
    return {
      threadId: thread.id,
      messageId: message.id,
      threadUrl: `https://discord.com/channels/guild/${this.channelId}/${thread.id}`,
      success: true,
      createdAt: new Date()
    };
  }

  /**
   * 承認完了時のスレッド処理
   * @param {ApprovalRequest} approvalRequest - 承認依頼
   * @param {ApprovalResponse} approvalResponse - 承認応答
   * @returns {Promise<void>}
   */
  async onApprovalCompleted(approvalRequest, approvalResponse) {
    const threadId = approvalRequest.discordThreadId;
    if (!threadId) {
      console.warn('承認依頼にスレッドIDが関連付けられていません:', approvalRequest.id);
      return;
    }

    try {
      // 完了メッセージ送信
      const completionMessage = this._buildCompletionMessage(approvalResponse);
      await this.client.channels.threads.send(threadId, completionMessage);

      // スレッドを自動アーカイブ
      await this.client.channels.threads.setArchived(
        threadId, 
        true, 
        '承認完了のため自動アーカイブ'
      );

      // ローカル管理データ更新
      const thread = this.activeThreads.get(threadId);
      if (thread) {
        thread.status = ThreadStatus.ARCHIVED;
        thread.archived = true;
      }

    } catch (error) {
      console.error('承認完了時スレッド処理エラー:', error);
      throw error;
    }
  }

  /**
   * スレッド情報を取得
   * @param {string} threadId - スレッドID
   * @returns {Promise<ApprovalThread|null>} スレッド情報またはnull
   */
  async getThread(threadId) {
    // ローカルキャッシュから取得
    const cached = this.activeThreads.get(threadId);
    if (cached) {
      return cached;
    }

    // Discord APIから取得
    try {
      const discordThread = await this.client.channels.threads.fetch(threadId);
      if (discordThread) {
        const approvalThread = {
          id: discordThread.id,
          parentId: discordThread.parentId,
          name: discordThread.name,
          ownerId: discordThread.ownerId,
          createdAt: discordThread.createdAt,
          expiresAt: new Date(discordThread.createdAt.getTime() + TWENTY_FOUR_HOURS_MS),
          archived: discordThread.archived,
          locked: discordThread.locked,
          status: discordThread.archived ? ThreadStatus.ARCHIVED : ThreadStatus.ACTIVE
        };
        
        this.activeThreads.set(threadId, approvalThread);
        return approvalThread;
      }
    } catch (error) {
      console.error('スレッド取得エラー:', error);
    }

    return null;
  }

  /**
   * 全スレッドを取得
   * @param {Object} [options={}] - フィルタリングオプション
   * @returns {Promise<ApprovalThread[]>} スレッド配列
   */
  async getAllThreads(options = {}) {
    return Array.from(this.activeThreads.values());
  }

  /**
   * スレッドステータスを更新
   * @param {string} threadId - スレッドID
   * @param {ThreadStatus} status - 新しいステータス
   * @returns {Promise<boolean>} 更新成功フラグ
   */
  async updateThreadStatus(threadId, status) {
    const thread = this.activeThreads.get(threadId);
    if (!thread) {
      throw new Error('指定されたスレッドが見つかりません');
    }

    try {
      switch (status) {
        case ThreadStatus.ARCHIVED:
          await this.client.channels.threads.setArchived(threadId, true);
          thread.archived = true;
          break;
        case ThreadStatus.LOCKED:
          await this.client.channels.threads.setLocked(threadId, true);
          thread.locked = true;
          break;
        case ThreadStatus.ACTIVE:
          await this.client.channels.threads.setArchived(threadId, false);
          thread.archived = false;
          break;
      }

      thread.status = status;
      return true;

    } catch (error) {
      console.error('スレッドステータス更新エラー:', error);
      throw error;
    }
  }

  /**
   * スレッドにメッセージを送信
   * @param {string} threadId - スレッドID
   * @param {string} content - メッセージ内容
   * @returns {Promise<Message>} 送信されたメッセージ
   */
  async sendMessage(threadId, content) {
    try {
      return await this.client.channels.threads.send(threadId, content);
    } catch (error) {
      console.error('メッセージ送信エラー:', error);
      throw error;
    }
  }

  /**
   * 期限切れスレッドを処理
   * @returns {Promise<string[]>} 処理されたスレッドIDの配列
   */
  async processExpiredThreads() {
    const now = new Date();
    const expiredIds = [];

    for (const [threadId, thread] of this.activeThreads.entries()) {
      if (thread.status === ThreadStatus.ACTIVE && thread.expiresAt < now) {
        try {
          await this.updateThreadStatus(threadId, ThreadStatus.ARCHIVED);
          expiredIds.push(threadId);
        } catch (error) {
          console.error(`スレッド期限切れ処理エラー (${threadId}):`, error);
        }
      }
    }

    return expiredIds;
  }

  /**
   * 関連する承認依頼を取得
   * @param {string} threadId - スレッドID
   * @returns {Promise<ApprovalRequest|null>} 承認依頼またはnull
   */
  async getLinkedApprovalRequest(threadId) {
    const thread = this.activeThreads.get(threadId);
    if (!thread || !thread.approvalRequestId) {
      return null;
    }

    if (this.approvalManager) {
      return await this.approvalManager.getRequest(thread.approvalRequestId);
    }

    return null;
  }

  /**
   * 初期メッセージテンプレートを構築
   * @param {Object} request - スレッド作成リクエスト
   * @returns {string} フォーマットされたメッセージ
   */
  buildInitialMessage(request) {
    return this._buildInitialMessage(request);
  }

  /**
   * 作成リクエストの入力値検証
   * @param {Object} request - 検証対象リクエスト
   * @private
   */
  _validateCreateThreadRequest(request) {
    if (!request.approvalRequestId || typeof request.approvalRequestId !== 'string') {
      throw new Error('承認依頼IDは必須です');
    }
    if (!request.testName || typeof request.testName !== 'string') {
      throw new Error('テスト名は必須です');
    }
    if (!request.errorSummary || typeof request.errorSummary !== 'string') {
      throw new Error('エラー概要は必須です');
    }
    if (!Array.isArray(request.fixSuggestions)) {
      throw new Error('修正提案は配列である必要があります');
    }
    if (!request.requesterUserId || typeof request.requesterUserId !== 'string') {
      throw new Error('依頼者ユーザーIDは必須です');
    }
  }

  /**
   * チャンネル存在確認
   * @private
   */
  async _validateChannelExists() {
    const channel = this.client.channels.cache.get(this.channelId);
    if (!channel) {
      throw new Error('チャンネルが見つかりません');
    }
  }

  /**
   * スレッド名を構築
   * @param {string} testName - テスト名
   * @returns {string} フォーマットされたスレッド名
   * @private
   */
  _buildThreadName(testName) {
    return `🔧 修正作業: ${testName}`;
  }

  /**
   * Discord スレッドを作成
   * @param {string} threadName - スレッド名
   * @returns {Promise<Thread>} 作成されたスレッド
   * @private
   */
  async _createDiscordThread(threadName) {
    return await this.client.channels.threads.create({
      name: threadName,
      autoArchiveDuration: this.autoArchiveDuration,
      type: 'GUILD_PUBLIC_THREAD',
      reason: '承認依頼スレッド作成'
    });
  }

  /**
   * 初期メッセージを構築
   * @param {Object} request - スレッド作成リクエスト
   * @returns {string} フォーマットされた初期メッセージ
   * @private
   */
  _buildInitialMessage(request) {
    const expiresAt = new Date(Date.now() + TWENTY_FOUR_HOURS_MS);
    const fixSuggestionsList = request.fixSuggestions.map(s => `• ${s}`).join('\n');
    
    return `🔧 **テスト修正依頼** - #${request.approvalRequestId}

**テスト名**: \`${request.testName}\`
**エラー概要**: ${request.errorSummary}

**修正提案**:
${fixSuggestionsList}

**操作方法**:
✅ 承認: \`!approve ${request.approvalRequestId} [コメント]\`
❌ 拒否: \`!reject ${request.approvalRequestId} [理由]\`
📝 進捗: このスレッド内で作業進捗を報告してください

⏰ **自動期限**: ${expiresAt.toLocaleString()} (24時間後)
🎯 **依頼者**: <@${request.requesterUserId}>`;
  }

  /**
   * 完了メッセージを構築
   * @param {ApprovalResponse} response - 承認応答
   * @returns {string} フォーマットされた完了メッセージ
   * @private
   */
  _buildCompletionMessage(response) {
    const result = response.approved ? '✅ 承認' : '❌ 拒否';
    const processTime = response.processedAt ? 
      `${Math.round((response.processedAt - new Date()) / (1000 * 60))} 分` : 
      '不明';

    return `🎉 **修正作業完了** - #${response.requestId}

**結果**: ${result}
**処理時間**: ${processTime}
**完了理由**: ${response.comment || 'コメントなし'}

このスレッドは自動的にアーカイブされます。`;
  }

  /**
   * ApprovalThread オブジェクトを作成
   * @param {Thread} discordThread - Discord Thread
   * @param {Object} request - スレッド作成リクエスト
   * @returns {ApprovalThread} 作成されたApprovalThread
   * @private
   */
  _createApprovalThread(discordThread, request) {
    return {
      id: discordThread.id,
      parentId: this.channelId,
      name: discordThread.name,
      ownerId: discordThread.ownerId,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + TWENTY_FOUR_HOURS_MS),
      archived: false,
      locked: false,
      status: ThreadStatus.ACTIVE,
      approvalRequestId: request.approvalRequestId
    };
  }
}