"""
DiscordProxy - セッション間Discord通信管理
dpコマンド経由でのメッセージ送信と/resumeコマンド自動実行
"""

import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class DiscordMessage:
    """Discordメッセージデータクラス"""
    session_id: str
    channel_id: Optional[str]
    content: str
    timestamp: datetime
    message_type: str  # work_request, status_update, completion_report
    metadata: Dict[str, Any]

@dataclass
class AutomationCommand:
    """自動実行コマンドデータクラス"""
    command: str
    session_id: str
    delay: int  # 実行前の遅延（秒）
    retry_count: int
    success_pattern: Optional[str]

class DiscordProxy:
    """Discord通信プロキシクラス"""
    
    def __init__(self, bridge_base_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.bridge_base_dir = bridge_base_dir or Path(__file__).parent.parent.parent / 'claude-discord-bridge-server'
        
        # セッションマッピング設定
        self.session_mapping = self._load_session_mapping()
        
        # コマンド履歴
        self.command_history: List[Dict[str, Any]] = []
        
        # dpコマンドのパス
        self.dp_command = self._find_dp_command()
        
        # resumeコマンドのパターン
        self.resume_commands = [
            '/resume',
            '/project-resume',
            '/continue-implementation',
            '/proceed'
        ]
    
    def _load_session_mapping(self) -> Dict[str, str]:
        """セッションマッピングを読み込む"""
        mapping_file = self.bridge_base_dir / 'sessions.json'
        
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    sessions_data = json.load(f)
                    return {str(k): v.get('channel_id', '') for k, v in sessions_data.get('sessions', {}).items()}
            except Exception as e:
                self.logger.error(f"Failed to load session mapping: {e}")
        
        # デフォルトマッピング
        return {
            '1': '1405815779198369903',  # session 1
            '2': '1410119446835630151',  # session 2  
            '3': '1410119561562558534',  # session 3
            '4': ''  # session 4 (no channel configured)
        }
    
    def _find_dp_command(self) -> str:
        """dpコマンドのパスを探す"""
        # 可能なパスを試行
        possible_paths = [
            self.bridge_base_dir / 'src' / 'discord_post.py',
            Path('/home/node/.claude-discord-bridge/src/discord_post.py'),
            Path('./src/discord_post.py')
        ]
        
        for path in possible_paths:
            if path.exists():
                return f"python3 {path}"
        
        self.logger.warning("dp command not found, using fallback")
        return "echo"  # フォールバック
    
    def send_message(self, session_id: str, content: str, 
                    message_type: str = "status_update",
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """指定セッションにメッセージを送信"""
        if metadata is None:
            metadata = {}
        
        try:
            # セッションIDからチャンネルIDを取得
            channel_id = self.session_mapping.get(session_id)
            if not channel_id:
                self.logger.error(f"No channel mapped for session {session_id}")
                return False
            
            # メッセージオブジェクト作成
            message = DiscordMessage(
                session_id=session_id,
                channel_id=channel_id,
                content=content,
                timestamp=datetime.now(),
                message_type=message_type,
                metadata=metadata
            )
            
            # dpコマンドでメッセージ送信
            success = self._execute_dp_command(session_id, content)
            
            # 履歴に記録
            self.command_history.append({
                'type': 'message',
                'data': asdict(message),
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            if success:
                self.logger.info(f"Sent message to session {session_id}: {content[:100]}...")
            else:
                self.logger.error(f"Failed to send message to session {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending message to session {session_id}: {e}")
            return False
    
    def send_work_request(self, target_session: str, request_data: Dict[str, Any]) -> bool:
        """作業依頼書をセッションに送信"""
        # 依頼書を整形
        content = self._format_work_request(request_data)
        
        return self.send_message(
            session_id=target_session,
            content=content,
            message_type="work_request",
            metadata=request_data
        )
    
    def send_completion_report(self, session_id: str, report_data: Dict[str, Any]) -> bool:
        """完了報告書を送信"""
        # 報告書を整形
        content = self._format_completion_report(report_data)
        
        return self.send_message(
            session_id=session_id,
            content=content,
            message_type="completion_report",
            metadata=report_data
        )
    
    def execute_resume_command(self, session_id: str, command: Optional[str] = None) -> bool:
        """resumeコマンドを実行"""
        if command is None:
            command = '/resume'  # デフォルトコマンド
        
        try:
            # resumeコマンドを送信
            success = self.send_message(
                session_id=session_id,
                content=command,
                message_type="automation_command",
                metadata={'command_type': 'resume', 'auto_generated': True}
            )
            
            if success:
                self.logger.info(f"Executed resume command for session {session_id}: {command}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing resume command for session {session_id}: {e}")
            return False
    
    def broadcast_message(self, content: str, exclude_sessions: Optional[List[str]] = None) -> Dict[str, bool]:
        """全セッションにメッセージをブロードキャスト"""
        if exclude_sessions is None:
            exclude_sessions = []
        
        results = {}
        
        for session_id in self.session_mapping.keys():
            if session_id not in exclude_sessions:
                results[session_id] = self.send_message(session_id, content, "broadcast")
        
        success_count = sum(results.values())
        total_count = len(results)
        
        self.logger.info(f"Broadcast complete: {success_count}/{total_count} sessions")
        
        return results
    
    def get_session_status(self) -> Dict[str, Any]:
        """セッション通信ステータスを取得"""
        return {
            'session_mapping': self.session_mapping,
            'dp_command': self.dp_command,
            'command_history_count': len(self.command_history),
            'last_activity': self.command_history[-1]['timestamp'] if self.command_history else None,
            'active_sessions': list(self.session_mapping.keys())
        }
    
    def _execute_dp_command(self, session_id: str, content: str) -> bool:
        """dpコマンドを実行"""
        try:
            # contentをパイプ経由で渡す
            cmd = f'echo "{content}" | {self.dp_command} {session_id}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.bridge_base_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"dp command failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("dp command timed out")
            return False
        except Exception as e:
            self.logger.error(f"dp command execution error: {e}")
            return False
    
    def _format_work_request(self, request_data: Dict[str, Any]) -> str:
        """作業依頼書をDiscordメッセージ形式に整形"""
        content = f"""🔔 **作業依頼書**

**依頼ID**: {request_data.get('request_id', 'N/A')}
**優先度**: {request_data.get('priority', 'Medium')}
**期限**: {request_data.get('deadline', '未指定')}

**タスク内容**:
{request_data.get('task_description', '詳細未指定')}

**要件**:
{self._format_requirements(request_data.get('requirements', []))}

**依存関係**:
{self._format_dependencies(request_data.get('dependencies', []))}

/resume で作業を開始してください。"""
        
        return content
    
    def _format_completion_report(self, report_data: Dict[str, Any]) -> str:
        """完了報告書をDiscordメッセージ形式に整形"""
        content = f"""✅ **作業完了報告書**

**セッション**: {report_data.get('session_id', 'N/A')}
**完了タイプ**: {report_data.get('completion_type', 'N/A')}
**完了時刻**: {report_data.get('timestamp', 'N/A')}

**概要**:
{report_data.get('summary', '詳細なし')}

**詳細**:
{self._format_details(report_data.get('details', {}))}

**次のアクション**:
{self._format_next_actions(report_data.get('next_actions', []))}"""
        
        return content
    
    def _format_requirements(self, requirements: List[str]) -> str:
        """要件リストを整形"""
        if not requirements:
            return "• なし"
        return "\n".join(f"• {req}" for req in requirements)
    
    def _format_dependencies(self, dependencies: List[str]) -> str:
        """依存関係リストを整形"""
        if not dependencies:
            return "• なし"
        return "\n".join(f"• {dep}" for dep in dependencies)
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """詳細情報を整形"""
        if not details:
            return "詳細情報なし"
        
        formatted = []
        for key, value in details.items():
            formatted.append(f"**{key}**: {value}")
        
        return "\n".join(formatted)
    
    def _format_next_actions(self, actions: List[str]) -> str:
        """次のアクションリストを整形"""
        if not actions:
            return "• アクションなし"
        return "\n".join(f"• {action}" for action in actions)
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """コマンド履歴を取得"""
        return self.command_history[-limit:] if self.command_history else []
    
    def clear_history(self):
        """コマンド履歴をクリア"""
        self.command_history.clear()
        self.logger.info("Command history cleared")