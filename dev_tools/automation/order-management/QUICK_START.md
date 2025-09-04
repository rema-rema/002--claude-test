# Order Management Server - クイックスタート

## 🚀 5分で始める Order Management

### Step 1: セットアップ（1分）

```bash
# プロジェクトディレクトリに移動
cd order-management-server

# 自動セットアップ実行
./start-order-management.sh
```

これだけで完了！スクリプトが自動的に：
- 依存関係をインストール
- 設定ファイルを作成
- ディレクトリ構造を初期化
- システム動作確認

### Step 2: 基本的な使い方（2分）

#### 👤 Session A が Session B に作業依頼する場合

```python
# Python で実行
from src.discord_proxy import DiscordProxy

dp = DiscordProxy()

# Session B に依頼書送信
dp.send_work_request('2', {
    'request_id': 'AUTH_TASK_001',
    'priority': 'High',
    'task_description': 'ユーザー認証機能を実装してください',
    'requirements': ['JWT認証', 'セッション管理'],
    'dependencies': []
})

# /resume コマンドを自動実行
dp.execute_resume_command('2')
```

#### 📨 Discord での確認

1. Session B (Discord) で依頼書が届く
2. `/resume` が自動実行される
3. Session B で作業開始
4. 完了すると自動で報告書が送信される

### Step 3: 実際のシナリオ例（2分）

#### 🎯 シナリオ: 「認証機能を3人で分担開発」

```python
# 複数セッションに一斉配布
from src.queue_manager import QueueManager, WorkRequest, Priority
from src.discord_proxy import DiscordProxy
from datetime import datetime, timedelta

qm = QueueManager()
dp = DiscordProxy()

# 3つのタスクを作成
tasks = [
    {
        'target': '2',  # Session B
        'task': 'JWT認証ライブラリの実装',
        'requirements': ['セキュリティ', 'テスト']
    },
    {
        'target': '3',  # Session C  
        'task': 'ログイン画面のフロントエンド',
        'requirements': ['レスポンシブ', 'UX']
    },
    {
        'target': '4',  # Session D
        'task': 'データベース設計・マイグレーション',
        'requirements': ['パフォーマンス', 'スケーラビリティ']
    }
]

# 一斉配布
for i, task_info in enumerate(tasks):
    # 依頼書作成
    request = WorkRequest(
        request_id=f'AUTH_PROJECT_{i+1:02d}',
        session_id='session_a',
        target_session=f'session_{task_info["target"]}',
        priority=Priority.HIGH,
        task_description=task_info['task'],
        requirements=task_info['requirements'],
        deadline=datetime.now() + timedelta(hours=8),
        dependencies=[],
        created_at=datetime.now(),
        status='QUEUED',
        metadata={'project': 'authentication', 'phase': 'implementation'}
    )
    
    # エンキュー・送信
    qm.enqueue_request(request)
    dp.send_work_request(task_info['target'], request.__dict__)
    dp.execute_resume_command(task_info['target'])
    
    print(f"✅ Task {i+1} sent to Session {task_info['target']}")

# 結果: 3つのSessionで並行開発開始！
```

## 🛠️ よくある使用パターン

### パターン1: 単純依頼
```python
dp = DiscordProxy()
dp.send_work_request('2', {
    'request_id': 'SIMPLE_001',
    'task_description': '簡単なタスクをお願いします'
})
```

### パターン2: 緊急タスク
```python
dp.send_work_request('2', {
    'request_id': 'URGENT_001', 
    'priority': 'Critical',
    'task_description': '緊急バグ修正',
    'deadline': '2時間以内'
})
dp.execute_resume_command('2')  # 即座に開始
```

### パターン3: 階層エスカレーション
```python
from src.session_manager import SessionManager, Task

sm = SessionManager()

# 複雑なタスク（Workerでは難しい）
complex_task = Task(
    task_id='COMPLEX_001',
    description='システム全体アーキテクチャ見直し',
    priority=1
)

# WorkerからManagerにエスカレート
sm.escalate_to_parent('worker_session', complex_task)
```

## 📊 システム監視

### セッション状態確認
```python
from src.session_manager import SessionManager

sm = SessionManager()
hierarchy = sm.get_session_hierarchy()

print(f"Total sessions: {hierarchy['total_sessions']}")
print(f"Active sessions: {hierarchy['active_sessions']}")
```

### キュー状況確認
```python
from src.queue_manager import QueueManager

qm = QueueManager()
status = qm.get_queue_status()

print(f"Queue: {status['queue']} requests")
print(f"Active: {status['active']} requests")  
print(f"Completed: {status['completed']} requests")
```

### Discord通信履歴
```python
from src.discord_proxy import DiscordProxy

dp = DiscordProxy()
history = dp.get_command_history(limit=5)

for cmd in history:
    print(f"{cmd['timestamp']}: {cmd['data']['message_type']}")
```

## 🎯 実践的なワークフロー

### 毎日の開発フロー

```python
#!/usr/bin/env python3
# daily_workflow.py

def morning_startup():
    """朝の一斉起動"""
    dp = DiscordProxy()
    sessions = ['2', '3', '4']
    
    for session in sessions:
        dp.send_message(session, "🌅 おはようございます！今日もよろしくお願いします")

def assign_daily_tasks():
    """日次タスク配布"""
    tasks = [
        "今日の新機能実装",
        "昨日のバグ修正", 
        "テストケース追加"
    ]
    
    dp = DiscordProxy()
    sessions = ['2', '3', '4']
    
    for i, task in enumerate(tasks):
        session = sessions[i % len(sessions)]
        dp.send_work_request(session, {
            'request_id': f'DAILY_{datetime.now().strftime("%Y%m%d")}_{i+1:02d}',
            'task_description': task,
            'priority': 'Medium'
        })

def evening_report():
    """夕方の進捗確認"""
    qm = QueueManager()
    status = qm.get_queue_status()
    
    dp = DiscordProxy()
    dp.broadcast_message(f"""📊 今日の進捗報告
    
✅ 完了: {status['completed']} タスク
🔄 進行中: {status['active']} タスク  
📋 待機中: {status['queue']} タスク

お疲れ様でした！""")

# 実行
if __name__ == "__main__":
    morning_startup()
    assign_daily_tasks() 
    # 夕方に evening_report() を実行
```

## ⚡ トラブルシューティング

### 💡 よくある問題と解決法

#### Q: 依頼書が送信されない
```python
# 解決法1: セッションマッピング確認
dp = DiscordProxy()
print(dp.session_mapping)  # {'1': 'channel_id', ...}

# 解決法2: Bridge連携確認
print(dp.bridge_base_dir)  # ../claude-discord-bridge-server
```

#### Q: セッションが応答しない
```python
# 解決法: セッション状態確認・復旧
sm = SessionManager()
status = sm.get_session_status('problem_session')

if status == 'ERROR':
    sm.update_session_status('problem_session', 'IDLE')
    print("Session recovered")
```

#### Q: キューが詰まっている
```python
# 解決法: 衝突チェック・解決
qm = QueueManager()
conflicts = qm.check_conflicts('busy_session')

for conflict in conflicts:
    print(f"Conflict: {conflict.description}")
    print(f"Solution: {conflict.resolution_suggestion}")
```

## 🔧 カスタマイズ

### 独自のHookパターン追加

`config/hooks.json` を編集：

```json
{
  "patterns": {
    "custom_completion": "カスタム完了パターン",
    "my_pattern": "独自のパターン.*完了"
  }
}
```

### セッション能力カスタマイズ

```python
from src.session_manager import SessionCapabilities

custom_caps = SessionCapabilities(
    can_implement=True,
    can_review=True, 
    can_test=False,
    specializations=["frontend", "react"]
)

sm.create_session("frontend_specialist", SessionRole.WORKER, capabilities=custom_caps)
```

## 📈 次のステップ

1. **詳細ドキュメント**: `README.md` を読む
2. **使用例集**: `USAGE_EXAMPLES.md` で5つのシナリオを学ぶ
3. **テスト実行**: `python tests/test_simple_integration.py`
4. **本格運用**: Discord認証情報を `.env` に設定

---

**🎉 これで Order Management Server の基本的な使い方は完璧です！**

何か問題があれば、`./start-order-management.sh` でシステム状態を再確認してください。