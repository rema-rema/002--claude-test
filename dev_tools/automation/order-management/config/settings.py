"""
Configuration settings for Order Management Server
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class Settings:
    """Centralized settings management for the Order Management Server"""
    
    def __init__(self, env_file: Optional[str] = None):
        self.base_dir = Path(__file__).parent.parent
        self.env_file = env_file or self.base_dir / '.env'
        load_dotenv(self.env_file)
        
        # Directory paths
        self.queue_dir = self.base_dir / 'queue'
        self.active_dir = self.base_dir / 'active'
        self.completed_dir = self.base_dir / 'completed'
        self.templates_dir = self.base_dir / 'templates'
        self.logs_dir = self.base_dir / 'logs'
        
        # Create directories if they don't exist
        for dir_path in [self.queue_dir, self.active_dir, self.completed_dir, 
                         self.templates_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Discord settings
        self.discord_token = os.getenv('CC_DISCORD_TOKEN')
        self.discord_default_channel = os.getenv('CC_DISCORD_CHANNEL_ID')
        
        # Session settings
        self.max_concurrent_sessions = int(os.getenv('MAX_CONCURRENT_SESSIONS', '10'))
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))
        
        # Performance settings
        self.queue_check_interval = int(os.getenv('QUEUE_CHECK_INTERVAL', '5'))
        self.completion_check_patterns = self._load_completion_patterns()
        
        # Hook settings
        self.hooks_config_file = self.base_dir / 'config' / 'hooks.json'
        self.hooks_config = self._load_hooks_config()
    
    def _load_completion_patterns(self) -> Dict[str, str]:
        """Load completion detection patterns"""
        return {
            "todo_completion": r'"status":\s*"completed"',
            "serena_completion": r'mcp__serena__think_about_whether_you_are_done',
            "implementation_done": r'実装完了|implementation\s+completed',
            "test_success": r'All\s+tests\s+passed|テスト成功',
            "build_success": r'Build\s+successful|ビルド成功'
        }
    
    def _load_hooks_config(self) -> Dict[str, Any]:
        """Load hooks configuration from JSON file"""
        if self.hooks_config_file.exists():
            with open(self.hooks_config_file, 'r') as f:
                return json.load(f)
        return {
            "hooks": {
                "PostToolUse": [],
                "PreToolUse": [],
                "Notification": [],
                "Stop": []
            }
        }
    
    def save_hooks_config(self):
        """Save hooks configuration to JSON file"""
        self.hooks_config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.hooks_config_file, 'w') as f:
            json.dump(self.hooks_config, f, indent=2)
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Get configuration for a specific session"""
        return {
            "session_id": session_id,
            "queue_dir": str(self.queue_dir / session_id),
            "active_dir": str(self.active_dir / session_id),
            "completed_dir": str(self.completed_dir / session_id),
            "timeout": self.session_timeout
        }

# Global settings instance
settings = Settings()