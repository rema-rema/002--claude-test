#!/usr/bin/env python3
"""
Order Management Server - Basic Usage Example
基本的な使い方のデモンストレーション
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import datetime, timedelta
from session_manager import SessionManager, SessionRole
from queue_manager import QueueManager, WorkRequest, Priority, RequestStatus
from discord_proxy import DiscordProxy
from hooks_manager import HooksManager, HookContext

def main():
    """基本的な使用例のデモ"""
    
    print("🚀 Order Management Server - Basic Usage Demo")
    print("=" * 60)
    
    # 1. システムコンポーネント初期化
    print("\n📋 Step 1: System Initialization")
    
    try:
        sm = SessionManager()
        sm.monitoring = False  # Disable monitoring for demo
        qm = QueueManager()
        dp = DiscordProxy()
        hm = HooksManager()
        
        print("✅ All components initialized successfully")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # 2. セッション作成
    print("\n👥 Step 2: Session Creation")
    
    try:
        # 階層的セッション作成
        supreme = sm.create_session("supreme", SessionRole.SUPREME)
        coordinator = sm.create_session("coordinator", SessionRole.COORDINATOR, parent_id="supreme")
        manager = sm.create_session("manager", SessionRole.MANAGER, parent_id="coordinator")
        worker = sm.create_session("worker", SessionRole.WORKER, parent_id="manager")
        
        print(f"✅ Created session hierarchy:")
        print(f"   Supreme: {supreme.session_id}")
        print(f"   └─ Coordinator: {coordinator.session_id}")
        print(f"      └─ Manager: {manager.session_id}")
        print(f"         └─ Worker: {worker.session_id}")
        
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False
    
    # 3. 作業依頼書作成
    print("\n📝 Step 3: Work Request Creation")
    
    try:
        work_request = WorkRequest(
            request_id=qm.generate_request_id("coordinator", "demo_task"),
            session_id="coordinator",
            target_session="worker",
            priority=Priority.HIGH,
            task_description="デモ用のタスク実装",
            requirements=[
                "Python での実装",
                "ユニットテスト作成", 
                "ドキュメント作成"
            ],
            deadline=datetime.now() + timedelta(hours=8),
            dependencies=["環境設定完了"],
            created_at=datetime.now(),
            status=RequestStatus.QUEUED,
            metadata={
                "project": "order_management_demo",
                "complexity": "low",
                "estimated_hours": 2
            }
        )
        
        print(f"✅ Work request created:")
        print(f"   Request ID: {work_request.request_id}")
        print(f"   Task: {work_request.task_description}")
        print(f"   Priority: {work_request.priority.name}")
        print(f"   Target: {work_request.target_session}")
        
    except Exception as e:
        print(f"❌ Work request creation failed: {e}")
        return False
    
    # 4. キューへのエンキュー
    print("\n📤 Step 4: Enqueue Request")
    
    try:
        request_id = qm.enqueue_request(work_request)
        print(f"✅ Request enqueued: {request_id}")
        
        # キュー状態確認
        status = qm.get_queue_status()
        print(f"   Queue status: {status['queue']} queued, {status['active']} active")
        
    except Exception as e:
        print(f"❌ Enqueue failed: {e}")
        return False
    
    # 5. Discord通知送信（シミュレート）
    print("\n💬 Step 5: Discord Notification")
    
    try:
        # 作業依頼書をDiscordに送信
        request_data = {
            'request_id': work_request.request_id,
            'priority': work_request.priority.name,
            'deadline': work_request.deadline.isoformat() if work_request.deadline else None,
            'task_description': work_request.task_description,
            'requirements': work_request.requirements,
            'dependencies': work_request.dependencies
        }
        
        print("📤 Sending work request to Discord (simulated)...")
        print(f"   Target session: 2 (worker session)")
        print(f"   Message preview:")
        
        # フォーマットされたメッセージのプレビュー表示
        formatted_msg = dp._format_work_request(request_data)
        preview_lines = formatted_msg.split('\n')[:8]  # First 8 lines
        for line in preview_lines:
            print(f"     {line}")
        print("     ...")
        
        # 実際の送信は環境によりスキップ
        print("   (Note: Actual Discord sending skipped in demo mode)")
        
    except Exception as e:
        print(f"❌ Discord notification failed: {e}")
        return False
    
    # 6. タスク処理シミュレート
    print("\n⚡ Step 6: Task Processing Simulation")
    
    try:
        # Worker がタスクを取得
        dequeued_request = qm.dequeue_request("worker")
        
        if dequeued_request:
            print(f"✅ Worker dequeued request: {dequeued_request.request_id}")
            print(f"   Task: {dequeued_request.task_description}")
            
            # 作業完了シミュレート
            from queue_manager import WorkResult
            
            result = WorkResult(
                request_id=dequeued_request.request_id,
                session_id="worker",
                status="success",
                summary="デモタスクが正常に完了しました",
                details={
                    "files_created": ["demo_module.py", "test_demo_module.py"],
                    "lines_of_code": 150,
                    "test_coverage": "95%"
                },
                completed_at=datetime.now(),
                artifacts=["demo_module.py", "test_demo_module.py", "README.md"]
            )
            
            # タスク完了
            completion_success = qm.complete_request(dequeued_request.request_id, result)
            
            if completion_success:
                print(f"✅ Task completed successfully")
                print(f"   Status: {result.status}")
                print(f"   Summary: {result.summary}")
                print(f"   Artifacts: {len(result.artifacts)} files")
            else:
                print("❌ Task completion failed")
                
        else:
            print("❌ No request found for worker")
            
    except Exception as e:
        print(f"❌ Task processing failed: {e}")
        return False
    
    # 7. 完了検知シミュレート
    print("\n🔍 Step 7: Completion Detection")
    
    try:
        # 完了信号のシミュレート
        completion_output = '{"todos": [{"content": "デモタスク実装", "status": "completed"}]}'
        
        context = HookContext(
            hook_type='PostToolUse',
            session_id='worker',
            tool_name='TodoWrite',
            tool_output=completion_output,
            timestamp=datetime.now(),
            metadata={'demo': True}
        )
        
        hook_result = hm.process_hook(context)
        
        if hook_result.success and hook_result.actions:
            print(f"✅ Completion detected: {len(hook_result.actions)} actions")
            
            for action in hook_result.actions:
                if action['type'] == 'send_report':
                    report = action['report']
                    print(f"   📋 Report generated:")
                    print(f"      Session: {report['session_id']}")
                    print(f"      Type: {report['completion_type']}")
                    print(f"      Summary: {report['summary']}")
                    
        else:
            print("ℹ️  No completion detected (normal for demo)")
            
    except Exception as e:
        print(f"❌ Completion detection failed: {e}")
        return False
    
    # 8. システム状態確認
    print("\n📊 Step 8: System Status")
    
    try:
        # セッション階層表示
        hierarchy = sm.get_session_hierarchy()
        print(f"✅ Session hierarchy:")
        print(f"   Total sessions: {hierarchy['total_sessions']}")
        print(f"   Active sessions: {hierarchy['active_sessions']}")
        
        # キュー状態表示
        final_status = qm.get_queue_status()
        print(f"✅ Queue status:")
        print(f"   Queue: {final_status['queue']} requests")
        print(f"   Active: {final_status['active']} requests")
        print(f"   Completed: {final_status['completed']} requests")
        
        # Discord通信状態
        discord_status = dp.get_session_status()
        print(f"✅ Discord integration:")
        print(f"   Active sessions: {len(discord_status['active_sessions'])}")
        print(f"   Command history: {discord_status['command_history_count']} entries")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False
    
    # 9. クリーンアップ
    print("\n🧹 Step 9: Cleanup")
    
    try:
        sm.shutdown()
        print("✅ System shutdown completed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False
    
    # 成功メッセージ
    print("\n" + "=" * 60)
    print("🎉 Basic Usage Demo Completed Successfully!")
    print("")
    print("📚 Next Steps:")
    print("  • Try the advanced examples in examples/")
    print("  • Read USAGE_EXAMPLES.md for detailed scenarios")
    print("  • Run integration tests: python tests/test_simple_integration.py")
    print("  • Start actual Discord integration with real sessions")
    print("")
    print("🔗 For actual usage:")
    print("  1. Configure .env with your Discord credentials")
    print("  2. Ensure Claude Discord Bridge is running")
    print("  3. Use DiscordProxy.send_work_request() to send real requests")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)