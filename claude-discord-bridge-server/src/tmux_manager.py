#!/usr/bin/env python3
"""
Tmux Manager - マルチセッション対応tmux管理システム

このモジュールは以下の責任を持つ：
1. 複数Claude Codeセッションの並行管理
2. セッション別tmuxセッション作成・削除
3. セッション死活監視・健康状態管理
4. セッション状態の永続化
5. セッション統計情報提供

拡張性のポイント：
- セッション自動復旧機能
- セッション間通信・連携
- リソース使用量監視
- セッション設定のカスタマイズ
- セッションクラスタリング対応
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from datetime import datetime

# パッケージルートの追加（相対インポート対応）
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SettingsManager

# ログ設定
logger = logging.getLogger(__name__)

class TmuxManager:
    """
    tmuxセッション管理システム（マルチセッション対応）
    
    アーキテクチャ特徴：
    - 複数Claude Codeセッションの並行管理
    - セッション別死活監視
    - 動的セッション追加・削除
    - セッション状態の永続化
    
    将来の拡張：
    - セッション復旧自動化
    - セッション間通信機能
    - リソース使用量監視
    - セッションクラスタリング
    """
    
    # Claude Codeセッション設定
    CLAUDE_SESSION_PREFIX = "claude-session"
    DEFAULT_CLAUDE_OPTIONS = "--dangerously-skip-permissions"
    
    def __init__(self, session_name: str = "claude-discord-bridge"):
        """
        TmuxManagerの初期化
        
        Args:
            session_name: メインセッション名
        """
        self.session_name = session_name
        self.claude_session_prefix = self.CLAUDE_SESSION_PREFIX
        self.settings = SettingsManager()
        self.sessions_cache = {}  # {session_id: session_status}
        self._load_session_states()
        
    def is_session_exists(self) -> bool:
        """tmuxセッションが存在するかチェック"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("Error: tmux is not installed")
            return False
            
    def create_session(self) -> bool:
        """新しいtmuxセッションを作成"""
        if self.is_session_exists():
            print(f"tmux session '{self.session_name}' already exists")
            return True
            
        try:
            # Create new detached session
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", self.session_name],
                check=True
            )
            print(f"✅ Created tmux session: {self.session_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating tmux session: {e}")
            return False
            
    def kill_session(self) -> bool:
        """tmuxセッションを終了"""
        if not self.is_session_exists():
            print(f"tmux session '{self.session_name}' does not exist")
            return True
            
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", self.session_name],
                check=True
            )
            print(f"✅ Killed tmux session: {self.session_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error killing tmux session: {e}")
            return False
            
    def send_command(self, pane: str, command: str) -> bool:
        """tmuxペインにコマンドを送信"""
        if not self.is_session_exists():
            print(f"tmux session '{self.session_name}' does not exist")
            return False
            
        try:
            subprocess.run(
                ["tmux", "send-keys", "-t", f"{self.session_name}:{pane}", command, "Enter"],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error sending command to tmux: {e}")
            return False
            
    def create_panes(self) -> bool:
        """必要なペインを作成"""
        if not self.is_session_exists():
            if not self.create_session():
                return False
                
        try:
            # Split window horizontally
            subprocess.run(
                ["tmux", "split-window", "-h", "-t", f"{self.session_name}:0"],
                check=True
            )
            
            # Split the right pane vertically
            subprocess.run(
                ["tmux", "split-window", "-v", "-t", f"{self.session_name}:0.1"],
                check=True
            )
            
            print("✅ Created tmux panes")
            return True
        except subprocess.CalledProcessError:
            # Panes might already exist
            return True
            
    def attach(self):
        """tmuxセッションにアタッチ"""
        if not self.is_session_exists():
            print(f"tmux session '{self.session_name}' does not exist")
            return
            
        try:
            subprocess.run(["tmux", "attach-session", "-t", self.session_name])
        except subprocess.CalledProcessError as e:
            print(f"Error attaching to tmux session: {e}")
            
    def list_panes(self) -> list:
        """ペインのリストを取得"""
        if not self.is_session_exists():
            return []
            
        try:
            result = subprocess.run(
                ["tmux", "list-panes", "-t", self.session_name, "-F", "#{pane_index}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            return []
        except subprocess.CalledProcessError:
            return []
    
    def _load_session_states(self):
        """
        セッション状態キャッシュの初期化
        
        拡張ポイント：
        - セッション状態の永続化
        - 前回終了時の復旧情報
        - セッション設定の読み込み
        """
        try:
            # 現在稼働中のClaude セッションを検出してキャッシュ更新
            claude_sessions = self.list_claude_sessions()
            for session_id, session_name in claude_sessions:
                self.sessions_cache[session_id] = {
                    'status': 'active',
                    'session_name': session_name,
                    'last_checked': datetime.now().isoformat()
                }
            logger.info(f"Loaded {len(claude_sessions)} active Claude sessions")
        except Exception as e:
            logger.error(f"Failed to load session states: {e}")
            self.sessions_cache = {}
    
    def create_claude_session(self, session_id: int, work_dir: str, options: str = None) -> bool:
        """
        Claude Code用のtmuxセッション作成（マルチセッション対応）
        
        拡張ポイント：
        - セッション別設定管理
        - 起動前環境チェック
        - セッション復旧機能
        
        Args:
            session_id: セッション番号
            work_dir: 作業ディレクトリ
            options: Claude Code オプション（None時はデフォルト使用）
            
        Returns:
            bool: 作成成功フラグ
        """
        session_name = f"{self.claude_session_prefix}-{session_id}"
        
        # 既存セッション確認
        if self.is_claude_session_exists(session_id):
            logger.info(f"Claude session {session_id} already exists")
            return True
        
        try:
            # オプション設定
            claude_options = options if options is not None else self.DEFAULT_CLAUDE_OPTIONS
            
            # Claude Code コマンド構築
            claude_cmd = f"cd \"{work_dir}\" && claude {claude_options}".strip()
            
            # tmuxセッション作成
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session_name, claude_cmd],
                check=True
            )
            
            # セッション状態更新
            self.sessions_cache[session_id] = {
                'status': 'active',
                'session_name': session_name,
                'work_dir': work_dir,
                'options': claude_options,
                'created_at': datetime.now().isoformat(),
                'last_checked': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully created Claude session {session_id}: {session_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Claude session {session_id}: {e}")
            return False
    
    def is_claude_session_exists(self, session_id: int) -> bool:
        """
        Claude Codeセッション存在チェック（マルチセッション対応）
        
        Args:
            session_id: セッション番号
            
        Returns:
            bool: セッション存在フラグ
        """
        session_name = f"{self.claude_session_prefix}-{session_id}"
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                capture_output=True
            )
            exists = result.returncode == 0
            
            # セッション状態キャッシュ更新
            if session_id in self.sessions_cache:
                self.sessions_cache[session_id]['last_checked'] = datetime.now().isoformat()
                if not exists:
                    self.sessions_cache[session_id]['status'] = 'stopped'
            
            return exists
        except FileNotFoundError:
            logger.error("tmux is not installed")
            return False
    
    def kill_claude_session(self, session_id: int) -> bool:
        """
        Claude Codeセッション終了（マルチセッション対応）
        
        Args:
            session_id: セッション番号
            
        Returns:
            bool: 終了成功フラグ
        """
        session_name = f"{self.claude_session_prefix}-{session_id}"
        
        if not self.is_claude_session_exists(session_id):
            logger.info(f"Claude session {session_id} does not exist")
            return True
            
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", session_name],
                check=True
            )
            
            # セッション状態更新
            if session_id in self.sessions_cache:
                self.sessions_cache[session_id]['status'] = 'stopped'
                self.sessions_cache[session_id]['last_checked'] = datetime.now().isoformat()
            
            logger.info(f"Successfully killed Claude session {session_id}: {session_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to kill Claude session {session_id}: {e}")
            return False
    
    def kill_all_claude_sessions(self) -> Tuple[bool, List[int]]:
        """
        全Claude Codeセッション終了（マルチセッション対応）
        
        Returns:
            Tuple[bool, List[int]]: (成功フラグ, 終了されたセッション番号リスト)
        """
        killed_sessions = []
        try:
            # 現在のClaude セッションリスト取得
            claude_sessions = self.list_claude_sessions()
            
            for session_id, session_name in claude_sessions:
                try:
                    subprocess.run(["tmux", "kill-session", "-t", session_name], check=True)
                    
                    # セッション状態更新
                    if session_id in self.sessions_cache:
                        self.sessions_cache[session_id]['status'] = 'stopped'
                        self.sessions_cache[session_id]['last_checked'] = datetime.now().isoformat()
                    
                    killed_sessions.append(session_id)
                    logger.info(f"Killed Claude session {session_id}: {session_name}")
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to kill session {session_id}: {e}")
                    continue
            
            logger.info(f"Successfully killed {len(killed_sessions)} Claude sessions")
            return True, killed_sessions
            
        except Exception as e:
            logger.error(f"Error during kill all Claude sessions: {e}")
            return False, killed_sessions
    
    def list_claude_sessions(self) -> List[Tuple[int, str]]:
        """
        Claude Codeセッションリスト取得（マルチセッション対応）
        
        Returns:
            List[Tuple[int, str]]: (セッション番号, セッション名) のリスト
        """
        sessions = []
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                all_sessions = result.stdout.strip().split('\n')
                claude_sessions = [s for s in all_sessions if s.startswith(self.claude_session_prefix)]
                
                for session in claude_sessions:
                    try:
                        # セッション番号抽出
                        session_id = int(session.split('-')[-1])
                        sessions.append((session_id, session))
                        
                        # セッション状態キャッシュ更新
                        if session_id not in self.sessions_cache:
                            self.sessions_cache[session_id] = {}
                        
                        self.sessions_cache[session_id].update({
                            'status': 'active',
                            'session_name': session,
                            'last_checked': datetime.now().isoformat()
                        })
                        
                    except ValueError:
                        logger.warning(f"Invalid session name format: {session}")
                        continue
                        
                sessions.sort(key=lambda x: x[0])
            
            logger.debug(f"Found {len(sessions)} Claude sessions")
            return sessions
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list Claude sessions: {e}")
            return []

    def get_session_stats(self) -> Dict[str, any]:
        """
        セッション統計情報取得
        
        Returns:
            Dict[str, any]: セッション統計情報
        """
        try:
            claude_sessions = self.list_claude_sessions()
            active_count = len(claude_sessions)
            
            return {
                'total_sessions': len(self.sessions_cache),
                'active_sessions': active_count,
                'session_list': [s[0] for s in claude_sessions],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                'total_sessions': 0,
                'active_sessions': 0,
                'session_list': [],
                'error': str(e)
            }
    
    def check_session_health(self, session_id: int) -> bool:
        """
        セッション健康状態チェック
        
        Args:
            session_id: セッション番号
            
        Returns:
            bool: 健康フラグ
        """
        try:
            is_healthy = self.is_claude_session_exists(session_id)
            
            if session_id in self.sessions_cache:
                self.sessions_cache[session_id]['status'] = 'active' if is_healthy else 'error'
                self.sessions_cache[session_id]['last_checked'] = datetime.now().isoformat()
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for session {session_id}: {e}")
            return False
    
    def recover_session(self, session_id: int, max_retries: int = 3) -> bool:
        """
        セッション復旧機能（SessionManagerとの連携）
        
        Args:
            session_id: 復旧するセッション番号
            max_retries: 最大リトライ回数
            
        Returns:
            bool: 復旧成功フラグ
        """
        logger.info(f"Starting recovery for session {session_id} (max_retries: {max_retries})")
        
        # 既存セッション強制終了
        try:
            self.kill_claude_session(session_id)
        except Exception as e:
            logger.warning(f"Failed to kill existing session {session_id}: {e}")
        
        # リトライループ
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Recovery attempt {attempt}/{max_retries} for session {session_id}")
                
                # セッション情報取得（キャッシュから）
                if session_id not in self.sessions_cache:
                    logger.error(f"Session {session_id} not found in cache - cannot recover")
                    return False
                
                session_info = self.sessions_cache[session_id]
                work_dir = session_info.get('work_dir', '/workspaces/002--claude-test')
                options = session_info.get('options', self.DEFAULT_CLAUDE_OPTIONS)
                
                # セッション再作成
                success = self.create_claude_session(session_id, work_dir, options)
                
                if success:
                    # 健康状態チェック
                    if self.check_session_health(session_id):
                        # セッション状態更新
                        self.sessions_cache[session_id].update({
                            'status': 'recovered',
                            'recovery_count': self.sessions_cache[session_id].get('recovery_count', 0) + 1,
                            'last_recovery': datetime.now().isoformat(),
                            'recovery_attempt': attempt
                        })
                        
                        logger.info(f"✅ Session {session_id} recovered successfully (attempt {attempt})")
                        return True
                    else:
                        logger.warning(f"Session {session_id} created but health check failed")
                else:
                    logger.error(f"Failed to create session {session_id} on attempt {attempt}")
                
            except Exception as e:
                logger.error(f"Recovery attempt {attempt} failed for session {session_id}: {e}")
                
            # 最後の試行でない場合は待機
            if attempt < max_retries:
                import time
                time.sleep(2)  # 2秒待機してリトライ
        
        # 全リトライ失敗
        if session_id in self.sessions_cache:
            self.sessions_cache[session_id].update({
                'status': 'recovery_failed',
                'last_recovery_attempt': datetime.now().isoformat(),
                'recovery_attempts': max_retries
            })
        
        logger.error(f"❌ Failed to recover session {session_id} after {max_retries} attempts")
        return False
    
    def get_session_detailed_status(self, session_id: int) -> Dict[str, any]:
        """
        セッション詳細状態取得
        
        Args:
            session_id: セッション番号
            
        Returns:
            Dict[str, any]: 詳細状態情報
        """
        try:
            # 基本情報
            is_active = self.is_claude_session_exists(session_id)
            cache_info = self.sessions_cache.get(session_id, {})
            
            return {
                'session_id': session_id,
                'session_name': f"{self.claude_session_prefix}-{session_id}",
                'is_active': is_active,
                'status': cache_info.get('status', 'unknown'),
                'work_dir': cache_info.get('work_dir', ''),
                'options': cache_info.get('options', ''),
                'created_at': cache_info.get('created_at', ''),
                'last_checked': cache_info.get('last_checked', ''),
                'last_recovery': cache_info.get('last_recovery', ''),
                'recovery_count': cache_info.get('recovery_count', 0),
                'recovery_attempts': cache_info.get('recovery_attempts', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get detailed status for session {session_id}: {e}")
            return {
                'session_id': session_id,
                'error': str(e),
                'status': 'error'
            }
    
    def get_all_sessions_status(self) -> List[Dict[str, any]]:
        """
        全セッション詳細状態取得
        
        Returns:
            List[Dict[str, any]]: 全セッション状態リスト
        """
        try:
            # 現在のClaude セッションリスト更新
            self.list_claude_sessions()
            
            # 全セッションの詳細状態取得
            all_statuses = []
            session_ids = set(self.sessions_cache.keys())
            
            # 現在稼働中のセッションも追加
            active_sessions = self.list_claude_sessions()
            session_ids.update([s[0] for s in active_sessions])
            
            for session_id in sorted(session_ids):
                status = self.get_session_detailed_status(session_id)
                all_statuses.append(status)
            
            return all_statuses
            
        except Exception as e:
            logger.error(f"Failed to get all sessions status: {e}")
            return []

def setup_tmux_environment():
    """
    tmux環境セットアップ（マルチセッション対応）
    """
    manager = TmuxManager()
    
    # tmuxインストール確認
    if subprocess.run(["which", "tmux"], capture_output=True).returncode != 0:
        print("❌ tmux is not installed. Please install it first.")
        print("  macOS: brew install tmux")
        print("  Ubuntu/Debian: sudo apt-get install tmux")
        return False
    
    # メインセッション作成
    if not manager.create_session():
        return False
        
    if not manager.create_panes():
        return False
        
    print("✅ tmux environment is ready")
    print(f"  Main session: tmux attach -t {manager.session_name}")
    print(f"  Claude sessions: use create_claude_session() method")
    
    return True

# テスト・デバッグ用関数  
def test_tmux_manager():
    """
    TmuxManagerの動作テスト（マルチセッション・復旧機能付き）
    """
    try:
        manager = TmuxManager()
        
        print("=== TmuxManager Multi-Session Test ===")
        print(f"Main session: {manager.session_name}")
        print(f"Claude session prefix: {manager.claude_session_prefix}")
        
        # セッション統計表示
        stats = manager.get_session_stats()
        print(f"Session stats: {stats}")
        
        # 現在のClaude セッション表示
        claude_sessions = manager.list_claude_sessions()
        print(f"Current Claude sessions: {claude_sessions}")
        
        # 全セッション詳細状態表示
        all_statuses = manager.get_all_sessions_status()
        print("\n=== Detailed Session Status ===")
        for status in all_statuses:
            print(f"Session {status['session_id']}: {status['status']} - {status.get('work_dir', 'N/A')}")
            if status.get('recovery_count', 0) > 0:
                print(f"  Recovery count: {status['recovery_count']}")
                print(f"  Last recovery: {status.get('last_recovery', 'N/A')}")
        
        # セッション健康状態チェック
        print("\n=== Health Check ===")
        for session_id, _ in claude_sessions:
            health = manager.check_session_health(session_id)
            detailed_status = manager.get_session_detailed_status(session_id)
            print(f"Session {session_id}: {'OK' if health else 'ERROR'}")
            print(f"  Status: {detailed_status['status']}")
            print(f"  Last checked: {detailed_status.get('last_checked', 'N/A')}")
        
        # 復旧機能テスト（コメントアウトして実際の復旧テストを防ぐ）
        # print("\n=== Recovery Test (Commented Out) ===")
        # if claude_sessions:
        #     test_session_id = claude_sessions[0][0]
        #     print(f"Testing recovery for session {test_session_id}...")
        #     recovery_success = manager.recover_session(test_session_id)
        #     print(f"Recovery result: {'SUCCESS' if recovery_success else 'FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    # テスト実行
    test_tmux_manager()