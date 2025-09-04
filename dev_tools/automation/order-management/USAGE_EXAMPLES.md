# Order Management Server - 使用例集

## 🎯 基本的な使用例

### 例1: 単純な2セッション間連携

```python
#!/usr/bin/env python3
"""
基本例: Session A → Session B の作業依頼フロー
"""

from pathlib import Path
from datetime import datetime, timedelta
from src.session_manager import SessionManager, SessionRole
from src.queue_manager import QueueManager, WorkRequest, Priority, RequestStatus
from src.discord_proxy import DiscordProxy

def basic_two_session_workflow():
    """2セッション間の基本的な作業フロー"""
    
    # 1. システムコンポーネント初期化
    sm = SessionManager()
    qm = QueueManager()
    dp = DiscordProxy()
    
    # 2. セッション作成
    session_a = sm.create_session("session_a", SessionRole.COORDINATOR)
    session_b = sm.create_session("session_b", SessionRole.WORKER)
    
    print(f"✅ Created sessions: {session_a.session_id}, {session_b.session_id}")
    
    # 3. 作業依頼書作成
    work_request = WorkRequest(
        request_id=qm.generate_request_id("session_a", "user_auth"),
        session_id="session_a",
        target_session="session_b",
        priority=Priority.HIGH,
        task_description="ユーザー認証機能を実装してください",
        requirements=[
            "JWT トークンベース認証",
            "パスワードハッシュ化（bcrypt）",
            "セッション管理機能",
            "ログイン・ログアウト API"
        ],
        deadline=datetime.now() + timedelta(hours=8),
        dependencies=["database_setup"],
        created_at=datetime.now(),
        status=RequestStatus.QUEUED,
        metadata={
            "project": "user_management",
            "complexity": "medium",
            "estimated_hours": 6
        }
    )
    
    # 4. 依頼書をキューに追加
    request_id = qm.enqueue_request(work_request)
    print(f"✅ Enqueued request: {request_id}")
    
    # 5. Session B用のDiscord通知送信
    request_data = {
        'request_id': request_id,
        'priority': 'High',
        'deadline': work_request.deadline.isoformat(),
        'task_description': work_request.task_description,
        'requirements': work_request.requirements,
        'dependencies': work_request.dependencies
    }
    
    success = dp.send_work_request('2', request_data)  # Session B = session 2
    
    if success:
        print("✅ Work request sent to Discord session 2")
        
        # 6. /resume コマンド自動実行
        dp.execute_resume_command('2')
        print("✅ Resume command sent to session 2")
        
        return request_id
    else:
        print("❌ Failed to send work request")
        return None

if __name__ == "__main__":
    basic_two_session_workflow()
```

### 例2: 階層的セッション管理

```python
#!/usr/bin/env python3
"""
階層例: Supreme → Coordinator → Manager → Worker の4階層管理
"""

from src.session_manager import SessionManager, SessionRole, Task
from datetime import datetime

def hierarchical_session_management():
    """階層的セッション管理の例"""
    
    sm = SessionManager()
    
    # 1. 階層的セッション作成
    # Supreme (最高責任者)
    supreme = sm.create_session("supreme_session", SessionRole.SUPREME)
    
    # Coordinator (統括) - Supremeの下
    coordinator = sm.create_session(
        "coordinator_session", 
        SessionRole.COORDINATOR,
        parent_id="supreme_session"
    )
    
    # Manager (管理署) - Coordinatorの下
    manager_a = sm.create_session(
        "manager_a_session",
        SessionRole.MANAGER, 
        parent_id="coordinator_session"
    )
    
    manager_b = sm.create_session(
        "manager_b_session",
        SessionRole.MANAGER,
        parent_id="coordinator_session"
    )
    
    # Worker (実装セッション) - 各Managerの下
    worker_a1 = sm.create_session(
        "worker_a1_session",
        SessionRole.WORKER,
        parent_id="manager_a_session"
    )
    
    worker_a2 = sm.create_session(
        "worker_a2_session", 
        SessionRole.WORKER,
        parent_id="manager_a_session"
    )
    
    worker_b1 = sm.create_session(
        "worker_b1_session",
        SessionRole.WORKER,
        parent_id="manager_b_session"
    )
    
    # 2. 階層構造確認
    hierarchy = sm.get_session_hierarchy()
    print(f"Total sessions: {hierarchy['total_sessions']}")
    
    def print_hierarchy(node, level=0):
        indent = "  " * level
        role = sm.sessions[node['id']].role.value
        status = node['status']
        print(f"{indent}├─ {node['id']} ({role}) [{status}]")
        for child in node['children']:
            print_hierarchy(child, level + 1)
    
    print("\n📊 Session Hierarchy:")
    for root in hierarchy['hierarchy']:
        print_hierarchy(root)
    
    # 3. 複雑なタスクのエスカレーション例
    complex_task = Task(
        task_id="COMPLEX_ARCH_TASK",
        description="システム全体のアーキテクチャ設計見直し",
        priority=1,
        assigned_to=None,
        created_by="supreme_session",
        created_at=datetime.now(),
        deadline=None,
        dependencies=["requirement_analysis"],
        status="escalated"
    )
    
    # Worker → Manager → Coordinator とエスカレート
    print("\n🔼 Task Escalation Demo:")
    
    # Worker A1に最初に割り当て（失敗想定）
    print("Attempting to assign complex task to worker_a1...")
    success = sm.assign_task(complex_task, "worker_a1_session")
    
    if success:
        print("✅ Task assigned to worker_a1")
        # 実際にはこの複雑なタスクはWorkerには難しすぎる想定
        
        # Manager A にエスカレート
        print("Escalating to manager_a...")
        escalate_success = sm.escalate_to_parent("worker_a1_session", complex_task)
        
        if escalate_success:
            print("✅ Task escalated to manager_a")
            
            # さらにCoordinatorにエスカレート
            print("Escalating to coordinator...")
            sm.escalate_to_parent("manager_a_session", complex_task)
            print("✅ Task escalated to coordinator")
    
    # 4. セッション状態の表示
    print("\n📈 Current Session Status:")
    for session_id, session in sm.sessions.items():
        current_task = session.current_task or "None"
        print(f"  {session_id}: {session.status.value} (Task: {current_task})")
    
    sm.shutdown()

if __name__ == "__main__":
    hierarchical_session_management()
```

### 例3: 完了検知とDiscord通知

```python
#!/usr/bin/env python3
"""
完了検知例: Claude Code Hooks統合による自動完了検知
"""

from src.hooks_manager import HooksManager, HookContext, CompletionSignal
from src.discord_proxy import DiscordProxy
from datetime import datetime

def completion_detection_workflow():
    """完了検知からDiscord通知までのワークフロー"""
    
    hm = HooksManager()
    dp = DiscordProxy()
    
    # 1. 様々な完了パターンのシミュレート
    completion_scenarios = [
        {
            "name": "TodoWrite完了",
            "output": '{"todos": [{"content": "Implement auth", "status": "completed"}]}',
            "session_id": "worker_session_1"
        },
        {
            "name": "Serena完了確認", 
            "output": "実行結果: mcp__serena__think_about_whether_you_are_done",
            "session_id": "worker_session_2"
        },
        {
            "name": "実装完了宣言",
            "output": "実装完了: ユーザー認証モジュールが完成しました。",
            "session_id": "worker_session_3"
        },
        {
            "name": "テスト成功",
            "output": "All tests passed: 15 tests, 0 failures",
            "session_id": "worker_session_4" 
        }
    ]
    
    print("🔍 Completion Detection Demo:\n")
    
    for scenario in completion_scenarios:
        print(f"Scenario: {scenario['name']}")
        
        # 2. Hook コンテキスト作成
        context = HookContext(
            hook_type='PostToolUse',
            session_id=scenario['session_id'], 
            tool_name='TodoWrite' if 'TodoWrite' in scenario['name'] else 'CustomTool',
            tool_output=scenario['output'],
            timestamp=datetime.now(),
            metadata={'scenario': scenario['name']}
        )
        
        # 3. Hook処理実行
        result = hm.process_hook(context)
        
        if result.success and result.actions:
            print(f"  ✅ Completion detected: {len(result.actions)} actions")
            
            # 4. 各アクションを処理
            for action in result.actions:
                if action['type'] == 'send_report':
                    report = action['report']
                    
                    print(f"  📋 Report generated:")
                    print(f"    Session: {report['session_id']}")
                    print(f"    Type: {report['completion_type']}")
                    print(f"    Summary: {report['summary']}")
                    
                    # 5. Discord通知送信
                    success = dp.send_completion_report('1', report)
                    
                    if success:
                        print("  📤 Report sent to Discord")
                    else:
                        print("  ❌ Failed to send report to Discord")
        else:
            print(f"  ➡️  No completion detected")
        
        print()
    
    # 6. コマンド履歴確認
    print("📜 Discord Command History:")
    history = dp.get_command_history()
    for i, cmd in enumerate(history[-5:], 1):  # 最後の5件
        print(f"  {i}. {cmd['data']['message_type']} -> Session {cmd['data']['session_id']}")
        print(f"     Success: {cmd['success']}")

if __name__ == "__main__":
    completion_detection_workflow()
```

### 例4: 大規模並行処理

```python
#!/usr/bin/env python3
"""
並行処理例: 複数セッションでの同時タスク処理
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from src.session_manager import SessionManager, SessionRole, Task
from src.queue_manager import QueueManager, WorkRequest, Priority, RequestStatus
from datetime import datetime, timedelta

def concurrent_processing_demo():
    """大規模並行処理のデモンストレーション"""
    
    sm = SessionManager()
    qm = QueueManager()
    
    # 1. 大量セッション作成
    num_coordinators = 2
    num_managers_per_coordinator = 2  
    num_workers_per_manager = 3
    
    print("🏗️  Creating large session hierarchy...")
    
    # Supreme
    sm.create_session("supreme", SessionRole.SUPREME)
    
    # Coordinators
    coordinators = []
    for i in range(num_coordinators):
        coord_id = f"coordinator_{i}"
        sm.create_session(coord_id, SessionRole.COORDINATOR, parent_id="supreme")
        coordinators.append(coord_id)
    
    # Managers and Workers
    all_workers = []
    for coord_id in coordinators:
        for j in range(num_managers_per_coordinator):
            manager_id = f"manager_{coord_id}_{j}"
            sm.create_session(manager_id, SessionRole.MANAGER, parent_id=coord_id)
            
            for k in range(num_workers_per_manager):
                worker_id = f"worker_{manager_id}_{k}"
                sm.create_session(worker_id, SessionRole.WORKER, parent_id=manager_id)
                all_workers.append(worker_id)
    
    total_sessions = 1 + num_coordinators + (num_coordinators * num_managers_per_coordinator) + len(all_workers)
    print(f"✅ Created {total_sessions} sessions ({len(all_workers)} workers)")
    
    # 2. 大量タスク生成
    num_tasks = 50
    tasks = []
    
    task_templates = [
        "Implement user registration API",
        "Create database migration scripts", 
        "Design UI mockups for dashboard",
        "Write unit tests for authentication",
        "Set up CI/CD pipeline configuration",
        "Optimize database query performance",
        "Implement real-time notifications",
        "Create API documentation",
        "Design responsive mobile layout",
        "Implement caching layer"
    ]
    
    print(f"📋 Generating {num_tasks} tasks...")
    
    for i in range(num_tasks):
        template = task_templates[i % len(task_templates)]
        task_description = f"{template} #{i+1}"
        
        request = WorkRequest(
            request_id=f"CONCURRENT_REQ_{i:03d}",
            session_id="supreme",
            target_session=all_workers[i % len(all_workers)],  # Round-robin assignment
            priority=Priority.MEDIUM,
            task_description=task_description,
            requirements=["quality", "testing"],
            deadline=datetime.now() + timedelta(hours=8),
            dependencies=[],
            created_at=datetime.now(),
            status=RequestStatus.QUEUED,
            metadata={
                "batch": "concurrent_demo",
                "task_number": i
            }
        )
        
        qm.enqueue_request(request)
        tasks.append(request)
    
    print(f"✅ Enqueued {len(tasks)} tasks")
    
    # 3. 並行処理実行
    def process_worker_queue(worker_id):
        """Worker用のキュー処理関数"""
        processed = 0
        
        while True:
            # タスクを取得
            request = qm.dequeue_request(worker_id)
            
            if request is None:
                break  # キューが空
            
            print(f"🔄 {worker_id} processing: {request.task_description}")
            
            # 作業シミュレート（1-3秒）
            work_time = 1 + (processed % 3)
            time.sleep(work_time)
            
            # 作業完了
            from src.queue_manager import WorkResult
            result = WorkResult(
                request_id=request.request_id,
                session_id=worker_id,
                status="success",
                summary=f"Completed {request.task_description}",
                details={"processing_time": work_time},
                completed_at=datetime.now(),
                artifacts=[f"result_{request.request_id}.json"]
            )
            
            qm.complete_request(request.request_id, result)
            processed += 1
            
            print(f"✅ {worker_id} completed: {request.task_description} ({processed} total)")
        
        return processed
    
    # 4. スレッドプールで並行実行
    print(f"\n🚀 Starting concurrent processing with {len(all_workers)} workers...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=len(all_workers)) as executor:
        # 各WorkerでキューからタスクをPull
        futures = {
            executor.submit(process_worker_queue, worker_id): worker_id 
            for worker_id in all_workers
        }
        
        # 進捗監視
        total_processed = 0
        for future in futures:
            worker_id = futures[future]
            try:
                processed_count = future.result()
                total_processed += processed_count
                print(f"📊 {worker_id} completed {processed_count} tasks")
            except Exception as e:
                print(f"❌ {worker_id} encountered error: {e}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # 5. 結果サマリー
    queue_status = qm.get_queue_status()
    
    print(f"\n📈 Concurrent Processing Results:")
    print(f"  Total tasks: {num_tasks}")
    print(f"  Tasks processed: {total_processed}")  
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Average time per task: {(processing_time/num_tasks):.2f} seconds")
    print(f"  Tasks per second: {(num_tasks/processing_time):.2f}")
    print(f"\n📊 Final Queue Status:")
    print(f"  Queue: {queue_status['queue']}")
    print(f"  Active: {queue_status['active']}")
    print(f"  Completed: {queue_status['completed']}")
    
    # 6. セッション統計
    hierarchy = sm.get_session_hierarchy()
    print(f"\n🏛️  Session Statistics:")
    print(f"  Total sessions: {hierarchy['total_sessions']}")
    print(f"  Active sessions: {hierarchy['active_sessions']}")
    
    sm.shutdown()

if __name__ == "__main__":
    concurrent_processing_demo()
```

### 例5: エラー処理と復旧

```python
#!/usr/bin/env python3
"""
エラー処理例: システム障害時の自動復旧デモ
"""

from src.session_manager import SessionManager, SessionRole, SessionStatus, Task
from src.queue_manager import QueueManager, WorkRequest, Priority, RequestStatus
from src.hooks_manager import HooksManager, HookContext
from datetime import datetime
import random

def error_handling_recovery_demo():
    """エラー処理と復旧機能のデモ"""
    
    sm = SessionManager()
    qm = QueueManager()
    hm = HooksManager()
    
    print("🛠️  Error Handling & Recovery Demo\n")
    
    # 1. テスト用セッション設定
    sm.create_session("manager", SessionRole.MANAGER)
    sm.create_session("worker_1", SessionRole.WORKER, parent_id="manager")
    sm.create_session("worker_2", SessionRole.WORKER, parent_id="manager")
    sm.create_session("worker_3", SessionRole.WORKER, parent_id="manager")
    
    # 2. エラーシナリオ1: セッション障害
    print("Scenario 1: Session Failure & Recovery")
    
    # Worker_1に問題が発生
    print("  Simulating worker_1 failure...")
    sm.update_session_status("worker_1", SessionStatus.ERROR)
    
    # 障害セッションに割り当てられていたタスク
    failed_task = Task(
        task_id="FAILED_TASK_001",
        description="Task that failed on worker_1",
        priority=1,
        assigned_to="worker_1",
        created_by="manager",
        created_at=datetime.now(),
        deadline=None,
        dependencies=[],
        status="failed"
    )
    
    # 親セッション（Manager）にエスカレート
    print("  Escalating failed task to manager...")
    escalation_success = sm.escalate_to_parent("worker_1", failed_task)
    
    if escalation_success:
        print("  ✅ Task escalated to manager successfully")
        
        # 代替Worker を見つけて再分散
        available_workers = sm.get_available_sessions(SessionRole.WORKER)
        if available_workers:
            backup_worker = available_workers[0]
            
            # タスクを代替Workerに再割り当て
            recovery_task = Task(
                task_id="RECOVERY_TASK_001",
                description=f"Recovery: {failed_task.description}",
                priority=failed_task.priority,
                assigned_to=None,
                created_by="manager",
                created_at=datetime.now(),
                deadline=None,
                dependencies=[],
                status="recovery"
            )
            
            success = sm.assign_task(recovery_task, backup_worker)
            if success:
                print(f"  ✅ Task reassigned to {backup_worker}")
            else:
                print(f"  ❌ Failed to reassign task to {backup_worker}")
    
    # 3. エラーシナリオ2: Queue/Active衝突
    print("\nScenario 2: Queue Conflict Resolution")
    
    # Worker_2に既にアクティブなタスクがある状況をシミュレート
    active_request = WorkRequest(
        request_id="ACTIVE_REQ_001",
        session_id="manager",
        target_session="worker_2",
        priority=Priority.MEDIUM,
        task_description="Already active task on worker_2",
        requirements=[],
        deadline=None,
        dependencies=[],
        created_at=datetime.now(),
        status=RequestStatus.QUEUED,
        metadata={}
    )
    
    qm.enqueue_request(active_request)
    qm.move_to_active(active_request.request_id, "worker_2")
    
    # 新しいタスクを同じWorkerに送る（衝突発生）
    conflicting_request = WorkRequest(
        request_id="CONFLICTING_REQ_001",  
        session_id="manager",
        target_session="worker_2",
        priority=Priority.HIGH,
        task_description="New task causing conflict",
        requirements=[],
        deadline=None,
        dependencies=[],
        created_at=datetime.now(),
        status=RequestStatus.QUEUED,
        metadata={}
    )
    
    qm.enqueue_request(conflicting_request)
    
    # 衝突検知
    print("  Checking for conflicts on worker_2...")
    conflicts = qm.check_conflicts("worker_2")
    
    if conflicts:
        print(f"  ⚠️  {len(conflicts)} conflicts detected:")
        for conflict in conflicts:
            print(f"    - {conflict.conflict_type}: {conflict.description}")
            print(f"      Resolution: {conflict.resolution_suggestion}")
        
        # 衝突解決: 別のWorkerに振り分け
        alternative_workers = [w for w in sm.get_available_sessions(SessionRole.WORKER) if w != "worker_2"]
        if alternative_workers:
            alternative_worker = alternative_workers[0]
            
            # 依頼書のターゲットを変更
            conflicting_request.target_session = alternative_worker
            
            # 再エンキュー
            qm.cancel_request(conflicting_request.request_id)
            new_request_id = qm.enqueue_request(conflicting_request)
            
            print(f"  ✅ Conflict resolved: reassigned to {alternative_worker}")
        else:
            print("  ❌ No alternative workers available")
    
    # 4. エラーシナリオ3: Hook処理エラー
    print("\nScenario 3: Hook Processing Error Recovery")
    
    # 不正なHookコンテキスト
    invalid_contexts = [
        HookContext(
            hook_type='InvalidHookType',  # 存在しないタイプ
            session_id='worker_3',
            tool_name='TestTool',
            tool_output=None,
            timestamp=datetime.now(),
            metadata={}
        ),
        HookContext(
            hook_type='PostToolUse',
            session_id='nonexistent_session',  # 存在しないセッション
            tool_name='TodoWrite', 
            tool_output='malformed json {',  # 不正なJSON
            timestamp=datetime.now(),
            metadata={}
        )
    ]
    
    for i, context in enumerate(invalid_contexts, 1):
        print(f"  Testing error case {i}...")
        
        try:
            result = hm.process_hook(context)
            
            if not result.success:
                print(f"    ✅ Error handled gracefully: {result.message}")
            else:
                print(f"    ⚠️  Unexpected success for error case")
                
        except Exception as e:
            print(f"    ❌ Unhandled exception: {e}")
    
    # 5. システム状態確認
    print(f"\n📊 System Status After Error Scenarios:")
    
    # セッション状態
    print("  Sessions:")
    for session_id, session in sm.sessions.items():
        status_icon = "❌" if session.status == SessionStatus.ERROR else "✅"
        current_task = session.current_task or "None"
        print(f"    {status_icon} {session_id}: {session.status.value} (Task: {current_task})")
    
    # キュー状態
    queue_status = qm.get_queue_status()
    print(f"  Queue Status:")
    print(f"    Queue: {queue_status['queue']} requests")
    print(f"    Active: {queue_status['active']} requests") 
    print(f"    Completed: {queue_status['completed']} requests")
    
    # 6. システム復旧手順
    print(f"\n🔧 System Recovery Procedures:")
    
    # 障害セッションの復旧
    print("  Recovering failed sessions...")
    for session_id, session in sm.sessions.items():
        if session.status == SessionStatus.ERROR:
            print(f"    Attempting to recover {session_id}...")
            
            # セッションをIDLEに戻す
            sm.update_session_status(session_id, SessionStatus.IDLE)
            
            # 未完了タスクをクリア
            session.current_task = None
            
            print(f"    ✅ {session_id} recovered")
    
    # キューの整理
    print("  Cleaning up queue...")
    # 実際の実装では、期限切れや孤立した依頼書を削除
    
    print("\n🎯 Error handling and recovery demo completed")
    
    sm.shutdown()

if __name__ == "__main__":
    error_handling_recovery_demo()
```

## 🎛️ 設定例

### カスタムHooks設定

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "name": "completion-detector",
        "matcher": "TodoWrite.*completed|mcp__serena__think_about_whether_you_are_done",
        "handler": {
          "type": "script",
          "path": "./scripts/completion-handler.py",
          "args": ["--session-id", "${SESSION_ID}", "--output", "${TOOL_OUTPUT}"]
        }
      },
      {
        "name": "test-result-parser", 
        "matcher": "pytest.*passed|All tests passed",
        "handler": {
          "type": "function",
          "module": "handlers.test_handlers",
          "function": "parse_test_results"
        }
      }
    ],
    "PreToolUse": [
      {
        "name": "resource-checker",
        "matcher": ".*",
        "handler": {
          "type": "script",
          "path": "./scripts/resource-checker.py",
          "blocking": true
        }
      },
      {
        "name": "security-filter",
        "matcher": "system|delete|rm -rf",
        "handler": {
          "type": "function", 
          "module": "handlers.security_handlers",
          "function": "check_dangerous_commands",
          "blocking": true
        }
      }
    ]
  }
}
```

### 環境変数設定例

```bash
# .env
CC_DISCORD_TOKEN="your_discord_bot_token"
CC_DISCORD_CHANNEL_ID="1405815779198369903"
CC_DISCORD_USER_ID="your_user_id"

# システム設定
MAX_CONCURRENT_SESSIONS=10
SESSION_TIMEOUT=3600
QUEUE_CHECK_INTERVAL=5

# パフォーマンス設定  
MEMORY_LIMIT_PER_SESSION=2048  # MB
CPU_LIMIT_PER_SESSION=1        # cores
DISK_QUOTA_PER_SESSION=10240   # MB

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=./logs/order-management.log
DISCORD_LOG_CHANNEL="monitoring_channel_id"
```

## 🎯 運用シナリオ

### 毎日の開発フロー自動化

```python
def daily_development_automation():
    """毎日の開発フローを自動化"""
    
    # 朝: 全セッション起動・状態チェック
    morning_startup()
    
    # 午前: 新機能開発タスクの分散
    distribute_feature_tasks()
    
    # 午後: バグ修正・テストタスクの処理
    process_maintenance_tasks()
    
    # 夕方: コードレビュー・統合作業
    perform_integration_work()
    
    # 夜: システム状態レポート生成
    generate_daily_report()
```

これらの例を参考に、あなたのプロジェクトに合わせてOrder Management Serverをカスタマイズしてください！