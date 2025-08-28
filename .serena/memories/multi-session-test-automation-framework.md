# Multi-Session Test Automation Framework

## テスト自動化アーキテクチャ

### テストランナー構成
- **メインテストランナー**: `test-runner.py` - テスト実行制御とレポート生成
- **個別テストスイート**: TC-001～TC-006の個別テスト実装
- **テストユーティリティ**: 共通処理・セッション操作・Discord API テスト支援

### 実装済みテストスイート
1. **TC-001**: 基本機能テスト（セッション並行稼働、独立性確認）
2. **TC-002**: ファイル管理テスト（attachments分離、競合解決）
3. **TC-003**: セッション管理テスト（CLI操作、状態確認）
4. **TC-004**: 復旧・エラー処理テスト（自動復旧、エラーハンドリング）
5. **TC-005**: パフォーマンステスト（応答時間、リソース制限）
6. **TC-006**: 拡張性テスト（動的セッション追加、スケーラビリティ）

### 自動実行可能な範囲
- **セッション作成・停止**: 完全自動化
- **ファイル操作テスト**: 完全自動化
- **CLI コマンドテスト**: 完全自動化
- **パフォーマンス測定**: 完全自動化（メモリ・CPU・応答時間）
- **Discord API テスト**: モック環境で自動化

### 手動確認が必要な項目
- **実際のDiscord送信**: Discord APIの実際の送信確認
- **ユーザー体験**: 実際のUI/UX確認
- **24時間安定性**: 長時間稼働テスト

## テスト実行方法
```bash
cd claude-discord-bridge-server
python tests/test-runner.py --all
python tests/test-runner.py --suite TC-001
python tests/test-runner.py --performance-only
```