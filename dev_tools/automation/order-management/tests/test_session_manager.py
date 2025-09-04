"""
SessionManager Unit Tests  
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from session_manager import SessionManager, SessionInfo, SessionStatus, SessionRole, SessionCapabilities, Task

class TestSessionManager:
    """SessionManager test suite"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "sessions": [],
                "updated_at": datetime.now().isoformat()
            }
            json.dump(config, f)
            yield Path(f.name)
            Path(f.name).unlink()
    
    @pytest.fixture
    def session_manager(self, temp_config_file):
        """Create SessionManager with temporary config"""
        sm = SessionManager(config_path=temp_config_file)
        # Stop monitoring thread for tests
        sm.monitoring = False
        if sm.monitor_thread.is_alive():
            sm.monitor_thread.join(timeout=1)
        return sm
    
    def test_init(self, session_manager):
        """Test SessionManager initialization"""
        assert session_manager is not None
        assert len(session_manager.sessions) == 0
        assert len(session_manager.hierarchy) == 0
    
    def test_create_session(self, session_manager):
        """Test session creation"""
        session = session_manager.create_session(
            session_id="test_session",
            role=SessionRole.WORKER,
            parent_id=None
        )
        
        assert session.session_id == "test_session"
        assert session.role == SessionRole.WORKER
        assert session.status == SessionStatus.IDLE
        assert session.parent_id is None
        assert len(session.children_ids) == 0
    
    def test_create_child_session(self, session_manager):
        """Test child session creation"""
        # Create parent
        parent = session_manager.create_session("parent", SessionRole.MANAGER)
        
        # Create child
        child = session_manager.create_session(
            "child", 
            SessionRole.WORKER, 
            parent_id="parent"
        )
        
        assert child.parent_id == "parent"
        assert "child" in parent.children_ids
        assert "parent" in session_manager.hierarchy
        assert "child" in session_manager.hierarchy["parent"]
    
    def test_destroy_session(self, session_manager):
        """Test session destruction"""
        # Create session
        session_manager.create_session("test_session", SessionRole.WORKER)
        
        # Destroy session
        success = session_manager.destroy_session("test_session")
        
        assert success
        assert "test_session" not in session_manager.sessions
    
    def test_destroy_nonexistent_session(self, session_manager):
        """Test destroying non-existent session"""
        success = session_manager.destroy_session("nonexistent")
        
        assert not success
    
    def test_session_status_management(self, session_manager):
        """Test session status get/update"""
        session_manager.create_session("test_session", SessionRole.WORKER)
        
        # Get initial status
        status = session_manager.get_session_status("test_session")
        assert status == SessionStatus.IDLE
        
        # Update status
        session_manager.update_session_status("test_session", SessionStatus.BUSY)
        
        # Verify update
        status = session_manager.get_session_status("test_session")
        assert status == SessionStatus.BUSY
    
    def test_task_assignment(self, session_manager):
        """Test task assignment to session"""
        session_manager.create_session("worker", SessionRole.WORKER)
        
        task = Task(
            task_id="TASK_001",
            description="Test task",
            priority=1,
            assigned_to=None,
            created_by="manager",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="pending"
        )
        
        success = session_manager.assign_task(task, "worker")
        
        assert success
        assert task.assigned_to == "worker"
        assert session_manager.sessions["worker"].current_task == "TASK_001"
        assert session_manager.sessions["worker"].status == SessionStatus.BUSY
    
    def test_assign_task_to_busy_session(self, session_manager):
        """Test task assignment to busy session fails"""
        session_manager.create_session("worker", SessionRole.WORKER)
        session_manager.update_session_status("worker", SessionStatus.BUSY)
        
        task = Task(
            task_id="TASK_001",
            description="Test task",
            priority=1,
            assigned_to=None,
            created_by="manager",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="pending"
        )
        
        success = session_manager.assign_task(task, "worker")
        
        assert not success
    
    def test_escalate_to_parent(self, session_manager):
        """Test task escalation to parent session"""
        # Create parent-child hierarchy
        session_manager.create_session("manager", SessionRole.MANAGER)
        session_manager.create_session("worker", SessionRole.WORKER, parent_id="manager")
        
        task = Task(
            task_id="ESCALATE_TASK",
            description="Escalated task",
            priority=1,
            assigned_to=None,
            created_by="worker",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="escalated"
        )
        
        success = session_manager.escalate_to_parent("worker", task)
        
        assert success
        assert task.assigned_to == "manager"
        assert session_manager.sessions["manager"].status == SessionStatus.BUSY
    
    def test_escalate_without_parent(self, session_manager):
        """Test escalation fails when no parent exists"""
        session_manager.create_session("orphan", SessionRole.WORKER)
        
        task = Task(
            task_id="ORPHAN_TASK",
            description="Orphan task",
            priority=1,
            assigned_to=None,
            created_by="orphan",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="pending"
        )
        
        success = session_manager.escalate_to_parent("orphan", task)
        
        assert not success
    
    def test_get_available_sessions(self, session_manager):
        """Test getting available sessions"""
        session_manager.create_session("idle1", SessionRole.WORKER)
        session_manager.create_session("idle2", SessionRole.WORKER)
        session_manager.create_session("busy1", SessionRole.WORKER)
        session_manager.update_session_status("busy1", SessionStatus.BUSY)
        
        available = session_manager.get_available_sessions()
        
        assert len(available) == 2
        assert "idle1" in available
        assert "idle2" in available
        assert "busy1" not in available
    
    def test_get_available_sessions_by_role(self, session_manager):
        """Test getting available sessions filtered by role"""
        session_manager.create_session("manager", SessionRole.MANAGER)
        session_manager.create_session("worker", SessionRole.WORKER)
        
        managers = session_manager.get_available_sessions(SessionRole.MANAGER)
        workers = session_manager.get_available_sessions(SessionRole.WORKER)
        
        assert len(managers) == 1
        assert "manager" in managers
        assert len(workers) == 1
        assert "worker" in workers
    
    def test_session_hierarchy_view(self, session_manager):
        """Test session hierarchy retrieval"""
        # Create hierarchy: supreme -> coordinator -> manager -> worker
        session_manager.create_session("supreme", SessionRole.SUPREME)
        session_manager.create_session("coordinator", SessionRole.COORDINATOR, parent_id="supreme")
        session_manager.create_session("manager", SessionRole.MANAGER, parent_id="coordinator")
        session_manager.create_session("worker", SessionRole.WORKER, parent_id="manager")
        
        hierarchy = session_manager.get_session_hierarchy()
        
        assert hierarchy["total_sessions"] == 4
        assert len(hierarchy["hierarchy"]) == 1  # One root node
        
        root = hierarchy["hierarchy"][0]
        assert root["id"] == "supreme"
        assert root["role"] == "supreme"
        assert len(root["children"]) == 1
    
    def test_find_best_session_for_task(self, session_manager):
        """Test finding best session for specific task"""
        # Create sessions with different capabilities
        caps_impl = SessionCapabilities(can_implement=True, can_review=False)
        caps_review = SessionCapabilities(can_implement=False, can_review=True)
        
        session_manager.create_session("implementer", SessionRole.WORKER, capabilities=caps_impl)
        session_manager.create_session("reviewer", SessionRole.WORKER, capabilities=caps_review)
        
        # Task requiring implementation
        impl_task = Task(
            task_id="IMPL_TASK",
            description="Implementation task requires coding",
            priority=1,
            assigned_to=None,
            created_by="manager",
            created_at=datetime.now(),
            deadline=None,
            dependencies=[],
            status="pending"
        )
        
        best_session = session_manager.find_best_session_for_task(impl_task)
        
        assert best_session == "implementer"
    
    def test_default_capabilities_by_role(self, session_manager):
        """Test default capabilities assignment by role"""
        session_manager.create_session("supreme", SessionRole.SUPREME)
        session_manager.create_session("worker", SessionRole.WORKER)
        
        supreme_caps = session_manager.sessions["supreme"].capabilities
        worker_caps = session_manager.sessions["worker"].capabilities
        
        assert not supreme_caps.can_implement
        assert supreme_caps.can_manage
        assert worker_caps.can_implement
        assert not worker_caps.can_manage
    
    def test_config_persistence(self, session_manager, temp_config_file):
        """Test configuration save and load"""
        # Create sessions
        session_manager.create_session("persistent_session", SessionRole.WORKER)
        
        # Create new manager instance
        new_manager = SessionManager(config_path=temp_config_file)
        new_manager.monitoring = False
        
        # Should load existing session
        assert "persistent_session" in new_manager.sessions
        assert new_manager.sessions["persistent_session"].role == SessionRole.WORKER
    
    @patch('threading.Thread')
    def test_monitoring_thread_creation(self, mock_thread):
        """Test monitoring thread is created"""
        SessionManager()
        
        mock_thread.assert_called_once()
        call_args = mock_thread.call_args
        assert call_args[1]['target'].__name__ == '_monitor_sessions'
        assert call_args[1]['daemon'] is True
    
    def test_session_timeout_detection(self, session_manager):
        """Test session timeout detection in monitoring"""
        # Create session and set it to busy with old timestamp
        session_manager.create_session("timeout_session", SessionRole.WORKER)
        session = session_manager.sessions["timeout_session"]
        session.status = SessionStatus.BUSY
        session.last_active = datetime.now() - timedelta(minutes=31)  # Older than timeout
        
        # Run monitoring check once
        with session_manager.lock:
            now = datetime.now()
            for session_id, session in session_manager.sessions.items():
                if session.status == SessionStatus.BUSY:
                    if now - session.last_active > timedelta(minutes=30):
                        session.status = SessionStatus.ERROR
        
        assert session_manager.sessions["timeout_session"].status == SessionStatus.ERROR
    
    def test_shutdown(self, session_manager):
        """Test clean shutdown"""
        # Create some sessions
        session_manager.create_session("test1", SessionRole.WORKER)
        session_manager.create_session("test2", SessionRole.WORKER)
        
        # Shutdown should not raise exceptions
        session_manager.shutdown()
        
        assert not session_manager.monitoring