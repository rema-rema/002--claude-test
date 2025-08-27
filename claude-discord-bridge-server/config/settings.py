#!/usr/bin/env python3
"""
設定管理モジュール
Claude-Discord Bridgeの設定を管理する
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List
import configparser

class SettingsManager:
    """設定の読み込み、保存、管理を行うクラス"""
    
    def __init__(self):
        # Support both old and new config directory names for backward compatibility
        old_config_dir = Path.home() / '.claude-cli-toolkit'
        new_config_dir = Path.home() / '.claude-discord-bridge'
        
        # Migrate from old to new if old exists and new doesn't
        if old_config_dir.exists() and not new_config_dir.exists():
            try:
                old_config_dir.rename(new_config_dir)
                print(f"📦 Migrated config directory: {old_config_dir} → {new_config_dir}")
            except Exception as e:
                print(f"⚠️  Failed to migrate config directory: {e}")
                print(f"Using existing: {old_config_dir}")
                self.config_dir = old_config_dir
                self.env_file = self.config_dir / '.env'
                self.sessions_file = self.config_dir / 'sessions.json'
                self.toolkit_root = Path(__file__).parent.parent
                return
        
        # Use new config directory (either migrated or new installation)
        self.config_dir = new_config_dir if new_config_dir.exists() or not old_config_dir.exists() else old_config_dir
        self.env_file = self.config_dir / '.env'
        self.sessions_file = self.config_dir / 'sessions.json'
        self.toolkit_root = Path(__file__).parent.parent
        
    def ensure_config_dir(self):
        """設定ディレクトリを作成"""
        self.config_dir.mkdir(exist_ok=True)
        
    def load_env(self) -> Dict[str, str]:
        """環境変数を読み込み"""
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def save_env(self, env_vars: Dict[str, str]):
        """環境変数を保存"""
        self.ensure_config_dir()
        with open(self.env_file, 'w') as f:
            f.write("# Claude-Discord Bridge Configuration\n")
            f.write("# This file contains sensitive information. Do not share!\n\n")
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Set permissions to 600 (owner read/write only)
        os.chmod(self.env_file, 0o600)
    
    def load_sessions(self) -> Dict[str, str]:
        """セッション設定を読み込み"""
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_sessions(self, sessions: Dict[str, str]):
        """セッション設定を保存"""
        self.ensure_config_dir()
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def get_token(self) -> Optional[str]:
        """Discord bot tokenを取得"""
        env_vars = self.load_env()
        return env_vars.get('DISCORD_BOT_TOKEN')
    
    def set_token(self, token: str):
        """Discord bot tokenを設定"""
        env_vars = self.load_env()
        env_vars['DISCORD_BOT_TOKEN'] = token
        self.save_env(env_vars)
    
    def get_session_channel(self, session_num: int) -> Optional[str]:
        """セッション番号からチャンネルIDを取得"""
        sessions = self.load_sessions()
        return sessions.get(str(session_num))
    
    def add_session(self, channel_id: str) -> int:
        """新しいセッションを追加"""
        sessions = self.load_sessions()
        
        # Find next available session number
        existing_nums = [int(k) for k in sessions.keys() if k.isdigit()]
        next_num = 1
        if existing_nums:
            next_num = max(existing_nums) + 1
        
        sessions[str(next_num)] = channel_id
        self.save_sessions(sessions)
        return next_num
    
    def remove_session(self, session_num: int) -> bool:
        """セッションを削除"""
        sessions = self.load_sessions()
        if str(session_num) in sessions:
            del sessions[str(session_num)]
            self.save_sessions(sessions)
            return True
        return False
    
    def list_sessions(self) -> List[tuple]:
        """全セッションをリスト形式で取得"""
        sessions = self.load_sessions()
        return [(int(num), channel_id) for num, channel_id in sorted(sessions.items(), key=lambda x: int(x[0]))]
    
    def get_default_session(self) -> int:
        """デフォルトセッション番号を取得"""
        env_vars = self.load_env()
        return int(env_vars.get('DEFAULT_SESSION', '1'))
    
    def set_default_session(self, session_num: int):
        """デフォルトセッション番号を設定"""
        env_vars = self.load_env()
        env_vars['DEFAULT_SESSION'] = str(session_num)
        self.save_env(env_vars)
    
    def channel_to_session(self, channel_id: str) -> Optional[int]:
        """チャンネルIDからセッション番号を逆引き"""
        sessions = self.load_sessions()
        for num, ch_id in sessions.items():
            if ch_id == channel_id:
                return int(num)
        return None
    
    def get_port(self, service: str = 'flask') -> int:
        """サービスのポート番号を取得"""
        env_vars = self.load_env()
        port_map = {
            'flask': int(env_vars.get('FLASK_PORT', '5001'))  # macOS ControlCenter対策
        }
        return port_map.get(service, 5000)
    
    def get_claude_work_dir(self) -> str:
        """Claude Codeの作業ディレクトリを取得"""
        env_vars = self.load_env()
        return env_vars.get('CLAUDE_WORK_DIR', os.getcwd())
    
    def get_claude_options(self) -> str:
        """Claude Codeの起動オプションを取得"""
        env_vars = self.load_env()
        return env_vars.get('CLAUDE_OPTIONS', '')
    
    def is_configured(self) -> bool:
        """初期設定が完了しているかチェック"""
        return (self.env_file.exists() and 
                self.get_token() is not None and 
                self.get_token() != 'your_token_here' and
                len(self.list_sessions()) > 0)

if __name__ == "__main__":
    # Test settings manager
    manager = SettingsManager()
    print(f"Config directory: {manager.config_dir}")
    print(f"Is configured: {manager.is_configured()}")
    
    if manager.is_configured():
        print(f"Sessions: {manager.list_sessions()}")
        print(f"Default session: {manager.get_default_session()}")