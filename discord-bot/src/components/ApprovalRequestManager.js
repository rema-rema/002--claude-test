/**
 * Discord承認依頼管理システム
 * Playwright テストエラー時の承認依頼を管理し、24時間タイムアウトを処理
 * 
 * @author AI Assistant
 * @date 2025-08-25
 */

import { v4 as uuidv4 } from 'uuid';
import { RetryHandler } from './RetryHandler.js';

/**
 * 承認ステータス列挙型
 * @readonly
 * @enum {string}
 */
export const ApprovalStatus = {
  PENDING: 'PENDING',
  APPROVED: 'APPROVED', 
  REJECTED: 'REJECTED',
  EXPIRED: 'EXPIRED'
};

/**
 * 24時間をミリ秒で表現した定数
 * @constant {number}
 */
const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

/**
 * 承認依頼管理クラス
 * Discord内での承認フローを管理し、24時間自動タイムアウトを処理
 */
export class ApprovalRequestManager {
  constructor() {
    /**
     * 承認依頼のストレージ
     * @type {Map<string, ApprovalRequest>}
     * @private
     */
    this.requests = new Map();
    
    /**
     * タイムアウト処理用のタイマー管理
     * @type {Map<string, NodeJS.Timeout>}
     * @private
     */
    this.timeouts = new Map();
    
    /**
     * TASK-302: 再試行ハンドラー
     * @type {RetryHandler}
     * @private
     */
    this.retryHandler = new RetryHandler();
  }

  /**
   * 新しい承認依頼を作成
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @param {string[]} fixSuggestions - 修正提案の配列
   * @param {string} requesterUserId - 依頼者のユーザーID
   * @returns {Promise<ApprovalRequest>} 作成された承認依頼
   */
  async createRequest(testName, errorMessage, fixSuggestions, requesterUserId) {
    // 入力値検証を分離されたメソッドで実行
    this._validateCreateRequestParams(testName, errorMessage, fixSuggestions, requesterUserId);

    const requestId = uuidv4();
    const now = new Date();
    const expiresAt = new Date(now.getTime() + TWENTY_FOUR_HOURS_MS);

    const request = this._buildApprovalRequest(requestId, testName, errorMessage, fixSuggestions, requesterUserId, now, expiresAt);
    
    this.requests.set(requestId, request);
    this._scheduleTimeout(requestId);

    return request;
  }

  /**
   * 承認依頼作成時のパラメータ検証
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @param {string[]} fixSuggestions - 修正提案の配列
   * @param {string} requesterUserId - 依頼者のユーザーID
   * @private
   */
  _validateCreateRequestParams(testName, errorMessage, fixSuggestions, requesterUserId) {
    if (!testName || typeof testName !== 'string') {
      throw new Error('テスト名は必須で文字列である必要があります');
    }
    if (!errorMessage || typeof errorMessage !== 'string') {
      throw new Error('エラーメッセージは必須で文字列である必要があります');
    }
    if (!Array.isArray(fixSuggestions)) {
      throw new Error('修正提案は配列である必要があります');
    }
    if (!requesterUserId || typeof requesterUserId !== 'string') {
      throw new Error('依頼者ユーザーIDは必須で文字列である必要があります');
    }
  }

  /**
   * 承認依頼オブジェクトを構築
   * @param {string} requestId - 依頼ID
   * @param {string} testName - テスト名
   * @param {string} errorMessage - エラーメッセージ
   * @param {string[]} fixSuggestions - 修正提案の配列
   * @param {string} requesterUserId - 依頼者のユーザーID
   * @param {Date} now - 現在時刻
   * @param {Date} expiresAt - 期限時刻
   * @returns {ApprovalRequest} 構築された承認依頼
   * @private
   */
  _buildApprovalRequest(requestId, testName, errorMessage, fixSuggestions, requesterUserId, now, expiresAt) {
    return {
      id: requestId,
      testName,
      errorMessage,
      fixSuggestions,
      requesterUserId,
      status: ApprovalStatus.PENDING,
      createdAt: now,
      expiresAt,
      respondedAt: null,
      discordThreadId: null,
      discordMessageId: null
    };
  }

  /**
   * タイムアウトスケジュールを設定
   * @param {string} requestId - 依頼ID
   * @private
   */
  _scheduleTimeout(requestId) {
    const timeoutId = setTimeout(() => {
      this._expireRequest(requestId);
    }, TWENTY_FOUR_HOURS_MS);

    this.timeouts.set(requestId, timeoutId);
  }

  /**
   * 承認依頼を取得
   * @param {string} requestId - 依頼ID
   * @returns {Promise<ApprovalRequest|null>} 承認依頼またはnull
   */
  async getRequest(requestId) {
    if (!requestId || typeof requestId !== 'string') {
      throw new Error('依頼IDは必須で文字列である必要があります');
    }

    return this.requests.get(requestId) || null;
  }

  /**
   * 全ての承認依頼を取得
   * @param {Object} [options={}] - フィルタリングオプション
   * @param {ApprovalStatus} [options.status] - ステータスフィルタ
   * @param {string} [options.requesterUserId] - 依頼者フィルタ
   * @returns {Promise<ApprovalRequest[]>} 承認依頼の配列
   */
  async getAllRequests(options = {}) {
    let requests = Array.from(this.requests.values());

    if (options.status) {
      requests = requests.filter(r => r.status === options.status);
    }

    if (options.requesterUserId) {
      requests = requests.filter(r => r.requesterUserId === options.requesterUserId);
    }

    return requests;
  }

  /**
   * 承認・拒否レスポンスを処理
   * @param {string} requestId - 依頼ID
   * @param {boolean} approved - 承認フラグ（true: 承認, false: 拒否）
   * @param {string} [comment] - コメント
   * @returns {Promise<ApprovalResponse>} 処理結果
   */
  async processResponse(requestId, approved, comment = '') {
    // 入力値検証
    this._validateResponseParams(requestId, approved);
    
    const request = this._getRequestForProcessing(requestId);
    
    // ステータス更新
    const processedAt = new Date();
    request.status = approved ? ApprovalStatus.APPROVED : ApprovalStatus.REJECTED;
    request.respondedAt = processedAt;

    // タイムアウトタイマーをクリア
    this._clearTimeout(requestId);

    return {
      requestId,
      approved,
      comment,
      processedAt,
      success: true
    };
  }

  /**
   * レスポンス処理時のパラメータ検証
   * @param {string} requestId - 依頼ID
   * @param {boolean} approved - 承認フラグ
   * @private
   */
  _validateResponseParams(requestId, approved) {
    if (!requestId || typeof requestId !== 'string') {
      throw new Error('依頼IDは必須で文字列である必要があります');
    }

    if (typeof approved !== 'boolean') {
      throw new Error('承認フラグはboolean型である必要があります');
    }
  }

  /**
   * 処理対象の依頼を取得・検証
   * @param {string} requestId - 依頼ID
   * @returns {ApprovalRequest} 処理対象の依頼
   * @private
   */
  _getRequestForProcessing(requestId) {
    const request = this.requests.get(requestId);
    if (!request) {
      throw new Error('指定された依頼IDが見つかりません');
    }

    if (request.status !== ApprovalStatus.PENDING) {
      throw new Error('この依頼は既に処理済みです');
    }

    return request;
  }

  /**
   * タイムアウトタイマーをクリア
   * @param {string} requestId - 依頼ID
   * @private
   */
  _clearTimeout(requestId) {
    const timeoutId = this.timeouts.get(requestId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.timeouts.delete(requestId);
    }
  }

  /**
   * 期限切れの依頼を自動処理
   * @returns {Promise<string[]>} 処理された依頼IDの配列
   */
  async processTimeouts() {
    const now = new Date();
    const expiredIds = [];

    for (const [requestId, request] of this.requests.entries()) {
      if (request.status === ApprovalStatus.PENDING && request.expiresAt < now) {
        this._expireRequest(requestId);
        expiredIds.push(requestId);
      }
    }

    return expiredIds;
  }

  /**
   * 承認依頼を削除
   * @param {string} requestId - 依頼ID
   * @returns {Promise<boolean>} 削除成功フラグ
   */
  async deleteRequest(requestId) {
    if (!requestId || typeof requestId !== 'string') {
      throw new Error('依頼IDは必須で文字列である必要があります');
    }

    const existed = this.requests.has(requestId);
    if (existed) {
      this._clearTimeout(requestId);
      this.requests.delete(requestId);
    }

    return existed;
  }

  /**
   * Discord関連情報を更新（スレッドID、メッセージID）
   * TASK-302: 再試行機能付き
   * @param {string} requestId - 依頼ID
   * @param {string} threadId - DiscordスレッドID
   * @param {string} messageId - DiscordメッセージID
   * @returns {Promise<boolean>} 更新成功フラグ
   */
  async updateDiscordInfo(requestId, threadId, messageId) {
    return await this.retryHandler.retry(async () => {
      if (!requestId || typeof requestId !== 'string') {
        throw new Error('依頼IDは必須で文字列である必要があります');
      }

      if (!threadId || typeof threadId !== 'string') {
        throw new Error('スレッドIDは必須で文字列である必要があります');
      }

      if (!messageId || typeof messageId !== 'string') {
        throw new Error('メッセージIDは必須で文字列である必要があります');
      }

      const request = this.requests.get(requestId);
      if (!request) {
        throw new Error('指定された依頼IDが見つかりません');
      }

      request.discordThreadId = threadId;
      request.discordMessageId = messageId;

      return true;
    });
  }

  /**
   * 依頼を期限切れ状態に変更（内部メソッド）
   * @param {string} requestId - 依頼ID
   * @private
   */
  _expireRequest(requestId) {
    const request = this.requests.get(requestId);
    if (request && request.status === ApprovalStatus.PENDING) {
      request.status = ApprovalStatus.EXPIRED;
      request.respondedAt = new Date();
    }

    // タイムアウトタイマーをクリア（統一メソッドを使用）
    this._clearTimeout(requestId);
  }
}