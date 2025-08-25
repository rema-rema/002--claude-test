# Playwright Discord通知システム - タスク分解（修正版）

## フェーズ1: 基盤準備

### Task 1.1: ディレクトリ・ファイル構造作成
**優先度**: High  
**工数**: 0.5h  
**担当**: 開発者  

- [ ] `discord-bot/src/reporters/` ディレクトリ作成
- [ ] `discord-bot/src/services/` ディレクトリ作成  
- [ ] `discord-bot/src/utils/` ディレクトリ作成
- [ ] `discord-bot/__tests__/` ディレクトリ作成（単体・結合テスト用）

**成果物**: discord-bot内のフォルダ構造

### Task 1.2: package.json依存関係追加・スクリプト設定
**優先度**: High  
**工数**: 0.5h  
**担当**: 開発者

- [ ] Jest依存関係追加（テスト用）
- [ ] 必要なNode.js標準ライブラリの確認
- [ ] `npm run capacity-check` スクリプト追加（discord-bot/src/utils/capacity-monitor.js実行）

**成果物**: package.json更新

## フェーズ2: 容量監視機能（独立性が高いため先行）

### Task 2.1: CapacityMonitor基本クラス実装
**優先度**: Medium  
**工数**: 2h  
**担当**: 開発者

- [ ] `discord-bot/src/utils/capacity-monitor.js` 作成
- [ ] `analyzeDirectory()` メソッド実装
- [ ] `formatBytes()` メソッド実装  
- [ ] `checkCapacity()` メソッド実装

**成果物**: CapacityMonitorクラス

### Task 2.2: CLI実行機能実装
**優先度**: Medium  
**工数**: 1h  
**担当**: 開発者

- [ ] `runCLI()` メソッド実装
- [ ] コンソール出力フォーマット実装
- [ ] コマンドライン実行対応（`node discord-bot/src/utils/capacity-monitor.js`）

**成果物**: `npm run capacity-check` 実行可能

### Task 2.3: CapacityMonitor単体テスト
**優先度**: Medium  
**工数**: 1.5h  
**担当**: 開発者

- [ ] `formatBytes()` 境界値テスト（0バイト、1024バイト等、モック使用）
- [ ] `checkCapacity()` 閾値判定テスト（モック使用）
- [ ] エラーハンドリングテスト

**成果物**: `discord-bot/__tests__/utils/capacity-monitor.test.js`

## フェーズ3: Discord通知サービス

### Task 3.1: DiscordNotificationService基本クラス
**優先度**: High  
**工数**: 2.5h  
**担当**: 開発者

- [ ] `discord-bot/src/services/discord-notification-service.js` 作成
- [ ] 同一フォルダ内の既存DiscordBotクラス（./discord-bot.js）のインポート・統合
- [ ] `initialize()` メソッド実装
- [ ] `formatSummaryMessage()` メソッド実装

**成果物**: Discord通知サービス基本機能

### Task 3.2: ファイル添付・サイズ制限機能
**優先度**: High  
**工数**: 2h  
**担当**: 開発者

- [ ] `isValidFileSize()` メソッド実装（25MB制限）
- [ ] `sendFailureDetails()` メソッド実装
- [ ] 大容量ファイル時のパス表示機能
- [ ] ファイル存在チェック・エラーハンドリング

**成果物**: ファイル添付機能

### Task 3.3: DiscordNotificationService単体テスト
**優先度**: Medium  
**工数**: 2h  
**担当**: 開発者

- [ ] `formatSummaryMessage()` 境界値テスト（0件、全失敗等）
- [ ] `isValidFileSize()` 境界値テスト（25MB制限、モック使用）
- [ ] エラー時の動作テスト

**成果物**: `discord-bot/__tests__/services/discord-notification-service.test.js`

## フェーズ4: Playwrightレポーター統合

### Task 4.1: PlaywrightDiscordReporter基本実装
**優先度**: High  
**工数**: 2h  
**担当**: 開発者

- [ ] `discord-bot/src/reporters/playwright-discord-reporter.js` 作成
- [ ] `onEnd()` フック実装
- [ ] `createTestSummary()` メソッド実装
- [ ] DiscordNotificationService（../services/discord-notification-service.js）との連携

**成果物**: Playwrightカスタムレポーター

### Task 4.2: テスト証跡ファイル収集機能
**優先度**: High  
**工数**: 1.5h  
**担当**: 開発者

- [ ] `collectFailureArtifacts()` メソッド実装
- [ ] スクリーンショット検索ロジック
- [ ] 動画ファイル検索ロジック
- [ ] ファイルパス解析処理

**成果物**: 証跡ファイル収集機能

### Task 4.3: playwright.config.js統合
**優先度**: High  
**工数**: 0.5h  
**担当**: 開発者

- [ ] 既存設定にカスタムレポーター追加（'./discord-bot/src/reporters/playwright-discord-reporter.js'）
- [ ] 既存機能との競合回避確認
- [ ] 設定の動作確認

**成果物**: playwright.config.js更新

## フェーズ5: テスト・検証

### Task 5.1: 結合テスト実装
**優先度**: High  
**工数**: 3h  
**担当**: 開発者

- [ ] 成功時フローの結合テスト
- [ ] 失敗時フロー（SS・動画添付）の結合テスト  
- [ ] 大容量ファイル処理の結合テスト
- [ ] エラー耐性の結合テスト

**成果物**: `discord-bot/__tests__/integration/playwright-discord.test.js`

### Task 5.2: 手動検証・デバッグ
**優先度**: High  
**工数**: 2h  
**担当**: 開発者

- [ ] 実際のPlaywrightテスト実行での動作確認
- [ ] Discord通知の実際の送信確認
- [ ] 容量監視バッチの実行確認
- [ ] エラーケースの動作確認

**成果物**: 動作確認レポート

### Task 5.3: ドキュメント作成
**優先度**: Medium  
**工数**: 1h  
**担当**: 開発者

- [ ] 使用方法の簡易ドキュメント作成
- [ ] 設定方法の説明
- [ ] トラブルシューティング情報

**成果物**: 使用ドキュメント

## 修正後のファイル構成

```
discord-bot/
├── src/
│   ├── claude-service.js          # 既存
│   ├── config.js                  # 既存  
│   ├── discord-bot.js             # 既存
│   ├── index.js                   # 既存
│   ├── reporters/                 # 新規
│   │   └── playwright-discord-reporter.js
│   ├── services/                  # 新規
│   │   └── discord-notification-service.js
│   └── utils/                     # 新規
│       └── capacity-monitor.js
└── __tests__/                     # 新規（テスト用）
    ├── utils/
    │   └── capacity-monitor.test.js
    ├── services/
    │   └── discord-notification-service.test.js
    └── integration/
        └── playwright-discord.test.js

playwright.config.js               # レポーターパス修正
package.json                       # スクリプト追加
```

## 設定修正内容

### playwright.config.js
```javascript
export default defineConfig({
  // ... 既存設定
  reporter: [
    ['html'],
    ['./discord-bot/src/reporters/playwright-discord-reporter.js']  // 修正
  ],
  // ... 既存設定
});
```

### package.json
```json
{
  "scripts": {
    "capacity-check": "node discord-bot/src/utils/capacity-monitor.js"  // 修正
  }
}
```

## 実装順序・依存関係

```
Phase 1 (基盤) 
    ↓
Phase 2 (容量監視) ← discord-bot内で独立実装可能
    ↓
Phase 3 (Discord通知) ← 既存DiscordBotクラスと同一フォルダで統合
    ↓  
Phase 4 (Playwright統合)
    ↓
Phase 5 (テスト・検証)
```

## 総工数見積り
- **開発**: 約18時間
- **テスト**: 約6.5時間  
- **検証・ドキュメント**: 約3時間
- **総計**: 約27.5時間

## 修正による利点

1. **既存システムとの統合が自然**: 同一フォルダ内での相対インポート
2. **プロジェクト全体の汚染回避**: discord-bot内で機能が完結
3. **保守性向上**: 関連コードが近い場所に配置
4. **依存関係の簡素化**: 既存の設定・認証情報を直接利用可能

この修正版で進めますか？