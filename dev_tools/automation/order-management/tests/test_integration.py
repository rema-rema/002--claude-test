"""
Integration Tests for Order Management Server
User Acceptance Test scenarios
"""

import pytest
import tempfile
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hooks_manager import HooksManager, HookContext, CompletionSignal
from queue_manager import QueueManager, WorkRequest, WorkResult, RequestStatus, Priority
from session_manager import SessionManager, SessionRole, SessionStatus, Task
from discord_proxy import DiscordProxy

class TestOrderManagementIntegration:
    """Order Management System Integration Tests"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for all components"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create config files
            config_dir = base_dir / 'config'
            config_dir.mkdir()
            
            # Create sessions config
            sessions_config = config_dir / 'sessions.json'
            sessions_data = {
                "sessions": [],
                "updated_at": datetime.now().isoformat()
            }
            with open(sessions_config, 'w') as f:
                json.dump(sessions_data, f)
            
            # Create hooks config
            hooks_config = config_dir / 'hooks.json'
            hooks_data = {
                "hooks": {"PostToolUse": [], "PreToolUse": []},
                "patterns": {
                    "todo_completion": r'"status":\s*"completed"',
                    "implementation_done": r'実装完了'
                }
            }
            with open(hooks_config, 'w') as f:
                json.dump(hooks_data, f)
            
            # Create bridge directory
            bridge_dir = base_dir / 'bridge'
            bridge_dir.mkdir()
            bridge_sessions = bridge_dir / 'sessions.json'
            bridge_data = {
                "sessions": {
                    "1": {"channel_id": "1405815779198369903"},
                    "2": {"channel_id": "1410119446835630151"}
                }
            }
            with open(bridge_sessions, 'w') as f:
                json.dump(bridge_data, f)
            
            yield {
                'base_dir': base_dir,
                'sessions_config': sessions_config,
                'hooks_config': hooks_config,
                'bridge_dir': bridge_dir
            }
    
    @pytest.fixture
    def system_components(self, temp_dirs):
        """Create all system components"""
        # Stop monitoring threads for tests
        session_manager = SessionManager(config_path=temp_dirs['sessions_config'])
        session_manager.monitoring = False
        if session_manager.monitor_thread.is_alive():
            session_manager.monitor_thread.join(timeout=1)
        
        return {
            'hooks_manager': HooksManager(config_path=temp_dirs['hooks_config']),
            'queue_manager': QueueManager(base_dir=temp_dirs['base_dir']),
            'session_manager': session_manager,
            'discord_proxy': DiscordProxy(bridge_base_dir=temp_dirs['bridge_dir'])
        }
    
    def test_user_story_1_basic_workflow(self, system_components):
        """
        User Story 1: セッション間基本連携フロー
        Given: 2つのClaude Codeセッションが稼働中
        When: Session Aでタスクが完了
        Then: Session Bに自動的に次の依頼書が送信される
        """
        hm = system_components['hooks_manager']
        qm = system_components['queue_manager']
        sm = system_components['session_manager']
        dp = system_components['discord_proxy']
        
        # Step 1: セッション設定
        sm.create_session("session_a", SessionRole.COORDINATOR)
        sm.create_session("session_b", SessionRole.WORKER)
        
        # Step 2: 依頼書作成・エンキュー
        work_request = WorkRequest(
            request_id=qm.generate_request_id("session_a", "test_task"),
            session_id="session_a",
            target_session="session_b",
            priority=Priority.HIGH,
            task_description="Implement user authentication module",
            requirements=["security", "testing"],
            deadline=datetime.now() + timedelta(hours=24),
            dependencies=[],
            created_at=datetime.now(),
            status=RequestStatus.QUEUED,
            metadata={"test_scenario": "user_story_1"}
        )
        
        request_id = qm.enqueue_request(work_request)
        assert request_id == work_request.request_id
        
        # Step 3: Session Bが依頼書を取得
        dequeued_request = qm.dequeue_request("session_b")
        assert dequeued_request is not None
        assert dequeued_request.task_description == "Implement user authentication module"
        
        # Step 4: 完了信号検知のシミュレート
        completion_output = '{"content": "user authentication", "status": "completed"}'
        context = HookContext(
            hook_type='PostToolUse',
            session_id='session_b',
            tool_name='TodoWrite',
            tool_output=completion_output,
            timestamp=datetime.now(),
            metadata={}
        )
        
        result = hm.process_hook(context)
        assert result.success
        assert len(result.actions) == 1
        assert result.actions[0]['type'] == 'send_report'
        
        # Step 5: 依頼書完了処理
        work_result = WorkResult(
            request_id=request_id,
            session_id="session_b",
            status="success",
            summary="User authentication module implemented successfully",
            details={"files_created": ["auth.py", "test_auth.py"]},
            completed_at=datetime.now(),
            artifacts=["auth.py", "test_auth.py", "auth_tests.json"]
        )
        
        completion_success = qm.complete_request(request_id, work_result)
        assert completion_success
        
        # Verification: 完了ファイルが作成されている
        completed_files = list(qm.completed_dir.glob("*.json"))
        assert len(completed_files) == 1
    
    def test_user_story_2_hierarchical_escalation(self, system_components):
        """
        User Story 2: 階層的エスカレーション
        Given: 親子関係のセッション階層
        When: 子セッションで問題が発生
        Then: 親セッションに自動エスカレート
        """
        sm = system_components['session_manager']
        
        # 階層作成: manager -> worker
        sm.create_session("manager", SessionRole.MANAGER)
        sm.create_session("worker", SessionRole.WORKER, parent_id="manager")
        
        # 問題のあるタスク
        problematic_task = Task(
            task_id="ESCALATE_TASK_001",
            description="Complex task requiring escalation",
            priority=1,
            assigned_to=None,
            created_by="system",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="escalated"
        )
        
        # エスカレーション実行
        escalation_success = sm.escalate_to_parent("worker", problematic_task)
        
        assert escalation_success
        assert problematic_task.assigned_to == "manager"
        assert sm.sessions["manager"].status == SessionStatus.BUSY
        assert sm.sessions["manager"].current_task == "ESCALATE_TASK_001"
    
    def test_user_story_3_conflict_resolution(self, system_components):
        """
        User Story 3: 衝突検知・解決
        Given: セッションに既にアクティブなタスクがある
        When: 新しい依頼書が同じセッションに送られる
        Then: 衝突が検知され、適切に処理される
        """
        qm = system_components['queue_manager']
        sm = system_components['session_manager']
        
        # セッション作成
        sm.create_session("busy_session", SessionRole.WORKER)
        
        # 最初の依頼書（アクティブ）
        first_request = WorkRequest(
            request_id="ACTIVE_REQ_001",
            session_id="requester",
            target_session="busy_session",
            priority=Priority.MEDIUM,
            task_description="First active task",
            requirements=[],
            deadline=None,
            dependencies=[],
            created_at=datetime.now(),
            status=RequestStatus.QUEUED,
            metadata={}
        )
        
        qm.enqueue_request(first_request)
        qm.move_to_active(first_request.request_id, "busy_session")
        
        # 衝突検知
        conflicts = qm.check_conflicts("busy_session")
        
        assert len(conflicts) >= 1
        conflict = conflicts[0]
        assert conflict.conflict_type == "session"
        assert conflict.description.find("already has an active request") != -1
        
        # 2つ目の依頼書はデキューできない
        second_dequeue = qm.dequeue_request("busy_session")
        assert second_dequeue is None
    
    @patch('subprocess.run')
    def test_user_story_4_discord_integration(self, mock_subprocess, system_components):
        """
        User Story 4: Discord統合・通知
        Given: Discord Proxyが設定済み
        When: 作業依頼書を送信
        Then: 適切なフォーマットでDiscordに通知される
        """
        dp = system_components['discord_proxy']
        mock_subprocess.return_value = Mock(returncode=0)
        
        # 作業依頼書データ
        request_data = {
            'request_id': 'DISCORD_REQ_001',
            'priority': 'High',
            'deadline': '2025-08-30T18:00:00Z',
            'task_description': 'Implement Discord notification system',
            'requirements': ['real-time', 'reliable'],
            'dependencies': ['webhook_setup']
        }
        
        # Discord送信
        success = dp.send_work_request('1', request_data)
        
        assert success
        mock_subprocess.assert_called_once()
        
        # 送信内容を検証
        call_args = mock_subprocess.call_args[0][0]
        assert '作業依頼書' in call_args
        assert 'DISCORD_REQ_001' in call_args
        assert 'Implement Discord notification system' in call_args
        assert '/resume' in call_args
        
        # 履歴記録を確認
        history = dp.get_command_history()
        assert len(history) == 1
        assert history[0]['data']['message_type'] == 'work_request'
    
    @patch('subprocess.run')
    def test_user_story_5_completion_reporting(self, mock_subprocess, system_components):
        """
        User Story 5: 自動完了報告
        Given: タスクが完了した
        When: 完了パターンが検知される
        Then: 自動的に完了報告書が生成・送信される
        """
        hm = system_components['hooks_manager']
        dp = system_components['discord_proxy']
        mock_subprocess.return_value = Mock(returncode=0)
        
        # 完了信号作成
        completion_signal = CompletionSignal(
            type='implementation_done',
            timestamp=datetime.now(),
            session_id='session_1',
            context={'pattern': '実装完了'},
            raw_output='実装完了: ユーザ認証モジュール'
        )
        
        # 完了報告書生成
        report = hm.generate_completion_report(completion_signal)
        
        assert report.session_id == 'session_1'
        assert report.completion_type == 'implementation_done'
        assert '実装が完了しました' in report.summary
        
        # Discord送信
        report_data = {
            'session_id': report.session_id,
            'completion_type': report.completion_type,
            'timestamp': report.timestamp.isoformat(),
            'summary': report.summary,
            'details': report.details,
            'next_actions': report.next_actions
        }
        
        success = dp.send_completion_report('1', report_data)
        
        assert success
        mock_subprocess.assert_called_once()
        
        # 報告書内容確認
        call_args = mock_subprocess.call_args[0][0]
        assert '作業完了報告書' in call_args
        assert 'session_1' in call_args
        assert 'implementation_done' in call_args
    
    def test_user_story_6_concurrent_sessions(self, system_components):
        """
        User Story 6: 並行セッション管理
        Given: 複数セッションが並行稼働
        When: 各セッションが独立してタスクを実行
        Then: セッション間の干渉なく処理が完了する
        """
        sm = system_components['session_manager']
        qm = system_components['queue_manager']
        
        # 複数セッション作成
        sessions = []
        for i in range(3):
            session_id = f"concurrent_session_{i}"
            sm.create_session(session_id, SessionRole.WORKER)
            sessions.append(session_id)
        
        # 各セッション用のタスク作成
        tasks = []
        for i, session_id in enumerate(sessions):
            task = Task(
                task_id=f"CONCURRENT_TASK_{i}",
                description=f"Concurrent task for {session_id}",
                priority=1,
                assigned_to=None,
                created_by="system",
                created_at=datetime.now(),
                deadline=None,
                dependencies=[],
                status="pending"
            )
            tasks.append(task)
        
        # 並行タスク割り当て
        assignment_results = []
        for task, session_id in zip(tasks, sessions):
            result = sm.assign_task(task, session_id)
            assignment_results.append(result)
        
        # すべて成功する必要がある
        assert all(assignment_results)
        
        # 各セッションが独立してBUSY状態
        for session_id in sessions:
            assert sm.sessions[session_id].status == SessionStatus.BUSY
            assert sm.sessions[session_id].current_task is not None
        
        # セッション階層確認
        hierarchy = sm.get_session_hierarchy()
        assert hierarchy['total_sessions'] == 3
        assert hierarchy['active_sessions'] == 3
    
    def test_user_story_7_error_recovery(self, system_components):
        """
        User Story 7: エラー処理・復旧
        Given: システム実行中にエラーが発生
        When: エラーハンドリングが動作
        Then: 適切にエラーログが記録され、システムが継続稼働
        """
        hm = system_components['hooks_manager']
        qm = system_components['queue_manager']
        
        # 不正なHookコンテキスト（エラーケース）
        invalid_context = HookContext(
            hook_type='InvalidHookType',  # 存在しないフックタイプ
            session_id='test_session',
            tool_name='TestTool',
            tool_output=None,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # エラーハンドリングのテスト
        result = hm.process_hook(invalid_context)
        
        assert not result.success
        assert result.message == "Unknown hook type: InvalidHookType"
        
        # 不正なリクエストIDでの完了処理（エラーケース）
        invalid_result = WorkResult(
            request_id="NONEXISTENT_REQ",
            session_id="test_session",
            status="success",
            summary="Test",
            details={},
            completed_at=datetime.now(),
            artifacts=[]
        )
        
        completion_result = qm.complete_request("NONEXISTENT_REQ", invalid_result)
        
        # 失敗するが、システムは継続稼働
        assert not completion_result
    
    def test_performance_benchmark(self, system_components):
        """
        Performance Test: システムパフォーマンス検証
        """
        qm = system_components['queue_manager']
        sm = system_components['session_manager']
        
        # パフォーマンステスト設定
        num_requests = 50
        num_sessions = 5
        
        # セッション準備
        for i in range(num_sessions):
            sm.create_session(f"perf_session_{i}", SessionRole.WORKER)
        
        # 大量依頼書作成・エンキューのタイミング測定
        start_time = time.time()
        
        request_ids = []
        for i in range(num_requests):
            request = WorkRequest(
                request_id=f"PERF_REQ_{i:03d}",
                session_id="system",
                target_session=f"perf_session_{i % num_sessions}",
                priority=Priority.MEDIUM,
                task_description=f"Performance test task {i}",
                requirements=[],
                deadline=None,
                dependencies=[],
                created_at=datetime.now(),
                status=RequestStatus.QUEUED,
                metadata={"perf_test": True}
            )
            
            request_id = qm.enqueue_request(request)
            request_ids.append(request_id)
        
        enqueue_time = time.time() - start_time
        
        # パフォーマンス検証
        assert enqueue_time < 10.0  # 50リクエストを10秒以内で処理
        assert len(request_ids) == num_requests
        
        # キューステータス確認
        status = qm.get_queue_status()
        assert status['queue'] == num_requests
        
        print(f"Performance Test Results:")
        print(f"  Enqueued {num_requests} requests in {enqueue_time:.2f}s")
        print(f"  Average time per request: {(enqueue_time/num_requests)*1000:.1f}ms")

if __name__ == "__main__":
    # Run user acceptance tests
    pytest.main([__file__, "-v", "-s"])