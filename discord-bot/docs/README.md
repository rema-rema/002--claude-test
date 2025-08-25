# Discord Bot 開発ドキュメント

## ディレクトリ構成

```
discord-bot/docs/
├── README.md                    # このファイル
└── implementation/              # 実装ドキュメント
    └── approval-system/         # 承認システム機能
        └── TASK-001/           # TestFailureAnalyzer実装
            ├── TestFailureAnalyzer-requirements.md
            ├── TestFailureAnalyzer-testcases.md
            └── TDD-completion-summary.md
```

## ドキュメント管理ルール

### 機能別ディレクトリ構成
各Discord Bot機能は独立したフォルダで管理：

- **approval-system/**: テスト失敗承認システム関連
- **notification-system/**: 通知システム関連（将来追加予定）
- **capacity-monitoring/**: 容量監視システム関連（将来追加予定）

### タスク別ドキュメント
各TASKの実装ドキュメントは以下の構成で管理：

- **requirements.md**: TDD要件定義書
- **testcases.md**: テストケース定義書  
- **completion-summary.md**: 実装完了サマリー

### 更新ルール
- 実装完了時に必ずドキュメントを更新
- 機能追加時は適切な機能フォルダに配置
- 他機能との混在を避ける明確な分離を維持

## 関連ファイル

### 実装ファイル
- `../src/components/`: コンポーネント実装
- `../src/tests/`: テストファイル
- `../src/test-results/`: テスト実行結果

### 設計ファイル  
- `../../spec/kairo/discord-approval-system/`: 全体設計書