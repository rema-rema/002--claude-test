# Order Management Server

Claude Code Hooks統合による階層的セッション間自動連携システム

## 🎯 概要

Order Management Serverは、Claude Code Hooksを活用して複数のClaude Codeセッションを階層的に管理し、人間の介入なしに5-10セッション同時並行開発を実現するシステムです。

### 主要機能

- **Claude Code Hooks統合**: PostToolUse, PreToolUse, Notification, Stop hookの完全対応
- **Queue/Active管理**: 依頼書のライフサイクル管理と衝突回避
- **階層的セッション管理**: 最高責任者→統括→管理署→実装セッションの階層制御
- **Discord通信統合**: dpコマンドを経由した自動メッセージ送信
- **自動完了検知**: TodoWrite、Serena完了パターンの自動検知と報告書生成

## 🏗️ システム構成

```
order-management-server/
├── src/                    # コアモジュール
│   ├── hooks_manager.py    # Claude Code Hooks統合
│   ├── queue_manager.py    # 依頼書管理システム
│   ├── session_manager.py  # セッション階層管理
│   └── discord_proxy.py    # Discord通信プロキシ
├── config/                 # 設定ファイル
│   └── settings.py         # 統合設定管理
├── tests/                  # テストスイート
├── queue/                  # 待機中の依頼書
├── active/                 # 処理中の依頼書
├── completed/              # 完了済み依頼書
└── templates/              # 依頼書テンプレート
```

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
cd order-management-server
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# .env ファイルを作成
CC_DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
CC_DISCORD_CHANNEL_ID="YOUR_CHANNEL_ID"
MAX_CONCURRENT_SESSIONS=10
SESSION_TIMEOUT=3600
QUEUE_CHECK_INTERVAL=5
```

### 3. 初期設定

```bash
# Hooks設定ファイル作成
python -c "
import json
from pathlib import Path

config = {
    'hooks': {
        'PostToolUse': [{
            'name': 'completion-detector',
            'matcher': 'TodoWrite.*completed|mcp__serena__think_about_whether_you_are_done',
            'handler': {
                'type': 'script',
                'path': './scripts/completion-handler.py'
            }
        }],
        'PreToolUse': [{
            'name': 'resource-checker',
            'matcher': '.*',
            'handler': {
                'type': 'script', 
                'path': './scripts/resource-checker.py'
            }
        }]
    }
}

Path('config/hooks.json').write_text(json.dumps(config, indent=2))
print('Hooks configuration created')
"
```

## 📋 使用方法

### 基本的なワークフロー

1. **セッション作成**:
```python
from src.session_manager import SessionManager, SessionRole

sm = SessionManager()

# 階層的セッション作成
sm.create_session("supreme", SessionRole.SUPREME)
sm.create_session("coordinator", SessionRole.COORDINATOR, parent_id="supreme")
sm.create_session("manager", SessionRole.MANAGER, parent_id="coordinator")
sm.create_session("worker", SessionRole.WORKER, parent_id="manager")
```

2. **作業依頼書作成**:
```python
from src.queue_manager import QueueManager, WorkRequest, Priority
from datetime import datetime, timedelta

qm = QueueManager()

request = WorkRequest(
    request_id=qm.generate_request_id("session_a", "auth_implementation"),
    session_id="session_a",
    target_session="worker", 
    priority=Priority.HIGH,
    task_description="Implement user authentication system",
    requirements=["security", "testing", "documentation"],
    deadline=datetime.now() + timedelta(hours=24),
    dependencies=["database_setup"],
    created_at=datetime.now(),
    status=RequestStatus.QUEUED,
    metadata={"project": "user_management"}
)

qm.enqueue_request(request)
```

3. **完了検知の設定**:
```python
from src.hooks_manager import HooksManager, HookContext

hm = HooksManager()

# PostToolUse完了検知
context = HookContext(
    hook_type='PostToolUse',
    session_id='worker',
    tool_name='TodoWrite',
    tool_output='{"status": "completed"}',
    timestamp=datetime.now(),
    metadata={}
)

result = hm.process_hook(context)
if result.success and result.actions:
    print(f"Completion detected: {len(result.actions)} actions")
```

4. **Discord通知送信**:
```python
from src.discord_proxy import DiscordProxy

dp = DiscordProxy()

# 作業依頼書送信
success = dp.send_work_request('1', {
    'request_id': 'REQ_001',
    'priority': 'High',
    'task_description': 'Implement authentication',
    'requirements': ['security'],
    'dependencies': []
})

# /resumeコマンド自動実行
dp.execute_resume_command('1')
```

### Claude Code Hooks統合

システムは以下のHookパターンを自動検知します：

```python
COMPLETION_PATTERNS = {
    "todo_completion": r'"status":\s*"completed"',
    "serena_completion": r'mcp__serena__think_about_whether_you_are_done',
    "implementation_done": r'実装完了|implementation\s+completed',
    "test_success": r'All\s+tests\s+passed|テスト成功',
    "build_success": r'Build\s+successful|ビルド成功'
}
```

## 🧪 テスト実行

### ユニットテスト
```bash
# 全テスト実行
python -m pytest tests/ -v

# 特定コンポーネントのテスト
python -m pytest tests/test_hooks_manager.py -v
python -m pytest tests/test_queue_manager.py -v
python -m pytest tests/test_session_manager.py -v
python -m pytest tests/test_discord_proxy.py -v
```

### インテグレーションテスト
```bash
# 簡易統合テスト
python tests/test_simple_integration.py

# 完全統合テスト
python -m pytest tests/test_integration.py -v
```

### カバレッジレポート
```bash
python -m pytest --cov=src --cov-report=html tests/
```

## 📊 監視とログ

### セッション状態確認
```python
sm = SessionManager()

# セッション階層の表示
hierarchy = sm.get_session_hierarchy()
print(f"Total sessions: {hierarchy['total_sessions']}")
print(f"Active sessions: {hierarchy['active_sessions']}")

# セッション状態確認
for session_id in ["supreme", "coordinator", "manager", "worker"]:
    status = sm.get_session_status(session_id)
    print(f"{session_id}: {status.value}")
```

### キュー状態確認
```python
qm = QueueManager()

status = qm.get_queue_status()
print(f"Queue: {status['queue']} requests")
print(f"Active: {status['active']} requests") 
print(f"Completed: {status['completed']} requests")

# 依頼書履歴
history = qm.get_request_history(limit=5)
for req in history:
    print(f"Request {req['request_id']}: {req['result']['status']}")
```

### Discord通信履歴
```python
dp = DiscordProxy()

# コマンド履歴確認
history = dp.get_command_history(limit=10)
for cmd in history:
    print(f"{cmd['timestamp']}: {cmd['data']['message_type']} -> Session {cmd['data']['session_id']}")

# セッション通信状態
status = dp.get_session_status()
print(f"Active sessions: {status['active_sessions']}")
print(f"Last activity: {status['last_activity']}")
```

## 🛠️ 運用ガイド

### システム起動
```bash
# Order Management Server起動
python -c "
from src.session_manager import SessionManager
from src.queue_manager import QueueManager
from src.hooks_manager import HooksManager

print('🚀 Order Management Server starting...')

# システム初期化
sm = SessionManager()
qm = QueueManager() 
hm = HooksManager()

print('✅ All components initialized')
print('🎯 Ready for session automation')
"
```

### トラブルシューティング

#### セッションが応答しない場合
```python
# セッション復旧
sm = SessionManager()
sm.update_session_status("stuck_session", SessionStatus.ERROR)

# タスクを親にエスカレート
task = Task(...)  # 問題のタスク
sm.escalate_to_parent("stuck_session", task)
```

#### 依頼書の処理が停滞している場合
```python
# 衝突チェック
qm = QueueManager()
conflicts = qm.check_conflicts("target_session")

for conflict in conflicts:
    print(f"Conflict: {conflict.conflict_type} - {conflict.description}")
    print(f"Resolution: {conflict.resolution_suggestion}")

# 強制完了またはキャンセル
qm.cancel_request("stuck_request_id")
```

#### Discord通信エラーの場合
```python
# 通信履歴確認
dp = DiscordProxy()
history = dp.get_command_history()

failed_commands = [cmd for cmd in history if not cmd['success']]
print(f"Failed commands: {len(failed_commands)}")

# セッションマッピング再読み込み
dp._load_session_mapping()
```

## 🔒 セキュリティ

- **セッション分離**: 各セッションは独立したディレクトリ空間で動作
- **アクセス制御**: セッション間のファイルアクセスは制限
- **ログマスキング**: 機密情報の自動マスキング機能
- **コマンドフィルタリング**: 危険なコマンドの実行ブロック

## 📈 パフォーマンス

- **並行処理**: 最大10セッション同時処理対応
- **メモリ効率**: セッションあたり2GB制限
- **応答性**: 依頼書処理3秒以内、セッション間通信1秒以内
- **スケーラビリティ**: 大量依頼書対応（1000+リクエスト）

## 📚 API リファレンス

詳細なAPIドキュメントは以下を参照：

- [HooksManager API](docs/api/hooks_manager.md)
- [QueueManager API](docs/api/queue_manager.md)
- [SessionManager API](docs/api/session_manager.md)
- [DiscordProxy API](docs/api/discord_proxy.md)

## 🤝 貢献

1. フォークしてブランチ作成
2. 機能実装・テスト追加
3. コードレビュー（100回仮想会議・80点以上）
4. プルリクエスト作成

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

## 📞 サポート

- Issues: [GitHub Issues](https://github.com/your-org/order-management-server/issues)
- Documentation: [Wiki](https://github.com/your-org/order-management-server/wiki)
- Chat: Discord #order-management-server

---

**開発チーム**: Session Automation Team  
**最終更新**: 2025-08-29  
**バージョン**: 1.0.0