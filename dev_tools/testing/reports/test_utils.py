#!/usr/bin/env python3
"""
Test Utilities for Multi-Session Test Framework
Common utilities, helpers, and base classes for test automation
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import threading
import psutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables from .env file
def load_env_from_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment at module import
load_env_from_file()

def get_test_channel_ids():
    """Get test channel IDs from environment variables"""
    return {
        1: os.getenv('CC_DISCORD_CHANNEL_ID_002', '1405815779198369903'),  # Default session (existing)
        2: os.getenv('CC_DISCORD_CHANNEL_ID_002', '1405815779198369903'),   # Channel A (reuse existing for now)
        3: os.getenv('CC_DISCORD_CHANNEL_ID_002_B', ''),                     # Channel B
        4: os.getenv('CC_DISCORD_CHANNEL_ID_002_C', '')                      # Channel C
    }

def validate_test_environment():
    """Validate that required environment variables are set"""
    channel_ids = get_test_channel_ids()
    missing_channels = []
    
    for session_id, channel_id in channel_ids.items():
        if not channel_id or channel_id.strip() == '':
            missing_channels.append(f"Session {session_id}")
            
    if missing_channels:
        return False, f"Missing channel IDs for: {', '.join(missing_channels)}"
        
    return True, "All channel IDs configured"

@dataclass
class TestResult:
    """Test execution result container"""
    suite_name: str
    passed_tests: int
    total_tests: int
    passed: bool
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)

class TestFramework:
    """Base test framework with common utilities"""
    
    def __init__(self):
        self.temp_dir = Path('tests/temp')
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.original_dir = os.getcwd()
        
    def create_temp_file(self, content: str, suffix: str = '.tmp') -> Path:
        """Create temporary file with content"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix=suffix, dir=self.temp_dir, delete=False
        )
        temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)
        
    def run_command(self, cmd: List[str], cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
        """Run shell command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd or self.original_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)
            
    def wait_for_file(self, filepath: Path, timeout: int = 30) -> bool:
        """Wait for file to exist"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if filepath.exists():
                return True
            time.sleep(0.1)
        return False
        
    def wait_for_condition(self, condition_func, timeout: int = 30, interval: float = 0.5) -> bool:
        """Wait for condition function to return True"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False
        
    def measure_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
        
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system resource metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'available_memory_mb': psutil.virtual_memory().available / 1024 / 1024
        }

class SessionTestHelper:
    """Helper for session-related test operations"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_sessions = {}  # Track test sessions for cleanup
        
    def create_test_session(self, session_id: int, channel_id: str) -> bool:
        """Create a test session configuration"""
        sessions_file = Path('config/sessions.json')
        
        try:
            # Load existing sessions
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
            else:
                sessions = {}
                
            # Add test session
            sessions[str(session_id)] = channel_id
            self.test_sessions[session_id] = channel_id
            
            # Write updated sessions
            with open(sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Failed to create test session {session_id}: {e}")
            return False
            
    def remove_test_session(self, session_id: int) -> bool:
        """Remove a test session configuration"""
        sessions_file = Path('config/sessions.json')
        
        try:
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
                    
                if str(session_id) in sessions:
                    del sessions[str(session_id)]
                    
                with open(sessions_file, 'w') as f:
                    json.dump(sessions, f, indent=2)
                    
            if session_id in self.test_sessions:
                del self.test_sessions[session_id]
                
            return True
            
        except Exception as e:
            print(f"Failed to remove test session {session_id}: {e}")
            return False
            
    def cleanup_test_sessions(self):
        """Clean up all test sessions created during testing"""
        for session_id in list(self.test_sessions.keys()):
            self.remove_test_session(session_id)
            
    def check_session_exists(self, session_id: int) -> bool:
        """Check if session exists in configuration"""
        sessions_file = Path('config/sessions.json')
        
        try:
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
                return str(session_id) in sessions
        except:
            pass
            
        return False
        
    def get_session_channel(self, session_id: int) -> Optional[str]:
        """Get channel ID for session"""
        sessions_file = Path('config/sessions.json')
        
        try:
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
                return sessions.get(str(session_id))
        except:
            pass
            
        return None

class AttachmentTestHelper:
    """Helper for attachment file test operations"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_files = []  # Track test files for cleanup
        
    def create_test_attachment(self, session_id: int, filename: str, content: str = "test content") -> Path:
        """Create test attachment file in session directory"""
        session_dir = Path(f'attachments/session_{session_id}')
        session_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = session_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
            
        self.test_files.append(file_path)
        return file_path
        
    def create_test_image(self, session_id: int, filename: str = "test_image.png") -> Path:
        """Create test image file (dummy PNG data)"""
        session_dir = Path(f'attachments/session_{session_id}')
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal PNG file (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        file_path = session_dir / filename
        with open(file_path, 'wb') as f:
            f.write(png_data)
            
        self.test_files.append(file_path)
        return file_path
        
    def check_file_exists(self, session_id: int, filename: str) -> bool:
        """Check if file exists in session directory"""
        file_path = Path(f'attachments/session_{session_id}') / filename
        return file_path.exists()
        
    def check_file_isolation(self, session_id: int, filename: str, other_session_ids: List[int]) -> bool:
        """Check that file exists only in specified session directory"""
        # File should exist in specified session
        if not self.check_file_exists(session_id, filename):
            return False
            
        # File should NOT exist in other sessions
        for other_id in other_session_ids:
            if self.check_file_exists(other_id, filename):
                return False
                
        return True
        
    def cleanup_test_files(self):
        """Clean up all test files created during testing"""
        for file_path in self.test_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to clean up {file_path}: {e}")
                
        self.test_files = []
        
    def get_directory_size(self, session_id: int) -> int:
        """Get total size of session directory in bytes"""
        session_dir = Path(f'attachments/session_{session_id}')
        if not session_dir.exists():
            return 0
            
        total_size = 0
        for file_path in session_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                
        return total_size

class TmuxTestHelper:
    """Helper for tmux session test operations"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.test_sessions = []  # Track test tmux sessions
        
    def create_test_tmux_session(self, session_name: str) -> bool:
        """Create test tmux session"""
        returncode, stdout, stderr = self.framework.run_command([
            'tmux', 'new-session', '-d', '-s', session_name
        ])
        
        if returncode == 0:
            self.test_sessions.append(session_name)
            return True
        else:
            print(f"Failed to create tmux session {session_name}: {stderr}")
            return False
            
    def check_tmux_session_exists(self, session_name: str) -> bool:
        """Check if tmux session exists"""
        returncode, stdout, stderr = self.framework.run_command([
            'tmux', 'has-session', '-t', session_name
        ])
        return returncode == 0
        
    def kill_tmux_session(self, session_name: str) -> bool:
        """Kill tmux session"""
        returncode, stdout, stderr = self.framework.run_command([
            'tmux', 'kill-session', '-t', session_name
        ])
        
        if session_name in self.test_sessions:
            self.test_sessions.remove(session_name)
            
        return returncode == 0
        
    def cleanup_test_sessions(self):
        """Clean up all test tmux sessions"""
        for session_name in list(self.test_sessions):
            self.kill_tmux_session(session_name)

class PerformanceTestHelper:
    """Helper for performance testing"""
    
    def __init__(self):
        self.framework = TestFramework()
        
    def measure_response_time(self, func, *args, **kwargs) -> float:
        """Measure function response time"""
        _, execution_time = self.framework.measure_time(func, *args, **kwargs)
        return execution_time
        
    def stress_test_file_operations(self, session_id: int, num_files: int = 20, file_size: int = 1024) -> Dict[str, float]:
        """Stress test file operations"""
        attachment_helper = AttachmentTestHelper()
        
        # Create files
        start_time = time.time()
        files_created = []
        
        for i in range(num_files):
            content = "x" * file_size
            file_path = attachment_helper.create_test_attachment(
                session_id, f"stress_test_{i}.txt", content
            )
            files_created.append(file_path)
            
        creation_time = time.time() - start_time
        
        # Read files
        start_time = time.time()
        for file_path in files_created:
            with open(file_path, 'r') as f:
                f.read()
        read_time = time.time() - start_time
        
        # Cleanup
        attachment_helper.cleanup_test_files()
        
        return {
            'creation_time': creation_time,
            'read_time': read_time,
            'files_per_second_create': num_files / creation_time if creation_time > 0 else 0,
            'files_per_second_read': num_files / read_time if read_time > 0 else 0
        }
        
    def monitor_system_resources(self, duration: float = 30.0, interval: float = 1.0) -> Dict[str, List[float]]:
        """Monitor system resources over time"""
        metrics = {
            'cpu_percent': [],
            'memory_percent': [],
            'disk_percent': []
        }
        
        start_time = time.time()
        while time.time() - start_time < duration:
            current_metrics = self.framework.get_system_metrics()
            metrics['cpu_percent'].append(current_metrics['cpu_percent'])
            metrics['memory_percent'].append(current_metrics['memory_percent'])
            metrics['disk_percent'].append(current_metrics['disk_percent'])
            
            time.sleep(interval)
            
        return metrics

class TestReporter:
    """Test result reporting utilities"""
    
    def __init__(self):
        self.reports_dir = Path('tests/reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def save_test_log(self, suite_name: str, content: str):
        """Save test log to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.reports_dir / f"{suite_name}_log_{timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def save_performance_metrics(self, suite_name: str, metrics: Dict[str, Any]):
        """Save performance metrics to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = self.reports_dir / f"{suite_name}_metrics_{timestamp}.json"
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, default=str)
            
    def generate_suite_summary(self, result: TestResult) -> str:
        """Generate text summary for test suite"""
        status = "PASS" if result.passed else "FAIL"
        
        summary = f"""
=== {result.suite_name} TEST SUMMARY ===
Status: {status}
Tests: {result.passed_tests}/{result.total_tests} passed
Execution Time: {result.execution_time:.2f}s
"""
        
        if result.failures:
            summary += "\nFailures:\n"
            for failure in result.failures:
                summary += f"  - {failure}\n"
                
        if result.warnings:
            summary += "\nWarnings:\n"
            for warning in result.warnings:
                summary += f"  - {warning}\n"
                
        if result.metrics:
            summary += "\nMetrics:\n"
            for key, value in result.metrics.items():
                summary += f"  {key}: {value}\n"
                
        return summary

# Mock Discord API for testing
class MockDiscordAPI:
    """Mock Discord API for testing without real API calls"""
    
    def __init__(self):
        self.messages_sent = []
        self.channels = {}
        
    def send_message(self, channel_id: str, content: str) -> bool:
        """Mock message sending"""
        self.messages_sent.append({
            'channel_id': channel_id,
            'content': content,
            'timestamp': datetime.now()
        })
        return True
        
    def create_channel(self, channel_id: str, name: str = "test-channel") -> bool:
        """Mock channel creation"""
        self.channels[channel_id] = {
            'name': name,
            'created_at': datetime.now()
        }
        return True
        
    def get_last_message(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get last message sent to channel"""
        channel_messages = [msg for msg in self.messages_sent if msg['channel_id'] == channel_id]
        return channel_messages[-1] if channel_messages else None
        
    def clear_history(self):
        """Clear mock API history"""
        self.messages_sent = []
        self.channels = {}