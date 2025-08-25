# Discord承認システム - 統合設計書

## 📁 **ディレクトリ構成**

```
spec/kairo/discord-approval-system/
├── README.md                           # このファイル（全体ガイド）
├── requirements.md                     # プロジェクト要件定義
├── design.md                          # アーキテクチャ・技術設計
├── tasks.md                           # タスク管理・進捗追跡・並列開発マイルストーン
├── track-coordination/                # 並列開発トラック調整
│   ├── TRACK-B-LATEST-PROMPT.md      # Track B最新プロンプト
│   └── TRACK-C-LATEST-PROMPT.md      # Track C最新プロンプト
└── implementation/                    # 実装詳細ドキュメント
    ├── TASK-001/                     # TestFailureAnalyzer
    ├── TASK-002/                     # ErrorPatternMatcher
    ├── TASK-003/                     # FixSuggestionGenerator
    ├── TASK-101/                     # ApprovalRequestManager  
    └── TASK-102/                     # ThreadManager
```

## 🎯 **設計書の読み方・優先順位**

### **1. 全体把握フェーズ**
```
requirements.md    → プロジェクト目的・スコープ理解
design.md         → アーキテクチャ・技術選定理解
tasks.md          → 現在の進捗・次のタスク確認
```

### **2. 並列開発参加フェーズ**
```
tasks.md  → 並列開発マイルストーン・自分の担当Track確認
track-coordination/TRACK-B-LATEST-PROMPT.md → Track B作業指示
track-coordination/TRACK-C-LATEST-PROMPT.md → Track C作業指示
```

### **3. 実装フェーズ**
```
implementation/TASK-xxx/  → 詳細TDD要件確認
(実装開始)
tasks.md                                → 進捗更新・完了報告
```

## 🔄 **並列開発ワークフロー**

### **Track A (Discord統合)**
- MS-A1: ApprovalRequestManager ✅
- MS-A2: ThreadManager ✅  
- MS-A3: DiscordNotificationService拡張 (継続中)
- MS-A4: ClaudeCodeIntegrator実装 (未開始)

### **Track B (基盤コンポーネント)**
- MS-B1: ErrorPatternMatcher ✅
- MS-B2: FixSuggestionGenerator ✅
- MS-B3: PlaywrightDiscordReporter統合 ✅
- **TASK-302**: エラーハンドリング強化 (統合テスト修正中)

### **Track C (Track A継承)**
- Track Aから引き継ぎ、MS-A3, MS-A4を継続実装

## 🎯 **現在の状況**

**進捗**: Phase 2 - 85%完成
**次のアクション**: 
- Track B: 統合テスト安定化 (8/20→18/20成功)
- Track C: MS-A3, MS-A4実装継続

**完成目標**: Phase 2 - 48時間以内完成

## 📋 **ドキュメント更新ルール**

1. **実装完了時**: `tasks.md`の進捗を必ず更新
2. **新機能追加**: `design.md`にアーキテクチャ影響を記載
3. **Track調整時**: `track-coordination/`でコミュニケーション
4. **要件変更時**: `requirements.md`を最初に更新

---

**重要**: このフォルダがDiscord承認システムの**唯一の公式設計書**です。他の場所にある設計書との混乱を避けるため、必ずここを参照してください。