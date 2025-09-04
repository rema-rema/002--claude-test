# Multi-Session Test Automation Framework

## 概要

Claude-Discord-Bridge Multi-Session Support の自動テストフレームワークです。SC-001～SC-006の成功基準を検証する包括的なテストスイートを提供します。

## テストスイート構成

### TC-001: Basic Functionality Tests (SC-001)
- **ファイル**: `tc001_basic_functionality.py`
- **対象**: 基本機能テスト
- **テストケース**: 
  - 複数セッション同時稼働
  - セッション独立したClaude Code操作
  - セッション別attachmentディレクトリ
  - dpコマンドセッション指定
  - 動的セッション追加

### TC-002: File Management Tests (SC-002 File Aspect)
- **ファイル**: `tc002_file_management.py`
- **対象**: ファイル管理テスト
- **テストケース**:
  - セッション別ディレクトリ分離
  - ファイル競合検出・解決
  - クロスセッション・アクセス防止
  - 重複ファイル処理
  - セッション別クリーンアップ

### TC-003: Session Management Tests (SC-004)
- **ファイル**: `tc003_session_management.py`
- **対象**: セッション管理テスト
- **テストケース**:
  - vai statusマルチセッション対応
  - セッション別ファイルクリーンアップ
  - 24時間連続稼働安定性（短縮版）
  - Session 1互換性維持
  - CLIセッション管理コマンド

### TC-004: Recovery and Error Handling Tests (SC-002 Recovery Aspect)
- **ファイル**: `tc004_recovery_error.py`
- **対象**: 復旧・エラー処理テスト
- **テストケース**:
  - 自動セッション復旧
  - 無効セッション操作エラーハンドリング
  - セッション障害検出・通知
  - 手動復旧コマンド
  - 復旧ログ・監査証跡

### TC-005: Performance Tests (SC-003)
- **ファイル**: `tc005_performance.py`
- **対象**: パフォーマンステスト
- **テストケース**:
  - Discord応答時間（3秒以内）
  - ファイル処理パフォーマンス（8MBファイル10秒以内）
  - セッション切替パフォーマンス（1秒以内）
  - メモリ使用量監視（2GB制限）
  - 同時ファイル処理（20ファイル同時）

### TC-006: Scalability Tests (SC-006)
- **ファイル**: `tc006_scalability.py`
- **対象**: 拡張性テスト
- **テストケース**:
  - 動的セッション追加（Session 5）
  - 自動session_Nディレクトリ作成
  - sessions.json動的エントリ追加
  - マルチセッション・スケーリング（10セッションまで）
  - 並行セッション操作検証

## 実行方法

### 全テスト実行
```bash
cd claude-discord-bridge-server
python tests/test-runner.py --all
```

### 個別テストスイート実行
```bash
python tests/test-runner.py --suite TC-001
python tests/test-runner.py --suite TC-005
```

### クイックテスト（長時間テスト除外）
```bash
python tests/test-runner.py --all --quick
```

### パフォーマンステストのみ
```bash
python tests/test-runner.py --performance-only
```

### 個別テストスイート直接実行
```bash
python tests/tc001_basic_functionality.py
python tests/tc005_performance.py
```

## テスト環境

### 前提条件
- Python 3.7+
- psutil ライブラリ（リソース監視用）
- tmux（セッション管理用）
- 既存のClaude-Discord-Bridge環境

### テスト用セッション
- **Session 1**: 既存セッション（互換性テスト）
- **Session 2-4**: 基本テスト用セッション
- **Session 5+**: 拡張性テスト用セッション

### テストデータ構造
```
tests/
├── temp/           # テンポラリファイル
├── logs/           # テストログ
├── reports/        # テストレポート
└── backups/        # 設定バックアップ
```

## 出力・レポート

### HTMLレポート
- ファイル: `tests/reports/test_report_YYYYMMDD_HHMMSS.html`
- 内容: 総合テスト結果、個別スイート詳細、パフォーマンスメトリクス

### JSONレポート  
- ファイル: `tests/reports/test_report_YYYYMMDD_HHMMSS.json`
- 内容: プログラマティックアクセス用のテスト結果データ

### ログファイル
- テストランナーログ: `tests/logs/test_runner.log`
- スイート別ログ: `tests/logs/{suite_name}_log_timestamp.txt`
- パフォーマンスメトリクス: `tests/logs/{suite_name}_metrics_timestamp.json`

## 成功基準マッピング

| Success Criteria | Test Suite | 評価方法 |
|------------------|------------|----------|
| SC-001: 基本機能 | TC-001 | 4セッション同時稼働、セッション独立性 |
| SC-002: セキュリティ・復旧 | TC-002, TC-004 | ファイル分離、復旧機能 |
| SC-003: パフォーマンス | TC-005 | 応答時間、リソース制限 |
| SC-004: 運用性・安定性 | TC-003 | CLI機能、24時間安定性 |
| SC-005: 監視・ログ | TC-004 | ログ記録、監査証跡 |
| SC-006: 拡張性検証 | TC-006 | 動的追加、10セッション拡張 |

## 品質しきい値

### 成功率
- **Critical Tests (TC-001, TC-003)**: 95%以上必須
- **Performance Tests (TC-005)**: 90%以上推奨
- **Scalability Tests (TC-006)**: 85%以上許容

### 実行時間
- **全テスト実行**: 15分以内（--quick）/ 30分以内（--all）
- **個別スイート**: 5分以内
- **パフォーマンステスト**: 10分以内

### リソース使用量
- **メモリ使用量**: システム全体90%未満
- **CPU使用量**: テスト実行中90%未満
- **ディスク使用量**: attachments 1GB未満

## トラブルシューティング

### よくある問題

1. **tmux セッション作成失敗**
   ```bash
   # tmux インストール確認
   which tmux
   
   # tmux サービス確認
   tmux list-sessions
   ```

2. **permissions エラー**
   ```bash
   # attachments ディレクトリ権限確認
   ls -la attachments/
   
   # 権限修正
   chmod -R 755 attachments/
   ```

3. **sessions.json 破損**
   ```bash
   # バックアップから復旧
   cp tests/temp/sessions_backup_*.json config/sessions.json
   ```

### デバッグモード
```bash
# 詳細ログ出力で実行
python tests/test-runner.py --suite TC-001 --verbose

# 単体テスト実行
python -m pytest tests/tc001_basic_functionality.py -v
```

## 拡張・カスタマイズ

### 新規テストケース追加
1. 対応するTC-XXXファイルにテストメソッドを追加
2. `run_tests()` メソッドのtestsリストに追加
3. テストランナーの`test_suites` ディクショナリに登録

### カスタムメトリクス追加
1. `test_utils.py` の `TestResult` クラスにメトリクスフィールド追加
2. 対応するテストケースでメトリクス収集処理実装
3. レポート生成にメトリクス表示追加

### 新規テストスイート追加
1. `tc_XXX_new_suite.py` ファイル作成
2. `TestFramework` 基底クラスから継承
3. `test-runner.py` の `test_suites` に登録

## ライセンス・保守

このテストフレームワークはClaude-Discord-Bridge Multi-Session Supportプロジェクトの一部として開発されています。

- **作成日**: 2025-08-28
- **バージョン**: 1.0.0
- **保守担当**: Claude Code AI開発チーム