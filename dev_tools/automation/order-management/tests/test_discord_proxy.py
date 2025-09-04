"""
DiscordProxy Unit Tests
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from discord_proxy import DiscordProxy, DiscordMessage

class TestDiscordProxy:
    """DiscordProxy test suite"""
    
    @pytest.fixture
    def temp_bridge_dir(self):
        """Create temporary bridge directory with sessions.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_dir = Path(temp_dir)
            
            # Create sessions.json
            sessions_data = {
                "sessions": {
                    "1": {"channel_id": "1405815779198369903"},
                    "2": {"channel_id": "1410119446835630151"},
                    "3": {"channel_id": "1410119561562558534"}
                }
            }
            
            sessions_file = bridge_dir / 'sessions.json'
            with open(sessions_file, 'w') as f:
                json.dump(sessions_data, f)
            
            # Create src directory for discord_post.py
            src_dir = bridge_dir / 'src'
            src_dir.mkdir()
            
            discord_post = src_dir / 'discord_post.py'
            discord_post.write_text('#!/usr/bin/env python3\nprint("Discord post script")')
            
            yield bridge_dir
    
    @pytest.fixture
    def discord_proxy(self, temp_bridge_dir):
        """Create DiscordProxy with temporary bridge directory"""
        return DiscordProxy(bridge_base_dir=temp_bridge_dir)
    
    def test_init(self, discord_proxy, temp_bridge_dir):
        """Test DiscordProxy initialization"""
        assert discord_proxy.bridge_base_dir == temp_bridge_dir
        assert len(discord_proxy.session_mapping) >= 3
        assert '1' in discord_proxy.session_mapping
        assert discord_proxy.session_mapping['1'] == '1405815779198369903'
    
    def test_session_mapping_load(self, discord_proxy):
        """Test session mapping loading from sessions.json"""
        expected_mapping = {
            '1': '1405815779198369903',
            '2': '1410119446835630151', 
            '3': '1410119561562558534'
        }
        
        for session_id, channel_id in expected_mapping.items():
            assert discord_proxy.session_mapping[session_id] == channel_id
    
    @patch('subprocess.run')
    def test_send_message_success(self, mock_subprocess, discord_proxy):
        """Test successful message sending"""
        # Mock successful subprocess call
        mock_subprocess.return_value = Mock(returncode=0)
        
        success = discord_proxy.send_message(
            session_id='1',
            content='Test message',
            message_type='test'
        )
        
        assert success
        mock_subprocess.assert_called_once()
        
        # Check command history
        assert len(discord_proxy.command_history) == 1
        assert discord_proxy.command_history[0]['success'] is True
    
    @patch('subprocess.run')
    def test_send_message_failure(self, mock_subprocess, discord_proxy):
        """Test failed message sending"""
        # Mock failed subprocess call
        mock_subprocess.return_value = Mock(returncode=1, stderr='Error message')
        
        success = discord_proxy.send_message(
            session_id='1',
            content='Test message'
        )
        
        assert not success
        assert len(discord_proxy.command_history) == 1
        assert discord_proxy.command_history[0]['success'] is False
    
    def test_send_message_invalid_session(self, discord_proxy):
        """Test sending message to invalid session"""
        success = discord_proxy.send_message(
            session_id='999',
            content='Test message'
        )
        
        assert not success
    
    @patch('subprocess.run')
    def test_send_work_request(self, mock_subprocess, discord_proxy):
        """Test sending work request"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        request_data = {
            'request_id': 'REQ_001',
            'priority': 'High',
            'deadline': '2025-08-30',
            'task_description': 'Implement user authentication',
            'requirements': ['security', 'performance'],
            'dependencies': ['database_setup']
        }
        
        success = discord_proxy.send_work_request('1', request_data)
        
        assert success
        mock_subprocess.assert_called_once()
        
        # Check that formatted message contains key information
        call_args = mock_subprocess.call_args[0][0]
        assert 'REQ_001' in call_args
        assert 'Implement user authentication' in call_args
        assert '/resume' in call_args
    
    @patch('subprocess.run')
    def test_send_completion_report(self, mock_subprocess, discord_proxy):
        """Test sending completion report"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        report_data = {
            'session_id': 'session_1',
            'completion_type': 'implementation_done',
            'timestamp': '2025-08-29T10:00:00Z',
            'summary': 'Authentication module implemented',
            'details': {'files_created': ['auth.py', 'test_auth.py']},
            'next_actions': ['Run tests', 'Code review']
        }
        
        success = discord_proxy.send_completion_report('1', report_data)
        
        assert success
        mock_subprocess.assert_called_once()
        
        # Check message formatting
        call_args = mock_subprocess.call_args[0][0]
        assert '作業完了報告書' in call_args
        assert 'session_1' in call_args
        assert 'Authentication module implemented' in call_args
    
    @patch('subprocess.run')
    def test_execute_resume_command(self, mock_subprocess, discord_proxy):
        """Test executing resume command"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        success = discord_proxy.execute_resume_command('1')
        
        assert success
        mock_subprocess.assert_called_once()
        
        # Check that resume command was sent
        call_args = mock_subprocess.call_args[0][0]
        assert '/resume' in call_args
        
        # Check history metadata
        assert len(discord_proxy.command_history) == 1
        history_item = discord_proxy.command_history[0]
        assert history_item['data']['message_type'] == 'automation_command'
        assert history_item['data']['metadata']['command_type'] == 'resume'
        assert history_item['data']['metadata']['auto_generated'] is True
    
    @patch('subprocess.run')
    def test_execute_custom_resume_command(self, mock_subprocess, discord_proxy):
        """Test executing custom resume command"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        custom_command = '/project-resume'
        success = discord_proxy.execute_resume_command('1', custom_command)
        
        assert success
        
        # Check custom command was used
        call_args = mock_subprocess.call_args[0][0]
        assert '/project-resume' in call_args
    
    @patch('subprocess.run')
    def test_broadcast_message(self, mock_subprocess, discord_proxy):
        """Test broadcasting message to all sessions"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        results = discord_proxy.broadcast_message('System announcement')
        
        # Should send to all configured sessions (1, 2, 3)
        assert len(results) == 3
        assert all(results.values())  # All should succeed
        assert mock_subprocess.call_count == 3
    
    @patch('subprocess.run') 
    def test_broadcast_message_with_exclusions(self, mock_subprocess, discord_proxy):
        """Test broadcasting with excluded sessions"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        results = discord_proxy.broadcast_message(
            'Announcement', 
            exclude_sessions=['2']
        )
        
        # Should exclude session 2
        assert len(results) == 2
        assert '1' in results
        assert '3' in results
        assert '2' not in results
    
    def test_get_session_status(self, discord_proxy):
        """Test getting session status"""
        status = discord_proxy.get_session_status()
        
        assert 'session_mapping' in status
        assert 'dp_command' in status
        assert 'command_history_count' in status
        assert 'active_sessions' in status
        
        assert status['command_history_count'] == 0
        assert len(status['active_sessions']) >= 3
    
    def test_format_work_request(self, discord_proxy):
        """Test work request formatting"""
        request_data = {
            'request_id': 'REQ_001',
            'priority': 'High',
            'deadline': '2025-08-30',
            'task_description': 'Implement feature X',
            'requirements': ['req1', 'req2'],
            'dependencies': ['dep1']
        }
        
        formatted = discord_proxy._format_work_request(request_data)
        
        assert '作業依頼書' in formatted
        assert 'REQ_001' in formatted
        assert 'High' in formatted
        assert 'Implement feature X' in formatted
        assert 'req1' in formatted
        assert 'dep1' in formatted
        assert '/resume' in formatted
    
    def test_format_completion_report(self, discord_proxy):
        """Test completion report formatting"""
        report_data = {
            'session_id': 'session_1',
            'completion_type': 'implementation_done', 
            'timestamp': '2025-08-29T10:00:00Z',
            'summary': 'Task completed',
            'details': {'key': 'value'},
            'next_actions': ['action1', 'action2']
        }
        
        formatted = discord_proxy._format_completion_report(report_data)
        
        assert '作業完了報告書' in formatted
        assert 'session_1' in formatted
        assert 'implementation_done' in formatted
        assert 'Task completed' in formatted
        assert 'action1' in formatted
    
    def test_format_requirements(self, discord_proxy):
        """Test requirements list formatting"""
        # Empty requirements
        formatted = discord_proxy._format_requirements([])
        assert formatted == '• なし'
        
        # With requirements
        formatted = discord_proxy._format_requirements(['req1', 'req2'])
        assert '• req1' in formatted
        assert '• req2' in formatted
    
    def test_format_dependencies(self, discord_proxy):
        """Test dependencies list formatting"""
        # Empty dependencies
        formatted = discord_proxy._format_dependencies([])
        assert formatted == '• なし'
        
        # With dependencies
        formatted = discord_proxy._format_dependencies(['dep1', 'dep2'])
        assert '• dep1' in formatted
        assert '• dep2' in formatted
    
    def test_get_command_history(self, discord_proxy):
        """Test command history retrieval"""
        # Add some history
        discord_proxy.command_history = [
            {'type': 'test1', 'timestamp': '2025-08-29T10:00:00Z'},
            {'type': 'test2', 'timestamp': '2025-08-29T10:01:00Z'},
            {'type': 'test3', 'timestamp': '2025-08-29T10:02:00Z'}
        ]
        
        # Get limited history
        history = discord_proxy.get_command_history(limit=2)
        
        assert len(history) == 2
        assert history[0]['type'] == 'test2'  # Latest first
        assert history[1]['type'] == 'test3'
    
    def test_clear_history(self, discord_proxy):
        """Test clearing command history"""
        # Add history
        discord_proxy.command_history = [{'type': 'test'}]
        
        # Clear history
        discord_proxy.clear_history()
        
        assert len(discord_proxy.command_history) == 0
    
    def test_find_dp_command_fallback(self, temp_bridge_dir):
        """Test fallback when dp command not found"""
        # Remove the discord_post.py file
        discord_post = temp_bridge_dir / 'src' / 'discord_post.py'
        discord_post.unlink()
        
        proxy = DiscordProxy(bridge_base_dir=temp_bridge_dir)
        
        # Should fallback to echo
        assert proxy.dp_command == 'echo'
    
    @patch('subprocess.run')
    def test_subprocess_timeout(self, mock_subprocess, discord_proxy):
        """Test subprocess timeout handling"""
        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired('cmd', 30)
        
        success = discord_proxy.send_message('1', 'test')
        
        assert not success
    
    @patch('subprocess.run')
    def test_subprocess_exception(self, mock_subprocess, discord_proxy):
        """Test subprocess exception handling"""
        # Mock general exception
        mock_subprocess.side_effect = Exception('Test error')
        
        success = discord_proxy.send_message('1', 'test')
        
        assert not success