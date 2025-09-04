"""
HooksManager Unit Tests
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hooks_manager import HooksManager, HookContext, CompletionSignal

class TestHooksManager:
    """HooksManager test suite"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "hooks": {
                    "PostToolUse": [],
                    "PreToolUse": [],
                    "Notification": [],
                    "Stop": []
                },
                "patterns": {
                    "todo_completion": r'"status":\s*"completed"',
                    "test_pattern": r'test_success'
                }
            }
            json.dump(config, f)
            yield Path(f.name)
            Path(f.name).unlink()
    
    @pytest.fixture
    def hooks_manager(self, temp_config_file):
        """Create HooksManager instance with temporary config"""
        return HooksManager(config_path=temp_config_file)
    
    def test_init(self, hooks_manager):
        """Test HooksManager initialization"""
        assert hooks_manager is not None
        assert 'PostToolUse' in hooks_manager.handlers
        assert 'PreToolUse' in hooks_manager.handlers
        assert len(hooks_manager.patterns) >= 2
    
    def test_pattern_compilation(self, hooks_manager):
        """Test regex pattern compilation"""
        assert 'todo_completion' in hooks_manager.patterns
        assert 'test_pattern' in hooks_manager.patterns
        
        # Test pattern matching
        todo_pattern = hooks_manager.patterns['todo_completion']
        assert todo_pattern.search('{"status": "completed"}')
        assert not todo_pattern.search('{"status": "pending"}')
    
    def test_completion_detection(self, hooks_manager):
        """Test completion pattern detection"""
        test_output = '{"content": "task1", "status": "completed"}'
        session_id = "test_session"
        
        signals = hooks_manager.detect_completion_patterns(test_output, session_id)
        
        assert len(signals) == 1
        assert signals[0].type == 'todo_completion'
        assert signals[0].session_id == session_id
        assert isinstance(signals[0].timestamp, datetime)
    
    def test_completion_report_generation(self, hooks_manager):
        """Test completion report generation"""
        signal = CompletionSignal(
            type='todo_completion',
            timestamp=datetime.now(),
            session_id='test_session',
            context={'pattern': 'test'},
            raw_output='test output'
        )
        
        report = hooks_manager.generate_completion_report(signal)
        
        assert report.session_id == 'test_session'
        assert report.completion_type == 'todo_completion'
        assert 'タスクが完了しました' in report.summary
        assert len(report.next_actions) > 0
    
    def test_posttool_hook_processing(self, hooks_manager):
        """Test PostToolUse hook processing"""
        context = HookContext(
            hook_type='PostToolUse',
            session_id='test_session',
            tool_name='TodoWrite',
            tool_output='{"status": "completed"}',
            timestamp=datetime.now(),
            metadata={}
        )
        
        result = hooks_manager.process_hook(context)
        
        assert result.success
        assert not result.should_block
        assert len(result.actions) == 1
        assert result.actions[0]['type'] == 'send_report'
    
    def test_pretool_hook_blocking(self, hooks_manager):
        """Test PreToolUse hook blocking functionality"""
        context = HookContext(
            hook_type='PreToolUse',
            session_id='test_session',
            tool_name='system_shutdown',
            tool_output=None,
            timestamp=datetime.now(),
            metadata={}
        )
        
        result = hooks_manager.process_hook(context)
        
        assert result.success
        assert result.should_block
        assert 'blocked' in result.message
    
    def test_handler_registration(self, hooks_manager):
        """Test custom handler registration"""
        def custom_handler(context):
            return Mock(success=True, should_block=False, message="custom", actions=[])
        
        initial_count = len(hooks_manager.handlers['PostToolUse'])
        hooks_manager.register_handler('PostToolUse', custom_handler)
        
        assert len(hooks_manager.handlers['PostToolUse']) == initial_count + 1
    
    def test_multiple_pattern_detection(self, hooks_manager):
        """Test detection of multiple completion patterns"""
        test_output = '{"status": "completed"} test_success implementation completed'
        
        signals = hooks_manager.detect_completion_patterns(test_output, 'test_session')
        
        # Should detect todo_completion and test_pattern
        assert len(signals) >= 2
        types = [s.type for s in signals]
        assert 'todo_completion' in types
        assert 'test_pattern' in types
    
    def test_config_save_load(self, temp_config_file):
        """Test configuration save and load"""
        hm1 = HooksManager(config_path=temp_config_file)
        
        # Modify config
        hm1.config['test_key'] = 'test_value'
        hm1.save_config()
        
        # Load new instance
        hm2 = HooksManager(config_path=temp_config_file)
        
        assert hm2.config.get('test_key') == 'test_value'
    
    def test_error_handling_invalid_pattern(self, temp_config_file):
        """Test error handling for invalid regex patterns"""
        with open(temp_config_file, 'w') as f:
            config = {
                "patterns": {
                    "invalid_pattern": "["  # Invalid regex
                }
            }
            json.dump(config, f)
        
        hm = HooksManager(config_path=temp_config_file)
        
        # Should not crash and should log error
        assert 'invalid_pattern' not in hm.patterns
    
    def test_no_completion_detected(self, hooks_manager):
        """Test case where no completion patterns are detected"""
        test_output = 'regular output without completion markers'
        
        signals = hooks_manager.detect_completion_patterns(test_output, 'test_session')
        
        assert len(signals) == 0
    
    @patch('subprocess.run')
    def test_hook_context_metadata(self, mock_subprocess, hooks_manager):
        """Test hook context with metadata"""
        context = HookContext(
            hook_type='PostToolUse',
            session_id='test_session',
            tool_name='TestTool',
            tool_output='test output',
            timestamp=datetime.now(),
            metadata={'custom_data': 'test_value'}
        )
        
        result = hooks_manager.process_hook(context)
        
        assert result.success
        # Metadata should be preserved in processing
        assert context.metadata['custom_data'] == 'test_value'