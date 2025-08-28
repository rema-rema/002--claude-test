# Playwright-Discord マルチチャンネル通知システム 詳細設計書

## 1. アーキテクチャ設計

### 1.1 システム全体構成
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Discord       │    │  claude-discord  │    │  Playwright     │
│   Channel 1,2,3 │◄──►│  bridge-server   │◄──►│  Test Runner    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌──────────────────┐
                       │ マルチチャンネル  │
                       │ 通知システム      │ 
                       └──────────────────┘
```

### 1.2 コンポーネント設計

#### 1.2.1 ChannelConfigManager
**責務**: .env設定の動的解析とチャンネル管理
```javascript
class ChannelConfigManager {
  // .envからチャンネル設定をパース
  static parseChannelConfig()
  
  // セッション番号からチャンネルID取得
  getChannelBySession(sessionId)
  
  // 全チャンネル一覧取得
  getAllChannels()
  
  // 設定変更の自動検出
  watchConfigChanges()
}
```

#### 1.2.2 MultiChannelNotifier
**責務**: チャンネル固有の通知処理
```javascript
class MultiChannelNotifier {
  // チャンネル特定通知送信
  async sendToChannel(channelId, message, attachments)
  
  // 複数チャンネル一斉通知
  async broadcastToChannels(channelIds, message)
  
  // 通知失敗時のリトライ処理
  async retryNotification(channelId, payload)
}
```

#### 1.2.3 PlaywrightChannelReporter
**責務**: Playwright統合とチャンネル情報連携
```javascript
class PlaywrightChannelReporter extends PlaywrightReporter {
  // 現在実行セッションの検出
  detectCurrentSession()
  
  // テスト結果のチャンネル特定処理
  async routeTestResults(testResult, channelId)
  
  // 失敗時の包括的通知処理
  async handleTestFailure(test, result, targetChannel)
}
```

## 2. データ設計

### 2.1 環境変数構造
```bash
# 既存フォーマット（維持）
CC_DISCORD_CHANNEL_ID_001=1111111111111111111
CC_DISCORD_CHANNEL_ID_002=1405815779198369903  
CC_DISCORD_CHANNEL_ID_003=3333333333333333333
CC_DISCORD_CHANNEL_ID_004=4444444444444444444

# 新規追加設定
PLAYWRIGHT_CHANNEL_DETECTION_MODE=auto
PLAYWRIGHT_NOTIFICATION_TIMEOUT=5000
```

### 2.2 内部データ構造
```javascript
// チャンネル設定オブジェクト
const channelConfig = {
  "001": "1111111111111111111",
  "002": "1405815779198369903",
  "003": "3333333333333333333", 
  "004": "4444444444444444444"
};

// 通知ペイロード構造
const notificationPayload = {
  channelId: "1405815779198369903",
  sessionId: "002",
  testResult: {
    summary: {...},
    failures: [...],
    artifacts: [...]
  },
  timestamp: "2025-08-28T07:30:00Z"
};
```

## 3. API設計

### 3.1 内部API仕様

#### getCurrentChannelId()
```javascript
/**
 * 現在実行セッションのチャンネルIDを取得
 * @returns {string} Discord Channel ID
 * @throws {Error} セッション検出失敗時
 */
function getCurrentChannelId(): string
```

#### sendTestNotification()
```javascript
/**
 * テスト結果の通知送信
 * @param {Object} testResult テスト結果オブジェクト
 * @param {string} channelId 送信先チャンネルID
 * @param {Array} attachments 添付ファイル配列
 * @returns {Promise<Object>} 送信結果
 */
async function sendTestNotification(testResult, channelId, attachments): Promise<Object>
```

## 4. シーケンス設計

### 4.1 正常系フロー
```
User -> Discord -> Claude Code -> Playwright -> Test Execution
                                     ↓
                              Session Detection
                                     ↓  
                              Channel ID Lookup
                                     ↓
                              Result Notification -> Discord Channel
```

### 4.2 失敗時フロー  
```
Playwright Test Failure -> Error Analysis -> Artifact Collection
                              ↓
                        Channel Detection
                              ↓
                     Comprehensive Failure Report -> Target Channel
                              ↓
                        Approval Request Creation
```

## 5. エラーハンドリング設計

### 5.1 エラー分類と対応

#### E001: チャンネル検出失敗
- **原因**: セッション情報取得エラー
- **対応**: デフォルトチャンネルへフォールバック

#### E002: 通知送信失敗
- **原因**: Discord API制限、ネットワーク障害
- **対応**: 指数バックオフによるリトライ

#### E003: 設定パースエラー  
- **原因**: .env設定不正、フォーマット違反
- **対応**: 既知の設定でフォールバック動作

### 5.2 ログ設計
```javascript
// 構造化ログフォーマット
{
  timestamp: "2025-08-28T07:30:00Z",
  level: "INFO|WARN|ERROR",
  component: "ChannelConfigManager|MultiChannelNotifier|PlaywrightChannelReporter",
  sessionId: "002",
  channelId: "1405815779198369903", 
  message: "詳細メッセージ",
  metadata: {...}
}
```

## 6. パフォーマンス設計

### 6.1 処理時間目標
- チャンネル検出: < 50ms
- 設定パース: < 100ms  
- 通知送信: < 3000ms
- 総処理時間: < 5000ms

### 6.2 最適化戦略
- **設定キャッシュ**: .env変更検出までキャッシュ保持
- **並列処理**: 複数添付ファイルの並列アップロード
- **コネクションプール**: Discord API呼び出し最適化

## 7. セキュリティ設計

### 7.1 アクセス制御
- チャンネル権限の事前検証
- 不正セッションからのアクセス拒否

### 7.2 データ保護
- チャンネルID情報の暗号化保存
- ログ内機密情報のマスキング

## 8. 拡張性設計

### 8.1 新チャンネル対応
```javascript
// プラガブル設定パーサー
interface ChannelConfigParser {
  parseConfig(envVars): ChannelConfig;
}

class EnvFileParser implements ChannelConfigParser { ... }
class JsonConfigParser implements ChannelConfigParser { ... }
```

### 8.2 通知チャネル拡張
```javascript  
// 抽象通知インターフェース
interface NotificationChannel {
  send(message, attachments): Promise<Result>;
}

class DiscordNotifier implements NotificationChannel { ... }
class SlackNotifier implements NotificationChannel { ... }
```

## 9. テスト設計

### 9.1 単体テスト範囲
- ChannelConfigManager.parseChannelConfig()
- MultiChannelNotifier.sendToChannel()  
- PlaywrightChannelReporter.detectCurrentSession()

### 9.2 統合テスト範囲
- 複数セッション並列実行
- 通信障害時のフォールバック
- 設定変更時の動的反映

### 9.3 E2Eテスト範囲
- 実際のDiscord環境での通知確認
- マルチチャンネル同時実行検証

---

**文書バージョン**: v1.0  
**作成日**: 2025-08-28  
**最終更新**: 2025-08-28