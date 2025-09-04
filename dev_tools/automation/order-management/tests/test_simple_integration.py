"""
Simple Integration Test for Order Management Server
Simplified User Acceptance Test scenarios
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import with error handling
try:
    from hooks_manager import HooksManager, HookContext, CompletionSignal
    from queue_manager import QueueManager, WorkRequest, WorkResult, RequestStatus, Priority
    from session_manager import SessionManager, SessionRole, SessionStatus, Task
    from discord_proxy import DiscordProxy
except ImportError as e:
    print(f"Import error: {e}")
    exit(1)

def test_basic_functionality():
    """Basic functionality test without pytest fixtures"""
    print("Running basic functionality tests...")
    
    # Test 1: HooksManager basic operation
    print("Test 1: HooksManager")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        config = {
            "hooks": {"PostToolUse": [], "PreToolUse": []},
            "patterns": {"todo_completion": r'"status":\s*"completed"'}
        }
        json.dump(config, f)
        f.flush()
        
        hm = HooksManager(config_path=Path(f.name))
        
        # Test completion detection
        output = '{"content": "task", "status": "completed"}'
        signals = hm.detect_completion_patterns(output, "test_session")
        
        assert len(signals) == 1
        assert signals[0].type == 'todo_completion'
        print("✅ HooksManager: Completion detection working")
    
    # Test 2: QueueManager basic operation
    print("Test 2: QueueManager")
    with tempfile.TemporaryDirectory() as temp_dir:
        qm = QueueManager(base_dir=Path(temp_dir))
        
        # Create and enqueue request
        request = WorkRequest(
            request_id="TEST_REQ_001",
            session_id="session_a",
            target_session="session_b",
            priority=Priority.HIGH,
            task_description="Test task",
            requirements=[],
            deadline=None,
            dependencies=[],
            created_at=datetime.now(),
            status=RequestStatus.QUEUED,
            metadata={}
        )
        
        request_id = qm.enqueue_request(request)
        assert request_id == "TEST_REQ_001"
        
        # Dequeue request
        dequeued = qm.dequeue_request("session_b")
        assert dequeued is not None
        assert dequeued.request_id == "TEST_REQ_001"
        
        print("✅ QueueManager: Request enqueue/dequeue working")
    
    # Test 3: SessionManager basic operation
    print("Test 3: SessionManager")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        config = {"sessions": [], "updated_at": datetime.now().isoformat()}
        json.dump(config, f)
        f.flush()
        
        sm = SessionManager(config_path=Path(f.name))
        sm.monitoring = False  # Disable monitoring for test
        
        # Create session
        session = sm.create_session("test_session", SessionRole.WORKER)
        assert session.session_id == "test_session"
        assert session.role == SessionRole.WORKER
        
        # Test task assignment
        task = Task(
            task_id="TEST_TASK_001",
            description="Test task",
            priority=1,
            assigned_to=None,
            created_by="test",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="pending"
        )
        
        success = sm.assign_task(task, "test_session")
        assert success
        assert task.assigned_to == "test_session"
        
        sm.shutdown()
        print("✅ SessionManager: Session creation and task assignment working")
    
    # Test 4: DiscordProxy basic operation
    print("Test 4: DiscordProxy")
    with tempfile.TemporaryDirectory() as temp_dir:
        bridge_dir = Path(temp_dir)
        
        # Create sessions.json
        sessions_data = {
            "sessions": {
                "1": {"channel_id": "1405815779198369903"}
            }
        }
        sessions_file = bridge_dir / 'sessions.json'
        with open(sessions_file, 'w') as f:
            json.dump(sessions_data, f)
        
        dp = DiscordProxy(bridge_base_dir=bridge_dir)
        
        # Test session mapping
        assert '1' in dp.session_mapping
        assert dp.session_mapping['1'] == '1405815779198369903'
        
        # Test message formatting
        request_data = {
            'request_id': 'TEST_REQ',
            'priority': 'High',
            'task_description': 'Test task',
            'requirements': ['req1'],
            'dependencies': ['dep1']
        }
        
        formatted = dp._format_work_request(request_data)
        assert '作業依頼書' in formatted
        assert 'TEST_REQ' in formatted
        
        print("✅ DiscordProxy: Message formatting working")
    
    print("\n🎉 All basic functionality tests passed!")
    return True

def test_integration_scenarios():
    """Integration test scenarios"""
    print("\nRunning integration scenarios...")
    
    # Scenario 1: End-to-end workflow
    print("Scenario 1: End-to-end workflow")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        
        # Setup configs
        hooks_config = base_dir / 'hooks.json'
        with open(hooks_config, 'w') as f:
            json.dump({
                "hooks": {"PostToolUse": []},
                "patterns": {"todo_completion": r'"status":\s*"completed"'}
            }, f)
        
        sessions_config = base_dir / 'sessions.json'
        with open(sessions_config, 'w') as f:
            json.dump({"sessions": [], "updated_at": datetime.now().isoformat()}, f)
        
        # Create components
        hm = HooksManager(config_path=hooks_config)
        qm = QueueManager(base_dir=base_dir)
        sm = SessionManager(config_path=sessions_config)
        sm.monitoring = False
        
        # Create sessions
        sm.create_session("session_a", SessionRole.COORDINATOR)
        sm.create_session("session_b", SessionRole.WORKER)
        
        # Create work request
        request = WorkRequest(
            request_id="WORKFLOW_REQ_001",
            session_id="session_a",
            target_session="session_b",
            priority=Priority.HIGH,
            task_description="Integration test workflow",
            requirements=["testing"],
            deadline=datetime.now() + timedelta(hours=1),
            dependencies=[],
            created_at=datetime.now(),
            status=RequestStatus.QUEUED,
            metadata={"scenario": "end_to_end"}
        )
        
        # Execute workflow
        request_id = qm.enqueue_request(request)
        dequeued = qm.dequeue_request("session_b")
        
        assert dequeued is not None
        assert dequeued.request_id == request_id
        
        # Simulate task completion
        completion_output = '{"content": "integration test", "status": "completed"}'
        context = HookContext(
            hook_type='PostToolUse',
            session_id='session_b',
            tool_name='TodoWrite',
            tool_output=completion_output,
            timestamp=datetime.now(),
            metadata={}
        )
        
        hook_result = hm.process_hook(context)
        assert hook_result.success
        
        # Complete request
        work_result = WorkResult(
            request_id=request_id,
            session_id="session_b",
            status="success",
            summary="Integration test completed",
            details={"test_result": "passed"},
            completed_at=datetime.now(),
            artifacts=[]
        )
        
        completion_success = qm.complete_request(request_id, work_result)
        assert completion_success
        
        sm.shutdown()
        print("✅ End-to-end workflow completed successfully")
    
    print("\n🎉 All integration scenarios passed!")
    return True

if __name__ == "__main__":
    try:
        success1 = test_basic_functionality()
        success2 = test_integration_scenarios()
        
        if success1 and success2:
            print("\n🌟 USER ACCEPTANCE TESTS: ALL PASSED")
            print("Order Management Server is ready for production!")
            exit(0)
        else:
            print("\n❌ Some tests failed")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)